"""Three 6 x 2 pegboard racks for the 2026-10-25 Bolt Depot order: layout, quantities, checks.

Writes racks.json, which build.py (FreeCAD) and site.py read. Front row bins are 6u, back
row 7u. A bin is 1 or 2 cells wide and holds one or more compartments side by side; each
compartment is one Bolt Depot line. Compartment widths follow the given fractions.

Fill uses bulk volume = count x piece mass / steel density / packing fraction (0.30 screws,
0.45 nuts and washers) against about 40 cm3 per 6u cell and 47 cm3 per 7u cell, a
comfortable fill rather than the brim. Masses are typical A2 catalogue figures (+-20 %).
"""

import json
from pathlib import Path

R = Path(__file__).resolve().parent
STEEL = 8.0
CELL_CM3 = {6: 40.0, 7: 47.0}

# key: (thread, symbol, length mm or None, pieces, grams each, Bolt Depot #, Brushwarden)
PARTS = {
    "M2-S6": ("M2", "socket", 6, 30, 0.25, 6363, False),
    "M2-S10": ("M2", "socket", 10, 30, 0.35, 6365, False),
    "M2-P16": ("M2", "pan", 16, 50, 0.40, 6818, True),
    "M2-N": ("M2", "nut", None, 120, 0.10, 7362, True),
    "M2-W": ("M2", "washer", None, 120, 0.04, 7364, True),
    "M2.5-S6": ("M2.5", "socket", 6, 30, 0.40, 6370, False),
    "M2.5-S10": ("M2.5", "socket", 10, 30, 0.55, 6372, False),
    "M2.5-N": ("M2.5", "nut", None, 100, 0.15, 7363, False),
    "M2.5-W": ("M2.5", "washer", None, 100, 0.05, 7365, False),
    "M3-S6": ("M3", "socket", 6, 30, 0.85, 6378, False),
    "M3-S8": ("M3", "socket", 8, 50, 0.95, 6379, False),
    "M3-S10": ("M3", "socket", 10, 50, 1.05, 6380, False),
    "M3-S12": ("M3", "socket", 12, 50, 1.15, 6381, False),
    "M3-S16": ("M3", "socket", 16, 50, 1.35, 6382, False),
    "M3-S20": ("M3", "socket", 20, 30, 1.55, 6383, False),
    "M3-S25": ("M3", "socket", 25, 30, 1.80, 6384, False),
    "M3-S30": ("M3", "socket", 30, 30, 2.05, 6385, False),
    "M3-B6": ("M3", "button", 6, 30, 0.60, 7218, False),
    "M3-B8": ("M3", "button", 8, 50, 0.70, 7219, False),
    "M3-B10": ("M3", "button", 10, 30, 0.80, 7220, False),
    "M3-C8": ("M3", "csk", 8, 30, 0.60, 7213, False),
    "M3-C12": ("M3", "csk", 12, 33, 0.80, 7215, True),
    "M3-C16": ("M3", "csk", 16, 30, 1.00, 7216, False),
    "M3-P12": ("M3", "pan", 12, 40, 0.90, 6833, True),
    "M3-N": ("M3", "nut", None, 103, 0.25, 4773, True),
    "M3-NL": ("M3", "nyloc", None, 110, 0.35, 4792, True),
    "M3-W": ("M3", "washer", None, 100, 0.12, 4513, False),
    "M4-S8": ("M4", "socket", 8, 30, 2.0, 6392, False),
    "M4-S12": ("M4", "socket", 12, 50, 2.4, 6394, False),
    "M4-S16": ("M4", "socket", 16, 30, 2.8, 6396, False),
    "M4-S20": ("M4", "socket", 20, 30, 3.2, 6398, False),
    "M4-S25": ("M4", "socket", 25, 30, 3.7, 6399, False),
    "M4-B8": ("M4", "button", 8, 30, 1.5, 6622, False),
    "M4-B12": ("M4", "button", 12, 30, 1.9, 6624, False),
    "M4-C12": ("M4", "csk", 12, 30, 1.7, 6665, False),
    "M4-N": ("M4", "nut", None, 100, 0.6, 4774, False),
    "M4-NL": ("M4", "nyloc", None, 100, 0.8, 4793, False),
    "M4-W": ("M4", "washer", None, 100, 0.2, 4514, False),
    "M5-S8": ("M5", "socket", 8, 30, 3.6, 6406, False),
    "M5-S10": ("M5", "socket", 10, 50, 3.9, 6407, False),
    "M5-S16": ("M5", "socket", 16, 30, 4.8, 6409, False),
    "M5-S20": ("M5", "socket", 20, 30, 5.4, 6410, False),
    "M5-S25": ("M5", "socket", 25, 30, 6.2, 6411, False),
    "M5-B10": ("M5", "button", 10, 30, 2.9, 6632, False),
    "M5-N": ("M5", "nut", None, 100, 1.1, 4775, False),
    "M5-NL": ("M5", "nyloc", None, 100, 1.4, 4794, False),
    "M5-W": ("M5", "washer", None, 100, 0.35, 4515, False),
}

# Racks: rows of bins, left to right; a bin is (cells wide, [(part key, width fraction)]).
# An empty compartment list is a spare bin.
RACKS = [
    {"id": "m3", "name": "M3", "rows": {
        "front": [(1, [("M3-N", 1), ("M3-NL", 1), ("M3-W", 1)]), (1, [("M3-S6", 1), ("M3-S8", 1)]),
                  (1, [("M3-S10", 1)]), (1, [("M3-S12", 1)]), (1, [("M3-S16", 1)]),
                  (1, [("M3-S20", 1), ("M3-S25", 1)])],
        "back": [(1, [("M3-S30", 1), ("M3-P12", 1)]), (1, [("M3-B6", 1), ("M3-B8", 1)]),
                 (1, [("M3-B10", 1), ("M3-C8", 1)]), (1, [("M3-C12", 1), ("M3-C16", 1)]),
                 (1, []), (1, [])]}},
    {"id": "m2-m4", "name": "M2 · M2.5 · M4", "rows": {
        "front": [(1, [("M2-S6", 1), ("M2-S10", 1)]), (1, [("M4-S8", 1)]), (1, [("M4-S16", 1)]),
                  (1, [("M4-S20", 1)]), (1, [("M4-C12", 1), ("M4-N", 1)]),
                  (1, [("M4-NL", 0.62), ("M4-W", 0.38)])],
        "back": [(1, [("M2-P16", 0.5), ("M2-N", 0.25), ("M2-W", 0.25)]),
                 (1, [("M2.5-S6", 1), ("M2.5-S10", 1)]), (1, [("M2.5-N", 1), ("M2.5-W", 1)]),
                 (1, [("M4-S12", 1)]), (1, [("M4-S25", 1)]), (1, [("M4-B8", 1), ("M4-B12", 1)])]}},
    {"id": "m5", "name": "M5", "rows": {
        "front": [(2, [("M5-S10", 1)]), (2, [("M5-S16", 1)]), (1, [("M5-N", 1)]), (1, [("M5-B10", 1)])],
        "back": [(2, [("M5-S20", 1)]), (2, [("M5-S25", 1)]), (1, [("M5-S8", 1)]),
                 (1, [("M5-NL", 0.75), ("M5-W", 0.25)])]}},
]

HEIGHT_U = {"front": 6, "back": 7}


def bulk(key):
    _, symbol, _, n, g, _, _ = PARTS[key]
    return n * g / STEEL / (0.45 if symbol in ("nut", "nyloc", "washer") else 0.30)


def main():
    used, out, worst = [], [], []
    for rack in RACKS:
        rows = {}
        for row, bins in rack["rows"].items():
            assert sum(w for w, _ in bins) == 6, (rack["id"], row)
            u = HEIGHT_U[row]
            rows[row] = []
            for width, comps in bins:
                total = sum(f for _, f in comps) or 1
                threads = {PARTS[k][0] for k, _ in comps}
                assert len(threads) <= 1, (rack["id"], comps)
                cells = []
                for key, frac in comps:
                    used.append(key)
                    cap = CELL_CM3[u] * width * frac / total
                    worst.append((bulk(key) / cap, key))
                    thread, symbol, length, n, _, bd, bw = PARTS[key]
                    cells.append({"key": key, "fraction": frac / total, "thread": thread, "symbol": symbol,
                                  "length": length, "pieces": n, "bolt_depot": bd, "brushwarden": bw,
                                  "bulk_cm3": round(bulk(key), 1), "fill": round(bulk(key) / cap, 2)})
                rows[row].append({"cells": width, "height_u": u, "thread": threads.pop() if threads else None,
                                  "compartments": cells})
        out.append({"id": rack["id"], "name": rack["name"], "rows": rows})
    assert sorted(used) == sorted(PARTS), set(PARTS) ^ set(used)
    worst.sort(reverse=True)
    (R / "racks.json").write_text(json.dumps({"racks": out}, indent=1, ensure_ascii=False))
    print("racks.json:", len(out), "racks,", len(used), "lines; fullest:",
          ", ".join(f"{k} {r:.0%}" for r, k in worst[:5]))


if __name__ == "__main__":
    main()
