## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Rebuild the Black Church scan as a solid, watertight, 180 mm STL.

Pipeline: keep the church meshes of the glb, rotate y-up to z-up, scale,
voxelize the surface, seal the bottom, fill the volume, keep the largest
island, marching cubes, decimate, place on z=0 at x=y=0.
'''
import argparse, json, re, time
import numpy as np
import trimesh, pymeshlab
from scipy import ndimage as ndi
from skimage import measure

def load_church(path, prefix):
    '''
    Concatenate the glb nodes whose geometry name starts with prefix.

    Args:
        path   (str): glb file
        prefix (str): geometry name prefix of the church scan pieces

    Returns:
        trimesh.Trimesh: church mesh in world coordinates, y-up
    '''
    scn = trimesh.load(path)
    out = []
    for nd in scn.graph.nodes_geometry:
        tf, gn = scn.graph[nd]
        if gn.startswith(prefix):
            g = scn.geometry[gn].copy()
            g.apply_transform(tf)
            out.append(g)
    return trimesh.util.concatenate(out)

def to_voxels(mesh, vox, nsamp_per_vox2=3.0):
    '''
    Occupancy grid of the mesh surface from dense surface samples.

    Args:
        mesh (Trimesh): mesh in mm, z up, min corner anywhere
        vox  (float):   voxel size [mm]

    Returns:
        (ndarray, ndarray): bool grid, origin of voxel (0,0,0) [mm]
    '''
    org = mesh.bounds[0] - 3 * vox
    shp = np.ceil((mesh.bounds[1] - org) / vox).astype(int) + 4
    grd = np.zeros(shp, bool)
    npt = int(mesh.area / vox**2 * nsamp_per_vox2)
    for _ in range(max(1, npt // 5_000_000)):
        pts, _ = trimesh.sample.sample_surface(mesh, min(npt, 5_000_000))
        idx = np.floor((pts - org) / vox).astype(int)
        grd[idx[:, 0], idx[:, 1], idx[:, 2]] = True
    vtx = np.floor((mesh.vertices - org) / vox).astype(int)
    grd[vtx[:, 0], vtx[:, 1], vtx[:, 2]] = True
    return grd, org

def main(par):
    t0 = time.time()
    msh = load_church(par['glb'], par['prefix'])
    print('church tris', len(msh.faces), flush=True)
    ## glb is y-up, make the long axis x and the vertical axis z
    msh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    msh.apply_scale(par['maxdim'] / msh.extents.max())
    msh.apply_translation(-msh.bounds[0])
    print('scaled extents', msh.extents, flush=True)

    grd, org = to_voxels(msh, par['vox'])
    del msh
    print('grid', grd.shape, 'surface vox', grd.sum(), round(time.time() - t0), 's', flush=True)

    ## seal small gaps, then cut the ground
    grd = ndi.binary_closing(grd, structure=ndi.generate_binary_structure(3, 1), iterations=par['close'])
    zcut = int(round(par['cut'] / par['vox'])) + 3
    grd[:, :, :zcut] = False

    ## footprint of the church walls (ground fringe is too thin to survive the opening)
    ftp = grd[:, :, zcut + int(8 / par['vox']):zcut + int(30 / par['vox'])].any(axis=2)
    ftp = ndi.binary_closing(ftp, iterations=4)
    ftp = ndi.binary_fill_holes(ftp)
    ftp = ndi.binary_opening(ftp, iterations=par['open'])
    lab, nlab = ndi.label(ftp)
    ftp = lab == np.bincount(lab.ravel())[1:].argmax() + 1
    ftp = ndi.binary_dilation(ftp, iterations=2)

    ## keep the connected church shell inside the footprint, then fill each column up to its top
    grd &= ftp[:, :, None]
    lab, nlab = ndi.label(grd, structure=ndi.generate_binary_structure(3, 3))
    cnt = np.bincount(lab.ravel()); cnt[0] = 0
    grd = lab == cnt.argmax()
    top = grd.shape[2] - 1 - np.argmax(grd[:, :, ::-1], axis=2)
    top[~grd.any(axis=2)] = 0
    zz = np.arange(grd.shape[2])[None, None, :]
    sol = (zz >= zcut) & (zz <= top[:, :, None]) & ftp[:, :, None]
    print('solid vox', sol.sum(), 'islands', nlab, round(time.time() - t0), 's', flush=True)

    sol = ndi.gaussian_filter(sol.astype(np.float32), 0.7)
    sol = np.pad(sol, 1)
    vrt, fac, _, _ = measure.marching_cubes(sol, 0.5, spacing=(par['vox'],) * 3)
    vrt += org - par['vox']
    out = trimesh.Trimesh(vrt, fac, process=True)
    print('mc tris', len(out.faces), round(time.time() - t0), 's', flush=True)

    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(out.vertices, out.faces))
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=par['ntri'], preservenormal=True,
        preservetopology=True, qualitythr=0.5)
    ms.meshing_remove_duplicate_faces(); ms.meshing_remove_duplicate_vertices()
    ms.meshing_repair_non_manifold_edges(); ms.meshing_close_holes(maxholesize=50)
    cur = ms.current_mesh()
    out = trimesh.Trimesh(cur.vertex_matrix(), cur.face_matrix(), process=True)
    bod = out.split(only_watertight=False)
    out = max(bod, key=lambda b: len(b.faces))
    print('bodies', len(bod), 'kept', len(out.faces), flush=True)
    trimesh.repair.fix_normals(out); trimesh.repair.fix_inversion(out)

    ## the ground cut shrinks the long axis, restore the target size
    out.apply_scale(par['maxdim'] / out.extents.max())

    ## center on x=y=0 and rest on z=0
    bnd = out.bounds
    out.apply_translation([-(bnd[0, 0] + bnd[1, 0]) / 2, -(bnd[0, 1] + bnd[1, 1]) / 2, -bnd[0, 2]])
    out.export(par['out'])
    print(json.dumps({'tris': len(out.faces), 'extents_mm': out.extents.round(2).tolist(),
        'watertight': bool(out.is_watertight), 'winding': bool(out.is_winding_consistent),
        'volume_cm3': round(out.volume / 1000, 2), 'sec': round(time.time() - t0)}, indent=1))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cfg', default='config.json')
    ap.add_argument('--vox', type=float)
    ap.add_argument('--out')
    a = ap.parse_args()
    par = json.load(open(a.cfg))
    for k in ('vox', 'out'):
        if getattr(a, k) is not None: par[k] = getattr(a, k)
    main(par)
