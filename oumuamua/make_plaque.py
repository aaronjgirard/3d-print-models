## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Name plaque for the 'Oumuamua print: a rounded plate with a raised border
and raised lines of text (name, scale), centered, printed flat.
'''
import argparse, json

import manifold3d as m3d
import numpy as np
import trimesh
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

def text_section(text, font, cap):
    '''
    Text outline as a cross section centered on x and on the cap height.

    Args:
        text (str):   text
        font (str):   font file
        cap  (float): cap height [mm]

    Returns:
        tuple: CrossSection, text width [mm]
    '''
    prop  = FontProperties(fname=font)
    ref   = TextPath((0, 0), 'H', size=10, prop=prop).get_extents()
    path  = TextPath((0, 0), text, size=10 * cap / ref.height, prop=prop)
    ext   = path.get_extents()
    rings = [p - [ext.x0 + ext.width / 2, cap / 2] for p in path.to_polygons()]
    return m3d.CrossSection(rings, fillrule=m3d.FillRule.EvenOdd), ext.width

def rounded_rect(wid, hgt, rad):
    '''
    Rounded rectangle centered on the origin.

    Args:
        wid (float): width [mm]
        hgt (float): height [mm]
        rad (float): corner radius [mm]

    Returns:
        CrossSection: outline
    '''
    box = m3d.CrossSection.square([wid - 2 * rad, hgt - 2 * rad], center=True)
    return box.offset(rad, m3d.JoinType.Round, circular_segments=48)

def main(par):
    out = rounded_rect(par['width'], par['height'], par['radius'])
    sol = out.extrude(par['base'])
    if par['border'] > 0:
        ## one block with the face pocketed out, so the rim and the edge share one wall
        pkt = out.offset(-par['border'], m3d.JoinType.Round, circular_segments=48)
        sol = out.extrude(par['base'] + par['rise']) - pkt.extrude(par['rise'] + 1).translate([0, 0, par['base']])

    ## stack the lines, block centered on the plate
    room = par['width'] - 2 * (par['border'] + par['margin'])
    caps = list(par['caps'])
    secs = []
    for txt, i in zip(par['lines'], range(len(caps))):
        sec, wid = text_section(txt, par['font'], caps[i])
        if wid > room:
            caps[i] *= room / wid
            sec, wid = text_section(txt, par['font'], caps[i])
        secs.append((sec, wid))
    tot = sum(caps) + par['gap'] * (len(caps) - 1)
    yc  = tot / 2
    for (sec, wid), cap in zip(secs, caps):
        yc  -= cap / 2
        sol  = sol + sec.extrude(par['rise']).translate([0, yc, par['base']])
        print(f'line cap {cap:.2f} mm, width {wid:.1f} mm, center y {yc:+.2f} mm')
        yc  -= cap / 2 + par['gap']

    msh = sol.to_mesh()
    tri = trimesh.Trimesh(np.asarray(msh.vert_properties)[:, :3], np.asarray(msh.tri_verts))
    tri.export(par['out'])
    print(json.dumps({'out': par['out'], 'extents_mm': tri.extents.round(2).tolist(),
        'watertight': bool(tri.is_watertight), 'genus': sol.genus(),
        'text_from_z_mm': par['base']}, indent=1))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cfg', default='plaque.json')
    ap.add_argument('--out')
    a   = ap.parse_args()
    par = json.load(open(a.cfg))
    if a.out is not None: par['out'] = a.out
    main(par)
