'''
Add a climbing route to the Rainier relief STL as a raised ridge, with round
pads at named points (camp, trailhead).

The route comes from OpenStreetMap trails: --fetch downloads the paths in
osm_bbox, finds the shortest trail path start -> via -> end and saves it as
route_csv (lat, lon, way name); later runs read the csv only. The ridge is a
chain of hulls of vertical cylinders (ridge_w across) whose top sits ridge_h
above the highest terrain under it and whose bottom sinks below the lowest,
the same rule as the Kilauea receiver dots. Pads (pad_d across) stand pad_h
above the highest terrain under them. Everything is unioned onto the input
mesh, unchanged or with its heights multiplied by --z-scale (the base sits at
z = 0, so 1.5 turns the 2x model into 3x vertical exaggeration).

Usage:
    python add_route.py [--config route_config.json] [--fetch [--osm-json saved.json]]
        [--z-scale 1.5 --out name_3x.stl]
'''
import argparse
import csv
import json
import os
import struct
import urllib.parse
import urllib.request

import networkx as nx
import numpy as np
from manifold3d import Manifold, Mesh, OpType
from pyproj import Transformer
from scipy.interpolate import RegularGridInterpolator


def load_config(path):
    '''
    Read the json config; file names are taken from the config's folder.

    Returns:
        dict: configuration
    '''
    with open(path) as f:
        cfg = json.load(f)
    base = os.path.dirname(os.path.abspath(path))
    for k in ['stl_in', 'stl_out', 'route_csv']:
        cfg[k] = os.path.join(base, cfg[k])
    return cfg


def haversine(a, b):
    '''Great-circle distance [m] between (lat, lon) points.'''
    la1, lo1, la2, lo2 = map(np.radians, (a[0], a[1], b[0], b[1]))
    h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000.0 * np.arcsin(np.sqrt(h))


def fetch_route(cfg, osm_json=None):
    '''
    Download OSM trails in osm_bbox (or read a saved Overpass response) and
    return the shortest trail path from start through each via point to end.

    Returns:
        list: rows (lat, lon, way name)
    '''
    s, w, n, e = cfg['osm_bbox']
    qry = ('[out:json][timeout:150];way["highway"~"path|footway|track|steps"]'
           '(%g,%g,%g,%g);out geom tags;' % (s, w, n, e))
    if osm_json:
        with open(osm_json) as f:
            ways = json.load(f)['elements']
    else:
        req = urllib.request.Request(cfg['overpass'], data=urllib.parse.urlencode({'data': qry}).encode(),
                                     headers={'User-Agent': 'relief-route-builder/1.0'})
        with urllib.request.urlopen(req, timeout=200) as r:
            ways = json.load(r)['elements']

    ## graph on shared vertex coordinates, edges weighted by length
    G = nx.Graph()
    for wy in ways:
        pts  = [(round(p['lat'], 7), round(p['lon'], 7)) for p in wy['geometry']]
        name = wy.get('tags', {}).get('name', '')
        for a, b in zip(pts[:-1], pts[1:]):
            G.add_edge(a, b, weight=haversine(a, b), name=name)
    nodes = np.array(list(G.nodes))

    def nearest(p):
        d = haversine((nodes[:, 0], nodes[:, 1]), (p['lat'], p['lon']))
        i = int(np.argmin(d))
        print('%-18s snapped %6.1f m to the trail network' % (p['name'], d[i]))
        return tuple(nodes[i])

    stops = [nearest(p) for p in [cfg['start']] + cfg['via'] + [cfg['end']]]
    path  = [stops[0]]
    for a, b in zip(stops[:-1], stops[1:]):
        path += nx.shortest_path(G, a, b, weight='weight')[1:]
    names = [''] + [G.edges[a, b]['name'] for a, b in zip(path[:-1], path[1:])]
    return [(p[0], p[1], nm) for p, nm in zip(path, names)]


def save_route(rows, path):
    with open(path, 'w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['lat', 'lon', 'way'])
        wr.writerows(rows)


def read_route(path):
    '''
    Returns:
        tuple: lat (n,), lon (n,), way names (n,)
    '''
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return (np.array([float(r['lat']) for r in rows]), np.array([float(r['lon']) for r in rows]),
            [r['way'] for r in rows])


def to_model(cfg, lat, lon):
    '''
    WGS84 to model coordinates [mm]: UTM offset from center_utm times the map scale.

    Returns:
        numpy.ndarray: (n, 2) x, y
    '''
    tr   = Transformer.from_crs('EPSG:4326', cfg['crs'], always_xy=True)
    e, n = tr.transform(np.atleast_1d(lon), np.atleast_1d(lat))
    scl  = cfg['side_mm'] / cfg['side_m']                   # [mm/m] map scale
    return np.column_stack([(e - cfg['center_utm'][0]) * scl, (n - cfg['center_utm'][1]) * scl])


def simplify(p, tol):
    '''Douglas-Peucker simplification of a 2D polyline.'''
    if len(p) < 3:
        return p
    a, b = p[0], p[-1]
    ab   = b - a
    L    = np.linalg.norm(ab)
    d    = (np.abs(ab[0] * (p[:, 1] - a[1]) - ab[1] * (p[:, 0] - a[0])) / L if L > 0
            else np.linalg.norm(p - a, axis=1))
    i    = int(np.argmax(d))
    if d[i] <= tol:
        return np.vstack([a, b])
    return np.vstack([simplify(p[:i + 1], tol)[:-1], simplify(p[i:], tol)])


def densify(p, step):
    '''Keep every vertex and add points so no gap exceeds step.'''
    out = [p[0]]
    for a, b in zip(p[:-1], p[1:]):
        k    = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        out += list(a + (b - a) * (np.arange(1, k + 1)[:, None] / k))
    return np.array(out)


def load_stl(path):
    '''
    Binary STL to merged vertices and faces.

    Returns:
        tuple: vertices (n, 3), faces (m, 3)
    '''
    with open(path, 'rb') as f:
        f.read(80)
        n   = struct.unpack('<I', f.read(4))[0]
        rec = np.frombuffer(f.read(n * 50), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    u, inv = np.unique(rec['v'].reshape(-1, 3), axis=0, return_inverse=True)
    return u, inv.reshape(-1, 3)


def terrain_grid(V):
    '''
    Interpolator of the heightfield top surface (all vertices above z = 0).

    Returns:
        scipy.interpolate.RegularGridInterpolator: z [mm] at (y, x) [mm]
    '''
    top    = V[V[:, 2] > 0]
    xs, ix = np.unique(top[:, 0], return_inverse=True)
    ys, iy = np.unique(top[:, 1], return_inverse=True)
    Z      = np.full((len(ys), len(xs)), np.nan)
    Z[iy, ix] = top[:, 2]
    if np.isnan(Z).any():
        raise RuntimeError('top surface is not a full grid')
    return RegularGridInterpolator((ys, xs), Z)


def disc_range(zf, p, r):
    '''
    Highest and lowest terrain under discs of radius r centred on points p.

    Returns:
        tuple: zmax (n,), zmin (n,)
    '''
    ang  = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    offs = [np.zeros((1, 2))] + [f * r * np.column_stack([np.cos(ang), np.sin(ang)]) for f in (0.35, 0.7, 1.0)]
    offs = np.vstack(offs)
    q    = p[:, None, :] + offs[None, :, :]
    z    = zf(q[..., ::-1].reshape(-1, 2)).reshape(q.shape[:2])
    return z.max(axis=1), z.min(axis=1)


def post(xy, z0, z1, r, segs):
    '''Vertical cylinder from z0 to z1 at xy.'''
    return Manifold.cylinder(z1 - z0, r, r, segs).translate([xy[0], xy[1], z0])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--config',   default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'route_config.json'))
    ap.add_argument('--fetch',    action='store_true', help='rebuild route_csv from OpenStreetMap')
    ap.add_argument('--osm-json', default=None, help='saved Overpass response to use instead of downloading')
    ap.add_argument('--z-scale',  default=1.0,  type=float, help='multiply the input mesh heights first')
    ap.add_argument('--out',      default=None, help='output STL, overrides stl_out')
    args = ap.parse_args()
    cfg  = load_config(args.config)
    if args.out:
        cfg['stl_out'] = os.path.join(os.path.dirname(cfg['stl_out']), args.out)

    if args.fetch or not os.path.exists(cfg['route_csv']):
        save_route(fetch_route(cfg, args.osm_json), cfg['route_csv'])
    lat, lon, ways = read_route(cfg['route_csv'])
    used = [w for i, w in enumerate(ways) if w and w not in ways[:i]]
    print('route: %d points, ways: %s' % (len(lat), ', '.join(used)))

    V, F  = load_stl(cfg['stl_in'])
    V[:, 2] *= args.z_scale
    base  = Manifold(Mesh(vert_properties=V.astype(np.float32), tri_verts=F.astype(np.uint32)))
    if base.status().name != 'NoError':
        raise RuntimeError('input mesh is not manifold: %s' % base.status())
    zf    = terrain_grid(V)

    ## ridge: hull of consecutive posts along the densified route
    xy    = to_model(cfg, lat, lon)
    xy    = densify(simplify(xy, cfg['simplify']), cfg['step'])
    r     = cfg['ridge_w'] / 2
    zmax, zmin = disc_range(zf, xy, r)
    ztop  = zmax + cfg['ridge_h']
    zbot  = zmin - cfg['sink']
    posts = [post(p, b, t, r, cfg['segs']) for p, b, t in zip(xy, zbot, ztop)]
    parts = [Manifold.batch_hull([a, b]) for a, b in zip(posts[:-1], posts[1:])]
    plen  = np.linalg.norm(np.diff(xy, axis=0), axis=1).sum()
    print('ridge: %.1f mm long, %d segments, x %.1f to %.1f, y %.1f to %.1f mm, top %.2f to %.2f mm, '
          'stands %.2f to %.2f mm above the terrain beside it'
          % (plen, len(parts), xy[:, 0].min(), xy[:, 0].max(), xy[:, 1].min(), xy[:, 1].max(),
             ztop.min(), ztop.max(), (ztop - zmax).min(), (ztop - zmin).max()))

    ## pads at named points
    for pd in cfg['pads']:
        c       = to_model(cfg, pd['lat'], pd['lon'])
        hi, lo  = disc_range(zf, c, cfg['pad_d'] / 2)
        t       = hi[0] + cfg['pad_h']
        parts  += [post(c[0], lo[0] - cfg['sink'], t, cfg['pad_d'] / 2, 2 * cfg['segs'])]
        print('pad %-18s at x %6.2f y %6.2f mm, top %.2f mm, %.2f to %.2f mm above the terrain under it'
              % (pd['name'], c[0, 0], c[0, 1], t, cfg['pad_h'], t - lo[0]))

    out  = Manifold.batch_boolean([base] + parts, OpType.Add)
    mesh = out.to_mesh()
    v    = np.asarray(mesh.vert_properties)[:, :3]
    p    = v[np.asarray(mesh.tri_verts)]
    nrm  = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-30
    rec  = np.zeros(len(p), dtype=[('n', '<f4', 3), ('p', '<f4', (3, 3)), ('a', '<u2')])
    rec['n'], rec['p'] = nrm, p
    with open(cfg['stl_out'], 'wb') as f:
        f.write(b'binary stl'.ljust(80, b' '))
        f.write(np.uint32(len(rec)).tobytes())
        f.write(rec.tobytes())
    print('volume %.2f -> %.2f cm3 (+%.3f), genus %d, %d triangles -> %s'
          % (base.volume() / 1e3, out.volume() / 1e3, (out.volume() - base.volume()) / 1e3,
             out.genus(), len(p), os.path.basename(cfg['stl_out'])))


if __name__ == '__main__':
    main()
