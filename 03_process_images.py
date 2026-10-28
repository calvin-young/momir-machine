#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import (
    Image,
    ImageEnhance,
    ImageFilter,
    ImageOps,
)

IMAGE_INPUT_DIR = Path("img/raw")
IMAGE_OUTPUT_DIR = Path("img/processed")
PRINTER_WIDTH = 384 # pixels
MAX_WORKERS = 8

IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def process_image(input_path, output_path, brightness=1.2, contrast=1.1):
    """Resize and convert an image into a printer-ready 1-bit PNG."""

    img = Image.open(input_path).convert("L")

    # Resize to printer width while preserving aspect ratio
    scale = PRINTER_WIDTH / img.width
    new_height = int(img.height * scale)
    img = img.resize((PRINTER_WIDTH, new_height), Image.Resampling.LANCZOS)

    # Stretch histogram
    img = ImageOps.autocontrast(img)

    # Brightness / contrast tweaks
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)

    # Mild sharpening
    img = img.filter(ImageFilter.SHARPEN)

    # Floyd-Steinberg dither
    img = img.convert("1")

    # Save Image
    img.save(output_path)

def process_card(card_id):
    art = IMAGE_INPUT_DIR / f"{card_id}.jpg"
    out = IMAGE_OUTPUT_DIR / f"{card_id}.png"
    if not out.exists():
        process_image(art, out)
    return card_id

card_ids = set()

for f in IMAGE_INPUT_DIR.glob("*.jpg"):
    card_ids.add(f.stem)

card_ids = sorted(card_ids)

print(f"Found {len(card_ids):,} cards.")

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {
        executor.submit(process_card, cid): cid
        for cid in card_ids
    }

    for i, future in enumerate(as_completed(futures), start=1):
        future.result()
        print(
            f"\rProcessed {i:,}/{len(futures):,}",
            end="",
            flush=True,
        )

print("\nDone.")