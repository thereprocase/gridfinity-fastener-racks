"""Shared geometry for the fastener racks: rounded loft sections and Fillaprint label inlays.

Labels are sized for one extrusion width w = 0.42 mm (0.4 mm nozzle): capitals 14w tall,
symbols from icons.json on the same baseline, and every stroke and gap at least 2w.
"""

import json
import math
from pathlib import Path

import FreeCAD as A
import Part

V = A.Vector
R = Path(__file__).resolve().parent
FONT_DIR, FONT = str(R / "fonts") + "/", "Fillaprint-Regular.ttf"  # Fillaprint, SIL OFL 1.1

PITCH, BODY, WALL = 42.0, 41.5, 1.26
W_LINE = 0.42  # extrusion width the labels are sized for
CAP = 14 * W_LINE  # 5.88 mm capital height
LINE_PITCH = 28 * W_LINE  # 11.76 mm baseline to baseline
SIZE_PER_CAP = 10.0 / 15.36  # FreeCAD makeWireString size per mm of Fillaprint capital
INLAY = 2 * W_LINE  # inlay depth, and the wall thickening that holds it
ICONS = json.loads((R / "icons.json").read_text())
GAP = 1.5 * W_LINE  # space between a symbol and its text

def rounded_wire(w, h, r, z, cx=0, cy=0):
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    pts = [(x0 + r, y0), (x1 - r, y0), (x1, y0 + r), (x1, y1 - r), (x1 - r, y1), (x0 + r, y1),
           (x0, y1 - r), (x0, y0 + r)]
    edges = [Part.makeLine(V(*pts[a], z), V(*pts[b], z)) for a, b in [(0, 1), (2, 3), (4, 5), (6, 7)]]
    for ax, ay, a0 in [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]:
        circle = Part.Circle(V(ax, ay, z), V(0, 0, 1), r)
        edges.append(Part.ArcOfCircle(circle, math.radians(a0), math.radians(a0 + 90)).toShape())
    return Part.Wire(Part.sortEdges(edges)[0])


def loft(sections, cx=0, cy=0):
    return Part.makeLoft([rounded_wire(w, h, r, z, cx, cy) for z, w, h, r in sections], True, True)


def text_faces(s, scale=1.0):
    """Fillaprint text as flat faces in XY, baseline on y = 0, left edge at x = 0."""
    if not s:
        return [], 0.0
    chars = Part.makeWireString(s, FONT_DIR, FONT, CAP * scale * SIZE_PER_CAP, 0)
    faces = [Part.makeFace(wires, "Part::FaceMakerBullseye") for wires in chars if wires]
    bb = Part.Compound(faces).BoundBox
    for f in faces:
        f.translate(V(-bb.XMin, 0, 0))
    return faces, bb.XLength


def icon_faces(name, scale=1.0):
    """A symbol from icons.json as flat faces in XY (mm), baseline on y = 0, left edge at x = 0."""
    icon = ICONS[name]
    half, unit = icon["width_w"] / 2, W_LINE * scale
    faces = []
    for poly in icon["polygons"]:
        def wire(ring):
            return Part.makePolygon([V((x + half) * unit, y * unit, 0) for x, y in ring])
        face = Part.Face(wire(poly["exterior"]))
        for hole in poly["holes"]:
            face = face.cut(Part.Face(wire(hole)))
        faces += face.Faces
    return faces, icon["width_w"] * unit


# Where each screw's length is measured, in w above the baseline (icons.py profiles):
# under the head for socket, button and pan; overall for countersunk.
LENGTH_SPAN = {"socket": 10.0, "button": 10.0, "pan": 10.5, "csk": 14.0}


def dimension_faces(icon, scale=1.0):
    """A vertical dimension line from the screw's tip to where its length is measured.

    2w shaft, arrowheads 2.5w tall and 4.5w wide; tips on the baseline and at the span.
    """
    u = W_LINE * scale
    top, head, half = LENGTH_SPAN[icon] * u, 2.5 * u, 2.25 * u

    def poly(pts):
        return Part.Face(Part.makePolygon([V(x, y, 0) for x, y in pts + [pts[0]]]))

    parts = [poly([(half, 0), (2 * half, head), (0, head)]),
             poly([(half, top), (2 * half, top - head), (0, top - head)]),
             poly([(half - u, head - u), (half + u, head - u), (half + u, top - head + u), (half - u, top - head + u)])]
    return parts[0].fuse(parts[1:]).removeSplitter().Faces, 2 * half


def piece(icon, length, scale=1.0):
    """Symbol, then for screws the dimension line and the length."""
    if not length:
        return [icon_faces(icon, scale)]
    return [icon_faces(icon, scale), dimension_faces(icon, scale), text_faces(length, scale)]


def label_line(parts, x_center, baseline, place, scale=1.0):
    """Lay out [faces, width] pieces on one centred line and turn them into inlay solids.

    place="front": standing in a wall whose outside face is y = baseline[1], read from -Y,
    inlaid toward +Y. place="top": lying on a face z = baseline[1], read from -Y, inlaid
    downward; baseline[0] is then the baseline's y.
    """
    gap = GAP * scale
    total = sum(w for _, w in parts) + gap * (len(parts) - 1)
    x = x_center - total / 2
    solids = []
    for faces, width in parts:
        for f in faces:
            g = f.copy()
            g.translate(V(x, 0, 0))
            solid = g.extrude(V(0, 0, INLAY))
            if place == "front":
                # Face +Y becomes +Z; the depth (+Z) turns into the wall (+Y).
                solid.rotate(V(0, 0, 0), V(1, 0, 0), 90)
                solid.translate(V(0, baseline[1] + INLAY, baseline[0]))
            else:
                solid.translate(V(0, baseline[0], baseline[1] - INLAY))
            solids.append(solid)
        x += width + gap
    return solids, total
