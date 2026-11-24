## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Turn ESO's ʻOumuamua model (ESO/M. Kornmesser,
https://www.eso.org/public/products/models3d/oumuamua/) into a printable STL.

Pipeline: load the obj, merge the uv-seam vertices so the shell closes,
align the principal axes (long axis on x, thinnest axis on z), scale the
long axis to the real length over the map scale (400 m at 1:2000 is 200 mm),
decimate, turn about z (diagonal on the bed), center on x=y=0 and rest on
z=0. The model floats on its curved underside, so print it with supports.
'''
import argparse, json, time
import numpy as np
import trimesh, pymeshlab

def load_closed(path):
    '''
    Load the obj and weld the vertices split along uv seams.

    Args:
        path (str): obj file

    Returns:
        trimesh.Trimesh: single closed shell
    '''
    raw = trimesh.load(path, force='mesh', process=False)
    msh = trimesh.Trimesh(raw.vertices, raw.faces, process=True)
    msh.merge_vertices(digits_vertex=4)
    return msh

def align_axes(msh):
    '''
    Rotate so the principal axes of the shell lie on x (longest), y, z (thinnest).

    Args:
        msh (Trimesh): closed mesh

    Returns:
        trimesh.Trimesh: rotated mesh
    '''
    msh.apply_translation(-msh.center_mass)
    _, vec = np.linalg.eigh(np.cov(msh.vertices.T))
    rot      = np.eye(4)
    rot[:3, :3] = vec[:, ::-1].T
    if np.linalg.det(rot[:3, :3]) < 0:
        rot[2, :3] *= -1
    msh.apply_transform(rot)
    return msh

def decimate(msh, ntri):
    '''
    Quadric decimation to ntri triangles, keeping the topology closed.

    Args:
        msh  (Trimesh): input mesh
        ntri (int):     target triangle count

    Returns:
        trimesh.Trimesh: decimated mesh
    '''
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(msh.vertices, msh.faces))
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=ntri, preservenormal=True,
        preservetopology=True, qualitythr=0.5)
    cur = ms.current_mesh()
    out = trimesh.Trimesh(cur.vertex_matrix(), cur.face_matrix(), process=True)
    trimesh.repair.fix_normals(out)
    return out

def main(par):
    t0  = time.time()
    msh = load_closed(par['obj'])
    print('obj tris', len(msh.faces), 'watertight', msh.is_watertight, flush=True)
    msh = align_axes(msh)
    lng = par['real_m'] * 1000 / par['scale']     # [mm] printed long axis
    msh.apply_scale(lng / msh.extents[0])
    if par['ntri'] < len(msh.faces):
        msh = decimate(msh, par['ntri'])
    msh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(par['rotz']), [0, 0, 1]))
    bnd = msh.bounds
    msh.apply_translation([-(bnd[0, 0] + bnd[1, 0]) / 2, -(bnd[0, 1] + bnd[1, 1]) / 2, -bnd[0, 2]])
    msh.export(par['out'])
    print(json.dumps({'scale': f"1:{par['scale']:g}", 'length_mm': round(lng, 2),
        'tris': len(msh.faces), 'extents_mm': msh.extents.round(2).tolist(),
        'watertight': bool(msh.is_watertight), 'winding': bool(msh.is_winding_consistent),
        'volume_cm3': round(msh.volume / 1000, 2), 'sec': round(time.time() - t0)}, indent=1))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cfg', default='config.json')
    ap.add_argument('--scale', type=float, help='map scale denominator (2000 for 1:2000)')
    ap.add_argument('--rotz',  type=float, help='turn about z on the bed [deg]')
    ap.add_argument('--out')
    a   = ap.parse_args()
    par = json.load(open(a.cfg))
    for k in ('scale', 'rotz', 'out'):
        if getattr(a, k) is not None: par[k] = getattr(a, k)
    main(par)
