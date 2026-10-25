"""A pegboard section for the whole-board render: 1 inch grid, 1/4 inch holes, aligned to the hooks."""

from pathlib import Path

import FreeCAD as A
import MeshPart
import Part

R = Path.cwd()
V = A.Vector
INCH, T = 25.4, 6.35
Y0 = 2 * 42.0 + 5.0  # back face of the rack panels
X0, Z0 = 126.0 - 4 * INCH, 58.0  # a hook hole; every other hole is a whole number of inches away
OFFSETS = [0.0, 11 * INCH, 22 * INCH]  # rack placements, so every hook meets a hole
xmin, xmax, zmin, zmax = -1.5 * INCH, 22 * INCH + 252 + 1.5 * INCH, -2 * INCH, 6 * INCH
board = Part.makeBox(xmax - xmin, T, zmax - zmin, V(xmin, Y0, zmin))
holes = []
k0, k1 = int((xmin - X0) / INCH) + 1, int((xmax - X0) / INCH)
j0, j1 = int((zmin - Z0) / INCH) + 1, int((zmax - Z0) / INCH)
for k in range(k0, k1 + 1):
    for j in range(j0, j1 + 1):
        holes.append(Part.makeCylinder(T / 2, T + 2, V(X0 + k * INCH, Y0 - 1, Z0 + j * INCH), V(0, 1, 0)))
board = board.cut(Part.Compound(holes))
MeshPart.meshFromShape(Shape=board, LinearDeflection=0.05, AngularDeflection=0.2, Relative=False).write(
    str(R / "out" / "render" / "board-pegboard.stl"))
print("BOARD PASS", len(holes), "holes")
