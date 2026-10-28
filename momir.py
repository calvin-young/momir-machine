#!/usr/bin/env python3

import json
import pickle
import random
import textwrap
from pathlib import Path
from collections import Counter

from escpos.printer import Usb
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
CARDS_UB = False
CARDS_LEGALITY = False

# Legalities that pick_card() filters on; the catalog cache drops the others
LEGALITIES_USED = ("standard", "premodern", "modern", "pauper")

def trim_card(card):
    card = dict(card)
    card.pop("flavor_text", None)
    if card.get("legalities"):
        card["legalities"] = {k: card["legalities"][k] for k in LEGALITIES_USED if k in card["legalities"]}
    if card.get("face_b"):
        card["face_b"] = trim_card(card["face_b"])
    return card

class Momir:

    def __init__(
        self,
        catalog_path = BASE_DIR / "data" / "catalog.json",
        image_root = BASE_DIR / "img",
        image_boot = BASE_DIR / "img/assets/processed/momir.png",
        image_pauper = BASE_DIR / "img/assets/processed/pauper.png",
        image_ub_true = BASE_DIR / "img/assets/processed/ub_true.png",
        image_ub_false = BASE_DIR / "img/assets/processed/ub_false.png",
        printer_vendor=0x28E9,
        printer_product=0x0289,
        printer_out_ep=0x03,
        printer_in_ep=0x81,
        printer_max_a = 32, # max chars per line with font a
        printer_max_b = 42 # max chars per line with font b
    ):
        
        self.cards_ub = CARDS_UB
        self.cards_legality = CARDS_LEGALITY
        self.image_root = Path(image_root)
        self.image_boot = Path(image_boot)
        self.image_pauper = Path(image_pauper)
        self.image_ub_true = Path(image_ub_true)
        self.image_ub_false = Path(image_ub_false)
        self.printer_max_a = printer_max_a
        self.printer_max_b = printer_max_b

        self.catalog_path = Path(catalog_path)
        self.catalog = None

        print("Connecting to printer...")

        self.printer = Usb(
            printer_vendor,
            printer_product,
            out_ep=printer_out_ep,
            in_ep=printer_in_ep,
        )
        
        self.printer.profile.profile_data["media"]["width"]["pixel"] = 384

        print("Printer ready.")

        self.random = random.Random()

    def load_catalog(self):
        # Loaded after the startup print so the printer responds quickly at power on.
        # catalog.json is slow to parse on a Pi Zero, so a trimmed pickle of it is kept
        # next to it and rebuilt whenever catalog.json is newer.
        print("Loading catalog...")

        cache_path = self.catalog_path.with_suffix(".pkl")
        try:
            if cache_path.stat().st_mtime < self.catalog_path.stat().st_mtime:
                raise FileNotFoundError
            with open(cache_path, "rb") as f:
                self.catalog = pickle.load(f)
        except (OSError, pickle.UnpicklingError, EOFError):
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                self.catalog = json.load(f)
            self.catalog = {cmc: [trim_card(c) for c in cards] for cmc, cards in self.catalog.items()}
            try:
                tmp_path = cache_path.with_suffix(".pkl.tmp")
                with open(tmp_path, "wb") as f:
                    pickle.dump(self.catalog, f, protocol=pickle.HIGHEST_PROTOCOL)
                tmp_path.replace(cache_path)
            except OSError as e:
                print(f"Could not write catalog cache: {e}")

        self.total_cards = sum(len(v) for v in self.catalog.values())
        self.cmc_counts = Counter({int(cmc): len(cards) for cmc, cards in self.catalog.items()})

        print(f"Loaded {self.total_cards:,} cards.")

    def load_card_image(self, path, mode="crop", target_aspect=1.47):
        img = Image.open(path).convert("L")

        if mode == "crop":
            w, h = img.size
            aspect = w / h

            if aspect < target_aspect:
                new_h = int(w / target_aspect)
                top = (h - new_h) // 2
                img = img.crop((0, top, w, top + new_h))

            elif aspect > target_aspect:
                new_w = int(h * target_aspect)
                left = (w - new_w) // 2
                img = img.crop((left, 0, left + new_w, h))

        elif mode == "resize":
            img = img.resize((384, int(384 / target_aspect)))

        return img

    def print_inline(self, left, right):
        left = str(left or "")
        right = str(right or "")
        max_a = self.printer_max_a
        max_b = self.printer_max_b
        min_dots = 2

        lenl = len(left)
        lenr = len(right)
        lent = lenl + lenr + min_dots

        if lent > max_b:
            # Too long for either font; break into two lines
            if lenl > max_a:
                # Still too long for font a; switch to font b
                self.printer.set(font='b')
                self.printer.textln(left+' '*(max_b-lenl))
            else:
                self.printer.set(font='a')
                self.printer.textln(left+' '*(max_a-lenl))
            self.printer.textln(' '*(max_a-lenl)+right)
        elif lent > max_a:
            # Too long for font a; switch to font b
            self.printer.set(font='b')
            self.printer.textln(left+' '*(max_b-lenl-lenr)+right)
        else:
            # Short enough for font a
            self.printer.set(font='a')
            self.printer.textln(left+' '*(max_a-lenl-lenr)+right)
        # self.printer.print_and_feed()

    def print_startup(self):
        self.printer.set(align='left', font='a')
        self.printer.textln("Momir Vig")
        self.printer.image(Image.open(self.image_boot))
        self.printer.set(align='left', font='b')
        self.printer.textln("Players start with 24 life")
        self.printer.ln(1)
        txt = "X, Discard a card: Create a token that's a copy of a creature card with converted mana cost X chosen at random. Activate this ability only any time you could cast a sorcery and only once each turn."
        self.printer.textln(textwrap.fill(txt, width=self.printer_max_b, break_long_words=False))
        self.printer.ln(2)

    def print_ready(self):
        # Printed once the catalog is loaded; the printer's feed noise tells players the button is ready
        self.printer.set(align='left', font='b')
        self.printer.textln(f"{self.total_cards:,} creatures lurk in the vat...")
        self.printer.print_and_feed(3)

    def pick_card(self, cmc, max_year=2100, ub=False, legality=False, sets_banned=["UNK"]):
        sets_banned = {s.lower() for s in (sets_banned or [])}

        allowable_cards = [
            card for card in self.catalog.get(str(cmc), [])
            if card["year"] <= max_year
            and card["set"].lower() not in sets_banned
            and (ub or card.get("promo_types") != "universesbeyond")
            and (legality != "standard" or card["legalities"]["standard"] == "legal")
            and (legality != "premodern" or card["legalities"]["premodern"] == "legal")
            and (legality != "modern" or card["legalities"]["modern"] == "legal")
            and (legality != "pauper" or card["legalities"]["pauper"] == "legal")
        ]

        if not allowable_cards:
            self.printer.image(Image.open(self.image_boot)) # replace with a more thematic image
            self.printer.ln(2)
            self.printer.set(align='left', font='b')
            self.printer.textln(f"No creatures exist with these filters:")
            self.printer.textln(f"CMC: {cmc}")
            self.printer.textln(f"Year: <= {max_year}")
            self.printer.textln(f"Banned Sets: {", ".join(sets_banned)}")
            self.printer.textln(f"Legality: {legality.capitalize()}")
            self.printer.textln(f"Universes Beyond: {'Allowed' if ub else 'Disallowed'}")
            self.printer.print_and_feed(4)

            return None
        
        return self.random.choice(allowable_cards)

    def pick_card_by_name(self, name):
        name = name.casefold()
        return next(
            (
                card
                for cards in self.catalog.values()
                for card in cards
                if card["name"].casefold() == name
            ),
            None,
        )

    def print_card(self, card):
        # Face A or B, and Separator
        face = card.get("face")
        path = None
        if face == "a":
            print(f"Printing {card.get('name')}")
            path = self.image_root / "processed" / f"{card.get('oracle_id')}.png"
        elif face == "b":
            self.printer.set(align='center', font='a')
            self.printer.ln()
            self.printer.textln("- - - - FOLD HERE - - - -")
            self.printer.ln()
        else:
            return False
    
        # Header
        self.printer.set(align='left', font='b')
        self.printer.textln('-'*self.printer_max_b)
        self.printer.set(align='left', font='a')
        left = card.get('name')
        right = card.get('mana_cost')
        self.print_inline(left, right)
        self.printer.set(align='left', font='b')
        self.printer.textln('-'*self.printer_max_b)

        # Art 
        if face == "a":
            if path.exists():
                self.printer.image(self.load_card_image(path))
                self.printer.set(align='left', font='b')
            else:
                self.printer.set(align='center')
                self.printer.qr(card.get('scryfall_uri'), size=6)

        # Type
        self.printer.set(align='left', font='b')
        if face == "a":
            self.printer.textln('-'*self.printer_max_b)
        self.printer.textln(card.get('type_line'))
        self.printer.textln('-'*self.printer_max_b)

        # Rules Text
        self.printer.set(align='left', font='b')
        paragraphs = card.get('oracle_text', '').split("\n")
        for i, paragraph in enumerate(paragraphs):
            txt = textwrap.fill(paragraph, width=self.printer_max_b, break_long_words=False)
            self.printer.textln(txt)
            if i < len(paragraphs) - 1: self.printer.ln()
        self.printer.textln('-'*self.printer_max_b)
        
        # Power / Toughness
        if "Creature" in card.get('type_line'):
            self.printer.set(align='right', font='a')
            left = card.get('artist')
            right = f"[{card.get('power')}/{card.get('toughness')}]"
            self.print_inline(left, right)
        else:
            self.printer.set(align='left', font='a')
            self.printer.textln(card.get('artist'))
        self.printer.set(align='left', font='b')
        self.printer.textln('-'*self.printer_max_b)

        # Print Second Face?
        if face == "a" and card.get('face_b'):
            return True
        else:
            self.printer.print_and_feed(2)
            return False

    def print_reference(self, ub, legality):
        self.printer.set(align='left', font='a')
        self.printer.textln(f"CMC 19: Reference Sheet")
        self.printer.textln(f"CMC 18: UB: {ub}")
        self.printer.textln(f"CMC 17: Pauper: {legality == 'pauper'}")
        self.printer.textln(f"CMC 16: Creatures...")
        for cmc, count in sorted(self.cmc_counts.items()):
            print(f"CMC {cmc}: {count:,}")
        self.printer.print_and_feed(2)

    def pool(self, setting):
        match setting:
            case "ub":
                self.cards_ub = not self.cards_ub
                if self.cards_ub:
                    self.printer.image(Image.open(self.image_ub_true))
                    self.printer.set(align='left', font='a')
                    self.printer.textln("Universes Beyond: ALLOWED")
                    self.printer.ln(2)
                    txt = '"Cowabunga!"'
                    self.printer.textln(textwrap.fill(txt, width=self.printer_max_a, break_long_words=False))
                    self.printer.textln("-Benedict Cumberbatch, Probably")
                    self.printer.print_and_feed(2)
                else:
                    self.printer.image(Image.open(self.image_ub_false))
                    self.printer.set(align='left', font='b')
                    self.printer.textln("Universes Beyond: DISALLOWED")
                    self.printer.ln(2)
                    txt = '"All memory of your existence will be wiped from reality. You will die, and no one will mourn."'
                    self.printer.textln(textwrap.fill(txt, width=self.printer_max_b, break_long_words=False))
                    self.printer.textln("-Memnarch")
                    self.printer.print_and_feed(2)
            case "oldschool":
                # figure this out later
                pass
            case _:
                self.cards_legality = setting if self.cards_legality != setting else False
                self.printer.image(Image.open(self.image_pauper))
                self.printer.set(align='left', font='a')
                self.printer.textln(f"Legality: {self.cards_legality.upper() if self.cards_legality else 'ALL'}")
                self.printer.print_and_feed(2)




    def button(self, cmc):
        match cmc:
            case 19: self.print_reference(ub=self.cards_ub, legality=self.cards_legality)
            case 18: self.pool('ub')
            case 17: self.pool('pauper')
            case _: 
                card = self.pick_card(cmc=cmc, ub=self.cards_ub, legality=self.cards_legality)
                if card:
                    if self.print_card(card) and card.get('face_b'):
                        self.print_card(card['face_b'])