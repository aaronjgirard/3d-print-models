## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Cut recessed text into a vertical side wall of a relief STL.

The wall is the longest straight edge of the footprint whose outward normal
points within --tol degrees of --side. The text is centered on that edge,
reads left to right for a viewer standing outside the wall, and is cut
--depth mm into the wall. --along places the text center that many mm from
the wall's left end as seen from outside (default: centered).

Usage:
    python add_wall_text.py IN.stl OUT.stl --text "1:29,420" [--side west]
        [--cap 7] [--depth 0.8] [--zc 7.5] [--along MM] [--font "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]
'''
import argparse

import manifold3d as m3d
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

sides = {'east': 0.0, 'north': 90.0, 'west': 180.0, 'south': 270.0}
rec   = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])


def read_stl(path):
    '''
    Read a binary STL into an (n, 3, 3) triangle array.

    Args:
        path (str): binary STL

    Returns:
        ndarray: triangle vertices [mm]
    '''
    raw = np.fromfile(path, dtype=np.uint8)
    n   = int(raw[80:84].view(np.uint32)[0])
    return np.frombuffer(raw[84:84 + 50 * n].tobytes(), dtype=rec)['v'].astype(np.float64)


def write_stl(path, tri):
    '''
    Write an (n, 3, 3) triangle array as a binary STL.

    Args:
        path (str)    : output STL
        tri  (ndarray): triangle vertices [mm]
    '''
    nrm  = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-15
    out  = np.zeros(len(tri), dtype=rec)
    out['n'], out['v'] = nrm, tri
    with open(path, 'wb') as fh:
        fh.write(b'add_wall_text'.ljust(80, b' '))
        fh.write(np.uint32(len(tri)).tobytes())
        fh.write(out.tobytes())


def to_manifold(tri):
    '''
    Merge shared vertices and build a manifold3d solid.

    Args:
        tri (ndarray): triangle vertices [mm]

    Returns:
        Manifold: solid
    '''
    vert, idx = np.unique(tri.reshape(-1, 3).astype(np.float32), axis=0, return_inverse=True)
    mesh      = m3d.Mesh(vert_properties=vert, tri_verts=idx.reshape(-1, 3).astype(np.uint32))
    solid     = m3d.Manifold(mesh)
    if solid.status() != m3d.Error.NoError:
        raise ValueError(f'input mesh is not manifold: {solid.status()}')
    return solid


def pick_wall(tri, side, tol):
    '''
    Find the longest footprint edge facing the requested side.

    Args:
        tri  (ndarray): triangle vertices [mm]
        side (str)    : east, north, west or south
        tol  (float)  : allowed azimuth misfit [deg]

    Returns:
        tuple: edge start, edge end (xy) and unit outward normal (xy)
    '''
    zmin = tri[:, :, 2].min()
    bot  = tri[(np.abs(tri[:, :, 2] - zmin) < 1e-6).all(1)]
    foot = orient(unary_union([Polygon(t[:, :2]) for t in bot]).simplify(0.01), sign=1.0)
    ring = np.array(foot.exterior.coords)
    best = None
    for a, b in zip(ring[:-1], ring[1:]):
        d   = b - a
        nrm = np.array([d[1], -d[0]]) / np.linalg.norm(d)
        az  = np.degrees(np.arctan2(nrm[1], nrm[0])) % 360
        mis = abs((az - sides[side] + 180) % 360 - 180)
        if mis <= tol and (best is None or np.linalg.norm(d) > np.linalg.norm(best[1] - best[0])):
            best = (a, b, nrm)
    if best is None:
        raise ValueError(f'no footprint edge faces {side} within {tol} deg')
    return best


def text_solid(text, font, cap, depth):
    '''
    Build text as a solid in local coordinates: x along the reading direction,
    y up, z out of the wall. Centered on x and on the cap height, spanning
    z = -depth to +1.

    Args:
        text  (str)  : text to cut
        font  (str)  : font file
        cap   (float): cap height [mm]
        depth (float): recess depth [mm]

    Returns:
        tuple: Manifold, text width [mm]
    '''
    prop  = FontProperties(fname=font)
    ref   = TextPath((0, 0), '0', size=10, prop=prop).get_extents()
    scl   = cap / ref.height
    path  = TextPath((0, 0), text, size=10 * scl, prop=prop)
    ext   = path.get_extents()
    rings = [p - [ext.x0 + ext.width / 2, cap / 2] for p in path.to_polygons()]
    sec   = m3d.CrossSection(rings, fillrule=m3d.FillRule.EvenOdd)
    return sec.extrude(depth + 1.0).translate([0, 0, -depth]), ext.width


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('inp')
    ap.add_argument('out')
    ap.add_argument('--text' , required=True)
    ap.add_argument('--side' , default='west', choices=sides)
    ap.add_argument('--tol'  , type=float, default=30.0)     # [deg] wall azimuth tolerance
    ap.add_argument('--cap'  , type=float, default=7.0)      # [mm] cap height
    ap.add_argument('--depth', type=float, default=0.8)      # [mm] recess depth
    ap.add_argument('--zc'   , type=float, default=7.5)      # [mm] height of text center above the underside
    ap.add_argument('--along', type=float, default=None)     # [mm] text center from the wall's left end seen from outside
    ap.add_argument('--font' , default='/System/Library/Fonts/Supplemental/Arial Bold.ttf')
    args = ap.parse_args()

    tri          = read_stl(args.inp)
    a, b, nrm    = pick_wall(tri, args.side, args.tol)
    model        = to_manifold(tri)
    txt, width   = text_solid(args.text, args.font, args.cap, args.depth)

    ## local frame: x = reading direction (viewer's right), y = up, z = outward normal
    ux           = np.array([nrm[1], -nrm[0], 0.0]) * -1
    uz           = np.array([nrm[0], nrm[1], 0.0])
    uy           = np.array([0.0, 0.0, 1.0])
    left         = a if (a - b) @ ux[:2] < 0 else b
    mid          = (a + b) / 2 if args.along is None else left + args.along * ux[:2]
    org          = np.array([mid[0], mid[1], tri[:, :, 2].min() + args.zc])
    mat          = np.column_stack([ux, uy, uz, org])
    txt          = txt.transform(mat)

    ## wall top along the text span, to confirm the text sits inside the wall
    edge         = (b - a) / np.linalg.norm(b - a)
    vert         = tri.reshape(-1, 3)
    rel          = vert[:, :2] - mid
    near         = (np.abs(rel @ nrm) < 0.05) & (np.abs(rel @ edge) < width / 2)
    wall_top     = vert[near, 2].max() if near.any() else np.nan
    low_top      = np.nan
    if near.any():
        s       = rel[near] @ edge
        bins    = np.linspace(-width / 2, width / 2, 11)
        tops    = [vert[near][(s >= lo) & (s < hi), 2].max() for lo, hi in zip(bins[:-1], bins[1:]) if ((s >= lo) & (s < hi)).any()]
        low_top = min(tops)

    res          = model - txt
    mesh         = res.to_mesh()
    out_tri      = np.asarray(mesh.vert_properties)[:, :3][np.asarray(mesh.tri_verts)]
    write_stl(args.out, out_tri.astype(np.float32))

    print(f'wall edge      : ({a[0]:.2f}, {a[1]:.2f}) to ({b[0]:.2f}, {b[1]:.2f}), length {np.linalg.norm(b - a):.1f} mm')
    print(f'outward azimuth: {np.degrees(np.arctan2(nrm[1], nrm[0])) % 360:.1f} deg')
    print(f'text           : "{args.text}", width {width:.1f} mm, cap {args.cap} mm, z {args.zc - args.cap / 2:.1f} to {args.zc + args.cap / 2:.1f} mm, depth {args.depth} mm')
    print(f'wall top       : lowest {low_top:.2f} mm, highest {wall_top:.2f} mm along the text span')
    print(f'volume removed : {model.volume() - res.volume():.1f} mm3, output {len(out_tri)} triangles, genus {res.genus()}')


if __name__ == '__main__':
    main()
