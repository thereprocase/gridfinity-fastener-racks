"""Fastener symbols for Fillaprint labels, drawn to the font's two-bead rule.

Units are w (one extrusion width); symbols stand on the baseline and reach the capital
height, 14w. Every stroke and every gap must be at least 2w: eroding a symbol by just
under 1w may not split or remove any part of it, and dilating it by just under 1w may
not close a hole or join two parts. Convex corners are rounded by 0.5w, as in the font.

Writes icons.json (polygons in w); specimen.py draws them. Needs shapely (the double-bead
venv has it).
"""

import json
import math
import sys
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

CAP = 14.0
SHANK = 3.5  # shank width; thick enough that a socket cap does not read as the letter T
R = Path(__file__).resolve().parent


def soft(g, r=0.5):
    """Round convex corners by r, as the font's finish does."""
    return g.buffer(-r, join_style="round").buffer(r, join_style="round")


def shank(top):
    return box(-SHANK / 2, 0, SHANK / 2, top)


def hexagon(flats, cx, cy):
    rad = flats / math.sqrt(3)
    return Polygon([(cx + rad * math.cos(math.radians(a)), cy + rad * math.sin(math.radians(a)))
                    for a in range(0, 360, 60)])


ICONS = {
    # Side profiles with short heads and long shanks, close to a real screw's proportions,
    # so the dimension line beside the shank has room. Plain side profiles, no drive shown.
    "socket": unary_union([box(-4.75, 10, 4.75, CAP), shank(10.1)]),
    "button": unary_union([affinity.scale(Point(0, 10).buffer(5.25), 1, 4 / 5.25, origin=(0, 10))
                           .intersection(box(-6, 10, 6, CAP)), shank(10.1)]),
    "csk": unary_union([Polygon([(-5, CAP), (5, CAP), (SHANK / 2, 10), (-SHANK / 2, 10)]), shank(10.1)]),
    "pan": unary_union([box(-4.75, 10.5, 4.75, CAP).buffer(-1.5).buffer(1.5).union(box(-4.75, 10.5, 4.75, 12)),
                        shank(10.6)]),
    # Nut seen from above: hexagon with its threaded hole.
    "nut": hexagon(13, 0, 7).difference(Point(0, 7).buffer(2.75)),
    # Nyloc seen from the side: hex body, a 2w gap, then the rounded nylon collar.
    "nyloc": unary_union([
        box(-6.5, 0, 6.5, 7),
        box(-4.75, 9, 4.75, 13.5).buffer(-1.75).buffer(1.75).union(box(-4.75, 9, 4.75, 11)),
    ]),
    # Washer from above: a ring.
    "washer": Point(0, 7).buffer(6.5).difference(Point(0, 7).buffer(2.75)),
}
ICONS = {k: soft(v) for k, v in ICONS.items()}


def parts(g):
    return list(getattr(g, "geoms", [g]))


def holes(g):
    return sum(len(p.interiors) for p in parts(g))


def check(name, g):
    eps = 1e-3
    eroded = g.buffer(-(1 - eps))
    dilated = g.buffer(1 - eps)
    problems = []
    if eroded.is_empty or len(parts(eroded)) != len(parts(g)):
        problems.append("a stroke is under 2w")
    if len(parts(dilated)) != len(parts(g)) or holes(dilated) != holes(g):
        problems.append("a gap is under 2w")
    b = g.bounds
    if b[1] < -eps or b[3] > CAP + eps:
        problems.append(f"outside baseline/cap: {b}")
    return problems


def to_json(g):
    out = []
    for p in parts(g):
        out.append({"exterior": [list(c) for c in p.exterior.coords],
                    "holes": [[list(c) for c in i.coords] for i in p.interiors]})
    return out


if __name__ == "__main__":
    failed = False
    data = {}
    for name, g in ICONS.items():
        problems = check(name, g)
        b = g.bounds
        print(f"{name:7} width {b[2] - b[0]:5.2f}w height {b[3] - b[1]:5.2f}w "
              f"{'OK' if not problems else 'FAIL: ' + '; '.join(problems)}")
        failed |= bool(problems)
        data[name] = {"width_w": b[2] - b[0], "polygons": to_json(affinity.translate(g, -(b[0] + b[2]) / 2, 0))}
    (R / "icons.json").write_text(json.dumps(data))

    sys.exit(1 if failed else 0)
