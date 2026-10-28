# Hardware

Parts, wiring, and pinout for version 1.0. This build is specific to these parts.

<!-- PHOTO: save the photo as docs/images/machine-inside.jpg, then uncomment the line below.
![Inside the Momir Vig machine](images/machine-inside.jpg)
-->

## Parts

**Cost per machine** counts only the parts one machine uses. **Cost to buy** is what you pay up front, since several parts only come in multi-packs. Prices are what I paid.

| Part | Used | Unit price | Cost per machine | Sold as | Cost to buy |
| --- | --- | --- | --- | --- | --- |
| [EM5820 58 mm thermal receipt printer module](https://www.amazon.com/dp/B0FCXQPB4V) (USB and serial) | 1 | $30.00 | $30.00 | single | $30.00 |
| [Raspberry Pi Zero W v1.1](https://www.adafruit.com/product/3400) | 1 | $15.00 | $15.00 | single | $15.00 |
| [Panasonic NCR18650GA 18650 Li-ion cell](https://liionwholesale.com/products/panasonic-sanyo-ncr18650ga-flat-top-1?variant=12534245700) (3500 mAh, 10 A) | 2 | $4.44 | $8.88 | single | $8.88 |
| [2S battery protection board (BMS)](https://www.amazon.com/dp/B087M1KJLQ) with cell balancing, 8 A | 1 | $3.50 | $3.50 | 2-pack | $7.00 |
| [USB-C charger board for 2S Li-ion](https://www.amazon.com/dp/B0BRSDS6CS) (5 V in, 8.4 V charge, 2 A) | 1 | $4.00 | $4.00 | single | $4.00 |
| [Mini panel-mount toggle switch](https://www.adafruit.com/product/3221) (SPDT, power) | 1 | $0.95 | $0.95 | single | $0.95 |
| [MT3608 boost converter](https://www.amazon.com/dp/B0HBBPLDN7) (adjustable, for the printer) | 1 | $2.00 | $2.00 | 6-pack | $12.00 |
| [LM2596 buck converter](https://www.amazon.com/dp/B07VVXF7YX) (adjustable, for the Pi) | 1 | $1.20 | $1.20 | 10-pack | $12.00 |
| [Mechanical decade counter](https://www.adafruit.com/product/1082) (thumbwheel digit, 0 to 9) | 2 | $1.50 | $3.00 | 5-pack | $7.50 |
| [LED illuminated triangle pushbutton](https://www.adafruit.com/product/4186) | 1 | $3.95 | $3.95 | single | $3.95 |
| 220 ohm resistor (in series with the button's LED) | 1 | | | | |
| [Micro-USB to mini-USB cable](https://www.amazon.com/dp/B0DJVG778V), 10 in | 1 | $3.00 | $3.00 | 3-pack | $9.00 |
| **Total** | | | **$75.48** | | **$110.28** |

Not counted: the resistor, wire, the enclosure, and the USB-A charger and USB-A to USB-C cable used for charging.

## Wiring

```mermaid
flowchart LR
    wall["USB-A charger<br/>and USB-A to C cable"] --> charger["USB-C 2S charger board"]
    cells["2x 18650 cells"] <--> bms["2S battery<br/>protection board"]
    charger -- "charging" --> bms
    bms --> switch["Power switch"]
    switch --> boost["MT3608 boost<br/>7 V"]
    switch --> buck["LM2596 buck<br/>5 V"]
    boost --> printer["EM5820 printer"]
    buck -- "USB power port" --> pi["Raspberry Pi Zero W"]
    pi -- "USB data port<br/>micro-to-mini cable" --> printer
    dial["2 decade counters<br/>tens 0-1, ones 0-9"] -- "12 GPIO lines" --> pi
    btn["Triangle pushbutton<br/>with LED"] -- "GPIO 14 button<br/>GPIO 4 LED" --> pi
```

- **Power:** The two cells sit in series behind the battery protection board, which guards against overcharge, overdischarge and short circuits, and balances the cells. The power switch sits between the protection board and the two converters, so with the switch off, nothing draws from the cells. Past the switch, the MT3608 boost converter supplies 7 V to the printer, and the LM2596 buck converter supplies 5 V to the Pi through its USB power port.
- **Charging:** A USB-A charger and a USB-A to USB-C cable plug into the charger board, which boosts the 5 V from USB up to 8.4 V to charge the 2S pack. The charger board connects straight to the protection board, ahead of the power switch, so the machine charges with the switch off. It can also run while it charges.
- **Printer:** It connects to the Pi's USB data port with the micro-to-mini cable, for data only. The code finds it by USB ID `28e9:0289`.
- **Dial:** Two [mechanical decade counters](https://www.adafruit.com/product/1082). Each has a common contact and ten digit contacts, and only one digit contact touches the common at a time. The commons go to ground, and each digit goes to a GPIO with the Pi's internal pull-up, so the selected digit reads low. Only the tens counter's 0 and 1 positions are wired.
- **Button:** Active low, with an internal pull-up. The LED runs from GPIO 4 through a 220 ohm resistor. It's lit while the machine is ready, and it blinks while it's busy.
- **Headless:** There's no display, keyboard, or other USB device. Flipping the power switch boots the Pi, and a systemd service starts the program. See [SETUP.md](SETUP.md#start-at-boot).

### Quirks

- **It needs a plain 5 V USB charger.** The charger board accepts 5 V only and doesn't support USB Power Delivery (PD). In practice it won't charge from USB-C chargers, such as a laptop charger. Use a USB-A charger and a USB-A to USB-C cable, which always supply 5 V. The likely cause is that the board lacks the CC pull-down resistors a USB-C charger looks for before it turns on its output. That isn't confirmed for this board.
- **The power switch cuts power hard.** There's no clean shutdown, so the Pi checks its filesystem at every boot. See [DECISIONS.md](DECISIONS.md#boot-time).

## Pinout

BCM numbering. CMC X0 to X9 are the ones digits, and CMC 0X and 1X are the tens.

Key: 🟧 3.3 V · 🟥 5 V · ⬛ ground · 🟨 ID EEPROM (don't use) · 🟦 LED · 🟪 button · 🟩 dial

| Usage | BCM | Pin | Pin | BCM | Usage |
| --- | --- | ---: | :--- | --- | --- |
| | 🟧 3V3 | 1 | 2 | 🟥 5V | |
| | GPIO 2 | 3 | 4 | 🟥 5V | |
| | GPIO 3 | 5 | 6 | ⬛ Ground | 🟪 Button Ground |
| 🟦 LED | GPIO 4 | 7 | 8 | GPIO 14[^uart] | 🟪 Button |
| 🟦 LED Ground | ⬛ Ground | 9 | 10 | GPIO 15[^uart] | |
| | GPIO 17 | 11 | 12 | GPIO 18 | |
| | GPIO 27 | 13 | 14 | ⬛ Ground | |
| | GPIO 22 | 15 | 16 | GPIO 23 | |
| | 🟧 3V3 | 17 | 18 | GPIO 24 | |
| | GPIO 10 | 19 | 20 | ⬛ Ground | |
| | GPIO 9 | 21 | 22 | GPIO 25 | 🟩 CMC X0 |
| | GPIO 11 | 23 | 24 | GPIO 8 | 🟩 CMC X1 |
| | ⬛ Ground | 25 | 26 | GPIO 7 | 🟩 CMC X2 |
| | 🟨 ID_SD | 27 | 28 | 🟨 ID_SC | |
| 🟩 CMC X7 | GPIO 5 | 29 | 30 | ⬛ Ground | |
| 🟩 CMC X8 | GPIO 6 | 31 | 32 | GPIO 12 | 🟩 CMC X3 |
| 🟩 CMC X9 | GPIO 13 | 33 | 34 | ⬛ Ground | 🟩 CMC Ones Ground |
| 🟩 CMC 0X | GPIO 19 | 35 | 36 | GPIO 16 | 🟩 CMC X4 |
| 🟩 CMC 1X | GPIO 26 | 37 | 38 | GPIO 20 | 🟩 CMC X5 |
| 🟩 CMC Tens Ground | ⬛ Ground | 39 | 40 | GPIO 21 | 🟩 CMC X6 |

[^uart]: GPIO 14 and 15 are the Pi's serial port (UART). The button uses GPIO 14, so the serial console has to stay off.
