## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Display stand for the ʻOumuamua print: a base plate as long as the rock and a
little wider, two posts whose tops are cups cast from the rock's underside
(lower envelope minus a clearance, so the rock lifts straight off), and a
tilted slot with a prop behind it for the plaque, which stands under the rock
between the posts.

The rock is taken from the print STL, turned back to its display pose
(rotz in the rock config undone) and lifted above the base.
'''
import argparse, json

import manifold3d as m3d
import numpy as np
import trimesh

def display_pose(par):
    '''
    Rock in display pose: long axis on x, centered on x=y=0, lowest point at z=0.

    Args:
        par (dict): stand parameters

    Returns:
        trimesh.Trimesh: rock
    '''
    rck = trimesh.load(par['rock'])
    rot = json.load(open(par['rock_cfg']))['rotz']
    rck.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-rot), [0, 0, 1]))
    bnd = rck.bounds
    rck.apply_translation([-(bnd[0, 0] + bnd[1, 0]) / 2, -(bnd[0, 1] + bnd[1, 1]) / 2, -bnd[0, 2]])
    return rck

def lower_envelope(rck, xs, ys):
    '''
    Lowest z of the rock above each grid node (inf outside its silhouette),
    by rasterizing the downward-facing triangles.

    Args:
        rck (Trimesh): rock
        xs  (ndarray): grid x [mm]
        ys  (ndarray): grid y [mm]

    Returns:
        ndarray: (nx, ny) lowest z [mm]
    '''
    env = np.full((len(xs), len(ys)), np.inf)
    tri = rck.triangles[rck.face_normals[:, 2] < 0]
    tri = tri[(tri[:, :, 0].max(1) >= xs[0]) & (tri[:, :, 0].min(1) <= xs[-1])]
    dx  = xs[1] - xs[0]
    dy  = ys[1] - ys[0]
    for t in tri:
        i0 = max(int(np.ceil((t[:, 0].min() - xs[0]) / dx)), 0)
        i1 = min(int(np.floor((t[:, 0].max() - xs[0]) / dx)), len(xs) - 1)
        j0 = max(int(np.ceil((t[:, 1].min() - ys[0]) / dy)), 0)
        j1 = min(int(np.floor((t[:, 1].max() - ys[0]) / dy)), len(ys) - 1)
        if i1 < i0 or j1 < j0:
            continue
        gx, gy = np.meshgrid(xs[i0:i1 + 1], ys[j0:j1 + 1], indexing='ij')
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = t
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-12:
            continue
        a  = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / den
        b  = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / den
        c  = 1 - a - b
        ok = (a >= -1e-9) & (b >= -1e-9) & (c >= -1e-9)
        z  = np.where(ok, a * z0 + b * z1 + c * z2, np.inf)
        env[i0:i1 + 1, j0:j1 + 1] = np.minimum(env[i0:i1 + 1, j0:j1 + 1], z)
    return env

def heightfield(xs, ys, top, zb):
    '''
    Closed solid between z=zb and the top surface over a rectangular grid.

    Args:
        xs  (ndarray): grid x [mm]
        ys  (ndarray): grid y [mm]
        top (ndarray): (nx, ny) top z [mm]
        zb  (float):   bottom z [mm]

    Returns:
        Manifold: solid
    '''
    nx, ny = top.shape
    gx, gy = np.meshgrid(xs, ys, indexing='ij')
    vrt    = np.vstack([np.c_[gx.ravel(), gy.ravel(), top.ravel()],
                        np.c_[gx.ravel(), gy.ravel(), np.full(nx * ny, zb)]])
    idx    = np.arange(nx * ny).reshape(nx, ny)
    a, b   = idx[:-1, :-1].ravel(), idx[1:, :-1].ravel()
    c, d   = idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()
    off    = nx * ny
    fac    = [np.c_[a, b, c], np.c_[a, c, d], np.c_[a, c, b] + off, np.c_[a, d, c] + off]
    ## boundary loop, counterclockwise seen from above
    loop   = np.r_[idx[:, 0], idx[-1, 1:], idx[-2::-1, -1], idx[0, -2:0:-1]]
    p, q   = loop, np.roll(loop, -1)
    fac   += [np.c_[q, p, p + off], np.c_[q, p + off, q + off]]
    msh    = trimesh.Trimesh(vrt, np.vstack(fac), process=False)
    if msh.volume < 0:
        msh.invert()
    return m3d.Manifold(m3d.Mesh(vert_properties=msh.vertices.astype(np.float32),
                                 tri_verts=msh.faces.astype(np.uint32)))

def post(rck, xc, par):
    '''
    One post with a cup cast from the rock's underside.

    Args:
        rck (Trimesh): rock in display pose, already lifted
        xc  (float):   post center x [mm]
        par (dict):    stand parameters

    Returns:
        tuple: Manifold, dict of post facts
    '''
    hw  = par['post_w'] / 2
    xs  = np.arange(xc - hw, xc + hw + 1e-9, par['grid'])
    ys  = np.arange(rck.bounds[0, 1] - 1, rck.bounds[1, 1] + 1 + 1e-9, par['grid'])
    env = lower_envelope(rck, xs, ys)
    zcp = env.min() + par['cup']
    ## keep the rows where the cup reaches the rim height, so the post ends at the rim
    rim = (env - par['gap'] <= zcp).any(axis=0)
    jj  = np.flatnonzero(rim)
    ys  = ys[jj[0]:jj[-1] + 1]
    env = env[:, jj[0]:jj[-1] + 1]
    top = np.minimum(env - par['gap'], zcp)
    sol = heightfield(xs, ys, top, par['base_t'] - 1.0)
    return sol, {'x': xc, 'y': [round(ys[0], 2), round(ys[-1], 2)],
                 'cup_bottom': round(float(top.min()), 2), 'rim': round(float(zcp), 2),
                 'min_clearance': round(float((env - top)[np.isfinite(env)].min()), 3)}

def plaque_frame(par, yb):
    '''
    4x3 transform from plaque coordinates (x along the width, y up the face,
    z out of the front) to the stand, back bottom edge at y=yb.

    Args:
        par (dict):  stand parameters
        yb  (float): y of the back bottom edge [mm]

    Returns:
        ndarray: (3, 4) matrix
    '''
    th = np.radians(par['tilt'])
    return np.array([[1, 0, 0, 0],
                     [0, np.cos(th), -np.sin(th), yb],
                     [0, np.sin(th),  np.cos(th), par['base_t'] - par['slot_d']]])

def main(par):
    rck = display_pose(par)
    rck.apply_translation([0, 0, par['base_t'] + par['lift']])
    lng = rck.extents[0]
    wid = rck.extents[1] + 2 * par['side']

    sec = m3d.CrossSection.square([lng - 2 * par['radius'], wid - 2 * par['radius']], center=True)
    sol = sec.offset(par['radius'], m3d.JoinType.Round, circular_segments=48).extrude(par['base_t'])

    pst = []
    for xc in (-par['post_x'], par['post_x']):
        p, inf = post(rck, xc, par)
        sol = sol + p
        pst.append(inf)

    ## plaque: front bottom corner sits par['front'] in from the front edge
    pw, ph, pt = par['plaque']
    th  = np.radians(par['tilt'])
    yb  = -wid / 2 + par['front'] + pt * np.sin(th)
    frm = plaque_frame(par, yb)
    c   = par['slot_c']
    slot = m3d.Manifold.cube([pw + 2 * c, ph + 2 * c, pt + 2 * c]).translate([-pw / 2 - c, -c, -c]).transform(frm)
    behind = m3d.Manifold.cube([200, 200, 100]).translate([-100, -50, -100 - c]).transform(frm)
    pw2, ph2, pd2 = par['prop']
    prop = m3d.Manifold.cube([pw2, pd2 + 2, ph2 + 1]).translate([-pw2 / 2, yb - 2, par['base_t'] - 1])
    sol  = (sol + (prop ^ behind)) - slot

    msh = sol.to_mesh()
    out = trimesh.Trimesh(np.asarray(msh.vert_properties)[:, :3], np.asarray(msh.tri_verts))
    out.export(par['out'])
    rck.export(par['out_rock'])
    ptop = par['base_t'] - par['slot_d'] + ph * np.sin(th) + pt * np.cos(th)
    fy   = (np.abs(rck.vertices[:, 0]) < pw / 2) & (rck.vertices[:, 1] < yb + ph * np.cos(th))
    print(json.dumps({'out': par['out'], 'extents_mm': out.extents.round(2).tolist(),
        'watertight': bool(out.is_watertight), 'genus': sol.genus(),
        'volume_cm3': round(out.volume / 1000, 2), 'posts': pst,
        'plaque_top_z': round(ptop, 2),
        'rock_low_over_plaque_z': round(float(rck.vertices[fy, 2].min()), 2)}, indent=1))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cfg', default='stand.json')
    ap.add_argument('--out')
    a   = ap.parse_args()
    par = json.load(open(a.cfg))
    if a.out is not None: par['out'] = a.out
    main(par)
