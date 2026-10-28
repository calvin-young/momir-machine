#!/usr/bin/env python3

import gzip
import json
from collections import Counter
from pathlib import Path

INPUT_FILE = Path("data/oracle-cards.jsonl.gz")
OUTPUT_FILE = Path("data/oracle-cards-filtered.jsonl")

FILTERS = {
    "paper_only": True,
    "creatures_only": True,
    "exclude_tokens": True,
    "castable_only": True,
}

def keep_card(card, reject_counts):
    """Permanently filter out cards that are not appropriate for the format, e.g. non-creature spells"""
    # OBSERVE! This only counts one flag per card.. helpful against double-counting, but still..
    if FILTERS["paper_only"] and "paper" not in card.get("games", []):
        reject_counts["paper_only"] += 1
        return False

    if FILTERS["creatures_only"] and "Creature" not in card.get("type_line", ""):
        reject_counts["non_creature"] += 1
        return False

    if FILTERS["exclude_tokens"] and "Token" in card.get("type_line", ""):
        reject_counts["token"] += 1
        return False

    if FILTERS["castable_only"] and card.get("card_faces"):
        if "Creature" in card["card_faces"][0]["type_line"]:
            pass
        elif card["layout"] == "modal_dfc" and "Creature" in card["card_faces"][1]["type_line"]:
            pass
        else:
            reject_counts["uncastable"] += 1
            return False

    return True

# Main
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

kept = 0
reject_counts = Counter()

with gzip.open(INPUT_FILE, "rt", encoding="utf-8") as infile, \
     OUTPUT_FILE.open("w", encoding="utf-8") as outfile:
    for line in infile:
        card = json.loads(line)
        if not keep_card(card, reject_counts):
            continue
        json.dump(card, outfile, separators=(",", ":"))
        outfile.write("\n")
        kept += 1

print(f"\nKept {kept:,} cards\n")
print("Rejected:")
for reason, count in reject_counts.most_common():
    print(f"  {reason:<20} {count:>8,}")