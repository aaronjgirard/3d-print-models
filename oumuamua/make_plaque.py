## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Name plaque for the ʻOumuamua print: a rounded plate with a raised border
and raised lines of text (name, scale), centered, printed flat.
'''
import argparse, json

import manifold3d as m3d
import numpy as np
import trimesh
from fontTools.ttLib import TTFont
from matplotlib.font_manager import FontPath, FontProperties
from matplotlib.textpath import TextPath

def face_runs(text, face, glyph_face):
    '''
    Split text into runs of one face, characters in glyph_face taking their own face.

    Args:
        text       (str):  text
        face       (int):  default face index
        glyph_face (dict): character -> face index

    Returns:
        list: [run, face] pairs
    '''
    runs = []
    for ch in text:
        f = glyph_face.get(ch, face)
        if runs and runs[-1][1] == f:
            runs[-1][0] += ch
        else:
            runs.append([ch, f])
    return runs

def run_advance(text, font, face, size):
    '''
    Summed advance widths of a run, without kerning.

    Args:
        text (str):   run
        font (str):   font file
        face (int):   face index
        size (float): em size [mm]

    Returns:
        float: advance [mm]
    '''
    ttf = TTFont(font, fontNumber=face, lazy=True)
    cmp = ttf.getBestCmap()
    return size * sum(ttf['hmtx'][cmp[ord(c)]][0] for c in text) / ttf['head'].unitsPerEm

def text_section(text, font, face, cap, glyph_face={}):
    '''
    Text outline as a cross section centered on x and on the cap height.

    Args:
        text       (str):   text
        font       (str):   font file (.ttf, or a .ttc collection)
        face       (int):   face index in a collection
        cap        (float): cap height of the default face [mm]
        glyph_face (dict):  character -> face index, for glyphs set in another face

    Returns:
        tuple: CrossSection, text width [mm]
    '''
    prop  = lambda f: FontProperties(fname=FontPath(font, f))
    ref   = TextPath((0, 0), 'H', size=10, prop=prop(face)).get_extents()
    size  = 10 * cap / ref.height
    x     = 0.0
    rings = []
    ## curves are flattened to about one path unit, so build at 100x and scale back
    for run, f in face_runs(text, face, glyph_face):
        rings += [q / 100 for q in TextPath((100 * x, 0), run, size=100 * size, prop=prop(f)).to_polygons()]
        x     += run_advance(run, font, f, size)
    pts   = np.vstack(rings)
    x0    = pts[:, 0].min()
    x1    = pts[:, 0].max()
    rings = [p - [(x0 + x1) / 2, cap / 2] for p in rings]
    return m3d.CrossSection(rings, fillrule=m3d.FillRule.EvenOdd), x1 - x0

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
        txt      = ''.join(par.get('glyph_sub', {}).get(ch, ch) for ch in txt)
        sec, wid = text_section(txt, par['font'], par.get('face', 0), caps[i], par.get('glyph_face', {}))
        if wid > room:
            caps[i] *= room / wid
            sec, wid = text_section(txt, par['font'], par.get('face', 0), caps[i], par.get('glyph_face', {}))
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
