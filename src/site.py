"""Generate the GitHub Pages site in ../docs from racks.json, build.json and slices.json."""

import html
import json
import shutil
from pathlib import Path

SRC = Path(__file__).resolve().parent
DOCS = SRC.parent / "docs"
BD = "https://www.boltdepot.com/Product-Details?product={}"
SYMBOL = {"socket": "Socket cap", "button": "Button head", "csk": "Countersunk", "pan": "Pan head",
          "nut": "Hex nut", "nyloc": "Nyloc nut", "washer": "Washer"}
ROW = {"front": "Front", "back": "Back"}

racks = json.loads((SRC / "racks.json").read_text())["racks"]
built = {r["id"]: r for r in json.loads((SRC / "build.json").read_text())["racks"]}
slices = json.loads((SRC / "slices.json").read_text())

CSS = """
body{margin:0;background:#f3efe6;color:#1d1b18;font:16px/1.5 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:32px 24px 64px}
h1{font-size:34px;margin:0 0 4px;color:#243c43}h2{margin:40px 0 12px;color:#243c43}
p.sub{margin:0 0 24px;color:#536a6d}a{color:#2f6f7a}
img{max-width:100%;display:block;border-radius:6px}
nav{margin-bottom:24px}nav a{margin-right:16px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}
.card{background:#fbf9f4;border:1px solid #ddd5c4;border-radius:8px;padding:12px}
.card h3{margin:8px 0 2px}.card p{margin:0;color:#536a6d}
table{border-collapse:collapse;width:100%;font-size:14px;background:#fbf9f4}
th,td{padding:6px 10px;border-bottom:1px solid #e3dccd;text-align:left}th{color:#536a6d;font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums}
ul{padding-left:20px}code{background:#e9e3d6;padding:1px 4px;border-radius:3px}
"""


def page(title, body):
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><link rel=stylesheet href=style.css></head>"
            f"<body><main>{body}</main></body></html>")


def nav():
    links = ["<a href=index.html>Overview</a>"] + [f"<a href={r['id']}.html>{html.escape(r['name'])}</a>" for r in racks]
    return "<nav>" + "".join(links) + "</nav>"


def label(c):
    return f"{SYMBOL[c['symbol']]}" + (f" {c['length']} mm" if c["length"] else "")


def rack_page(r):
    b = built[r["id"]]
    s_bins, s_shell = slices[f"{r['id']}-bins"], slices[f"{r['id']}-shell"]
    rows = []
    for row in ("front", "back"):
        for i, (bin_, info) in enumerate(zip(r["rows"][row], [x for x in b["bins"] if x["row"] == row]), 1):
            comps = bin_["compartments"] or [None]
            for j, c in enumerate(comps):
                where = f"{ROW[row]} {i}" + (f" ({bin_['cells']} cells)" if bin_["cells"] > 1 else "") if j == 0 else ""
                if c is None:
                    rows.append(f"<tr><td>{where}</td><td colspan=4>Spare</td></tr>")
                    continue
                rows.append(f"<tr><td>{where}</td><td>{c['thread']} {label(c)}</td><td class=n>{c['pieces']}</td>"
                            f"<td><a href='{BD.format(c['bolt_depot'])}'>{c['bolt_depot']}</a></td>"
                            f"<td class=n>{c['fill']:.0%}</td></tr>")
    body = f"""{nav()}<h1>{html.escape(r['name'])} rack</h1>
<p class=sub>6 × 2 Gridfinity cells, 6u bins in front, 7u behind.</p>
<img src=img/{r['id']}.png alt="{html.escape(r['name'])} rack render">
<h2>Download</h2>
<ul>
<li><a href=downloads/{r['id']}-bins.3mf>{r['id']}-bins.3mf</a>: {len(b['bins'])} bins on one 256 mm plate. Labels are parts on filament 2.
 Stock 0.20 mm: {s_bins['time']}, {s_bins['grams'][0]:.0f} g + {s_bins['grams'][1]:.0f} g, {s_bins['label_changes']} colour changes.</li>
<li><a href=downloads/{r['id']}-shell.3mf>{r['id']}-shell.3mf</a>: the rack. {s_shell['time']}, {s_shell['grams'][0]:.0f} g.</li>
</ul>
<h2>Bins</h2>
<table><tr><th>Bin</th><th>Compartment</th><th class=n>Pieces</th><th>Bolt Depot</th><th class=n>Fill</th></tr>
{''.join(rows)}</table>
<p class=sub>Fill: estimated bulk volume against a comfortable fill (40 cm³ per 6u cell, 47 cm³ per 7u).</p>"""
    return page(f"{r['name']} rack", body)


def index():
    cards = []
    for r in racks:
        n = len(built[r["id"]]["bins"])
        lines = sum(len(b["compartments"]) for row in r["rows"].values() for b in row)
        cards.append(f"<a class=card href={r['id']}.html><img src=img/{r['id']}.png alt=''>"
                     f"<h3>{html.escape(r['name'])}</h3><p>{n} bins, {lines} compartments</p></a>")
    parts = []
    for r in racks:
        for row in ("front", "back"):
            for b in r["rows"][row]:
                for c in b["compartments"]:
                    parts.append((c["thread"], c["symbol"], c["length"] or 0, c))
    order = {"socket": 0, "button": 1, "csk": 2, "pan": 3, "nut": 4, "nyloc": 5, "washer": 6}
    parts.sort(key=lambda p: (float(p[0][1:]), order[p[1]], p[2]))
    part_rows = "".join(f"<tr><td>{c['thread']}</td><td>{label(c)}</td><td class=n>{c['pieces']}</td>"
                        f"<td><a href='{BD.format(c['bolt_depot'])}'>{c['bolt_depot']}</a></td></tr>"
                        for _, _, _, c in parts)
    body = f"""{nav()}<h1>Fastener racks</h1>
<p class=sub>Three 6 × 2 Gridfinity racks on 1 inch pegboard. M2 to M5 stainless, two-colour Fillaprint labels.</p>
<img src=img/board.png alt="Three racks on pegboard">
<h2>Racks</h2><div class=cards>{''.join(cards)}</div>
<h2>Labels</h2>
<img src=img/symbols.png alt="Socket cap, button head, countersunk, pan head, hex nut, nyloc nut and washer symbols">
<ul>
<li>Front face: thread size, then symbol, dimension line and length. Inside back wall: the same, small.</li>
<li>Screws are side profiles; the dimension line runs where the length is measured.</li>
<li><a href=https://github.com/thereprocase/double-bead>Fillaprint</a> at the 0.42 mm reference size: every stroke and gap is at least two lines wide.</li>
<li>Labels are flush inlays 0.84 mm deep, on walls thickened by the same amount.</li>
</ul>
<h2>Print</h2>
<ul>
<li>0.4 mm nozzle, 0.42 mm line width, 0.20 mm layers. Bins: filament 1 body, filament 2 labels. Racks: one filament.</li>
<li>Pegboard: 1 inch grid, ¼ inch holes, ¼ inch board. Two upturned hooks and two pins per rack; racks 11 inches apart.</li>
<li>Rack shells sit on Gridfinity pockets; bins lift out.</li>
</ul>
<h2>Parts</h2>
<table><tr><th>Thread</th><th>Part</th><th class=n>Pieces</th><th>Bolt Depot</th></tr>{part_rows}</table>
<p class=sub>Stainless 18-8.</p>
<h2>Source</h2>
<p><a href=https://github.com/thereprocase/gridfinity-fastener-racks>Build scripts</a> (FreeCAD, Python). CC BY 4.0; Fillaprint under SIL OFL 1.1.</p>"""
    return page("Fastener racks", body)


def main():
    (DOCS / "img").mkdir(parents=True, exist_ok=True)
    (DOCS / "downloads").mkdir(parents=True, exist_ok=True)
    for name in ["board", *(r["id"] for r in racks)]:
        shutil.copy(SRC / "renders" / f"{name}.png", DOCS / "img" / f"{name}.png")
    shutil.copy(SRC / "specimen.png", DOCS / "img" / "symbols.png")
    for f in (SRC / "dist").glob("*.3mf"):
        shutil.copy(f, DOCS / "downloads" / f.name)
    (DOCS / "style.css").write_text(CSS.strip() + "\n")
    (DOCS / "index.html").write_text(index())
    for r in racks:
        (DOCS / f"{r['id']}.html").write_text(rack_page(r))
    (DOCS / ".nojekyll").write_text("")
    print("site written:", sorted(p.name for p in DOCS.iterdir()))


if __name__ == "__main__":
    main()
