'''
Make an extra fit-ladder block with a plug diameter between the existing steps.

fit_ladder.stl holds three tube blocks (sorted south to north = steps 1, 2, 3):
a 25.6 mm socket bore at the bottom and a split-ring plug on top of 25.7,
25.8 and 25.9 mm, marked by 1, 2 or 3 dots on the west side at z = 5 mm.
This copies the block below --step, grows only its plug's outer surface to
the diameter interpolated between the two neighbouring blocks (measured the
same way on both), adds a second marker dot --dot_dz above the first, and
centres it at --at.

Usage:
    python fit_ladder_step.py [--src fit_ladder.stl] [--step 1.5]
        [--out fit_ladder_1p5.stl] [--at 60 110]
'''
import argparse
import os

import manifold3d as m3d
import numpy as np
import trimesh

here = os.path.dirname(os.path.abspath(__file__))


def fit_circle(p):
    '''
    Least-squares circle through 2D points.

    Returns:
        tuple: centre (2,), radius [mm]
    '''
    A = np.c_[2 * p, np.ones(len(p))]
    c = np.linalg.lstsq(A, (p ** 2).sum(1), rcond=None)[0]
    return c[:2], np.sqrt(c[2] + (c[:2] ** 2).sum())


def plug_ring(b, z=15.0):
    '''
    Centre, outer and inner radius of the split-ring plug of one block.

    Returns:
        tuple: centre (2,), outer radius, inner radius [mm]
    '''
    pts   = np.vstack(b.section(plane_origin=(0, 0, z), plane_normal=(0, 0, 1)).discrete)[:, :2]
    c, _  = fit_circle(pts)
    rr    = np.linalg.norm(pts - c, axis=1)
    rmid  = 0.5 * (rr.min() + rr.max())
    _, ro = fit_circle(pts[rr > rmid])
    _, ri = fit_circle(pts[rr < rmid])
    return c, ro, ri


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--src'   , default=os.path.join(here, 'fit_ladder.stl'))
    ap.add_argument('--step'  , type=float, default=1.5)                      # new step, between 1 and 3
    ap.add_argument('--z_plug', type=float, default=9.99)                     # [mm] plug starts above this height
    ap.add_argument('--dot_r' , type=float, default=1.187)                    # [mm] marker dot radius
    ap.add_argument('--dot_z' , type=float, default=5.0)                      # [mm] existing marker dot height
    ap.add_argument('--dot_dz', type=float, default=3.0)                      # [mm] new dot above the existing one
    ap.add_argument('--at'    , type=float, nargs=2, default=[60.0, 110.0])   # [mm] bed position of the axis
    ap.add_argument('--out'   , default=os.path.join(here, 'fit_ladder_1p5.stl'))
    a = ap.parse_args()

    m  = trimesh.load(a.src)
    bs = sorted([b for b in m.split(only_watertight=False) if b.extents[2] > 1], key=lambda b: b.bounds[0, 1])
    lo = int(np.floor(a.step))
    lo = min(lo, len(bs) - 1)
    rs = [plug_ring(x)[1] for x in bs]
    b  = bs[lo - 1].copy()
    assert b.is_watertight
    c, r0, ri = plug_ring(b)
    rt        = rs[lo - 1] + (a.step - lo) * (rs[lo] - rs[lo - 1])

    ## push every plug vertex on the outer half of the ring wall out radially
    V   = b.vertices.copy()
    d   = V[:, :2] - c
    r   = np.linalg.norm(d, axis=1)
    sel = (V[:, 2] >= a.z_plug) & (r > 0.5 * (ri + r0)) & (r < r0 + 0.3)
    dr  = rt - r0
    V[sel, :2] += d[sel] / r[sel, None] * dr
    b.vertices = V
    print(f'steps measure {", ".join(f"{2 * x:.3f}" for x in rs)} mm; step {a.step:g} from block {lo}: '
          f'plug {2 * r0:.3f} -> {2 * rt:.3f} mm ({sel.sum()} vertices moved {dr:+.4f} mm)')

    ## second marker dot above the existing one, on the same side
    west = V[np.argmin(V[:, 0])]
    dot  = m3d.Manifold.sphere(a.dot_r, 48).translate((float(west[0] + a.dot_r), float(c[1]), a.dot_z + a.dot_dz))
    M    = m3d.Manifold(m3d.Mesh(vert_properties=b.vertices.astype(np.float32), tri_verts=b.faces.astype(np.uint32)))
    assert M.status() == m3d.Error.NoError, M.status()
    M    = (M + dot).translate((a.at[0] - float(c[0]), a.at[1] - float(c[1]), 0.0))
    mm   = M.to_mesh()
    out  = trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts))
    out.export(a.out)

    ## check the result
    _, ro2, _ = plug_ring(out)
    print(f'wrote {a.out}: plug {2 * ro2:.3f} mm, watertight {out.is_watertight}, '
          f'bounds {out.bounds.round(2).tolist()}')


if __name__ == '__main__':
    main()
