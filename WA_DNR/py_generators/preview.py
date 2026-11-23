## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
QC preview of the print: top view (shaded, model mm) with hole positions, and
an oblique view of the binary STL.

Usage:
    python preview.py [--config config.json]
'''
import argparse
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from make_print import load_config


def read_stl(path):
    '''
    Read a binary STL as an (n, 3, 3) array of triangle vertices [mm].
    '''
    rec = np.fromfile(path, dtype=[('n', '<f4', 3), ('p', '<f4', (3, 3)), ('a', '<u2')], offset=84)
    return rec['p'], rec['n']


def main(cfg, every):
    out = lambda ext: os.path.join(cfg['out_dir'], cfg['name'] + ext)
    tri, nrm = read_stl(out('.stl'))
    rcv      = pd.read_csv(out('_receivers.csv'))
    g        = np.load(out('_grid.npz'))
    scl, x0, y0 = float(g['scl']), float(g['x0']), float(g['y0'])

    fig = plt.figure(figsize=(14, 7))

    ## top view: shade the up-facing triangles by their normals
    ax = fig.add_subplot(1, 2, 1)
    top = nrm[:, 2] > 0.05
    ls  = np.array([-1.0, 1.0, 1.5]) / np.linalg.norm([-1.0, 1.0, 1.5])
    shd = np.clip(nrm[top] @ ls, 0, 1)
    ax.tripcolor(tri[top][:, :, 0].ravel(), tri[top][:, :, 1].ravel(),
                 np.arange(top.sum() * 3).reshape(-1, 3), facecolors=shd,
                 cmap='gray', vmin=0, vmax=1, rasterized=True)
    hx, hy = (rcv['hole_e'] - x0) * scl, (rcv['hole_n'] - y0) * scl
    mv     = rcv['shift_m'] > 0
    ax.plot(hx[~mv], hy[~mv], 'o', mfc='none', mec='tab:red', ms=4, label='hole at receiver')
    ax.plot(hx[mv],  hy[mv],  'o', mfc='none', mec='tab:blue', ms=4, label='hole nudged inward')
    ax.set_aspect('equal')
    ax.set_xlabel('x [mm]')
    ax.set_ylabel('y [mm] (north up)')
    ax.set_title(f"{cfg['name']}: top, {len(rcv)} holes")
    ax.legend(loc='lower left', fontsize=8)

    ## oblique view, every n-th triangle of the stl
    ax3 = fig.add_subplot(1, 2, 2, projection='3d')
    sub = tri[::every]
    sh  = np.clip(nrm[::every] @ ls, 0.15, 1)
    pc  = Poly3DCollection(sub, facecolors=plt.cm.gray(sh), linewidths=0)
    ax3.add_collection3d(pc)
    lo, hi = tri.reshape(-1, 3).min(0), tri.reshape(-1, 3).max(0)
    ax3.set_xlim(lo[0], hi[0]); ax3.set_ylim(lo[1], hi[1]); ax3.set_zlim(0, hi[2])
    ax3.set_box_aspect(hi - lo)
    ax3.view_init(elev=28, azim=-60)
    ax3.set_title(f"{hi[0]:.1f} x {hi[1]:.1f} x {hi[2]:.1f} mm, vexag {cfg['vexag']:g}")

    fig.tight_layout()
    fig.savefig(out('_preview.png'), dpi=150)
    print(out('_preview.png'))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json'))
    ap.add_argument('--every',  type=int, default=1, help='plot every n-th stl triangle in the oblique view')
    a = ap.parse_args()
    main(load_config(a.config), a.every)
