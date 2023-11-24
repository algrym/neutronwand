#!/usr/bin/env python
# code.py for Neutron Wand

import time

import board
import digitalio
import neopixel
import pwmio

# NeoPixel Strip info
NEOPIXEL_NUM_PIXELS = 5  # NeoPixel strip length (in pixels)
NEOPIXEL_PIN = board.D5
NEOPIXEL_BRIGHTNESS = 0.1

# 3 watt LED info
THREEWATT_PIN_RED = board.D11
THREEWATT_PIN_GREEN = board.D12
THREEWATT_PIN_BLUE = board.D13
THREEWATT_DUTY_CYCLE = 0
THREEWATT_FREQUENCY = 20000

strip = neopixel.NeoPixel(NEOPIXEL_PIN, NEOPIXEL_NUM_PIXELS, brightness=NEOPIXEL_BRIGHTNESS)

# Enable Prop-Maker FeatherWing board
enable = digitalio.DigitalInOut(board.D10)
enable.direction = digitalio.Direction.OUTPUT
enable.value = True


def colorwheel(pos):
    if pos < 0 or pos > 255:
        return 0, 0, 0
    if pos < 85:
        return int(255 - pos * 3), int(pos * 3), 0
    if pos < 170:
        pos -= 85
        return 0, int(255 - pos * 3), int(pos * 3)
    pos -= 170
    return int(pos * 3), 0, int(255 - pos * 3)


# Setup and turn off the 3 watt LED
threewatt_red = pwmio.PWMOut(THREEWATT_PIN_RED,
                             duty_cycle=0,
                             frequency=THREEWATT_FREQUENCY)
threewatt_green = pwmio.PWMOut(THREEWATT_PIN_GREEN,
                               duty_cycle=0,
                               frequency=THREEWATT_FREQUENCY)
threewatt_blue = pwmio.PWMOut(THREEWATT_PIN_BLUE,
                              duty_cycle=0,
                              frequency=THREEWATT_FREQUENCY)

# pre-calculate LED RGB scaling constant
LED_COLOR_SCALE = 65536 / 256

# main - loop forever
while True:
    for i in range(255):
        r, g, b = colorwheel(i)

        strip.fill((r, g, b))

        threewatt_red.duty_cycle = int(r * LED_COLOR_SCALE)
        threewatt_green.duty_cycle = int(g * LED_COLOR_SCALE)
        threewatt_blue.duty_cycle = int(b * LED_COLOR_SCALE)

        time.sleep(0.05)
