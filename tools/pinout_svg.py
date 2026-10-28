#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Draw the Pi header pinout as docs/images/pinout.svg, in the style of the original Notion table.

Run from the repo root after changing PINS: python3 tools/pinout_svg.py
"""

from html import escape
from pathlib import Path

OUTPUT_FILE = Path(__file__).resolve().parent.parent / "docs" / "images" / "pinout.svg"

# Fill colors for the Note/BCM/Pin cells (by pin type) and the Usage cell (by function)
PIN_COLORS = {"3v3": "#5b3a1f", "5v": "#5c2b29", "gnd": "#3b3b3b", "eeprom": "#564620"}
USE_COLORS = {"led": "#1f3a56", "button": "#4c2a3e", "cmc": "#24402e"}

# (pin, bcm, note, pin type, usage, usage group), in header order
PINS = [
    (1, "3V3", "Power", "3v3", "", None),
    (2, "5V", "Power", "5v", "", None),
    (3, "GPIO 2", "SDA I2C", None, "", None),
    (4, "5V", "Power", "5v", "", None),
    (5, "GPIO 3", "SCL I2C", None, "", None),
    (6, "Ground", "", "gnd", "Button Ground", "button"),
    (7, "GPIO 4", "", None, "LED", "led"),
    (8, "GPIO 14", "UART0_TXD", None, "Button", "button"),
    (9, "Ground", "", "gnd", "LED Ground", "led"),
    (10, "GPIO 15", "UART0_RXD", None, "", None),
    (11, "GPIO 17", "", None, "", None),
    (12, "GPIO 18", "PCM_CLK", None, "", None),
    (13, "GPIO 27", "", None, "", None),
    (14, "Ground", "", "gnd", "", None),
    (15, "GPIO 22", "", None, "", None),
    (16, "GPIO 23", "", None, "", None),
    (17, "3V3", "Power", "3v3", "", None),
    (18, "GPIO 24", "", None, "", None),
    (19, "GPIO 10", "MOSI", None, "", None),
    (20, "Ground", "", "gnd", "", None),
    (21, "GPIO 9", "MISO", None, "", None),
    (22, "GPIO 25", "", None, "CMC X0", "cmc"),
    (23, "GPIO 11", "SCLK", None, "", None),
    (24, "GPIO 8", "CE0_N", None, "CMC X1", "cmc"),
    (25, "Ground", "", "gnd", "", None),
    (26, "GPIO 7", "CE1_N", None, "CMC X2", "cmc"),
    (27, "ID_SD", "I2C ID EEPROM", "eeprom", "", None),
    (28, "ID_SC", "I2C ID EEPROM", "eeprom", "", None),
    (29, "GPIO 5", "", None, "CMC X7", "cmc"),
    (30, "Ground", "", "gnd", "", None),
    (31, "GPIO 6", "", None, "CMC X8", "cmc"),
    (32, "GPIO 12", "", None, "CMC X3", "cmc"),
    (33, "GPIO 13", "", None, "CMC X9", "cmc"),
    (34, "Ground", "", "gnd", "CMC Ones Ground", "cmc"),
    (35, "GPIO 19", "", None, "CMC 0X", "cmc"),
    (36, "GPIO 16", "", None, "CMC X4", "cmc"),
    (37, "GPIO 26", "", None, "CMC 1X", "cmc"),
    (38, "GPIO 20", "", None, "CMC X5", "cmc"),
    (39, "Ground", "", "gnd", "CMC Tens Ground", "cmc"),
    (40, "GPIO 21", "", None, "CMC X6", "cmc"),
]

# Column widths: Usage | Note | BCM | Pin | Pin | BCM | Note | Usage
WIDTHS = [128, 118, 74, 40, 40, 74, 118, 128]
ROW_H = 30
BG, GRID, TEXT = "#191919", "#2f2f2f", "#e3e3e3"


def cell(x, y, w, text, fill=None, bold=False, center=False):
    rect = f'<rect x="{x}" y="{y}" width="{w}" height="{ROW_H}" fill="{fill or BG}" stroke="{GRID}"/>'
    if not text:
        return rect
    tx, anchor = (x + w / 2, "middle") if center else (x + 8, "start")
    weight = ' font-weight="600"' if bold else ""
    return rect + (f'<text x="{tx}" y="{y + ROW_H / 2}" text-anchor="{anchor}"'
                   f' dominant-baseline="central"{weight}>{escape(text)}</text>')


def row_cells(y, left, right):
    """One header row: the odd pin on the left, mirrored by the even pin on the right."""
    lp, lb, ln, lt, lu, lg = left
    rp, rb, rn, rt, ru, rg = right
    values = [
        (lu, USE_COLORS.get(lg), False), (ln, PIN_COLORS.get(lt), False),
        (lb, PIN_COLORS.get(lt), False), (str(lp), PIN_COLORS.get(lt), True),
        (str(rp), PIN_COLORS.get(rt), True), (rb, PIN_COLORS.get(rt), False),
        (rn, PIN_COLORS.get(rt), False), (ru, USE_COLORS.get(rg), False),
    ]
    out, x = [], 0
    for w, (text, fill, center) in zip(WIDTHS, values):
        out.append(cell(x, y, w, text, fill, center=center))
        x += w
    return out


def main():
    width = sum(WIDTHS)
    height = ROW_H * (len(PINS) // 2 + 1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
        f'font-size="13" fill="{TEXT}">',
        f'<rect width="{width}" height="{height}" fill="{BG}"/>',
    ]
    x = 0
    for w, title in zip(WIDTHS, ["Usage", "Note", "BCM", "Pin", "Pin", "BCM", "Note", "Usage"]):
        parts.append(cell(x, 0, w, title, bold=True))
        x += w
    for i in range(0, len(PINS), 2):
        parts += row_cells(ROW_H * (i // 2 + 1), PINS[i], PINS[i + 1])
    parts.append("</svg>")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
