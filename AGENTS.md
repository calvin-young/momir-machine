# AGENTS.md

Notes for AI agents working in this repo. Humans should start with [README.md](README.md).

## Setup and commands

- Python 3.12 or newer. The code uses nested quotes inside f-strings.
- Run the machine: `python3 main.py`
- Look up a card (prints the front face only): `python3 main.py "Card Name"`
- Build the catalog: run `01_filter_cards.py` to `04_build_catalog.py` from the repo root, in order. See [docs/SETUP.md](docs/SETUP.md#build-the-catalog).
- There are no tests yet.
- The printer and GPIO libraries only work on the Pi. Don't try to run `main.py` on a laptop. `momir.py` imports `escpos` at load time, so it needs that package installed.

## Layout

| Path | What |
| --- | --- |
| `main.py` | GPIO loop: reads the dial and button, and drives the LED |
| `momir.py` | The `Momir` class: catalog loading, card picking, and printing |
| `01_filter_cards.py` to `04_build_catalog.py` | Build pipeline: filter, download art, process art, build catalog |
| `data/` | Generated: `oracle-cards*.jsonl*`, `catalog.json`, `catalog.pkl`. Not committed. |
| `img/raw/`, `img/processed/` | Generated card art. Not committed. |
| `img/assets/` | Hand-made boot and slip art. `raw/` is the source, `processed/` is the printer version. |
| `docs/` | Hardware, setup, and decisions |

## Conventions

- GPIO pins live in `main.py`. The printer's USB IDs, asset paths, and print widths live in `momir.py`.
- Scripts `01` to `03` use paths relative to the current folder. `04` and `momir.py` use the script's own folder. Keep it that way until the refactor.
- Docs describe what exists. Mark anything planned as planned.
- `docs/DECISIONS.md` records why things are built this way and lists known issues. Update it when a decision changes.
- Use `AGENTS.md`, not `CLAUDE.md`.

## Before changing things

- Read the issues in [docs/DECISIONS.md](docs/DECISIONS.md#issues-and-inconsistencies) first. Some are open bugs.
- Don't change the pinout without checking the hardware. It's in [docs/HARDWARE.md](docs/HARDWARE.md#pinout).
