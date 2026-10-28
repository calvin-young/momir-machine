# AGENTS.md

Notes for AI agents working in this repo. Humans should start with [README.md](README.md).

## Setup and commands

- Python 3.12 or newer. The code uses nested quotes inside f-strings.
- Run the machine: `python3 main.py`
- Look up a card (prints the front face only): `python3 main.py "Card Name"`
- Build the catalog: run `scripts/01_filter_cards.py` to `scripts/04_build_catalog.py` in order, from any folder. See [docs/SETUP.md](docs/SETUP.md#build-the-catalog).
- There are no tests yet.
- The printer and GPIO libraries only work on the Pi. Don't try to run `main.py` on a laptop. `momir.py` imports `escpos` at load time, so it needs that package installed.

## Layout

| Path | What |
| --- | --- |
| `main.py` | GPIO loop: reads the dial and button, and drives the LED |
| `momir.py` | The `Momir` class: catalog loading, card picking, and printing |
| `scripts/` | Build pipeline, `01` to `04`: filter, download art, process art, build catalog |
| `data/` | Generated: `oracle-cards*.jsonl*`, `catalog.json`, `catalog.pkl`. Not committed. |
| `img/raw/`, `img/processed/` | Generated card art. Not committed. |
| `img/assets/` | Hand-made boot and slip art. `raw/` is the source, `processed/` is the printer version. |
| `system/momir.service` | systemd service that starts `main.py` at boot. See [docs/SETUP.md](docs/SETUP.md#start-at-boot) |
| `docs/` | Hardware, setup, and decisions |

## Conventions

- GPIO pins live in `main.py`. The printer's USB IDs, asset paths, and print widths live in `momir.py`.
- Every script finds `data/` and `img/` from its own location (`BASE_DIR`), never from the current folder.
- Docs describe what exists. Mark anything planned as planned.
- `docs/DECISIONS.md` records why things are built this way and lists known issues. Update it when a decision changes. This project keeps no requested-vs-assumed tally there, which is an exception to the usual convention.
- Use `AGENTS.md`, not `CLAUDE.md`.

## Before changing things

- Read the issues in [docs/DECISIONS.md](docs/DECISIONS.md#issues-and-inconsistencies) first. Some are open bugs.
- Don't change the pinout without checking the hardware. It's in [docs/HARDWARE.md](docs/HARDWARE.md#pinout).
