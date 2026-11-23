## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Build a 3D-printable terrain model of the Horse Heaven Hills (WA DNR) survey
area from the USGS 3DEP 1 m lidar DEM, cut to the survey polygon, with a
blind hole at every recovered passive receiver.

Usage:
    python make_print.py [--config config.json]
'''
import argparse
import json
import os
import re
import struct
import zipfile

import numpy as np
import pandas as pd
import rasterio
from rasterio.merge import merge
from rasterio.transform import from_origin
from pyproj import Transformer
from scipy import ndimage
from shapely.geometry import Polygon, Point
from shapely.geometry.polygon import orient
from shapely.ops import nearest_points
from manifold3d import Manifold, Mesh, CrossSection


def load_config(path):
    '''
    Read the json config and expand user paths.

    Args:
        path (str): path to config.json

    Returns:
        dict: configuration
    '''
    with open(path) as f:
        cfg = json.load(f)
    for k in ['boundary_kmz', 'receiver_csv', 'out_dir']:
        cfg[k] = os.path.expanduser(cfg[k])
    return cfg


def read_kmz_ring(path):
    '''
    Read the first polygon ring of a kmz as [(lon, lat), ...].
    '''
    with zipfile.ZipFile(path) as z:
        kml = z.read(next(n for n in z.namelist() if n.endswith('.kml'))).decode()
    blk = re.search(r'<coordinates>(.*?)</coordinates>', kml, re.S).group(1)
    return [tuple(map(float, t.split(',')[:2])) for t in blk.split()]


def read_receivers(path, drop):
    '''
    Read receiver lon/lat and drop stations that were not recovered.

    Returns:
        pandas.DataFrame: columns station, lat, lon
    '''
    df = pd.read_csv(path)
    return df[~df['station'].isin(drop)].reset_index(drop=True)


def fetch_dem(tiles, bounds, crs, out_tif):
    '''
    Mosaic the 1 m DEM tiles over bounds (windowed remote reads) and cache it.
    Earlier tiles take priority; later tiles only fill nodata.

    Returns:
        (numpy.ndarray, affine.Affine): elevation [m] and its transform
    '''
    if os.path.exists(out_tif):
        with rasterio.open(out_tif) as s:
            return s.read(1, masked=True).filled(np.nan), s.transform
    srcs = [rasterio.open('/vsicurl/' + t) for t in tiles]
    arr, trn = merge(srcs, bounds=bounds, res=1.0, nodata=np.nan, dtype='float32')
    for s in srcs:
        s.close()
    dem = arr[0]
    with rasterio.open(out_tif, 'w', driver='GTiff', height=dem.shape[0],
                       width=dem.shape[1], count=1, dtype='float32', crs=crs,
                       transform=trn, nodata=np.nan, compress='deflate',
                       tiled=True) as d:
        d.write(dem, 1)
    return dem, trn


def fill_nan(a):
    '''
    Replace nan cells with the nearest valid value.
    '''
    bad = np.isnan(a)
    if not bad.any():
        return a
    idx = ndimage.distance_transform_edt(bad, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def heightfield_block(z, dx):
    '''
    Closed solid whose top is the grid z (rows = +y, cols = +x, spacing dx)
    and whose bottom is the plane z = 0.

    Returns:
        manifold3d.Manifold: the block
    '''
    ny, nx = z.shape
    yy, xx = np.mgrid[0:ny, 0:nx] * dx
    top = np.column_stack([xx.ravel(), yy.ravel(), z.ravel()])
    vid = np.arange(ny * nx).reshape(ny, nx)

    ## top surface, two ccw triangles per cell
    a, b = vid[:-1, :-1].ravel(), vid[:-1, 1:].ravel()
    c, d = vid[1:, 1:].ravel(),  vid[1:, :-1].ravel()
    tris = [np.column_stack([a, b, c]), np.column_stack([a, c, d])]

    ## perimeter loop (ccw from above), duplicated at z = 0 for the walls
    loop = np.concatenate([vid[0, :], vid[1:, -1], vid[-1, -2::-1], vid[-2:0:-1, 0]])
    nb   = len(loop)
    bot  = top[loop].copy()
    bot[:, 2] = 0.0
    bid  = ny * nx + np.arange(nb)
    p, q   = loop, np.roll(loop, -1)
    pb, qb = bid, np.roll(bid, -1)
    tris += [np.column_stack([p, pb, qb]), np.column_stack([p, qb, q])]

    ## bottom as a fan from its centre, facing down
    cid  = ny * nx + nb
    ctr  = np.array([[xx.max() / 2, yy.max() / 2, 0.0]])
    tris += [np.column_stack([np.full(nb, cid), qb, pb])]

    vert = np.vstack([top, bot, ctr]).astype(np.float32)
    tri  = np.vstack(tris).astype(np.uint32)
    return Manifold(Mesh(vert_properties=vert, tri_verts=tri))


def write_stl(mesh, path):
    '''
    Write a manifold3d Mesh as binary STL [mm].
    '''
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    p = v[t]
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-30
    rec = np.zeros(len(t), dtype=[('n', '<f4', 3), ('p', '<f4', (3, 3)), ('a', '<u2')])
    rec['n'], rec['p'] = n, p
    with open(path, 'wb') as f:
        f.write(b'hhh survey terrain'.ljust(80, b' '))
        f.write(struct.pack('<I', len(t)))
        rec.tofile(f)


def main(cfg):
    os.makedirs(cfg['out_dir'], exist_ok=True)
    out = lambda ext: os.path.join(cfg['out_dir'], cfg['name'] + ext)
    t2u = Transformer.from_crs('EPSG:4326', cfg['crs'], always_xy=True)

    ## survey polygon and receivers in utm [m]
    ring = [t2u.transform(*ll) for ll in read_kmz_ring(cfg['boundary_kmz'])]
    poly = orient(Polygon(ring).buffer(0), sign=1.0)
    rcv  = read_receivers(cfg['receiver_csv'], cfg['not_recovered'])
    rcv['e'], rcv['n'] = t2u.transform(rcv['lon'].values, rcv['lat'].values)
    inside = np.array([poly.contains(Point(e, n)) for e, n in zip(rcv['e'], rcv['n'])])
    edge   = np.array([poly.exterior.distance(Point(e, n)) for e, n in zip(rcv['e'], rcv['n'])])

    ## 1 m dem over the polygon bbox
    x0, y0, x1, y1 = poly.bounds
    pad = cfg['dem_pad_m']
    bnd = (np.floor(x0 - pad), np.floor(y0 - pad), np.ceil(x1 + pad), np.ceil(y1 + pad))
    dem, trn = fetch_dem(cfg['dem_tiles'], bnd, cfg['crs'], out('_dem_1m.tif'))
    dem = fill_nan(dem)

    ## horizontal scale [mm/m] and print grid
    scl  = cfg['max_dim_mm'] / max(x1 - x0, y1 - y0)
    dx   = cfg['cell_mm']
    nx   = int(np.ceil((x1 - x0) * scl / dx)) + 1
    ny   = int(np.ceil((y1 - y0) * scl / dx)) + 1
    gx   = x0 + np.arange(nx) * dx / scl                     # [m] utm easting
    gy   = y0 + np.arange(ny) * dx / scl                     # [m] utm northing
    col  = (gx - trn.c) / trn.a - 0.5
    row  = (gy - trn.f) / trn.e - 0.5
    sig  = 0.5 * dx / scl                                     # [px] antialias
    sm   = ndimage.gaussian_filter(dem, sig)
    rr, cc = np.meshgrid(row, col, indexing='ij')
    elev = ndimage.map_coordinates(sm, [rr, cc], order=1, mode='nearest')

    ## elevation inside the polygon sets the base so the thinnest point is min_thick_mm
    msk  = np.array([[poly.contains(Point(e, n)) for e in gx[::10]] for n in gy[::10]])
    emin = elev[::10, ::10][msk].min()
    emax = elev[::10, ::10][msk].max()
    zmm  = cfg['min_thick_mm'] + (elev - emin) * scl * cfg['vexag']
    zmm  = np.maximum(zmm, cfg['min_thick_mm'])

    ## solid = heightfield block intersected with the polygon prism
    blk  = heightfield_block(zmm.astype(np.float32), dx)
    pts  = [((e - x0) * scl, (n - y0) * scl) for e, n in poly.exterior.coords[:-1]]
    ztop = float(zmm.max()) + 5.0
    prism = Manifold.extrude(CrossSection([pts]), ztop + 5.0).translate([0, 0, -5.0])
    sol  = blk ^ prism

    ## holes too close to the edge move inward to keep edge_wall_mm of wall
    r     = 0.5 * cfg['hole_diam_mm']
    keep  = poly.buffer(-(r + cfg['edge_wall_mm']) / scl)
    he, hn = rcv['e'].values.copy(), rcv['n'].values.copy()
    for k in range(len(rcv)):
        p = Point(he[k], hn[k])
        if not keep.contains(p):
            he[k], hn[k] = nearest_points(keep, p)[0].coords[0]
    shift = np.hypot(he - rcv['e'].values, hn - rcv['n'].values)

    ## blind holes, depth measured from the lowest rim point
    rpx   = int(np.ceil(r / dx)) + 1
    holes = []
    for e, n in zip(he, hn):
        hx, hy = (e - x0) * scl, (n - y0) * scl
        i, j   = int(round(hx / dx)), int(round(hy / dx))
        rim    = zmm[max(j - rpx, 0):j + rpx + 1, max(i - rpx, 0):i + rpx + 1].min()
        zb     = rim - cfg['hole_depth_mm']
        cyl    = Manifold.cylinder(ztop - zb, r, r, cfg['hole_segs'])
        holes.append(cyl.translate([hx, hy, zb]))
    sol = sol - Manifold.compose(holes)                      # holes are disjoint

    sol  = sol.simplify(cfg['simplify_mm'])                  # drop sub-micron boolean slivers
    mesh = sol.to_mesh()
    write_stl(mesh, out('.stl'))
    rcv.assign(inside=inside, edge_m=edge, hole_e=he, hole_n=hn, shift_m=shift).to_csv(out('_receivers.csv'), index=False)

    ## report
    lo, hi = np.array(sol.bounding_box()[:3]), np.array(sol.bounding_box()[3:])
    rep = {
        'status'          : str(sol.status()),
        'genus'           : sol.genus(),
        'n_tri'           : int(sol.num_tri()),
        'size_mm'         : (hi - lo).round(2).tolist(),
        'scale_mm_per_m'  : scl,
        'map_scale'       : f'1:{1000 / scl:,.0f}',
        'elev_range_m'    : [float(emin), float(emax)],
        'relief_mm'       : float((emax - emin) * scl * cfg['vexag']),
        'n_holes'         : len(holes),
        'n_outside_poly'  : int((~inside).sum()),
        'closest_edge_m'  : float(edge.min()),
        'closest_edge_mm' : float(edge.min() * scl),
        'n_holes_shifted' : int((shift > 0).sum()),
        'max_shift_mm'    : float(shift.max() * scl),
        'volume_cm3'      : sol.volume() / 1000.0,
    }
    with open(out('_report.json'), 'w') as f:
        json.dump(rep, f, indent=2)
    print(json.dumps(rep, indent=2))
    np.savez_compressed(out('_grid.npz'), zmm=zmm, dx=dx, scl=scl, x0=x0, y0=y0)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json'))
    main(load_config(ap.parse_args().config))
