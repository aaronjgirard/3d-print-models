## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Check the sliced G-code of the spiky twisty sphere and draw its supports over the model.

G-code markers: START_PRINT before any move, END_PRINT last, no G28, and the
SET_VELOCITY_LIMIT and EXCLUDE_OBJECT lines the SV06 ACE preset writes.

Supports, from the support moves in the G-code against the mesh in the plate 3MF:
they stop below the designer's support blocker, every support island stands on
the plate and none rests on the ball, they stay inside the ball's plan-view
outline, and no support or brim move lies in a gap between two different
segments. The segments are 0.5 mm apart; a gap here is any slot between two
segments up to --slot wide (1 mm). Moves in wider slots, up to --valley (2 mm),
sit between the spike tips of neighboring segments and are only counted.

Usage: python slice/check.py [--gcode out/x.gcode] [--plate slice/plate/x_plate.3mf] [--fig out/x.png]
Exits 1 when a check fails.
'''
import argparse
import os
import re
import sys
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import shapely
import trimesh
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy import ndimage
from shapely.ops import unary_union

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)

sup_kinds  = ('Support', 'Support interface')
keep_kinds = sup_kinds + ('Brim',)
move_cmds  = ('G0', 'G1', 'G2', 'G3', 'G28')
count_cmds = ('START_PRINT', 'END_PRINT', 'G28', 'SET_VELOCITY_LIMIT', 'EXCLUDE_OBJECT_DEFINE',
              'EXCLUDE_OBJECT_START', 'EXCLUDE_OBJECT_END')
colors = {
    'surface' : '#fcfcfb',      # figure background
    'ink'     : '#0b0b0b',      # titles
    'ink2'    : '#52514e',      # labels, reference lines
    'grid'    : '#e1e0d9',      # hairlines
    'model'   : '#cfcec8',      # ball cross-section fill
    'edge'    : '#898781',      # ball cross-section outline
    'base'    : '#2a78d6',      # support base moves
    'iface'   : '#eb6834',      # support interface moves
    'brim'    : '#1baf7a',      # brim moves
    'slot'    : '#eda100',      # gaps between segments
    'flag'    : '#d03b3b',      # failed points
}


def read_gcode(path):
    '''
    Read the markers, the report values and the support and brim moves of a G-code file.

    Args:
        path    (str): G-code file

    Returns:
        dict: counts, command order, object center, layer heights, report values
              and one (n, 5) array of x0, y0, x1, y1, z per kept feature type
    '''
    num    = re.compile(r'([XYZE])(-?\d*\.?\d+)')
    count  = dict.fromkeys(count_cmds, 0)
    segs   = {kind: [] for kind in keep_kinds}
    info   = {'first_move': None, 'start_line': None, 'last_cmd': None, 'center': None}
    zlay   = []
    kind   = ''
    xpos = ypos = zpos = 0.0
    ncmd   = 0
    with open(path) as fid:
        for line in fid:
            if line[0] == ';':
                if line.startswith(';TYPE:'):
                    kind = line[6:].strip()
                elif line.startswith(';Z:'):
                    zlay.append(float(line[3:]))
                elif ' = ' in line or ': ' in line:
                    for key in ('estimated printing time (normal mode)', 'total filament used [g]',
                                'total layers count', 'total layer number', 'max_z_height'):
                        if line.startswith('; ' + key):
                            info[key] = re.split(r' = |: ', line.strip(), maxsplit=1)[1]
                continue
            cmd = line.split(';', 1)[0].strip()
            if not cmd or cmd.startswith('M73'):
                continue
            ncmd += 1
            word = cmd.split(None, 1)[0]
            if word in count:
                count[word] += 1
            if word == 'START_PRINT' and info['start_line'] is None:
                info['start_line'] = ncmd
            if word in move_cmds and info['first_move'] is None:
                info['first_move'] = ncmd
            if word == 'EXCLUDE_OBJECT_DEFINE' and info['center'] is None:
                cen = re.search(r'CENTER=(-?[\d.]+),(-?[\d.]+)', cmd)
                info['center'] = (float(cen.group(1)), float(cen.group(2)))
            info['last_cmd'] = cmd
            if word not in ('G0', 'G1'):
                continue
            vals = dict(num.findall(cmd))
            xnew = float(vals['X']) if 'X' in vals else xpos
            ynew = float(vals['Y']) if 'Y' in vals else ypos
            znew = float(vals['Z']) if 'Z' in vals else zpos
            if kind in segs and 'E' in vals and float(vals['E']) > 0 and (xnew != xpos or ynew != ypos):
                segs[kind].append((xpos, ypos, xnew, ynew, znew))
            xpos, ypos, zpos = xnew, ynew, znew
    info['count'] = count
    info['zlay']  = np.array(zlay)
    info['segs']  = {kind: np.array(val).reshape(-1, 5) for kind, val in segs.items()}
    return info


def read_plate(path):
    '''
    Read the ball mesh and the support blocker from the plate 3MF, in object coordinates.

    Args:
        path    (str): plate 3MF written by plate.py

    Returns:
        tuple: ball vertices (n, 3) [mm], ball faces (m, 3), blocker bounds (2, 3) [mm]
               and the height of the object origin above the plate [mm]
    '''
    with zipfile.ZipFile(path) as zin:
        model = zin.read('3D/3dmodel.model').decode('utf-8')
        mesh  = zin.read('3D/Objects/object_1.model').decode('utf-8')
    part = {}
    for comp in re.finditer(r'<component [^>]*objectid="(\d+)"[^>]*transform="([^"]+)"', model):
        vals = np.array(comp.group(2).split(), dtype=float)
        body = re.search(r'<object id="%s".*?</object>' % comp.group(1), mesh, re.S).group(0)
        vert = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', body), dtype=float)
        face = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', body), dtype=int)
        part[comp.group(1)] = (vert @ vals[:9].reshape(3, 3) + vals[9:], face)
    item  = re.search(r'<item [^>]*transform="([^"]+)"', model).group(1).split()
    block = np.array([part['2'][0].min(axis=0), part['2'][0].max(axis=0)])
    return part['1'][0], part['1'][1], block, float(item[11])


def layer_sections(bodies, zmid):
    '''
    Cut every body of the ball at one height.

    Args:
        bodies  (list): one trimesh per segment of the ball, in plate coordinates
        zmid    (float): [mm] height of the cut

    Returns:
        list: (segment index, shapely polygon) for every outline at that height
    '''
    out = []
    for ind, body in enumerate(bodies):
        if not body.bounds[0][2] < zmid < body.bounds[1][2]:
            continue
        sec = body.section(plane_origin=[0, 0, zmid], plane_normal=[0, 0, 1])
        if sec is None:
            continue
        flat, _ = sec.to_2D(to_2D=np.eye(4))
        out += [(ind, pol) for pol in flat.polygons_full if pol.area > 1e-4]
    return out


def slot_regions(polys, width):
    '''
    Find the space between two different segments that is narrower than a given width.

    Args:
        polys   (list): (segment index, polygon) pairs of one layer
        width   (float): [mm] widest slot that still counts as a gap

    Returns:
        shapely geometry: the slots (may be empty)
    '''
    solid = unary_union([pol for _, pol in polys])
    fill  = solid.buffer(width / 2).buffer(-width / 2).difference(solid)
    keep  = []
    for piece in getattr(fill, 'geoms', [fill]):
        if piece.is_empty or piece.area < 1e-4:
            continue
        near = {ind for ind, pol in polys if pol.distance(piece) < 0.02}
        if len(near) >= 2:
            keep.append(piece)
    return unary_union(keep)


def in_region(region, pts):
    '''
    Tell which points lie inside a region.

    Args:
        region  (shapely geometry): the region (may be empty)
        pts     (array): (n, 2) points [mm]

    Returns:
        array: (n,) bool
    '''
    if region.is_empty or len(pts) == 0:
        return np.zeros(len(pts), bool)
    return shapely.contains_xy(region, pts[:, 0], pts[:, 1])


def sample_moves(seg, step):
    '''
    Points along a set of moves, no farther apart than step.

    Args:
        seg     (array): (n, 5) moves x0, y0, x1, y1, z [mm]
        step    (float): [mm] largest spacing

    Returns:
        array: (m, 2) points [mm]
    '''
    if len(seg) == 0:
        return np.zeros((0, 2))
    lng  = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    npt  = np.ceil(lng / step).astype(int) + 1
    ind  = np.repeat(np.arange(len(seg)), npt)
    frac = np.concatenate([np.linspace(0, 1, n) for n in npt])
    return seg[ind, :2] + frac[:, None] * (seg[ind, 2:4] - seg[ind, :2])


def check_marks(gco):
    '''
    Check the G-code markers of the SV06 ACE preset.

    Args:
        gco     (dict): output of read_gcode

    Returns:
        list: (name, passed, detail)
    '''
    cnt = gco['count']
    return [
        ('START_PRINT once, before any move', cnt['START_PRINT'] == 1 and gco['start_line'] < gco['first_move'],
         f"count {cnt['START_PRINT']}, command {gco['start_line']}, first move is command {gco['first_move']}"),
        ('END_PRINT is the last command',     cnt['END_PRINT'] == 1 and gco['last_cmd'] == 'END_PRINT',
         f"count {cnt['END_PRINT']}, last command {gco['last_cmd']}"),
        ('no G28',                            cnt['G28'] == 0, f"count {cnt['G28']}"),
        ('SET_VELOCITY_LIMIT lines',          cnt['SET_VELOCITY_LIMIT'] > 0, f"count {cnt['SET_VELOCITY_LIMIT']}"),
        ('EXCLUDE_OBJECT lines',              cnt['EXCLUDE_OBJECT_DEFINE'] > 0 and cnt['EXCLUDE_OBJECT_START'] > 0,
         f"define {cnt['EXCLUDE_OBJECT_DEFINE']}, start {cnt['EXCLUDE_OBJECT_START']}, end {cnt['EXCLUDE_OBJECT_END']}"),
    ]


def check_supports(gco, vert, face, block, zorg, par):
    '''
    Check the support moves against the ball.

    Args:
        gco     (dict): output of read_gcode
        vert    (array): ball vertices in object coordinates [mm]
        face    (array): ball faces
        block   (array): support blocker bounds in object coordinates [mm]
        zorg    (float): [mm] height of the object origin above the plate
        par     (dict): slot and valley widths, sampling step, grid cell and rest depth

    Returns:
        tuple: list of (name, passed, detail) and a dict of geometry for the figure
    '''
    cen    = np.array([gco['center'][0], gco['center'][1], zorg])
    ball   = trimesh.Trimesh(vert + cen, face, process=False)
    bodies = list(ball.split(only_watertight=False))
    zblock = block[0][2] + zorg
    sup    = np.vstack([gco['segs'][kind] for kind in sup_kinds])
    zsup   = np.unique(sup[:, 4].round(3))
    zlay   = gco['zlay']
    ztop   = zsup.max() if len(zsup) else 0.0

    ## model outlines for every layer up to two layers above the last support layer
    zuse = zlay[zlay <= ztop + 0.01]
    zlow = np.concatenate([[0.0], zuse[:-1]])
    secs = [layer_sections(bodies, (za + zb) / 2) for za, zb in zip(zlow, zuse)]
    full = [unary_union([pol for _, pol in sec]) for sec in secs]

    ## per layer: points in a slot between segments, points inside the ball, clearance,
    ## points that sit on ball material one or two layers below
    nslot = nwide = ninside = nrest = npts = 0
    clear = np.inf
    flag  = []
    slots = []
    for lay, zval in enumerate(zuse):
        slot = slot_regions(secs[lay], par['slot'])
        slots.append(slot)
        seg = sup[np.abs(sup[:, 4] - zval) < 1e-3]
        pts = sample_moves(seg, par['step'])
        if len(pts) == 0:
            continue
        npts += len(pts)
        wide  = slot_regions(secs[lay], par['valley'])
        hit   = in_region(slot, pts)
        nwide += int(in_region(wide, pts).sum())
        dist  = shapely.distance(full[lay], shapely.points(pts))
        rest  = np.zeros(len(pts), bool)
        for below in range(1, par['rest'] + 1):
            if lay - below >= 0:
                rest |= shapely.contains_xy(full[lay - below], pts[:, 0], pts[:, 1])
        nslot   += int(hit.sum())
        ninside += int((dist <= 0).sum())
        nrest   += int(rest.sum())
        clear    = min(clear, float(dist.min()))
        bad      = hit | rest | (dist <= 0)
        flag.append(np.column_stack([pts[bad], np.full(bad.sum(), zval)]))
    ## brim moves of the first layer against the same gaps
    bpts  = sample_moves(gco['segs']['Brim'], par['step'])
    bhit  = in_region(slots[0], bpts)
    flag.append(np.column_stack([bpts[bhit], np.full(bhit.sum(), zuse[0])]))
    flag  = np.vstack(flag)

    ## support islands in 3d on a grid: every island has to reach the first layer
    lo    = sup[:, [0, 1]].min(axis=0) - 1.0
    hi    = sup[:, [2, 3]].max(axis=0) + 1.0
    lo    = np.minimum(lo, sup[:, [2, 3]].min(axis=0) - 1.0)
    hi    = np.maximum(hi, sup[:, [0, 1]].max(axis=0) + 1.0)
    shape = np.ceil((hi - lo) / par['cell']).astype(int) + 1
    grid  = np.zeros((len(zuse), shape[0], shape[1]), bool)
    for lay, zval in enumerate(zuse):
        pts = sample_moves(sup[np.abs(sup[:, 4] - zval) < 1e-3], par['cell'] / 2)
        idx = ((pts - lo) / par['cell']).astype(int)
        grid[lay, idx[:, 0], idx[:, 1]] = True
        grid[lay] = ndimage.binary_dilation(grid[lay], iterations=1)
    label, nisl = ndimage.label(grid, structure=np.ones((3, 3, 3)))
    first = ndimage.minimum(np.broadcast_to(np.arange(len(zuse))[:, None, None], grid.shape), label, np.arange(1, nisl + 1))
    nfloat = int((np.atleast_1d(first) > 0).sum())

    ## plan-view reach of the supports against the ball's widest outline
    rsup  = np.hypot(sup[:, [0, 2]] - cen[0], sup[:, [1, 3]] - cen[1]).max()
    rball = np.hypot(ball.vertices[:, 0] - cen[0], ball.vertices[:, 1] - cen[1]).max()

    res = [
        ('supports stop below the blocker',      ztop < zblock, f'highest support move {ztop:.2f} mm, blocker starts at {zblock:.2f} mm'),
        ('every support island stands on plate', nfloat == 0, f'{nisl} islands, {nfloat} start above the first layer'),
        ('no support rests on the ball',         nrest == 0, f"{nrest} of {npts} sampled points have ball material within {par['rest']} layers below"),
        ('no support in a gap between segments', nslot == 0, f"{nslot} of {npts} sampled points lie in a slot up to {par['slot']:g} mm wide between two segments "
                                                             f"({nwide} between spike tips of two segments up to {par['valley']:g} mm apart)"),
        ('no brim in a gap between segments',    bhit.sum() == 0, f"{int(bhit.sum())} of {len(bpts)} sampled brim points lie in such a slot"),
        ('no support inside the ball',           ninside == 0, f'{ninside} points inside an outline; closest approach {clear:.2f} mm in plan'),
        ('supports stay under the ball',         rsup <= rball, f'farthest support move {rsup:.1f} mm from the axis, ball reaches {rball:.1f} mm'),
    ]
    geo = {'ball': ball, 'cen': cen, 'zblock': zblock, 'zuse': zuse, 'secs': secs, 'slots': slots, 'flag': flag, 'ztop': ztop,
           'nbody': len(bodies), 'size': ball.extents, 'rmax': np.linalg.norm(ball.vertices - cen, axis=1).max()}
    return res, geo


def draw_section(ax, sec):
    '''
    Fill the ball outlines of one layer.

    Args:
        ax      (axes): matplotlib axes
        sec     (list): (segment index, polygon) pairs
    '''
    for _, pol in sec:
        ax.fill(*pol.exterior.xy, facecolor=colors['model'], edgecolor=colors['edge'], linewidth=0.3, zorder=1)
        for hole in pol.interiors:
            ax.fill(*hole.xy, facecolor=colors['surface'], edgecolor=colors['edge'], linewidth=0.3, zorder=1)


def draw_moves(ax, seg, col, color, width):
    '''
    Draw a set of moves projected on two of their coordinates.

    Args:
        ax      (axes): matplotlib axes
        seg     (array): (n, 5) moves x0, y0, x1, y1, z [mm]
        col     (tuple): columns of the start and end points, as ((a0, b0), (a1, b1))
        color   (str): line color
        width   (float): line width [pt]
    '''
    if len(seg) == 0:
        return
    line = np.stack([seg[:, list(col[0])], seg[:, list(col[1])]], axis=1)
    ax.add_collection(LineCollection(line, colors=color, linewidths=width, zorder=3, rasterized=True))


def render(gco, geo, path, zshow):
    '''
    Draw the support moves over the ball: a side view, a vertical cut through the
    axis, a view from below and three layers.

    Args:
        gco     (dict): output of read_gcode
        geo     (dict): geometry from check_supports
        path    (str): picture file to write
        zshow   (list): [mm] heights of the three layers shown
    '''
    ball, cen = geo['ball'], geo['cen']
    base  = gco['segs']['Support']
    iface = gco['segs']['Support interface']
    brim  = gco['segs']['Brim']
    flag  = geo['flag']
    ztop  = geo['zblock'] + 8.0
    half  = geo['size'][:2].max() / 2 + 2.0

    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': colors['edge'], 'axes.labelcolor': colors['ink2'],
                         'xtick.color': colors['ink2'], 'ytick.color': colors['ink2'], 'axes.titlecolor': colors['ink']})
    fig  = plt.figure(figsize=(16, 14.5), facecolor=colors['surface'])
    grid = fig.add_gridspec(3, 6, height_ratios=(3.8, 3.8, 5.6))
    top  = [fig.add_subplot(grid[0, :4]), fig.add_subplot(grid[1, :4]), fig.add_subplot(grid[:2, 4:])]
    low  = [fig.add_subplot(grid[2, 2 * col:2 * col + 2]) for col in range(3)]

    ## side view: every face below the top of the window, then every support move
    ax  = top[0]
    tri = ball.triangles[ball.triangles[:, :, 2].min(axis=1) < ztop][:, :, [0, 2]]
    ax.add_collection(PolyCollection(tri, facecolors=colors['model'], edgecolors='none', zorder=1, rasterized=True))
    draw_moves(ax, base,  ((0, 4), (2, 4)), colors['base'],  0.5)
    draw_moves(ax, iface, ((0, 4), (2, 4)), colors['iface'], 0.9)
    ax.set_title('Side view: all support moves in front of and behind the ball', loc='left')

    ## vertical cut through the axis with the support moves within 1 mm of the cut
    ax  = top[1]
    cut = ball.section(plane_origin=cen, plane_normal=[0, 1, 0])
    for loop in cut.discrete:
        ax.fill(loop[:, 0], loop[:, 2], facecolor=colors['model'], edgecolor=colors['edge'], linewidth=0.3, zorder=1)
    for seg, color, width in ((base, colors['base'], 1.2), (iface, colors['iface'], 1.6)):
        near = seg[(np.abs(seg[:, 1] - cen[1]) < 1.0) | (np.abs(seg[:, 3] - cen[1]) < 1.0)]
        draw_moves(ax, near, ((0, 4), (2, 4)), color, width)
    ax.set_title('Vertical cut through the axis: gaps are the white lines in the ball', loc='left')

    for ax in top[:2]:
        ax.axhline(geo['zblock'], color=colors['ink2'], linewidth=0.8, linestyle='--', zorder=4)
        ax.text(cen[0] - half + 1, geo['zblock'] + 0.6, f"support blocker from {geo['zblock']:.1f} mm up", color=colors['ink2'], fontsize=8)
        ax.axhline(0, color=colors['ink2'], linewidth=0.8, zorder=4)
        ax.set_xlim(cen[0] - half, cen[0] + half)
        ax.set_ylim(-1.5, ztop)
        ax.set_xlabel('x [mm]')
        ax.set_ylabel('z above the plate [mm]')

    ## from above: outline at the last support layer, all support moves on top
    ax  = top[2]
    lay = int(np.argmin(np.abs(geo['zuse'] - geo['ztop'])))
    draw_section(ax, geo['secs'][lay])
    draw_moves(ax, base,  ((0, 1), (2, 3)), colors['base'],  0.3)
    draw_moves(ax, iface, ((0, 1), (2, 3)), colors['iface'], 0.8)
    ax.set_title(f"Plan view: all support moves,\nover the ball outline at {geo['zuse'][lay]:.2f} mm", loc='left')

    if len(flag):
        ax.plot(flag[:, 0], flag[:, 1], 'x', color=colors['flag'], markersize=5, zorder=5)
    ax.set_xlim(cen[0] - half, cen[0] + half)
    ax.set_ylim(cen[1] - half, cen[1] + half)

    ## three layers, each zoomed on the ball outline of that layer, with its gaps
    for ax, zval in zip(low, zshow):
        lay = int(np.argmin(np.abs(geo['zuse'] - zval)))
        zl  = geo['zuse'][lay]
        draw_section(ax, geo['secs'][lay])
        for piece in getattr(geo['slots'][lay], 'geoms', [geo['slots'][lay]]):
            if not piece.is_empty:
                ax.fill(*piece.exterior.xy, facecolor=colors['slot'], edgecolor='none', zorder=2)
        draw_moves(ax, base[np.abs(base[:, 4] - zl) < 1e-3],   ((0, 1), (2, 3)), colors['base'],  0.6)
        draw_moves(ax, iface[np.abs(iface[:, 4] - zl) < 1e-3], ((0, 1), (2, 3)), colors['iface'], 0.9)
        draw_moves(ax, brim[np.abs(brim[:, 4] - zl) < 1e-3],   ((0, 1), (2, 3)), colors['brim'],  0.6)
        bad = flag[np.abs(flag[:, 2] - zl) < 1e-3]
        if len(bad):
            ax.plot(bad[:, 0], bad[:, 1], 'x', color=colors['flag'], markersize=5, zorder=5)
        box = unary_union([pol for _, pol in geo['secs'][lay]]).bounds
        rad = max(box[2] - box[0], box[3] - box[1]) / 2 + 5.0
        ax.set_xlim(cen[0] - rad, cen[0] + rad)
        ax.set_ylim(cen[1] - rad, cen[1] + rad)
        ax.set_title(f'Layer at {zl:.2f} mm, zoomed on the ball: {len(bad)} failed points', loc='left', fontsize=10)

    for ax in low + [top[2]]:
        ax.set_xlabel('x [mm]')
        ax.set_ylabel('y [mm]')

    for ax in top + low:
        ax.set_aspect('equal')
        ax.set_facecolor(colors['surface'])
        ax.grid(color=colors['grid'], linewidth=0.5, zorder=0)
        ax.set_axisbelow(True)

    keys = [Patch(facecolor=colors['model'], edgecolor=colors['edge'], label='ball'),
            Line2D([], [], color=colors['base'],  linewidth=2, label='support'),
            Line2D([], [], color=colors['iface'], linewidth=2, label='support interface'),
            Line2D([], [], color=colors['brim'],  linewidth=2, label='brim (first layer)'),
            Patch(facecolor=colors['slot'], edgecolor='none', label='gaps between segments'),
            Line2D([], [], color=colors['flag'],  marker='x', linestyle='none', label=f'failed points ({len(flag)})')]
    fig.legend(handles=keys, loc='upper center', ncol=6, frameon=False, bbox_to_anchor=(0.5, 0.972))
    fig.suptitle('Spiky twisty sphere: supports from the G-code over the model', x=0.012, y=0.99, ha='left',
                 fontsize=13, color=colors['ink'])
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    fig.savefig(path, dpi=170, facecolor=colors['surface'])
    plt.close(fig)


def main():
    name   = 'spiky_twisty_sphere'
    parser = argparse.ArgumentParser(description='check the sliced sphere and draw its supports')
    parser.add_argument('--gcode', default=os.path.join(root, 'out', name + '.gcode'),              help='sliced g-code')
    parser.add_argument('--plate', default=os.path.join(here, 'plate', name + '_plate.3mf'),        help='plate 3mf from plate.py')
    parser.add_argument('--fig',   default=os.path.join(root, 'out', name + '_supports.png'),       help='picture to write')
    parser.add_argument('--slot',  default=1.0,  type=float,                                        help='[mm] widest slot between two segments that counts as a gap')
    parser.add_argument('--valley', default=2.0, type=float,                                        help='[mm] widest slot between two segments that is counted, without failing')
    parser.add_argument('--step',  default=0.2,  type=float,                                        help='[mm] sampling step along support moves')
    parser.add_argument('--cell',  default=0.2,  type=float,                                        help='[mm] grid cell for the island search')
    parser.add_argument('--rest',  default=2,    type=int,                                          help='layers below a support that must be free of the ball')
    parser.add_argument('--show',  default=(0.25, 2.05, 8.05), type=float, nargs=3,                 help='[mm] heights of the three layers in the picture')
    args = parser.parse_args()

    gco = read_gcode(args.gcode)
    vert, face, block, zorg = read_plate(args.plate)
    par = {'slot': args.slot, 'valley': args.valley, 'step': args.step, 'cell': args.cell, 'rest': args.rest}
    marks     = check_marks(gco)
    sups, geo = check_supports(gco, vert, face, block, zorg, par)
    render(gco, geo, args.fig, args.show)

    fail = 0
    for title, res in (('g-code markers', marks), ('supports', sups)):
        print(title)
        for name, good, detail in res:
            fail += not good
            print(f"  {'PASS' if good else 'FAIL'}  {name:38s} {detail}")
    size = geo['size']
    nlay = len(gco['zlay'])
    print('report')
    print(f"  print time     {gco.get('estimated printing time (normal mode)')}")
    print(f"  filament       {gco.get('total filament used [g]')} g")
    print(f"  layers         {nlay} layer changes in the g-code, top at {gco['zlay'].max():.2f} mm "
          f"(header says {gco.get('total layer number')}, footer {gco.get('total layers count')})")
    print(f"  ball           {size[0]:.1f} x {size[1]:.1f} mm across the spikes, {size[2]:.1f} mm tall, "
          f"{2 * geo['rmax']:.1f} mm across the farthest spike tips, {geo['nbody']} segments")
    print(f"  object center  {gco['center'][0]:g}, {gco['center'][1]:g} mm")
    print('  picture       ', args.fig)
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
