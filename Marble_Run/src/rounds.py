## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Split-ring gap cutter with rounded top corners. Seen from the side, looking into the
gap, the top corner of each ring end (where the gap's side face meets the plug top)
becomes a radius instead of a point. No global manifold3d settings are touched, so
stand.py (96 segments) and parts.py (72) can both import it.
'''
import numpy as np
from manifold3d import Manifold, CrossSection


def slot_cutter(x0, x1, y, zb, zt, w, rf, nseg=16, d=0.03, e=1.0):
    '''
    Gap cut running along +x from x0 to x1, w wide about y, from zb up through the
    plug top at zt, with both top corners of the gap rounded to radius rf.

    The arc centres sit d higher than tangent so each arc crosses the plug top at an
    angle instead of grazing it (no sliver faces).

    Args:
        x0, x1 (float): [mm] extent of the cut along x
        y      (float): [mm] gap centre
        zb     (float): [mm] gap bottom
        zt     (float): [mm] plug top
        w      (float): [mm] gap width
        rf     (float): [mm] corner radius, 0 for square corners
        nseg   (int)  : points along each quarter arc
        d      (float): [mm] arc centre lift
        e      (float): [mm] overshoot above the top and past the arcs

    Returns:
        Manifold: the cutter, to subtract from the plug
    '''
    h  = w / 2
    zc = zt - rf + d
    a  = np.linspace(np.pi, np.pi / 2, nseg)
    rt = [(h + rf + rf * np.cos(t), zc + rf * np.sin(t)) for t in a]
    lt = [(-hy, z) for hy, z in rt[::-1]]
    pts = ([(-h, zb), (h, zb)] + rt + [(h + rf + e, zt + d), (h + rf + e, zt + e),
           (-h - rf - e, zt + e), (-h - rf - e, zt + d)] + lt)
    if rf <= 0:
        pts = [(-h, zb), (h, zb), (h, zt + e), (-h, zt + e)]
    prof = Manifold.extrude(CrossSection([pts]), x1 - x0)
    ## profile (u, v) and extrusion w map to world (y, z) and x
    rot = np.array([[0.0, 0.0, 1.0, x0], [1.0, 0.0, 0.0, y], [0.0, 1.0, 0.0, 0.0]])
    return prof.transform(rot)
