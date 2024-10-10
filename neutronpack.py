#!/usr/bin/env python

import gc
import os
import sys
import time

import board
import digitalio
import microcontroller
import neopixel
import pwmio

from code import __version__  # Import __version__ from code.py

# Constants
NEOPIXEL_NUM_PIXELS = 5
NEOPIXEL_BRIGHTNESS = 0.1
THREEWATT_FREQUENCY = 20000
LED_COLOR_SCALE = 65536 / 256

# NeoPixel Setup
strip = neopixel.NeoPixel(board.D5, NEOPIXEL_NUM_PIXELS, brightness=NEOPIXEL_BRIGHTNESS)

# Enable PropMaker FeatherWing
enable = digitalio.DigitalInOut(board.D10)
enable.direction = digitalio.Direction.OUTPUT
enable.value = True

# Setup 3 watt LEDs
threewatt_red = pwmio.PWMOut(board.D11, duty_cycle=0, frequency=THREEWATT_FREQUENCY)
threewatt_green = pwmio.PWMOut(board.D12, duty_cycle=0, frequency=THREEWATT_FREQUENCY)
threewatt_blue = pwmio.PWMOut(board.D13, duty_cycle=0, frequency=THREEWATT_FREQUENCY)


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
            return f"{size:.2f} {unit}"
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

    while True:
        for i in range(255):
            r, g, b = colorwheel(i)
            strip.fill((r, g, b))
            threewatt_red.duty_cycle = int(r * LED_COLOR_SCALE)
            threewatt_green.duty_cycle = int(g * LED_COLOR_SCALE)
            threewatt_blue.duty_cycle = int(b * LED_COLOR_SCALE)
            time.sleep(0.05)
