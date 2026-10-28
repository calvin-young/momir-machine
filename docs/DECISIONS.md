# Decisions

Why the machine works the way it does, what's still open, and what I found while writing the docs for 1.0. Items marked **Needs check** are things I could see in the code but couldn't confirm against card data, because the data isn't in the repo.

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
| `modal_dfc` | Either face can be cast. | Keeps the card if either face is a creature. Always catalogs the front. Prints the back only if the front text mentions "transform". | Mismatch, see issues 2 and 3 |
| `reversible_card` | They're not real. Ignore them. | Not excluded. | Mismatch, see issue 4 |

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
- **Fast boot over everything else.** The machine runs from a power switch, so the Pi is set up to reach the startup slip as fast as possible while WiFi and SSH come up later. The setup steps are in [SETUP.md](SETUP.md#faster-boot-optional).
- **The button locks out for 2 seconds after each print.** The LED blinks during the lockout. The code doesn't say why. I assume it stops double-prints.
- **Em dashes become hyphens** in the front face's text, so the printer's character set can print them.
- **The Universes Beyond and Pauper toggles live in memory.** They reset on power cycle.

## Issues and inconsistencies

These are things I found by reading the code and notes. I haven't changed any code yet.

1. **Needs check: the Universes Beyond filter may never exclude anything.** `pick_card` tests `card.get("promo_types") != "universesbeyond"`. Scryfall documents `promo_types` as an array, and a list never equals a string, so the test would always pass. Check: turn UB off and look for UB cards in the output. I also need to confirm the exact value Scryfall uses. Source: [Scryfall card objects](https://scryfall.com/docs/api/cards).
2. **Bug: a modal DFC with a non-creature front and a creature back gets the wrong face.** Your rule is "either face is a creature". But `04_build_catalog.py` always catalogs `card_faces[0]`, so the non-creature front is stored under its mana value and the creature back is never reachable. Check: any catalog entry whose `type_line` doesn't contain `Creature` should not exist.
3. **Bug: non-creature backs can print.** `04_build_catalog.py` keeps the back of a modal DFC when the front text contains "transform". It never checks that the back is a creature, and your rule says we don't print non-creature sides.
4. **Needs check: reversible cards aren't excluded.** `01_filter_cards.py` doesn't check `layout`, so a `reversible_card` with a creature first face gets through. Your notes say to ignore them.
5. **Dead filters.** `pick_card` takes a `max_year` argument, but `button` never passes it, so the year filter is always 2100. The `oldschool` field is written to the catalog and never read. `pool("oldschool")` is a placeholder that does nothing. `pick_card` can filter on Standard, Premodern, and Modern, but no dial value reaches them. Only Pauper is reachable. `PIN_SWITCH` (GPIO 24) is set up as an input and never read.
6. **The reference sheet's counts go to the console.** `print_reference` prints the per-mana-value counts with `print()`, not the printer. The sheet shows the headings with no numbers. Intended or not?
7. **Face B text is handled differently from face A.** `04_build_catalog.py` converts em dashes for face A only, and it doesn't default a missing `oracle_text` to an empty string. If face B has no oracle text, the stored value is `null`, and printing it would crash on `.split`. Needs check.
8. **The QR fallback never runs.** `04_build_catalog.py` skips any card without a processed image, so every catalog card has art. `print_card`'s QR branch only runs if images go missing later.
9. **The command-line lookup prints only the front face.** `python3 main.py "Name"` doesn't print the back of a DFC.
10. **Paths are relative in some scripts and not others.** `01` to `03` use paths relative to the current folder. `04` and `momir.py` use the script's own folder. Run `01` to `03` from the repo root. [SETUP.md](SETUP.md) says so.
11. **The input format may not match.** `01` reads JSON Lines. Scryfall's bulk download may be a JSON array. Needs check.
12. **Art assets aren't generated by the pipeline.** `img/assets/` holds the boot and slip images, but `03` only processes `img/raw`. The processed assets were made by hand. Write down how, or script it.
13. **Resolved: the "sound" comment.** It meant the noise of the printer feeding paper for the ready line. The comment in `print_ready` now says so.
14. **The pinout table doesn't match the code.** See [HARDWARE.md](HARDWARE.md#pinout).
15. **The BOM total doesn't add up.** See [HARDWARE.md](HARDWARE.md#parts).
16. **Repo hygiene.** There's no `.gitignore`, so `data/`, `img/raw/`, `img/processed/`, `catalog.pkl`, and `__pycache__/` could be committed by accident. There's also no `LICENSE`.
17. **Scryfall requests.** `02` uses 8 threads. Scryfall asks clients to keep their request rate gentle, so check its current API guidelines before rerunning the download.

## Tally

**Requested / agreed**

- Document the current state of the project as a 1.0 release. Refactor later.
- A concise, human-readable README, split into docs where it helps.
- A photo of the device, with a place to drop it in.
- A hardware diagram, Fritzing or similar.
- My design notes rewritten clearly, keeping my voice, with errors and inconsistencies noted.
- Prior art credited.
- The project isn't work-related.

**Assumed**

- The diagram is a Mermaid flowchart, which GitHub renders from the Markdown. I didn't make a Fritzing file. I can't reliably generate one here, and a Fritzing sketch needs the wiring confirmed first.
- The pinout follows the code, not the old table.
- The power chain and the dial's wiring are inferred from the parts list and the code.
- The dial is wired active-low with the common grounds on pins 34 and 39.
- The repo follows my conventions: `AGENTS.md`, `CONTRIBUTING.md`, a PR template with a requested-vs-assumed section, and this file.
- Nothing has been tagged as `v1.0.0` or published as a release yet. I wrote the docs and didn't tag them.
- The button lockout exists to stop double-prints.

**Questions not asked**

- Which way do the power converters feed the Pi and the printer, and where is the power switch? What is the GPIO 24 switch?
- How does the dial work? Is it a rotary decade switch, and is it wired that way?
- Is the pinout table or the code right for GPIO 5, 6, and 13?
- Is the Oracle Cards file a JSON array or JSON Lines?
- How does the program start at boot, and how does it get USB access?
- Which license should this use? The conventions default to Apache-2.0 for tools that aren't built on GPL code.
- Should the UB and Pauper toggles survive a power cycle?
- Is the "Cowabunga" line on the UB-on slip okay to keep, given it's a made-up quote attributed to a real actor?

**Follow-ups**

- Fix or confirm issues 1 to 13.
- Add `.gitignore` and `LICENSE`.
- Add a version constant that matches the 1.0 tag.
- Add tests for the card filter and the MDFC rules.
- Make a Fritzing or wiring diagram once the wiring is confirmed.
- Start `docs/PROMPT_STATS.md` for the collaboration log.
