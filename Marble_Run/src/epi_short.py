## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Shorter Epitrochoid ("epi_short" in config/project.json): fewer loops, plug top
on a smaller whole number of tube pitches (Aaron 2026-11-25: 3 tubes tall, 4 loops).

The track is one loop repeated: turning the piece by loop_deg about the post axis
and raising it by loop_dz puts every loop on the one above it (measured from the
piece itself). So drop loops are taken out by keeping everything below cut_z and
bringing everything above cut_z + drop * loop_dz down by drop * loop_dz onto it,
the lower part turned by drop * loop_deg to meet it (the two overlap by overlap mm). The plug top then sits
drop * loop_dz lower; the rest of the way to tubes * tube_pitch is taken out of
the band squash[0]..squash[1] (after the splice) by scaling z there, so the
socket, the exit window and the plug keep their sizes and the loops drop a
little less each.

Usage:
    python src/epi_short.py [--src STL] [--out STL]
'''
import argparse
import os
import sys

import numpy as np
import trimesh
from manifold3d import Manifold, Mesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import load_cfg, root


def to_manifold(path):
    t = trimesh.load(path)
    return Manifold(Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))


def splice(m, c):
    '''
    Take out c['drop'] loops.

    Returns:
        Manifold: the spliced piece
    '''
    n, th, dz = c['drop'], c['loop_deg'], c['loop_dz']
    z, ov     = c['cut_z'], c['overlap']
    ## the lower part is turned, not the upper: the top post holds the fine exit-window work,
    ## whose tiny faces would not survive turning and rounding to float32
    low  = m.trim_by_plane((0.0, 0.0, -1.0), -(z + ov)).rotate((0.0, 0.0, n * th))
    high = m.trim_by_plane((0.0, 0.0, 1.0), z + n * dz - ov).translate((0.0, 0.0, -n * dz))
    return low + high


def squash(m, z0, z1, k, step):
    '''
    Scale z by k between z0 and z1 (z above z1 moves down by (1 - k)(z1 - z0)),
    after cutting every edge to at most step mm so the bends at z0 and z1 stay on
    the mesh.
    '''
    def f(v):
        z = v[:, 2]
        v[:, 2] = np.where(z <= z0, z, np.where(z >= z1, z - (1 - k) * (z1 - z0), z0 + k * (z - z0)))
        return v

    return m.refine_to_length(step).warp_batch(f)


def main():
    cfg = load_cfg()
    c   = cfg['epi_short']
    ap  = argparse.ArgumentParser()
    ap.add_argument('--src', default=os.path.join(root, c['src']))
    ap.add_argument('--out', default=os.path.join(root, c['out']))
    a   = ap.parse_args()

    m    = to_manifold(a.src)
    top0 = m.bounding_box()[5]
    m    = splice(m, c)
    print('spliced: %d loops out, volume %.2f cm3, genus %d, top %.2f' % (c['drop'], m.volume() / 1000, m.genus(), m.bounding_box()[5]))
    ## plug top wanted at tubes pitches plus the plug, the same plug length above the shoulder as before
    plug  = top0 - cfg['epi_top']['plug_z'][0]
    want  = c['tubes'] * cfg['tube_pitch'] + plug
    z0, z1 = c['squash']
    k     = 1 - (m.bounding_box()[5] - want) / (z1 - z0)
    m     = squash(m, z0, z1, k, c['step'])
    print('squash z %.1f-%.1f by %.4f (%.1f%%): top %.2f (want %.2f), volume %.2f cm3, genus %d' % (z0, z1, k, 100 * (1 - k), m.bounding_box()[5], want, m.volume() / 1000, m.genus()))

    ## merge slivers left by turning the top part (float32 vertices) so the STL stays watertight
    if c['tol'] > 0:
        m = m.simplify(c['tol'])
    t = trimesh.Trimesh(*[np.asarray(x) for x in (m.to_mesh().vert_properties[:, :3], m.to_mesh().tri_verts)], process=False)
    t.export(a.out)
    print('wrote %s, %d faces, watertight %s, bounds %s' % (a.out, len(t.faces), t.is_watertight, np.round(t.bounds, 2).tolist()))


if __name__ == '__main__':
    main()
