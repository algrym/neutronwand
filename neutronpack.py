#!/usr/bin/env python
import time
from digitalio import DigitalInOut, Direction
from board import D5, D10, D11, D12, D13
import neopixel
import pwmio

# Constants
NEOPIXEL_NUM_PIXELS = 5
NEOPIXEL_BRIGHTNESS = 0.1
THREEWATT_FREQUENCY = 20000
LED_COLOR_SCALE = 65536 / 256

# NeoPixel Setup
strip = neopixel.NeoPixel(D5, NEOPIXEL_NUM_PIXELS, brightness=NEOPIXEL_BRIGHTNESS)

# Enable PropMaker FeatherWing
enable = DigitalInOut(D10)
enable.direction = Direction.OUTPUT
enable.value = True

# Setup 3 watt LEDs
threewatt_red = pwmio.PWMOut(D11, duty_cycle=0, frequency=THREEWATT_FREQUENCY)
threewatt_green = pwmio.PWMOut(D12, duty_cycle=0, frequency=THREEWATT_FREQUENCY)
threewatt_blue = pwmio.PWMOut(D13, duty_cycle=0, frequency=THREEWATT_FREQUENCY)

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
while True:
    for i in range(255):
        r, g, b = colorwheel(i)
        strip.fill((r, g, b))
        threewatt_red.duty_cycle = int(r * LED_COLOR_SCALE)
        threewatt_green.duty_cycle = int(g * LED_COLOR_SCALE)
        threewatt_blue.duty_cycle = int(b * LED_COLOR_SCALE)
        time.sleep(0.05)