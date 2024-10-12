#!/usr/bin/env python

import gc
import os
import random
import sys

import adafruit_fancyled.adafruit_fancyled as fancyled
import board
import digitalio
import microcontroller
import neopixel
import pwmio
import supervisor
from analogio import AnalogIn
from watchdog import WatchDogMode

from code import __version__  # Import __version__ from code.py


# Load constants
def load_constants():
    constants = {}

    # Convert environment variable strings to integers where appropriate
    constants['stat_clock_time_ms'] = int(os.getenv('stat_clock_time_ms', "5000"))
    constants['neopixel_stick_pin'] = get_pin(os.getenv('neopixel_stick_pin', "D5"))
    constants['neopixel_stick_size'] = int(os.getenv('neopixel_stick_size', "8"))
    constants['neopixel_stick_brightness'] = float(os.getenv('neopixel_stick_brightness', "0.1"))
    constants['threewatt_frequency'] = int(os.getenv('threewatt_frequency', "20000"))
    constants['watch_dog_timeout_secs'] = int(os.getenv('watch_dog_timeout_secs', "7"))
    constants['power_meter_speed'] = int(os.getenv('power_meter_speed', "50"))
    constants['power_meter_starting_speed'] = int(os.getenv('power_meter_starting_speed', "100"))
    constants['propmaker_featherwing_enable'] = get_pin(os.getenv('propmaker_featherwing_enable', "D10"))

    print(f" - Loaded {len(constants)} constants from settings.toml")
    for i in sorted(constants):
        print(f"    - {i} = {constants[i]}")
    return constants


# State definitions
class State:
    POWER_ON = 1  # Trigger active!
    STANDBY = 2  # Trigger inactive.
    LOOP_IDLE = 3  # Wall power on, hero power off


# Function to get a pin from board module
def get_pin(pin_name):
    try:
        return getattr(board, pin_name)
    except AttributeError:
        raise ValueError(f"Pin {pin_name} not found on board")


def setup_watch_dog(timeout):
    watch_dog = microcontroller.watchdog
    if timeout > 8:  # Hardware maximum of 8 secs
        timeout = 8
    watch_dog.timeout = timeout
    watch_dog.mode = WatchDogMode.RESET
    print(f"- Watch dog released.  Feed every {timeout} seconds or else.")
    watch_dog.feed()  # make sure the dog is fed before turning him loose
    return watch_dog


def format_time(milliseconds):
    seconds = milliseconds // 1000
    milliseconds = milliseconds % 1000
    tenths_of_seconds = milliseconds // 100  # Get the first digit of the milliseconds to represent tenths of a second

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}.{int(tenths_of_seconds)}"


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def print_state(state):
    if state == State.POWER_ON:
        return 'POWER_ON'
    elif state == State.STANDBY:
        return 'STANDBY'
    elif state == State.LOOP_IDLE:
        return 'LOOP_IDLE'
    else:
        return f"? ({state})"


def print_cpu_id():
    # Convert UID bytearray to a hex string and print it
    uid_hex = ':'.join(['{:02x}'.format(x) for x in microcontroller.cpu.uid])
    print(f" - cpu uid: {uid_hex}")


def pretty_print_bytes(size):
    # Define unit thresholds and labels
    units = ["bytes", "KB", "MB", "GB"]
    step = 1024

    # Find the largest unit to express the size in full units
    for unit in units:
        if size < step:
            return f"{size:.2f}{unit}"
        size /= step

    # If size is large, it will be formatted in GB from the loop
    return f"{size:.2f} GB"


def colorwheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return 255 - pos * 3, pos * 3, 0
    elif pos < 170:
        pos -= 85
        return 0, 255 - pos * 3, pos * 3
    else:
        pos -= 170
        return pos * 3, 0, 255 - pos * 3


# From https://learn.adafruit.com/adafruit-feather-m4-express-atsamd51/power-management
def get_voltage(pin):
    return (pin.value * 3.3) / 65536 * 2


# Main loop
def main_loop():
    # Print startup information
    print(f"-=< neutronwand v{__version__} - https://github.com/algrym/neutronwand/ >=-")
    print(f" - uname: {os.uname()}")
    print_cpu_id()
    print(f" -- freq: {microcontroller.cpu.frequency / 1e6} MHz")
    print(f" -- reset reason: {microcontroller.cpu.reset_reason}")
    print(f" -- nvm: {pretty_print_bytes(len(microcontroller.nvm))}")
    print(f" - python v{sys.version}")
    gc.collect()
    starting_memory_free = gc.mem_free()
    print(f" - Free memory: {pretty_print_bytes(starting_memory_free)}")

    # Initialize battery readings before we start beating it up
    vbat_voltage = AnalogIn(board.VOLTAGE_MONITOR)
    print(f" - Battery: {get_voltage(vbat_voltage):.2f}V")

    # Read in constants
    constants = load_constants()

    # Enable PropMaker FeatherWing
    print(f" - PropMaker FeatherWing enabled on {constants['propmaker_featherwing_enable']}")
    enable = digitalio.DigitalInOut(constants['propmaker_featherwing_enable'])
    enable.direction = digitalio.Direction.OUTPUT
    enable.value = True

    # Color constants
    brightness_levels = (0.25, 0.3, 0.15)
    RED = fancyled.gamma_adjust(fancyled.CRGB(255, 0, 0), brightness=brightness_levels).pack()
    ORANGE = fancyled.gamma_adjust(fancyled.CRGB(255, 165, 0), brightness=brightness_levels).pack()
    YELLOW = fancyled.gamma_adjust(fancyled.CRGB(255, 255, 0), brightness=brightness_levels).pack()
    GREEN = fancyled.gamma_adjust(fancyled.CRGB(0, 255, 0), brightness=brightness_levels).pack()
    BLUE = fancyled.gamma_adjust(fancyled.CRGB(0, 0, 255), brightness=brightness_levels).pack()
    PURPLE = fancyled.gamma_adjust(fancyled.CRGB(128, 0, 128), brightness=brightness_levels).pack()
    WHITE = fancyled.gamma_adjust(fancyled.CRGB(255, 255, 255), brightness=brightness_levels).pack()
    ON = (255, 255, 255)
    OFF = (0, 0, 0)
    color_list = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, WHITE]

    # Setup 3 watt LEDs
    threewatt_red = pwmio.PWMOut(board.D11, duty_cycle=0,
                                 frequency=constants['threewatt_frequency'])
    threewatt_green = pwmio.PWMOut(board.D12, duty_cycle=0,
                                   frequency=constants['threewatt_frequency'])
    threewatt_blue = pwmio.PWMOut(board.D13, duty_cycle=0,
                                  frequency=constants['threewatt_frequency'])
    threewatt_color = OFF
    LED_COLOR_SCALE = 65536 / 256

    def set_threewatt_color(color):
        """
        Set the three-watt LED color.

        :param color: The RGB color to set. Can be either a tuple (R, G, B) or an int (packed RGB).
        """
        LED_COLOR_SCALE = 65536 / 256  # Scale factor for PWM (0-255 to 0-65535)

        # If the color is a tuple, unpack the RGB components
        if isinstance(color, tuple):
            red, green, blue = color
        # If the color is an integer (packed RGB), extract the RGB components
        elif isinstance(color, int):
            red = (color >> 16) & 0xFF
            green = (color >> 8) & 0xFF
            blue = color & 0xFF
        else:
            raise ValueError("Color must be either a tuple (R, G, B) or an int (packed RGB)")

        # Convert color components to integers for PWM (scale to 0-65535)
        threewatt_red.duty_cycle = int(red * LED_COLOR_SCALE)  # Red component
        threewatt_green.duty_cycle = int(green * LED_COLOR_SCALE)  # Green component
        threewatt_blue.duty_cycle = int(blue * LED_COLOR_SCALE)  # Blue component

    # Setup Neopixel stick
    print(f" - neopixel v{neopixel.__version__}")
    print(f"   - NeoPixel stick size {constants['neopixel_stick_size']} on {constants['neopixel_stick_pin']}")
    stick_pixels = neopixel.NeoPixel(constants['neopixel_stick_pin'],
                                     constants['neopixel_stick_size'],
                                     brightness=constants['neopixel_stick_brightness'],
                                     pixel_order=neopixel.GRB)  # TODO: this should come from settings.toml
    stick_pixels.fill(OFF)

    watch_dog = setup_watch_dog(constants['watch_dog_timeout_secs'])

    # Initialize power meter counters
    power_meter_speed: int = constants['power_meter_speed']
    next_power_meter_clock: int = 0
    power_meter_max: int = 1
    power_meter_max_previous: int = 0
    power_meter_cursor: int = 1
    power_meter_limit: int = 1

    # Initialize timers and counters
    start_clock: int = supervisor.ticks_ms()
    next_stat_clock: int = supervisor.ticks_ms() + constants['stat_clock_time_ms']
    loop_count: int = 0
    next_watch_dog_clock: int = 0
    current_state = State.STANDBY  # Set once to establish scope

    # State transition
    #
    #   STANDBY = Wall power on, hero power off
    # LOOP_IDLE = Hero power on, trigger inactive.
    #  POWER_ON = Trigger active!
    def state_transition_to(new_state):
        global power_meter_cursor
        print(f"*** Switching from {print_state(current_state)} to {print_state(new_state)}")
        if new_state == State.LOOP_IDLE:  # Hero power on, trigger inactive
            stick_pixels.fill(OFF)
            power_meter_cursor = 0
            set_threewatt_color(OFF)
            pass
        elif new_state == State.STANDBY:  # Wall power on, hero power off
            stick_pixels.fill(OFF)
            power_meter_cursor = 0
            set_threewatt_color(OFF)
        elif new_state == State.POWER_ON:  # Trigger active!  Blast em!
            pass
        else:
            new_state = current_state
        return new_state

    state_transition_to(State.STANDBY)  # Set again to reset state

    # main driver loop
    print("- Starting main driver loop")
    gc.collect()  # garbage collect right before starting the while loop
    while True:
        clock = supervisor.ticks_ms()
        loop_count += 1

        # process the stats output
        if clock > next_stat_clock:
            # DEBUG: Remove this when a real state transition is added
            if current_state == State.STANDBY:
                current_state = state_transition_to(State.LOOP_IDLE)
            elif current_state == State.LOOP_IDLE:
                current_state = state_transition_to(State.POWER_ON)
            else:
                current_state = state_transition_to(State.STANDBY)

            elapsed_time = (clock - start_clock) / 1000  # Convert ms to seconds
            loops_per_second = loop_count / elapsed_time if elapsed_time > 0 else 0
            print(
                f"{format_time(clock - start_clock)} {print_state(current_state)} loop {loop_count:,} at {loops_per_second:.2f} loops/s free={pretty_print_bytes(gc.mem_free())} VBat={get_voltage(vbat_voltage):.2f}V")
            next_stat_clock = clock + constants['stat_clock_time_ms']

        # Periodically feed the watch dog
        if clock > next_watch_dog_clock:
            watch_dog.feed()
            print(
                f"{format_time(clock - start_clock)} watchdog fed, next in {(constants['watch_dog_timeout_secs'] * 0.5)} secs")

            next_watch_dog_clock = clock + (constants['watch_dog_timeout_secs'] * 500)

        # Handle updates by state
        if current_state == State.STANDBY:
            # Blink the Power Meter
            if clock > next_power_meter_clock:
                # Calculate time of next power meter update
                next_power_meter_clock = clock + (power_meter_speed / 100)
                # Blink quietly in STANDBY
                if power_meter_cursor >= 100:
                    stick_pixels[0] = RED
                    power_meter_cursor = 1
                else:
                    stick_pixels[0] = OFF
                    power_meter_cursor += 1

        elif current_state == State.POWER_ON:
            # Trigger active: flash the three-watt LED!
            flash_random = random.randrange(0, 20)
            if flash_random == 0:
                set_threewatt_color(RED)
            elif flash_random == 1:
                set_threewatt_color(BLUE)
            elif flash_random < 10:
                set_threewatt_color(WHITE)
            else:
                set_threewatt_color(OFF)

            # Trigger active: decrement the power meter!
            if clock > next_power_meter_clock:
                # Calculate time of next power meter update
                next_power_meter_clock = clock + (power_meter_speed * 50)
                if power_meter_cursor > 0 and power_meter_cursor < len(stick_pixels):
                    stick_pixels[power_meter_cursor] = OFF
                    stick_pixels[power_meter_max_previous] = ORANGE
                    power_meter_cursor -= 1

        elif current_state == State.LOOP_IDLE:
            # Update the Power Meter
            if clock > next_power_meter_clock:
                # Calculate time of next power meter update
                next_power_meter_clock = clock + power_meter_speed
                # reset if the cursor is over the max
                if power_meter_cursor > power_meter_max:
                    # Increment the limit until we reach maximum
                    if power_meter_limit < (len(stick_pixels) - 1):
                        power_meter_limit += 1
                    elif power_meter_limit > (len(stick_pixels) - 1):
                        power_meter_limit = len(stick_pixels) - 1

                    # Mark the limits and determine the next
                    power_meter_max_previous = clamp(power_meter_max, 0, len(stick_pixels))
                    power_meter_max = random.randrange(0, power_meter_limit)

                    # Blank the meter and start again
                    power_meter_cursor = 0
                    stick_pixels.fill(OFF)

                # turn on the appropriate pixels
                stick_pixels[power_meter_cursor] = ORANGE

                # Next time, try a little higher.
                power_meter_cursor = clamp(power_meter_cursor + 1, 0, len(stick_pixels) - 1)
        else:
            # We shouldn't be in this state
            print(
                f"*** Switching from {print_state(current_state)} to {print_state(State.STANDBY)}")
            current_state = State.STANDBY
