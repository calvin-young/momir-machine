#!/usr/bin/env python3

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import time
import requests

# Repo root; this script lives in scripts/
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = Path(BASE_DIR / "data/oracle-cards-filtered.jsonl")
IMAGE_DIR = Path(BASE_DIR / "img/raw")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "MomirPrinter/1.0"}
MAX_WORKERS = 8

session = requests.Session()
session.headers.update(HEADERS)

lock = threading.Lock()

downloaded = 0
skipped = 0
failed = 0

def download_card(card):
    image_filename = IMAGE_DIR / f"{card['oracle_id']}.jpg"

    if image_filename.exists():
        return "skipped", card["name"]

    try:
        image_uris = card.get("image_uris") or card["card_faces"][0]["image_uris"]

        for attempt in range(3):
            try:
                r = session.get(image_uris["art_crop"], timeout=20)
                r.raise_for_status()
                image_filename.write_bytes(r.content)
                return "downloaded", card["name"]
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(2)

    except Exception as e:
        return "failed", f"{card['name']} ({e})"

# Main
cards = []
with INPUT_FILE.open("r", encoding="utf-8") as f:
    for line in f:
        cards.append(json.loads(line))
total = len(cards)

print(f"Loaded {total:,} cards.")
print(f"Starting downloads using {MAX_WORKERS} workers...\n")

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {
        executor.submit(download_card, card): card
        for card in cards
    }

    for i, future in enumerate(as_completed(futures), start=1):
        status, message = future.result()
        with lock:
            if status == "downloaded":
                downloaded += 1
            elif status == "skipped":
                skipped += 1
            else:
                failed += 1
                print(f"FAILED: {message}")
            print(
                f"\r{i:5d}/{total}  "
                f"Downloaded:{downloaded:5d}  "
                f"Skipped:{skipped:5d}  "
                f"Failed:{failed:3d}",
                end="",
                flush=True,
            )

print("\n")
print(f"Downloaded : {downloaded}")
print(f"Skipped    : {skipped}")
print(f"Failed     : {failed}")