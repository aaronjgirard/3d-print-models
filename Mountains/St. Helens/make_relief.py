'''
Build 3D-printable relief models of Mount St. Helens before the 1980 eruption
and today, at the same footprint, scale and vertical exaggeration as the
Rainier model (../Rainier/mount_rainier_5in_square_2x.stl): a 36 km square
centred on the summit printed 127 mm wide, z = vexag * map scale * elevation
above sea level, flat bottom at z = 0.

Modern surface: Aug 2022 USGS lidar (crater and Toutle drainages) over the
newest 3DEP 1 m lidar per tile, gaps from the 3DEP 1/3 arc-second DEM.
Pre-1980 surface: the USGS 1952 DEM pasted into the modern surface, feathered
over blend_m inside its edge (outside it the 1980 changes are below print
resolution).

Usage:
    python make_relief.py [--config config.json] [--lidar-2022 path.tif]
'''
import argparse
import json
import os

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.windows import from_bounds
from scipy import ndimage
from manifold3d import Manifold, Mesh


def load_config(path):
    '''
    Read the json config; relative paths are taken from the config's folder.

    Args:
        path (str): path to config.json

    Returns:
        dict: configuration
    '''
    with open(path) as f:
        cfg = json.load(f)
    base = os.path.dirname(os.path.abspath(path))
    for k in ['pre_dem', 'out_dir', 'cache_dir']:
        cfg[k] = os.path.join(base, os.path.expanduser(cfg[k]))
    if cfg['lidar_2022'].startswith('/vsizip/') and not cfg['lidar_2022'].startswith('/vsizip//'):
        cfg['lidar_2022'] = '/vsizip/' + os.path.join(base, cfg['lidar_2022'][len('/vsizip/'):])
    return cfg


def work_grid(cfg):
    '''
    Work grid at work_res_m whose cells tile the print nodes exactly: node k
    is the mean of an f x f block of work cells.

    Returns:
        (affine.Affine, int, int): transform, size (cells per side), f
    '''
    dn   = cfg['side_m'] / (cfg['n_nodes'] - 1)        # [m] node spacing
    f    = int(round(dn / cfg['work_res_m']))
    cx, cy = cfg['center_utm']
    half = cfg['side_m'] / 2 + dn / 2
    trn  = from_origin(cx - half, cy + half, dn / f, dn / f)
    return trn, cfg['n_nodes'] * f, f


def write_tif(arr, trn, crs, path):
    '''
    Write a float32 GeoTIFF with nan nodata.
    '''
    with rasterio.open(path, 'w', driver='GTiff', height=arr.shape[0], width=arr.shape[1],
                       count=1, dtype='float32', crs=crs, transform=trn, nodata=np.nan,
                       compress='deflate', tiled=True) as d:
        d.write(arr.astype('float32'), 1)


def read_tif(path):
    with rasterio.open(path) as s:
        return s.read(1)


def warp_into(src_path, trn, n, crs, scale=1.0):
    '''
    Average-resample a raster of any CRS onto the work grid.

    Returns:
        numpy.ndarray: elevation [m], nan where the source has no data
    '''
    with rasterio.open(src_path) as s:
        with WarpedVRT(s, crs=crs, transform=trn, width=n, height=n,
                       resampling=Resampling.average, src_nodata=s.nodata,
                       nodata=np.nan, dtype='float32') as v:
            a = v.read(1)
    return np.where(np.isfinite(a), a * scale, np.nan)


def read_same_crs(url, trn, n):
    '''
    Read a remote COG in the work CRS straight into the work grid, letting
    GDAL pick the overview nearest the work resolution.

    Returns:
        numpy.ndarray: elevation [m], nan outside the tile or on nodata
    '''
    out = np.full((n, n), np.nan, dtype='float32')
    res = trn.a
    x0, y1 = trn.c, trn.f
    with rasterio.open('/vsicurl/' + url) as s:
        b  = s.bounds
        lx = max(b.left,  x0);           rx = min(b.right, x0 + n * res)
        by = max(b.bottom, y1 - n * res); ty = min(b.top,  y1)
        if lx >= rx or by >= ty:
            return out
        ## snap the overlap to work cell edges
        c0 = int(np.ceil((lx - x0) / res));  c1 = int(np.floor((rx - x0) / res))
        r0 = int(np.ceil((y1 - ty) / res));  r1 = int(np.floor((y1 - by) / res))
        if c1 <= c0 or r1 <= r0:
            return out
        win = from_bounds(x0 + c0 * res, y1 - r1 * res, x0 + c1 * res, y1 - r0 * res, s.transform)
        a   = s.read(1, window=win, out_shape=(r1 - r0, c1 - c0), masked=True,
                     resampling=Resampling.average)
    out[r0:r1, c0:c1] = a.filled(np.nan)
    return out


def build_modern(cfg, trn, n):
    '''
    Mosaic the modern surface on the work grid, newest source first; later
    sources only fill cells still empty. Cached in cache_dir.

    Returns:
        numpy.ndarray: elevation [m]
    '''
    path = os.path.join(cfg['cache_dir'], 'modern_%gm.tif' % trn.a)
    if os.path.exists(path):
        return read_tif(path)
    dem = warp_into(cfg['lidar_2022'], trn, n, cfg['crs'], cfg['ft_to_m'])
    src = np.where(np.isfinite(dem), 1, 0).astype('uint8')
    print('lidar 2022: %.1f%% of grid' % (100 * np.isfinite(dem).mean()))
    for i, url in enumerate(cfg['tiles_1m']):
        gap = np.isnan(dem)
        if not gap.any():
            break
        a    = read_same_crs(url, trn, n)
        fill = gap & np.isfinite(a)
        dem[fill], src[fill] = a[fill], 2
        print('1 m tile %2d/%d %-60s fills %.1f%%' % (i + 1, len(cfg['tiles_1m']),
              os.path.basename(url), 100 * fill.mean()))
    for url in cfg['tiles_13']:
        gap = np.isnan(dem)
        if not gap.any():
            break
        a    = warp_into('/vsicurl/' + url, trn, n, cfg['crs'])
        fill = gap & np.isfinite(a)
        dem[fill], src[fill] = a[fill], 3
        print('1/3 arc-second %s fills %.2f%%' % (os.path.basename(url), 100 * fill.mean()))
    if np.isnan(dem).any():
        raise RuntimeError('modern surface has %d empty cells' % np.isnan(dem).sum())
    write_tif(dem, trn, cfg['crs'], path)
    write_tif(src.astype('float32'), trn, cfg['crs'], path.replace('.tif', '_source.tif'))
    return dem


def build_pre(cfg, modern, trn, n):
    '''
    Paste the 1952 (pre-1980) DEM into the modern surface, weight ramping 0 to
    1 over blend_m inward from the edge of its coverage.

    Returns:
        numpy.ndarray: elevation [m]
    '''
    pre = warp_into(cfg['pre_dem'], trn, n, cfg['crs'])
    ok  = np.isfinite(pre)
    w   = np.clip(ndimage.distance_transform_edt(ok) * trn.a / cfg['blend_m'], 0, 1)
    print('pre-1980 DEM: %.1f%% of grid, %.1f%% at full weight' % (100 * ok.mean(), 100 * (w == 1).mean()))
    return np.where(ok, w * np.nan_to_num(pre) + (1 - w) * modern, modern)


def to_nodes(dem, f):
    '''
    Mean of each f x f block of work cells: one value per print node.
    '''
    m = dem.shape[0] // f
    return dem.reshape(m, f, m, f).mean(axis=(1, 3))


def heightfield_mesh(z, dx):
    '''
    Closed solid with top surface z (row 0 = north, spacing dx), vertical
    sides and a flat bottom at z = 0, centred on x = y = 0.

    Returns:
        manifold3d.Manifold: the solid (construction checks it is manifold)
    '''
    z      = z[::-1]                                    # row 0 = south, rows = +y
    ny, nx = z.shape
    yy, xx = np.mgrid[0:ny, 0:nx] * dx
    xx, yy = xx - xx.max() / 2, yy - yy.max() / 2
    top    = np.column_stack([xx.ravel(), yy.ravel(), z.ravel()])
    vid    = np.arange(ny * nx).reshape(ny, nx)

    ## top surface, two ccw triangles per cell
    a, b = vid[:-1, :-1].ravel(), vid[:-1, 1:].ravel()
    c, d = vid[1:, 1:].ravel(),   vid[1:, :-1].ravel()
    tris = [np.column_stack([a, b, c]), np.column_stack([a, c, d])]

    ## perimeter loop (ccw from above), duplicated at z = 0 for the walls
    loop   = np.concatenate([vid[0, :], vid[1:, -1], vid[-1, -2::-1], vid[-2:0:-1, 0]])
    nb     = len(loop)
    bot    = top[loop].copy()
    bot[:, 2] = 0.0
    bid    = ny * nx + np.arange(nb)
    p, q   = loop, np.roll(loop, -1)
    pb, qb = bid, np.roll(bid, -1)
    tris  += [np.column_stack([p, pb, qb]), np.column_stack([p, qb, q])]

    ## bottom as a fan from its centre, facing down
    cid   = ny * nx + nb
    tris += [np.column_stack([np.full(nb, cid), qb, pb])]

    vert = np.vstack([top, bot, [[0.0, 0.0, 0.0]]]).astype(np.float32)
    tri  = np.vstack(tris).astype(np.uint32)
    return Manifold(Mesh(vert_properties=vert, tri_verts=tri))


def write_stl(solid, path):
    '''
    Write a manifold3d solid as binary STL [mm].
    '''
    mesh = solid.to_mesh()
    v    = np.asarray(mesh.vert_properties)[:, :3]
    p    = v[np.asarray(mesh.tri_verts)]
    nrm  = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-30
    rec  = np.zeros(len(p), dtype=[('n', '<f4', 3), ('p', '<f4', (3, 3)), ('a', '<u2')])
    rec['n'], rec['p'] = nrm, p
    with open(path, 'wb') as f:
        f.write(b'binary stl'.ljust(80, b' '))
        f.write(np.uint32(len(rec)).tobytes())
        f.write(rec.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--config',     default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json'))
    ap.add_argument('--lidar-2022', default=None, help='extracted 2022dem.tif (faster than reading the zip)')
    args = ap.parse_args()
    cfg  = load_config(args.config)
    if args.lidar_2022:
        cfg['lidar_2022'] = args.lidar_2022
    os.makedirs(cfg['cache_dir'], exist_ok=True)

    trn, n, f = work_grid(cfg)
    zscl      = cfg['vexag'] * cfg['side_mm'] / cfg['side_m']       # [mm/m] vertical
    dx        = cfg['side_mm'] / (cfg['n_nodes'] - 1)              # [mm] node spacing
    modern    = build_modern(cfg, trn, n)
    surfs     = {'modern': modern, 'pre': build_pre(cfg, modern, trn, n)}
    ntrn      = from_origin(trn.c, trn.f, trn.a * f, trn.a * f)
    for key, dem in surfs.items():
        elev  = to_nodes(dem, f)
        name  = cfg['names'][key]
        write_tif(elev, ntrn, cfg['crs'], os.path.join(cfg['cache_dir'], name + '_nodes.tif'))
        solid = heightfield_mesh(elev * zscl, dx)
        path  = os.path.join(cfg['out_dir'], name + '.stl')
        write_stl(solid, path)
        print('%-40s elev %6.0f to %6.0f m  z %5.2f to %5.2f mm  volume %.1f cm3  -> %s'
              % (name, elev.min(), elev.max(), elev.min() * zscl, elev.max() * zscl,
                 solid.volume() / 1e3, os.path.basename(path)))


if __name__ == '__main__':
    main()
