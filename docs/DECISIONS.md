# Decisions

Why the machine works the way it does, what's still open, and what I found while writing the docs for 1.0. Card counts below come from the catalog on the Pi (18,216 creatures, checked 2026-10-27).

## Creature cards only

We don't want every creature in the game. We only want creatures that can be cast. So we filter out:

- Anything without `Creature` in the type line.
- Tokens.
- Cards that don't exist on paper.

That still leaves creatures that can't be cast, depending on the card's layout. Here's how each layout is handled:

| Layout | Rule | What the code does | Status |
| --- | --- | --- | --- |
| `split` | Either half can be cast. | Keeps the card if the first face is a creature (there are no creature split cards yet). Prints both halves. | Matches |
| `flip` | Cast the top face. The card rotates later. | Keeps the card if the first face is a creature. Prints both faces. | Matches |
| `transform` | Cast the front face. The card flips later. | Keeps the card if the first face is a creature. Prints both faces. | Matches |
| `modal_dfc` | Either face can be cast. | Keeps the card if either face is a creature. Always catalogs the front. Prints the back only if the front text mentions "transform". | Mismatch, but no cards are affected today (issues 4 and 5) |
| `reversible_card` | They're not real. Ignore them. | Not excluded, but none get through today. | Latent (issue 6) |
| `prepare` | The prepared spell can be cast while the creature is on the battlefield, so print it. | Keeps the card if the first face is a creature. Prints the spell half as a back face. | Matches |
| `adventure` | The Adventure is cast from hand, so it doesn't matter once the creature is on the battlefield. Don't print it, unless a card makes it relevant there. | Keeps the card if the first face is a creature. Prints the spell half as a back face. | Mismatch (issue 3) |
| `token` | Tokens are out. | Some get through, because their type line doesn't say "Token". | Bug (issue 2) |

### Modal double-faced cards

- We don't print non-creature sides. They aren't relevant once the card is on the battlefield.
- If both sides are creatures, we need to pick which side to print. Then we decide whether to print the other side.
- As of MOM, tokens *can* transform. So if the face we print can transform, we print the back side. Otherwise we leave it off. You can't flicker a token, after all.
- Moonmist exists, but I don't know of a way to conjure it or force one of these creatures to transform. I'd be excited if we found one!
- Only the front side is reachable right now. Making the back sides reachable means generating fake cards for them. There are 17 cards that need this, and most of them are UB, so I'm leaving it for later.

## Other decisions

- **The catalog is built ahead of time.** A Pi Zero is slow at parsing JSON, so the four scripts build `data/catalog.json` on a bigger machine. The first boot on the Pi writes a trimmed pickle cache next to it, which makes later starts faster.
- **The catalog is trimmed.** Flavor text and unused legalities are dropped to shrink the cache.
- **Art is prepared for the printer.** Each image is converted to grayscale, resized to the printer's 384-pixel width, autocontrasted, brightened, and sharpened, then dithered to 1-bit with Floyd–Steinberg. At print time, art is cropped to a 1.47 aspect ratio.
- **Dial values 17 to 19 are controls.** That leaves 0 to 16 for creature mana values.
- **The startup slip prints before the catalog loads.** The printer responds right away at power-on, and the catalog loads while the slip prints.
- **The button locks out for 2 seconds after each print.** The LED blinks during the lockout. The code doesn't say why. I assume it stops double-prints.
- **Em dashes become hyphens** in the front face's text, so the printer's character set can print them.
- **The Universes Beyond and Pauper toggles live in memory.** They reset on power cycle, on purpose for 1.0. Keeping them across power cycles is planned for 2.0.
- **The UB-on slip's quote is a joke.** It pokes fun at Universes Beyond, and it stays.

## Boot time

The machine runs from a power switch, so the goal is the shortest time from power-on to the startup slip. WiFi and SSH only have to come up eventually, for maintenance. The steps are in [SETUP.md](SETUP.md#faster-boot-optional).

- **The program doesn't wait for the system.** The service starts as soon as the SD card is mounted, while it's still read-only, in parallel with the filesystem check. It has real-time priority until the ready line prints. On a single-core Pi Zero, the rest of the boot otherwise more than doubles Python's import time.
- **WiFi and SSH come up late** (about 80 seconds) as a result. That's fine for maintenance access.
- **The filesystem check stays.** The power switch cuts power without a shutdown, so the check is worth its 3 seconds.
- **No initramfs.** It only handles first-boot setup and cases this machine doesn't have. Without it, the kernel stage drops from 11 to 4 seconds. The cost: if a kernel update ever needs it, the fix is one line in `config.txt`, on the SD card.
- **Bluetooth and the display driver are off.** Nothing uses them. Bluetooth may come back in a later version.
- **Python startup work happens after the slip.** The catalog loads after the startup slip, from a pickle cache. python-escpos's printer database cache lives in a fixed folder, because by default it goes to a new temp folder every start.

Measured on a warm reboot, from kernel start: the startup slip went from about 52 to 16 seconds, and the ready line from about 52 to 17 seconds.

## Issues and inconsistencies

These are open in 1.0 and will be fixed in later versions. Most have a GitHub issue.

1. **Bug: the Universes Beyond filter never excludes anything.** `pick_card` tests `card.get("promo_types") != "universesbeyond"`, but `promo_types` is a list (or missing), so the test always passes. With UB turned off, the 2,108 UB-tagged cards (about 12% of the pool) are still in it. That's easy to miss in play. The fix is `"universesbeyond" not in (card.get("promo_types") or [])`. ([#1](https://github.com/calvin-young/momir-machine/issues/1))
2. **Bug: 24 token cards are in the catalog.** Their Scryfall layout is `token`, but their type line doesn't say "Token", so `01_filter_cards.py` keeps them. Examples: the Theros challenge-deck monster cards (Hydra Head, Phoberos Reaver) and helper cards like Morph and Manifest. Filtering on `layout == "token"` would catch them. ([#2](https://github.com/calvin-young/momir-machine/issues/2))
3. **Bug: Adventure cards print their spell half.** 137 Adventure cards print the Adventure after "FOLD HERE", but it can't be cast from the battlefield. Prepare cards (67) print their spell half too, which is correct. ([#3](https://github.com/calvin-young/momir-machine/issues/3))
4. **Latent: a modal DFC with a non-creature front would get the wrong face.** The rule is "either face is a creature", but `04_build_catalog.py` always catalogs `card_faces[0]`. A non-creature front would be stored and the creature back would be unreachable. No catalog card has a non-creature front today. ([#4](https://github.com/calvin-young/momir-machine/issues/4))
5. **Latent: a modal DFC's non-creature back could print.** `04_build_catalog.py` keeps the back when the front text mentions "transform", and it never checks that the back is a creature. No card hits this today. ([#4](https://github.com/calvin-young/momir-machine/issues/4))
6. **Latent: reversible cards aren't excluded.** `01_filter_cards.py` doesn't check for `reversible_card`. None get through today. ([#4](https://github.com/calvin-young/momir-machine/issues/4))
7. **Dead code.** `pick_card` takes `max_year`, but `button` never passes it. The `oldschool` field is never read, and `pool("oldschool")` does nothing. The Standard, Premodern, and Modern filters exist, but no dial value reaches them. `PIN_SWITCH` (GPIO 24) is set up as an input, but nothing is wired to it. ([#8](https://github.com/calvin-young/momir-machine/issues/8))
8. **The reference sheet's counts go to the console.** `print_reference` prints the per-mana-value counts with `print()`, not the printer, so the sheet has headings with no numbers. ([#5](https://github.com/calvin-young/momir-machine/issues/5))
9. **Face B text isn't cleaned like face A.** Em dashes are converted on the front face only, so a back face with an em dash may print oddly. ([#6](https://github.com/calvin-young/momir-machine/issues/6))
10. **The QR fallback never runs.** `04_build_catalog.py` skips any card without art, so `print_card`'s QR branch only runs if images go missing later.
11. **The command-line lookup prints only the front face.** `python3 main.py "Name"` skips the back of a DFC. ([#7](https://github.com/calvin-young/momir-machine/issues/7))
12. **Paths are relative in some scripts and not others.** `01` to `03` use paths relative to the current folder. `04` and `momir.py` use the script's own folder. Run `01` to `03` from the repo root. ([#9](https://github.com/calvin-young/momir-machine/issues/9))
13. **Art assets aren't generated by the pipeline.** The boot and slip images in `img/assets/` were processed by hand. `03` only handles `img/raw`. ([#10](https://github.com/calvin-young/momir-machine/issues/10))
14. **Scryfall requests.** `02` uses 8 threads. Check Scryfall's API guidelines on request rates before rerunning the download. ([#11](https://github.com/calvin-young/momir-machine/issues/11))

Resolved while writing these docs:

- **The "sound" comment.** It meant the noise of the printer feeding paper for the ready line. The comment in `print_ready` now says so.
- **The pinout.** The code is right. The old table labeled GPIO 5, 6, and 13 as X6 to X8, and the new pinout follows the code.
- **The BOM total.** The batteries are $8.88 for both, and the dial uses two decade counters. One machine's parts cost $75.48, and buying them, multi-packs included, costs $110.28.
- **The input format.** The Scryfall download is JSON Lines (`oracle-cards.jsonl.gz`), which is what `01` expects.
- **Repo hygiene.** Added `LICENSE` (Apache-2.0) and `.gitignore`.

## Tally

**Requested / agreed**

- Document the current state of the project as a 1.0 release. Refactor later.
- A concise, human-readable README, split into docs where it helps.
- A photo of the device, with a place to drop it in.
- A hardware diagram, Fritzing or similar.
- My design notes rewritten clearly, keeping my voice, with errors and inconsistencies noted.
- Prior art credited.
- The project isn't work-related.
- The code is right about the pinout. GPIO 24 and its ground aren't wired, so they're out of the docs.
- Power: the battery protection board feeds a boost converter (about 7 V) for the printer and a buck converter (5 V) for the Pi. The Pi takes power on one USB port and drives the printer from the other. It's all headless.
- Charging: wall adapter, USB-C cable, USB-C charger board, protection board, cells. The power switch sits between the protection board and everything else, so it only charges while switched on. That's documented as a hardware quirk in HARDWARE.md, not as an issue.
- Part names can be rewritten to be clearer.
- The power switch starts the machine, and a systemd service runs `main.py`.
- The dial is two of Adafruit's mechanical decade counters (product 1082), at $1.50 each from a $7.50 5-pack.
- The parts list shows the cost per machine and the cost to buy, multi-packs included.
- Prepare cards print their spell half. Adventure cards don't, unless the Adventure matters on the battlefield.
- BOM links added. The battery price covers both cells.
- The pinout is drawn like the original Notion table.
- License: my choice, free and open source.
- The toggles reset on power cycle for now. Keeping them is planned for 2.0.
- The UB filter seems to work in practice. Flag the bug and fix it later.
- The "Cowabunga" quote stays.

**Assumed**

- The license is Apache-2.0, the convention's default for tools not built on GPL code. All the dependencies (python-escpos, Pillow, lgpio, requests) are compatible with it.
- The pinout is an SVG drawn by `tools/pinout_svg.py`, because GitHub drops cell colors from Markdown tables. A plain table is kept under it for search and copying.
- The wiring diagram is a Mermaid flowchart. There's no Fritzing file.
- Only the tens counter's 0 and 1 positions are wired.
- Pack sizes come from the product pages: the protection board is a 2-pack, the boost a 6-pack, the buck a 10-pack, and the cable a 3-pack. The charger board, switch, button and cells are bought singly.
- The MT3608 output is about 7 V, as you remember it. It hasn't been measured.
- The dial's common contacts go to the ground pins 34 (ones) and 39 (tens).
- The button lockout exists to stop double-prints.
- Nothing has been tagged as `v1.0.0` yet.

**Questions not asked**

- Does the button's LED have a series resistor? Adafruit recommends 220 to 1000 ohms, and none is in the parts list.
- Which Adventure cards, if any, make the Adventure relevant on the battlefield?

**Follow-ups**

- Fix issues 1 to 14 in later versions.
- 2.0: keep the toggles across power cycles ([#12](https://github.com/calvin-young/momir-machine/issues/12)).
- Add SPDX headers to the source files.
- Add a version constant that matches the 1.0 tag.
- Add tests for the card filter and the layout rules ([#13](https://github.com/calvin-young/momir-machine/issues/13)).
- Make a Fritzing sketch if a breadboard-style picture would help.
- Start `docs/PROMPT_STATS.md` for the collaboration log.
