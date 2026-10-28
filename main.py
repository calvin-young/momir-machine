#!/usr/bin/env python3

from momir import Momir
import sys
import time
import lgpio

# Pins (BCM numbering)
PIN_COUNT_X0 = 25
PIN_COUNT_X1 = 8
PIN_COUNT_X2 = 7
PIN_COUNT_X3 = 12
PIN_COUNT_X4 = 16
PIN_COUNT_X5 = 20
PIN_COUNT_X6 = 21
PIN_COUNT_X7 = 5
PIN_COUNT_X8 = 6
PIN_COUNT_X9 = 13
PIN_COUNT_0X = 19
PIN_COUNT_1X = 26
PIN_SWITCH = 24
PIN_BUTTON = 14
PIN_LED = 4

COUNT_ONES = [PIN_COUNT_X0, PIN_COUNT_X1, PIN_COUNT_X2, PIN_COUNT_X3, PIN_COUNT_X4,
            PIN_COUNT_X5, PIN_COUNT_X6, PIN_COUNT_X7, PIN_COUNT_X8, PIN_COUNT_X9]
COUNT_TENS = [PIN_COUNT_0X, PIN_COUNT_1X]

# Constants
BUSY_TIME = 2.00

def init_gpio():
    h = lgpio.gpiochip_open(0)
    for pin in COUNT_ONES + COUNT_TENS + [PIN_BUTTON, PIN_SWITCH]:
        lgpio.gpio_claim_input(h, pin, lgpio.SET_PULL_UP)
    lgpio.gpio_claim_output(h, PIN_LED)
    return h

def read_digit(pins):
    for digit, pin in enumerate(pins):
        if lgpio.gpio_read(h, pin) == 0:
            return digit
    return None

def read_count():
    ones = read_digit(COUNT_ONES)
    tens = read_digit(COUNT_TENS)
    return None if None in (ones, tens) else tens * 10 + ones

if len(sys.argv) > 1:
    momir = Momir()
    name = " ".join(sys.argv[1:])
    card = momir.pick_card_by_name(name)

    if card:
        momir.print_card(card)
    else:
        print(f"Card not found: {name}")

    sys.exit()

if __name__ == '__main__':
    h = init_gpio()
    momir = Momir()
    momir.print_startup()

    # Initialize Variables
    metadata = None
    busy_until = 0.0
    led_state = False
    last_blink = 0.0
    last_button = False

    try:
        while True:
            now = time.monotonic()

            # WAITING - Blink at ~4 Hz
            busy = now < busy_until
            if busy:
                if now - last_blink > 0.125:
                    led_state = not led_state
                    lgpio.gpio_write(h, PIN_LED, led_state)
                    last_blink = now
                time.sleep(0.01)
                continue
            else:
                lgpio.gpio_write(h, PIN_LED, 1)

            # READ SWITCHES
            button = lgpio.gpio_read(h, PIN_BUTTON) == 0
            count = read_count()

            # BUTTON PRESS (falling edge, active-low)
            if button and not last_button:
                momir.button(count)
                busy_until = time.monotonic() + BUSY_TIME

            last_button = button
            time.sleep(0.01)

    finally:
        lgpio.gpiochip_close(h)