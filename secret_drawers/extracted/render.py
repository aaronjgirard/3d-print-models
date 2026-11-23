## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Painter's-algorithm renders of the puzzle box: stills (outside + cut-away) and a GIF of the solve."""
import sys, os, numpy as np, trimesh
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import puzzle_drawers as P

CASE = np.array([0.78, 0.72, 0.62])     # warm grey
DRAW = np.array([0.20, 0.45, 0.62])     # blue drawers
DIAL = np.array([0.85, 0.55, 0.25])     # amber dial
PINC = np.array([0.90, 0.30, 0.25])     # red lock parts


def unit(v):
    v = np.asarray(v, float); return v / np.linalg.norm(v)


def camera(az, el):
    az, el = np.radians(az), np.radians(el)
    cam = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    right = unit(np.cross([0, 0, 1], cam)); upv = np.cross(cam, right)
    return cam, right, upv


def draw(ax, items, az=35, el=28, light=(0.4, -0.3, 0.85), cull=True):
    """items: list of (trimesh, rgb, alpha). Sort all triangles far-to-near and paint."""
    cam, right, upv = camera(az, el)
    light = unit(light)
    polys, cols, depth = [], [], []
    for mesh, rgb, alpha in items:
        V, F = mesh.vertices, mesh.faces
        N = mesh.face_normals
        facing = N @ cam
        keep = facing > -0.02 if (cull and alpha >= 1) else np.ones(len(F), bool)
        tri = V[F[keep]]                                    # (n, 3, 3)
        shade = np.clip(N[keep] @ light, 0, 1) * 0.65 + 0.35
        c = np.clip(rgb[None, :] * shade[:, None], 0, 1)
        rgba = np.concatenate([c, np.full((len(c), 1), alpha)], 1)
        xy = np.stack([tri @ right, tri @ upv], -1)
        polys.append(xy); cols.append(rgba); depth.append((tri @ cam).mean(1))
    polys = np.concatenate(polys); cols = np.concatenate(cols); depth = np.concatenate(depth)
    order = np.argsort(depth)
    pc = PolyCollection(polys[order], facecolors=cols[order], edgecolors=cols[order], linewidths=0.15)
    ax.add_collection(pc)
    ax.set_aspect('equal'); ax.axis('off')
    return pc


def scene(dial_deg=0.0, b_dy=0.0, a_dx=0.0, parts=None):
    """Meshes for one state. dial_deg: rotation from locked (negative = clockwise toward unlock)."""
    pr = parts
    tubes = [(pr['lower_tube'], CASE), (pr['upper_tube'], CASE)]
    a = pr['drawer_a'].copy(); a.apply_translation((a_dx, 0, 0))
    b = pr['drawer_b'].copy(); b.apply_translation((0, b_dy, 0))
    pin = pr['lock_pin'].copy(); pin.apply_translation((0, b_dy, 0))
    d = pr['dial'].copy()
    d.apply_transform(trimesh.transformations.rotation_matrix(np.radians(dial_deg), [0, 0, 1]))
    return tubes, [(a, DRAW), (b, DRAW)], [(d, DIAL), (pr['cap'], DIAL * 0.8), (pin, PINC)]


CUT_N = np.array([0.745, -0.667, 0.0])                       # cut plane normal (keeps the -X/+Y half)
CUT_O = np.array([P.PIN_X, P.PIN_Y, 0.0]) + 4.0 * CUT_N          # passes 4 mm beside the pin and the peg


def cut(mesh):
    return mesh.slice_plane(CUT_O, -CUT_N, cap=True)


VIEWS = {'out': dict(az=35, el=28), 'cut': dict(az=-20, el=36)}
LIMS = {}


def fit_limits(parts):
    """Projected bounds of the closed and fully open states for each view, with a margin."""
    for key, v in VIEWS.items():
        cam, right, upv = camera(v['az'], v['el'])
        pts = []
        for st in ((0, 0, 0), (-30, 60, 65), (-30, -6, 65)):
            tubes, drawers, small = scene(*st, parts=parts)
            for m, c in tubes + drawers:
                V = m.vertices
                pts.append(np.stack([V @ right, V @ upv], 1))
        pts = np.concatenate(pts)
        lo, hi = pts.min(0), pts.max(0)
        span = (hi - lo).max() * 0.5
        mid = (lo + hi) / 2
        LIMS[key] = [(mid[0] - span, mid[0] + span), (mid[1] - span, mid[1] + span)]


def frame(fig, state, caption, parts):
    if not LIMS:
        fit_limits(parts)
    fig.clf()
    fig.subplots_adjust(left=0.0, right=1.0, top=0.93, bottom=0.10, wspace=0.0)
    tubes, drawers, small = scene(*state, parts=parts)
    # outside view
    ax = fig.add_subplot(1, 2, 1)
    draw(ax, [(m, c, 1.0) for m, c in tubes + drawers + small], **VIEWS['out'])
    ax.set_xlim(*LIMS['out'][0]); ax.set_ylim(*LIMS['out'][1])
    ax.set_title('outside', fontsize=11, color='0.35')
    # cut-away: case and drawers sliced on a plane through both locks, small parts left whole
    ax = fig.add_subplot(1, 2, 2)
    tubes_c = [(parts['lower_tube'], CASE), (parts['upper_tube_window'], CASE)]
    a = np.radians(P.ARC_LOCK + state[0])
    peg = trimesh.creation.cylinder(radius=P.PEG_D / 2, height=P.TOP - 0.5 - (P.Z_CEIL_U - P.PEG_HANG), sections=24)
    peg.apply_translation((P.PEG_R * np.cos(a), P.PEG_R * np.sin(a), (P.TOP - 0.5 + P.Z_CEIL_U - P.PEG_HANG) / 2))
    items = [(cut(m), c, 1.0) for m, c in tubes_c + drawers] + [(small[2][0], PINC, 1.0), (small[1][0], DIAL * 0.8, 1.0),
                                                                 (peg, PINC, 1.0)]
    draw(ax, items, light=(0.5, -0.6, 0.6), **VIEWS['cut'])
    ax.set_xlim(*LIMS['cut'][0]); ax.set_ylim(*LIMS['cut'][1])
    ax.set_title('cut-away through both locks (dial hidden, its peg in red)', fontsize=11, color='0.35')
    fig.text(0.5, 0.04, caption, ha='center', fontsize=13)


def load_parts(max_edge=5.0):
    pm = P.all_parts()
    # upper tube with a window cut over drawer B's lock block, for the cut-away view only
    pm['upper_tube_window'] = pm['upper_tube'] - P.box(-35, 0.75 * P.PEG_R + 12, P.PEG_R - 25, P.HALF + 5, P.Z_CEIL_U - 0.1, P.TOP + 2)
    out = {}
    for k, v in pm.items():
        t = P.to_trimesh(v)
        V, F = trimesh.remesh.subdivide_to_size(t.vertices, t.faces, max_edge=max_edge, max_iter=8)
        out[k] = trimesh.Trimesh(V, F, process=False)
        print(k, len(t.faces), '->', len(F), 'tris')
    return out


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'out'
    os.makedirs(out, exist_ok=True)
    parts = load_parts()
    fig = plt.figure(figsize=(12, 5.4), dpi=100)
    # still
    frame(fig, (0, 0, 0), 'closed: a plain block with one dial and four look-alike faces', parts)
    fig.savefig(f'{out}/still_closed.png'); print('still done')
    frame(fig, (-30, -6, 65), 'solved: dial turned, B pushed in 6 mm, A pulled out', parts)
    fig.savefig(f'{out}/still_open.png')
    # gif
    from PIL import Image
    frames = []
    seq = []
    seq += [((0, 0, 0), '1. everything flush: pull on any face, nothing moves')] * 8
    for t in np.linspace(0, 1, 12):
        seq.append(((-30 * t, 0, 0), '2. the dial turns 30 deg clockwise, lifting its peg out of drawer B'))
    seq += [((-30, 0, 0), '2. the dial turns 30 deg clockwise, lifting its peg out of drawer B')] * 4
    for t in np.linspace(0, 1, 10):
        seq.append(((-30, 60 * t, 0), '3. B pulls out now, but A is still locked by the red pin under B'))
    seq += [((-30, 60, 0), '3. B pulls out now, but A is still locked by the red pin under B')] * 6
    for t in np.linspace(1, 0, 8):
        seq.append(((-30, 60 * t, 0), '4. close B...'))
    for t in np.linspace(0, 1, 8):
        seq.append(((-30, -6 * t, 0), '4. ...and PUSH it in 6 mm: the pin lines up with a notch in A'))
    seq += [((-30, -6, 0), '4. ...and PUSH it in 6 mm: the pin lines up with a notch in A')] * 6
    for t in np.linspace(0, 1, 14):
        seq.append(((-30, -6, 65 * t), '5. A slides out'))
    seq += [((-30, -6, 65), '5. A slides out: both drawers hold a candy bar')] * 12
    for i, (st, cap) in enumerate(seq):
        frame(fig, st, cap, parts)
        fig.canvas.draw()
        img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
        frames.append(Image.fromarray(img.copy()))
        if i % 10 == 0:
            print('frame', i, '/', len(seq))
    frames[0].save(f'{out}/how_it_works.gif', save_all=True, append_images=frames[1:], duration=110, loop=0, optimize=True)
    print('gif done', len(frames), 'frames')
