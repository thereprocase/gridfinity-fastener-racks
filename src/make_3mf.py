"""Pack the built meshes into 3MF plates for OrcaSlicer / Bambu Studio.

<rack>-bins.3mf: the rack's bins laid out as in the rack (6 x 2 cells fit a 256 mm bed);
each bin is one object with two parts, the body on filament 1 and the labels on filament 2.
<rack>-shell.3mf: the rack itself, on its base, filament 1.
"""

import json
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parent
OUT = R / "out"
DEST = Path(sys.argv[1]) if len(sys.argv) > 1 else R / "dist"


def read_stl(path):
    data = path.read_bytes()
    n = struct.unpack("<I", data[80:84])[0]
    tri = np.frombuffer(data[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))["v"]
    verts, idx = np.unique(tri.reshape(-1, 3).round(4), axis=0, return_inverse=True)
    return verts, idx.reshape(-1, 3)


def mesh_xml(verts, tris):
    v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in verts)
    t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
    return f"<mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh>"


def write_3mf(path, objects):
    """objects: [(name, [(part name, extruder, verts, tris)], (dx, dy))]."""
    resources, build, settings = [], [], []
    oid = 1
    for name, parts, (dx, dy) in objects:
        comp_ids = []
        part_cfg = []
        for pname, extruder, verts, tris in parts:
            resources.append(f'<object id="{oid}" type="model">{mesh_xml(verts, tris)}</object>')
            comp_ids.append(oid)
            part_cfg.append(f'<part id="{oid}" subtype="normal_part"><metadata key="name" value="{pname}"/>'
                            f'<metadata key="extruder" value="{extruder}"/></part>')
            oid += 1
        comps = "".join(f'<component objectid="{c}"/>' for c in comp_ids)
        resources.append(f'<object id="{oid}" type="model"><components>{comps}</components></object>')
        build.append(f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 {dx:.3f} {dy:.3f} 0" printable="1"/>')
        settings.append(f'<object id="{oid}"><metadata key="name" value="{name}"/>'
                        f'<metadata key="extruder" value="1"/>{"".join(part_cfg)}</object>')
        oid += 1
    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(resources)}</resources><build>{"".join(build)}</build></model>')
    config = f'<?xml version="1.0" encoding="UTF-8"?><config>{"".join(settings)}</config>'
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
                   '<Default Extension="config" ContentType="text/xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/model_settings.config", config)


def main():
    built = json.loads((R / "build.json").read_text())
    for rack in built["racks"]:
        rid = rack["id"]
        objects = []
        # Bins keep their rack positions, shifted to the bed centre (128, 128); the meshes
        # are already in rack coordinates (x 0-252, y 0-84).
        for b in rack["bins"]:
            parts = [("body", 1, *read_stl(OUT / rid / f"{b['name']}-body.stl"))]
            labels = OUT / rid / f"{b['name']}-labels.stl"
            if labels.exists():
                parts.append(("labels", 2, *read_stl(labels)))
            objects.append((f"{rid} {b['name']}", parts, (128 - 126, 128 - 42)))
        write_3mf(DEST / f"{rid}-bins.3mf", objects)
        verts, tris = read_stl(OUT / rid / "rack.stl")
        write_3mf(DEST / f"{rid}-shell.3mf", [(f"{rid} rack", [("rack", 1, verts, tris)], (128 - 126, 128 - 47))])
        print("packed", rid)


if __name__ == "__main__":
    main()
