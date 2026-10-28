#!/usr/bin/env python3

import json
from collections import defaultdict
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = Path(BASE_DIR / "data/oracle-cards-filtered.jsonl")
OUTPUT_FILE = Path(BASE_DIR / "data/catalog.json")
IMAGE_DIR = Path(BASE_DIR / "img/processed")

catalog = defaultdict(list)

# Initialize Tallies
total = 0
kept = 0
missing_images = 0

# Loop through cards
print("Opening filtered Oracle JSONL...")
with INPUT_FILE.open("r", encoding="utf-8") as f:

    for line in f:
        total += 1
        card = json.loads(line)
        print(f"Processing #{total}: {card["name"]}...")
        oracle_id = card["oracle_id"]
        image_path = IMAGE_DIR / f"{oracle_id}.png"

        if not image_path.exists():
            missing_images += 1
            continue

        if card.get("card_faces"):
            # Double-face card, or one with a special layout (e.g. prepared spell)
            face_a = card.get("card_faces")[0]

            if card["layout"] == "modal_dfc" and "transform" not in face_a.get("oracle_text", "").lower():
                # One that cannot be transformed; do not print second face
                face_b = None
            else:
                # One with a second face that is relevant once it's on the battlefield
                face_b = card.get("card_faces")[1]
        else:
            # Card with a 'normal' layout
            face_a = card
            face_b = None
        
        entry = {
            "cmc": int(card["cmc"]),
            "set": card["set"],
            "artist": card["artist"],
            "scryfall_uri": card["scryfall_uri"],
            "promo_types": card.get("promo_types"),
            "legalities": card.get("legalities"),
            "oracle_id": card["oracle_id"],
            "face": "a",

            "name": face_a.get("name"),
            "mana_cost": face_a.get("mana_cost"),
            "type_line": face_a.get("type_line"),
            "oracle_text": face_a.get("oracle_text", "").replace('—', '-'),
            "flavor_text": face_a.get("flavor_text", "").replace('—', '-'),
            "power": face_a.get("power"),
            "toughness": face_a.get("toughness"),

            "year": int(card.get("released_at")[:4]), # this is the latest, not original, print date
            "oldschool": int(card.get("released_at")[:4]) < 1995, # misses reprints...
        }

        if face_b:
            entry_b = {
                "name": face_b.get("name"),
                "mana_cost": face_b.get("mana_cost"),
                "type_line": face_b.get("type_line"),
                "oracle_text": face_b.get("oracle_text"),
                "flavor_text": face_b.get("flavor_text"),
                "artist": face_b.get("artist"),
                "power": face_b.get("power"),
                "toughness": face_b.get("toughness"),
                "face": "b"
            }

            entry["face_b"] = entry_b

        catalog[str(entry["cmc"])].append(entry)
        kept += 1

# Sort cards alphabetically within each CMC bucket
print("Finished, sorting cards by CMC...")
for cards in catalog.values():
    cards.sort(key=lambda c: c["name"])

# Sort CMC buckets numerically
catalog = dict(sorted(catalog.items(), key=lambda item: int(item[0])))

# Write catalog
with OUTPUT_FILE.open("w", encoding="utf-8") as f:
    json.dump(catalog, f, indent=2, ensure_ascii=False)

# Summary
print(f"Processed      : {total:,}")
print(f"Included       : {kept:,}")
print(f"Missing images : {missing_images:,}")
print()

for cmc, cards in catalog.items():
    print(f"CMC {int(cmc):2d}: {len(cards):4d}")