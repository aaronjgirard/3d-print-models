## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Render every project STL into one contact sheet, each tile labelled with the
piece name and its file name.

Marbleworks titles come from the original names in
config/marbleworks_names.json; tube and generated-piece titles from "titles"
in config/project.json, which also override Marbleworks titles. All pieces
are drawn at one scale. Tiles are cached in --tiles and only re-rendered when
the STL is newer.

Usage:
    python src/catalog.py [--out ref/catalog.png] [--tiles ref/tiles]
        [--ncol 8] [--jobs 8]
'''
import argparse
import json
import os
import re
import sys
from multiprocessing import Pool

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import load_cfg, out_dirs, root

groups = [
    ('marbleworks', 'Marbleworks Marble Mazes (Pyrce007, CC BY)', '#4a7fc1'),
    ('tubes'      , 'Tubes'                                     , '#8a8f98'),
    ('custom'     , 'Generated pieces'                          , '#d9822b'),
]
light = np.array([0.4, -0.6, 0.7]) / np.linalg.norm([0.4, -0.6, 0.7])


def mw_title(orig):
    '''
    Readable title from an original Marbleworks file stem.
    '''
    t = orig.replace('__', ' & ').replace('_-_', ' - ').replace('_', ' ')
    return t.replace('Epictrochoid', '').strip(' -')


def render_tile(job):
    '''
    Shaded isometric render of one STL to a square PNG.

    Args:
        job (tuple): stl path, png path, hex colour, pixel size, half-width of the view [mm]

    Returns:
        str: png path
    '''
    stl, png, color, px, h = job
    if os.path.exists(png) and os.path.getmtime(png) > os.path.getmtime(stl):
        return png
    m    = trimesh.load(stl)
    m.apply_translation(-m.bounds.mean(0))
    tri  = m.triangles
    shd  = 0.35 + 0.65 * np.clip(m.face_normals @ light, 0, 1)
    base = np.array(matplotlib.colors.to_rgb(color))
    fc   = np.clip(base[None, :] * shd[:, None] + 0.08, 0, 1)
    fig  = plt.figure(figsize=(px / 100, px / 100), dpi=100)
    ax   = fig.add_axes([0, 0, 1, 1], projection='3d')
    ax.add_collection3d(Poly3DCollection(tri, facecolors=fc, edgecolors='none', linewidths=0))
    ax.set_xlim(-h, h); ax.set_ylim(-h, h); ax.set_zlim(-h, h)
    ax.set_proj_type('ortho')
    ax.set_box_aspect((1, 1, 1), zoom=1.35)
    ax.view_init(elev=25, azim=-55)
    ax.set_axis_off()
    fig.savefig(png, dpi=100, transparent=False, facecolor='white')
    plt.close(fig)
    return png


def collect(cfg, names):
    '''
    List (group, stl path, title, file name) for every STL in the project.
    '''
    dirs   = out_dirs(cfg)
    titles = {v: mw_title(k) for k, v in names.items()}
    titles.update(cfg['titles'])
    nat    = lambda f: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', f)]
    items  = []
    for key, _, _ in groups:
        fs = sorted((f for f in os.listdir(dirs[key]) if f.lower().endswith('.stl')), key=lambda f: nat(os.path.splitext(f)[0]))
        for f in fs:
            stem = os.path.splitext(f)[0]
            items.append((key, os.path.join(dirs[key], f), titles.get(stem, stem), f))
    return items


def sheet(items, tiles, out, ncol, tile_in=2.2, scale=None):
    '''
    Lay the rendered tiles out by group with titles and file names below each.
    '''
    rows = []
    for key, head, color in groups:
        grp = [it for it in items if it[0] == key]
        if not grp:
            continue
        rows.append(('head', head, color))
        for i in range(0, len(grp), ncol):
            rows.append(('tiles', grp[i:i + ncol], color))
    hh, th = 0.45, tile_in + 0.55                  # [in] heading row, tile row incl. labels
    H      = sum(hh if r[0] == 'head' else th for r in rows) + 0.6
    W      = ncol * tile_in + 0.4
    fig    = plt.figure(figsize=(W, H), dpi=150)
    fig.text(0.5, 1 - 0.3 / H, 'Marble Run pieces', ha='center', va='center', fontsize=18, weight='bold')
    if scale:
        fig.text(0.5, 1 - 0.55 / H, f'all pieces drawn at the same scale (largest {scale:.0f} mm across)',
                 ha='center', va='center', fontsize=9, color='#555555')
    y = H - 0.6
    for r in rows:
        if r[0] == 'head':
            y -= hh
            fig.text(0.2 / W, (y + 0.12) / H, r[1], fontsize=13, weight='bold', color=r[2])
            fig.add_artist(plt.Line2D([0.2 / W, 1 - 0.2 / W], [(y + 0.05) / H] * 2, color=r[2], lw=1.2))
            continue
        y -= th
        for j, (key, stl, title, fname) in enumerate(r[1]):
            x0 = (0.2 + j * tile_in) / W
            ax = fig.add_axes([x0, (y + 0.55) / H, tile_in / W, tile_in / H])
            ax.imshow(plt.imread(tiles[stl]))
            ax.set_axis_off()
            xc = x0 + tile_in / 2 / W
            fig.text(xc, (y + 0.38) / H, title, ha='center', va='center', fontsize=7.5, weight='bold', wrap=True)
            fig.text(xc, (y + 0.17) / H, fname, ha='center', va='center', fontsize=7, family='monospace', color='#555555')
    fig.savefig(out, dpi=150, facecolor='white')
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out'  , default=os.path.join(root, 'ref', 'catalog.png'))
    ap.add_argument('--tiles', default=os.path.join(root, 'ref', 'tiles'))
    ap.add_argument('--ncol' , type=int, default=8)
    ap.add_argument('--px'   , type=int, default=500)     # [px] tile render size
    ap.add_argument('--jobs' , type=int, default=8)
    a = ap.parse_args()

    cfg   = load_cfg()
    names = json.load(open(os.path.join(root, 'config', 'marbleworks_names.json')))
    items = collect(cfg, names)
    os.makedirs(a.tiles, exist_ok=True)
    color = {k: c for k, _, c in groups}
    h     = 0.5 * max(trimesh.load(stl).extents.max() for _, stl, _, _ in items)
    jobs  = [(stl, os.path.join(a.tiles, f'{key}_{os.path.splitext(f)[0]}.png'), color[key], a.px, h)
             for key, stl, _, f in items]
    with Pool(a.jobs) as p:
        pngs = p.map(render_tile, jobs)
    tiles = {j[0]: png for j, png in zip(jobs, pngs)}
    sheet(items, tiles, a.out, a.ncol, scale=2 * h)
    print(f'wrote {a.out}: {len(items)} pieces')


if __name__ == '__main__':
    main()
