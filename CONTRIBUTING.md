# Contributing

Thanks for looking. This is a hobby project, and it's built around one specific hardware setup, so ideas and bug reports are welcome.

## Reporting a problem

Open an issue and include:

- What you expected and what happened.
- The dial setting and button press that caused it, if relevant.
- Your Python version and the Pi model.
- Any console output.

Hardware problems are easier to diagnose with a photo of the wiring.

## Suggesting a change

Open an issue first if the change is big, so we can talk about the approach. The known issues in [docs/DECISIONS.md](docs/DECISIONS.md#issues-and-inconsistencies) are a good place to start.

## Submitting a pull request

- Keep each pull request to one logical change.
- Match the style of the code around it.
- If you change a decision, update [docs/DECISIONS.md](docs/DECISIONS.md).
- If you change the pinout or the hardware, update [docs/HARDWARE.md](docs/HARDWARE.md).
- Test on a real Pi if the change touches printing or GPIO. There are no automated tests yet.
