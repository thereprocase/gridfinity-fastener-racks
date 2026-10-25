"""Draw icons.json as a sample sheet on the baseline/cap guides (needs matplotlib)."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

R = Path(__file__).resolve().parent
CAP = 14.0
icons = json.loads((R / "icons.json").read_text())
fig, ax = plt.subplots(figsize=(12, 2.6), dpi=150)
fig.patch.set_facecolor("#F6F1E4")
ax.set_facecolor("#F6F1E4")
x = 0.0
for name, icon in icons.items():
    half = icon["width_w"] / 2
    for poly in icon["polygons"]:
        verts, codes = [], []
        for ring in [poly["exterior"], *poly["holes"]]:
            verts += [(px + x + half, py) for px, py in ring]
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(ring) - 2) + [MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes), fc="#1F2A30", ec="none"))
    ax.text(x + half, -3.2, name, ha="center", fontsize=11, color="#1F2A30")
    x += icon["width_w"] + 6
ax.plot([-2, x - 4], [0, 0], color="#F9A048", lw=1)
ax.plot([-2, x - 4], [CAP, CAP], color="#F9A048", lw=1, ls="--")
ax.text(x - 3.5, CAP, "cap 14w = 5.88 mm", va="center", fontsize=9, color="#9A6A2A")
ax.text(x - 3.5, 0, "baseline", va="center", fontsize=9, color="#9A6A2A")
ax.set_xlim(-3, x + 14)
ax.set_ylim(-5, CAP + 2)
ax.set_aspect("equal")
ax.axis("off")
fig.savefig(R / "specimen.png", facecolor=fig.get_facecolor(), bbox_inches="tight")
