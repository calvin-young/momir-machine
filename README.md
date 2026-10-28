# Momir Vig Machine

A Raspberry Pi and a thermal receipt printer that prints a random creature card for Momir Vig. Set a mana value on the dial, press the button, and a card comes out.

<!-- PHOTO: save the photo as docs/images/machine.jpg, then uncomment the line below.
![The Momir Vig machine](docs/images/machine.jpg)
-->

## What is Momir Vig?

Momir Vig is a casual Magic: The Gathering format built around one card's ability: discard a card and pay X to create a token copy of a random creature with mana value X. The machine does the random part and prints the creature, so you can use it as the token.

## Features

- Dial a mana value from 0 to 16, press the button, and get a random creature card: art, type line, rules text, and power/toughness. Double-faced cards come out with a fold line.
- Toggle Universes Beyond cards on or off.
- Toggle a Pauper-only pool.
- Print a reference sheet.
- Look up a specific card from the command line.

## Quick start

1. Build the card catalog once, on any computer. See [docs/SETUP.md](docs/SETUP.md#build-the-catalog).
2. Install the software on the Pi. See [docs/SETUP.md](docs/SETUP.md#on-the-pi).
3. Run it:

   ```bash
   python3 main.py
   ```

## Controls

The dial is two digits: tens (0 or 1) and ones (0 to 9).

| Dial | Press the button and... |
| --- | --- |
| 0 to 16 | Print a random creature with that mana value |
| 17 | Toggle the Pauper-only pool |
| 18 | Toggle Universes Beyond cards |
| 19 | Print the reference sheet |

## How it works

At boot, the machine prints a startup slip, loads the creature catalog, and prints a "ready" slip. Each press reads the dial, picks a random card from the catalog for that mana value (after the Universes Beyond and Pauper filters), and prints it. The button is ignored for two seconds after each print, and the LED blinks during that time.

Card art is pre-processed into 384-pixel-wide, 1-bit dithered images for the printer. The catalog is built ahead of time from Scryfall data. The Pi only reads it. [docs/DECISIONS.md](docs/DECISIONS.md) explains why it's built this way.

## Documentation

- [Hardware](docs/HARDWARE.md): parts list, wiring, and pinout
- [Setup](docs/SETUP.md): building the catalog, installing on the Pi, running it
- [Decisions](docs/DECISIONS.md): design choices, known issues, and open questions
- [Contributing](CONTRIBUTING.md)

## Status

Version 1.0. It works, and it's a hobby project, so expect rough edges. The hardware and printer settings are specific to this build. Known issues are listed in [docs/DECISIONS.md](docs/DECISIONS.md#issues-and-inconsistencies).

## Prior art

When I started, there were already a few Momir Vig machines on GitHub. I thought about forking one, but I decided to start from scratch and learn as I went. These projects inspired this one:

- [Online version](https://ape3000.com/momir/)
- [Basic printer version](https://github.com/MoritzHayden/momir-basic-printer)
- [Deluxe printer version](https://www.reddit.com/r/magicTCG/comments/1tdpp16/the_tiny_mtg_printer_i_made_now_has_a_full_guide/)

## License

To be decided.

## Disclaimer

This is an unofficial fan project. Magic: The Gathering is a trademark of Wizards of the Coast, and this project isn't affiliated with or endorsed by them. Card data comes from [Scryfall](https://scryfall.com).

Made by [Calvin Young](https://github.com/calvin-young).
