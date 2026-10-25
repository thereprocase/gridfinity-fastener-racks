"""Write render scenes for the board and each rack, then capture them with the render skill."""

import json
import os
import subprocess
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
# The renderer is a separate WebGL tool (prepare.py, capture.mjs); point RENDERER at its scripts.
SKILL = Path(os.environ["RENDERER"])
INCH = 25.4
RACKS = [("m3", "M3", 0.0), ("m2-m4", "M2 · M2.5 · M4", 11 * INCH), ("m5", "M5", 22 * INCH)]
TEAL, RACK, IVORY, BOARD = [0.36, 0.64, 0.69], [0.30, 0.55, 0.60], [0.97, 0.95, 0.90], [0.80, 0.70, 0.55]


def crop(path, margin=24):
    """Trim the plain background around the model."""
    from PIL import Image, ImageChops
    im = Image.open(path).convert("RGB")
    bg = Image.new("RGB", im.size, im.getpixel((1, 1)))
    box = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 12 else 0).getbbox()
    if box:
        l, t, r, b = box
        im.crop((max(l - margin, 0), max(t - margin, 0), min(r + margin, im.width), min(b + margin, im.height))).save(path)


def tf(dx=0.0):
    # Z-up model to the renderer's -Y-up frame, after shifting the rack along the board.
    return [[1, 0, 0, dx], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]


def rack_parts(rid, dx=0.0):
    return [{"mesh": f"../out/render/{rid}-rack.stl", "color": RACK, "transform": tf(dx)},
            {"mesh": f"../out/render/{rid}-bins.stl", "color": TEAL, "transform": tf(dx)},
            {"mesh": f"../out/render/{rid}-labels.stl", "color": IVORY, "transform": tf(dx)}]


scenes = {
    "board": {"title": "Fastener racks", "subtitle": "Three 6 x 2 Gridfinity racks on 1 inch pegboard",
              "caption": "M3 · M2, M2.5, M4 · M5. Flush two-colour Fillaprint labels.",
              "camera": {"yaw": -1.5, "pitch": 0.3, "zoom": 0.66, "target": [405, -30, 40]},
              "parts": [{"mesh": "../out/render/board-pegboard.stl", "color": BOARD, "transform": tf()}]
              + [p for rid, _, dx in RACKS for p in rack_parts(rid, dx)]},
}
for rid, name, _ in RACKS:
    scenes[rid] = {"title": f"{name} rack", "subtitle": "6u bins in front, 7u behind",
                   "caption": "Labels: thread size, symbol, dimension line, length.",
                   "camera": {"yaw": -1.22, "pitch": 0.6, "zoom": 0.84}, "parts": rack_parts(rid)}

(R / "scenes").mkdir(exist_ok=True)
for name, scene in scenes.items():
    # The site supplies headings; the images carry the model only.
    scene.update(title="", subtitle="", caption="")
    path = R / "scenes" / f"{name}.json"
    path.write_text(json.dumps(scene, indent=1, ensure_ascii=False))
    work = R / "render-work" / name
    subprocess.run([sys.executable, str(SKILL / "prepare.py"), str(path), str(work)], check=True,
                   stdout=subprocess.DEVNULL)
    subprocess.run(["node", str(SKILL / "capture.mjs"), str(work), str(R / "renders" / f"{name}.png")],
                   check=True, stdout=subprocess.DEVNULL)
    crop(R / "renders" / f"{name}.png")
    print("rendered", name)
