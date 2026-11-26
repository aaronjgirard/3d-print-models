## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Write the STLs in print position (centered on the 220 x 220 bed) for the Orca project."""
import os
import numpy as np
import trimesh
from manifold3d import Manifold as M
import manifold3d as m3
import planter as P

BED_C = (110.0, 110.0)


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=False)


def placed(d):
    allp = M.batch_boolean([d["body"]] + d["legs"], m3.OpType.Add)
    b = allp.bounding_box()
    shift = (BED_C[0] - (b[0] + b[3]) / 2, BED_C[1] - (b[1] + b[4]) / 2, 0.0)
    return shift


def main(out="out/stl"):
    os.makedirs(out, exist_ok=True)
    d = P.build()
    shift = placed(d)
    items = {"planter_pot.stl": d["body"],
             "planter_legs.stl": M.batch_boolean(d["legs"], m3.OpType.Add),
             "bottom_text_modifier.stl": d["modifier"]}
    for name, m in items.items():
        tm = to_trimesh(m.translate(shift))
        assert tm.is_watertight and tm.is_volume, name
        tm.export(os.path.join(out, name))
        print(name, np.round(tm.bounds, 2).tolist(), "volume %.1f cm3" % (tm.volume / 1000))
    np.save(os.path.join(out, "shift.npy"), np.array(shift))
    return d, shift


if __name__ == "__main__":
    main()
