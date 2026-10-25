"""Build the three pegboard racks, their bins and label inlays from racks.json.

Run: flatpak run --command=FreeCADCmd org.freecad.FreeCAD -c "exec(open('build.py').read())"

Per rack, writes to out/<rack>/: rack.stl and rack.step (the shelf, Gridfinity pockets and
pegboard hooks), and for every bin <row>-<n>-body.stl and <row>-<n>-labels.stl, the two
bodies of a multi-material print, plus <row>-<n>.step with both. Render meshes go to
out/render/. The whole-board assembly is out/render/board-*.stl.

Units mm. X along the pegboard, Y from the front (0) toward the board, Z up. The front row
of bins is 6u (42 mm), the back row 7u (49 mm).
"""

import json
import sys
from pathlib import Path

import FreeCAD as A
import MeshPart
import Part

R = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(R))
import fr_geom as g  # noqa: E402

V = A.Vector
OUT = R / "out"
PITCH, WALL, FLOOR = 42.0, 1.26, 5.8
HEIGHT = {6: 42.0, 7: 49.0}
ROW_Y = {"front": PITCH / 2, "back": PITCH * 1.5}

# Rack: a 1.6 mm floor under the pockets, pockets as deep as the bin foot (4.75 mm).
BASE_FLOOR = 1.6
POCKET_CLEAR = 0.25
PANEL_T, PANEL_TOP = 5.0, 70.0
# US pegboard: 1 inch grid, 1/4 inch holes, 1/4 inch board.
INCH = 25.4
BOARD_T, HOLE_D = 6.35, 6.35
PIN_R = 2.9
HOOK_X = [126.0 - 4 * INCH, 126.0 + 4 * INCH]  # 8 inches apart, centred on the rack
HOOK_Z, PIN_Z = 58.0, 58.0 - INCH


def export(shape, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.1, Relative=False)
    mesh.write(str(path))


def bin_shell(cx, cy, cells, H):
    """Bench-bin body: Gridfinity feet, 1.26 mm walls, sloped inside floor edge."""
    bx, by = PITCH * cells - 0.5, PITCH - 0.5
    feet = [g.loft([(0, 35.6, 35.6, .8), (.8, 37.2, 37.2, 1.6), (2.6, 37.2, 37.2, 1.6), (4.75, 41.5, 41.5, 3.75)],
                   cx + (i - (cells - 1) / 2) * PITCH, cy) for i in range(cells)]
    outer = Part.Face(g.rounded_wire(bx, by, 3.75, 4.75, cx, cy)).extrude(V(0, 0, H - 4.75))
    solid = outer.multiFuse(feet).removeSplitter()
    ix, iy = bx - 2 * WALL, by - 2 * WALL
    cavity = g.loft([(FLOOR, bx - 6.52, by - 6.52, 1), (7.8, ix, iy, 3), (H + 1, ix, iy, 3)], cx, cy)
    return solid.cut(cavity), outer, bx, by, ix, iy


def build_bin(cx, cy, b):
    """One bin with its compartments and label inlays; returns (body, labels, report)."""
    H = HEIGHT[b["height_u"]]
    comps = b["compartments"]
    solid, outer, bx, by, ix, iy = bin_shell(cx, cy, b["cells"], H)
    x0, n = cx - ix / 2, max(len(comps), 1)
    usable = ix - (n - 1) * WALL
    slots, x = [], x0
    for c in comps or [{"fraction": 1.0}]:
        w = usable * c["fraction"]
        slots.append((x, w))
        x += w + WALL
    for sx, sw in slots[1:]:
        solid = solid.fuse(Part.makeBox(WALL, iy, H - FLOOR, V(sx - WALL, cy - iy / 2, FLOOR)).common(outer))
    if not comps:
        return solid.removeSplitter(), None, []
    front_out, back_face = cy - by / 2, cy + iy / 2
    back_in = back_face - g.INLAY
    # Both labelled walls are 2w thicker on the inside, so a full wall stands behind the inlay.
    solid = solid.fuse([Part.makeBox(ix, g.INLAY, H - FLOOR, V(x0, front_out + WALL, FLOOR)).common(outer),
                        Part.makeBox(ix, g.INLAY, H - FLOOR, V(x0, back_in, FLOOR)).common(outer)]).removeSplitter()
    texts, report = [], []
    thread, big = b["thread"], 1.5

    def place(parts, xc, base, face_y, scale, where, room, label):
        pieces, width = g.label_line(parts, xc, (base, face_y), "front", scale)
        texts.extend(pieces)
        report.append({"where": where, "label": label, "width_mm": round(width, 2), "room_mm": round(room, 2)})

    top = H - 3.0
    place([g.text_faces(thread, big)], cx, top - g.CAP * big, front_out, big, "front", bx - 8, thread)
    line2 = top - g.CAP * big - g.LINE_PITCH * big * 0.8
    for (sx, sw), c in zip(slots, comps):
        xc, room = sx + sw / 2, sw - 4 * g.W_LINE
        length = str(c["length"]) if c["length"] else ""
        name = f"{c['symbol']} {length}".strip()
        if n == 1:
            place(g.piece(c["symbol"], length, big), cx, line2, front_out, big, "front", bx - 8, name)
            word = ([], 3 * g.W_LINE)
            place([g.text_faces(thread), word] + g.piece(c["symbol"], length), xc, H - 2.5 - g.CAP, back_in, 1.0,
                  "inside", room, f"{thread} {name}")
        else:
            place(g.piece(c["symbol"], length), xc, line2, front_out, 1.0, "front", room, name)
            place(g.piece(c["symbol"], length), xc, H - 2.5 - g.CAP, back_in, 1.0, "inside", room, name)
            # The thread size again under the symbol where it fits; the front shows it big.
            thread_faces = g.text_faces(thread)
            if thread_faces[1] <= room:
                place([thread_faces], xc, H - 2.5 - g.CAP - g.LINE_PITCH, back_in, 1.0, "inside", room, thread)
    labels = Part.Compound(texts)
    return solid.cut(labels), labels, report


def pocket(cx, cy):
    c = 2 * POCKET_CLEAR
    return g.loft([(-0.01, 35.6 + c, 35.6 + c, .8 + POCKET_CLEAR), (.8, 37.2 + c, 37.2 + c, 1.6 + POCKET_CLEAR),
                   (2.6, 37.2 + c, 37.2 + c, 1.6 + POCKET_CLEAR), (4.76, 42.0, 42.0, 4.0)], cx, cy)


def pin(x, z, y0, length):
    """Teardrop pin along +Y, point down and cut flat at the radius, so it prints unsupported."""
    circle = Part.Face(Part.Wire(Part.makeCircle(PIN_R, V(x, y0, z), V(0, 1, 0))))
    t = PIN_R / 2 ** 0.5
    tip = Part.Face(Part.makePolygon([V(x - t, y0, z - t), V(x + t, y0, z - t), V(x + PIN_R - (PIN_R * 2 ** 0.5 - PIN_R), y0, z - PIN_R),
                                      V(x - PIN_R + (PIN_R * 2 ** 0.5 - PIN_R), y0, z - PIN_R), V(x - t, y0, z - t)]))
    return circle.fuse(tip).extrude(V(0, length, 0))


def build_rack():
    """Shelf with 6 x 2 Gridfinity pockets, back panel and pegboard hooks (one per rack)."""
    base = Part.makeBox(6 * PITCH, 2 * PITCH, BASE_FLOOR + 4.75, V(0, 0, -BASE_FLOOR))
    for row_y in ROW_Y.values():
        for i in range(6):
            base = base.cut(pocket(PITCH / 2 + i * PITCH, row_y))
    panel = Part.makeBox(6 * PITCH, PANEL_T, PANEL_TOP + BASE_FLOOR, V(0, 2 * PITCH, -BASE_FLOOR))
    back = 2 * PITCH + PANEL_T
    reach = BOARD_T + 0.5
    parts = [panel]
    for x in HOOK_X:
        parts.append(pin(x, HOOK_Z, back, reach + 4))
        parts.append(pin(x, PIN_Z, back, reach))
        # Upturned hook behind the board; 45-degree underside so it prints without support.
        y1 = back + reach
        prof = Part.makePolygon([V(x - PIN_R, y1, HOOK_Z - PIN_R), V(x - PIN_R, y1 + 4, HOOK_Z - PIN_R + 4),
                                 V(x - PIN_R, y1 + 4, HOOK_Z + 12), V(x - PIN_R, y1, HOOK_Z + 12),
                                 V(x - PIN_R, y1, HOOK_Z - PIN_R)])
        parts.append(Part.Face(prof).extrude(V(2 * PIN_R, 0, 0)))
    rack = base.fuse(parts).removeSplitter()
    assert rack.isValid() and len(rack.Solids) == 1
    return rack


def main():
    data = json.loads((R / "racks.json").read_text())
    rack_shape = build_rack()
    summary = {"racks": []}
    for rack in data["racks"]:
        rid = rack["id"]
        export(rack_shape, OUT / rid / "rack.stl")
        rack_shape.exportStep(str(OUT / rid / "rack.step"))
        bodies, labels, bins = [], [], []
        for row in ("front", "back"):
            x = 0.0
            for i, b in enumerate(rack["rows"][row], 1):
                cx = x + PITCH * b["cells"] / 2
                body, lab, report = build_bin(cx, ROW_Y[row], b)
                assert body.isValid(), (rid, row, i)
                name = f"{row}-{i}"
                export(body, OUT / rid / f"{name}-body.stl")
                shapes = [body]
                if lab is not None:
                    export(lab, OUT / rid / f"{name}-labels.stl")
                    labels.append(lab)
                    shapes.append(lab)
                Part.Compound(shapes).exportStep(str(OUT / rid / f"{name}.step"))
                bodies.append(body)
                bins.append({"name": name, "row": row, "cells": b["cells"], "height_u": b["height_u"],
                             "thread": b["thread"], "keys": [c["key"] for c in b["compartments"]],
                             "body_cm3": round(body.Volume / 1000, 1),
                             "labels_cm3": round(lab.Volume / 1000, 2) if lab is not None else 0, "labels": report})
                x += PITCH * b["cells"]
        export(rack_shape, OUT / "render" / f"{rid}-rack.stl")
        export(Part.Compound(bodies), OUT / "render" / f"{rid}-bins.stl")
        export(Part.Compound(labels), OUT / "render" / f"{rid}-labels.stl")
        summary["racks"].append({"id": rid, "rack_cm3": round(rack_shape.Volume / 1000, 1), "bins": bins})
    too_wide = [(r["id"], b["name"], l) for r in summary["racks"] for b in r["bins"] for l in b["labels"]
                if l["width_mm"] > l["room_mm"]]
    summary["too_wide"] = too_wide
    (R / "build.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    print("BUILD PASS", sum(len(r["bins"]) for r in summary["racks"]), "bins; too wide:", too_wide, flush=True)


main()
