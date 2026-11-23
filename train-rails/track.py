## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Printable track for a battery Christmas-train set: straight, 22.5 degree curve and a short
connector test piece. Units mm, z up, every part in print orientation (bottom on the bed).

Each piece is built in track coordinates (s, t): s runs along the centerline from the male (tab) end
at s = 0 to the female (prong) end at s = L, and t is the lateral offset, positive to the left of the
direction of travel. A Path maps (s, t) to the bed plane (straight, or an arc turning right), and
every feature is a 2D polygon in (s, t), mapped and then extruded between two heights. Past either
end the path continues straight along the end tangent, so the tab and the prongs stay straight on a
curve, as on the originals.

Measured on the originals (caliper, Nov 22 2026; the first batch of readings carried a 35.5 mm
offset and is corrected here):
  gauge 31.8 inside rail to inside rail, rail 1.55 to 1.7 thick and 7.0 tall, tie tops 2.2,
  ties 7.4 wide and 46 long, straight 164 rail end to rail end, 8 curves make 180 degrees.
  Male end: 1.0 mm plate reaching 5.3 past the end tie, then a 3.0 mm block 8.7 long and 15.2 wide;
  the plate is wider than the block (about 20 to 22 mm, from photos). The last tie has no ends past
  the rails, and the rail ends are raised underneath so the other piece's prongs slide under them.
  Female end: two prongs 10.25 wide (46 outside to outside, 25.5 apart), 19 long, reaching 13.5 past
  the rail ends; each is a 1.0 mm plate on the inside (7.25 wide) with a 2.1 mm rib on the outside
  (3.0 wide). The thin plate only starts at the rail ends; inside the piece the prong is rib height from
  the rail's outer face out, so the raised part is an L in plan view. Behind the end there is a bridge
  (4.1 to 5.0 long, from photos) over a recess for the plate, then a window (about 10.8 x 16.4) that
  the block rises into.
  Tie tops carry a wood grain on the originals; here it is a printable version (see grain_board).
  As far as the geometry shows, a joint goes together at an angle: the prongs have to get under the
  other piece's rail ends while the bridge drops onto the plate in front of the block, so the prongs flex.

Curve radius: a single curve measured 155.0 end to end at the outer rail (offset-corrected), which
gives 380 at the centerline; 8 curves measured 80 to 82 cm across the open ends, which gives 383 to
393 if measured at the outer rails, with the joints splaying a little. CURVE_R = 380.
Original curves turn right going from the tab end to the prong end; so do these.
"""
import math
import numpy as np
from manifold3d import Manifold, CrossSection, OpType, set_circular_segments
from shapely.geometry import LineString, box
from shapely.ops import unary_union

set_circular_segments(64)

# ---------------- track (measured) ----------------
GAUGE = 31.8
RAIL_IN = GAUGE / 2              # 15.9, inner face of each rail
RAIL_OUT = 17.6                  # 1.7 mm rails; only the inner face matters to the wheels
RAIL_H = 7.0
RAIL_END_CH = 0.5                # lead-in chamfer on the inner corner at each rail end
TIE_H = 2.2
TIE_W = 7.4
TIE_HALF = 23.0                  # 46 mm ties
WEB_IN = 10.0                    # low web along the inside of each rail; the windows between ties are 20 wide
WEB_H = 1.2
END_H = 3.0                      # male last tie and female deck (block height, so the block sits flush)
STRAIGHT_L = 164.0
CURVE_DEG = 22.5
CURVE_R = 380.0
TIE_PITCH = 21.0                 # target spacing; the originals are about 21 on the straight

# ---------------- male (tab) end, printed values ----------------
LAST_TIE_W = TIE_W               # last tie, no ends past the rails
PLATE_T = 0.8                    # under the original bridge, which clears a 1.0 plate
PLATE_HALF = 9.5                 # 19.0 wide (originals about 20 to 22)
PLATE_EAR = 5.0                  # the wide part of the plate stops here; the block width continues to the block
BLOCK_S0, BLOCK_S1 = 5.35, 13.9  # from the end face: original block 5.3 to 14.0
BLOCK_HALF = 7.55                # 15.1 wide (original 15.2)
BLOCK_CH = 0.4                   # chamfer on the block's top edges
M_RECESS_T = 12.3                # recess under the rail ends for the original prongs (inner edge 12.75)
M_RECESS_L = 14.2                # original prongs reach 13.5
M_RECESS_H = 1.4                 # original prong plate 1.0
FIRST_TIE_S = 14.7               # first full tie starts here, as on the originals
PRONG_CLEAR_X = 14.4             # on a curve, the inner end of the first radial tie stays this far along the start
                                 # tangent, clear of the original prongs (13.5)

# ---------------- female (prong) end, printed values ----------------
DECK_L = 17.0                    # solid deck behind the joint, END_H tall
BRIDGE_L = 4.6                   # original block starts 5.3 from the joint
WINDOW_S1 = 15.6                 # window far edge from the joint (original block ends at 14.0)
WINDOW_HALF = 8.2                # 16.4 wide (original block 15.2)
F_RECESS_HALF = 12.6             # recess under the bridge for the original plate (up to about 22 wide)
F_RECESS_L = 6.0                 # original plate is 5.3 long
F_RECESS_H = 1.4                 # original plate 1.0
PRONG_IN = 13.1                  # original gap 25.5 (12.75); 0.35 side clearance on the original male
PRONG_RIB_IN = 20.0
PRONG_OUT = TIE_HALF             # 46 outside to outside
PRONG_PAST = 13.3                # original 13.5; original male's first full tie starts at 14.7
PRONG_BACK = 5.5                 # prongs start this far inside the female end (19 long in total)
PRONG_THIN_H = 0.8               # under the original rail ends, which clear a 1.0 prong
PRONG_RIB_H = TIE_H
PRONG_TIP_R_OUT = 2.0            # rounded tip corners, as on the originals (outer corner of the rib)
PRONG_TIP_R_IN = 1.5             # inner corner of the thin plate
END_FACE_CH = 0.6                # chamfer on the top edge of both end faces between the rails, so a joint can close at an angle

TEST_L = 33.0                    # connector test piece, rail end to rail end

# ---------------- wood grain on the tie tops ----------------
GRAIN = True
GRAIN_W = 0.65                   # groove width: about 1.5 line widths, so the slicer leaves it open
GRAIN_D = 0.4                    # groove depth: two 0.2 mm layers
GRAIN_PITCH = 1.75               # grain line spacing; plain lands between grooves stay about 0.9 wide
GRAIN_EDGE = 0.5                 # plain land kept along the long edges of every tie
GRAIN_AMP_TIE = 0.3              # waviness of the grain on the ties
GRAIN_AMP_PLANK = 0.15           # straighter grain on the end planks
GRAIN_RAIL_GAP = 0.4             # no grooves this close to a rail
GRAIN_WINDOW_GAP = 0.8           # or to the window (on a curve the window follows the end tangent, 0.3 off the arc)


# ---------------- path ----------------
class Path:
    """Centerline from s = 0 to s = L, straight (R None) or an arc turning right; straight past the ends."""

    def __init__(self, L, R=None):
        self.L, self.R = float(L), (None if R is None else float(R))

    def frame(self, s):
        """Point and heading angle (radians, CCW from +x) on the centerline at s (0 <= s <= L)."""
        if self.R is None:
            return np.array([s, 0.0]), 0.0
        th = s / self.R
        return np.array([self.R * math.sin(th), -self.R + self.R * math.cos(th)]), -th

    def map(self, st):
        st = np.asarray(st, float)
        s, t = st[:, 0], st[:, 1]
        if self.R is None:
            return np.column_stack([s, t])
        out = np.empty_like(st)
        L, R = self.L, self.R
        a = s < 0
        out[a] = np.column_stack([s[a], t[a]])
        b = s > L
        th = L / R
        c = np.array([R * math.sin(th), -R + R * math.cos(th)])
        T = np.array([math.cos(th), -math.sin(th)])
        N = np.array([math.sin(th), math.cos(th)])
        out[b] = c + np.outer(s[b] - L, T) + np.outer(t[b], N)
        m = ~(a | b)
        thm = s[m] / R
        out[m] = np.column_stack([(R + t[m]) * np.sin(thm), -R + (R + t[m]) * np.cos(thm)])
        return out


class EndFrame:
    """Straight frame along the tangent at the female end (s = L) of a path: (s, t) -> C(L) + (s - L) T + t N.
    Connector cuts use this (start frame: a plain straight Path) so they line up with the straight tab and
    prongs of the neighbouring piece rather than following the arc."""

    def __init__(self, path):
        self.path, self.L, self.R = path, path.L, None
        p, ang = path.frame(path.L)
        self.c, self.T, self.N = p, np.array([math.cos(ang), math.sin(ang)]), np.array([-math.sin(ang), math.cos(ang)])

    def map(self, st):
        st = np.asarray(st, float)
        return self.c + np.outer(st[:, 0] - self.L, self.T) + np.outer(st[:, 1], self.N)


def _ccw(p):
    p = np.asarray(p, float)
    a = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    return p if a > 0 else p[::-1]


def _densify(poly, path, ds=0.75):
    """Subdivide edges along s on one global grid (multiples of ds, plus s = 0 and s = L), so that
    features sharing an arc get identical vertices and the booleans leave no sliver triangles."""
    poly = _ccw(poly)
    out = []
    n = len(poly)
    for i in range(n):
        p0, p1 = poly[i], poly[(i + 1) % n]
        cuts = [0.0, 1.0]
        dsg = p1[0] - p0[0]
        if path.R is not None and abs(dsg) > 1e-9:
            lo, hi = sorted((p0[0], p1[0]))
            grid = [k * ds for k in range(int(math.floor(lo / ds)) + 1, int(math.ceil(hi / ds)))]
            for sb in grid + [0.0, path.L]:
                f = (sb - p0[0]) / dsg
                if 1e-9 < f < 1 - 1e-9:
                    cuts.append(f)
        cuts = sorted(set(round(c, 12) for c in cuts))
        for c in cuts[:-1]:
            out.append(p0 + c * (p1 - p0))
    return np.array(out)


def prism(poly, z0, z1, path):
    """Extrude a polygon given in (s, t) between heights z0 and z1, bent along the path."""
    xy = path.map(_densify(poly, path))
    return Manifold.extrude(CrossSection([xy.tolist()]), z1 - z0).translate((0, 0, z0))


def rect(s0, s1, t0, t1):
    return [(s0, t0), (s1, t0), (s1, t1), (s0, t1)]


def union(parts):
    parts = [p for p in parts if p is not None and not p.is_empty()]
    return Manifold.batch_boolean(parts, OpType.Add) if parts else Manifold()


def diff(a, cuts):
    cuts = [c for c in cuts if c is not None and not c.is_empty()]
    return Manifold.batch_boolean([a] + cuts, OpType.Subtract) if cuts else a


# ---------------- layout ----------------
def tie_centers(L, R=None):
    """Full ties between the male end region and the female deck, evenly spaced near TIE_PITCH.
    On a curve the first tie moves back until its inner end clears the straight prongs of the next piece."""
    s0 = FIRST_TIE_S
    if R is not None:
        s0 = max(s0, R * math.asin(PRONG_CLEAR_X / (R - TIE_HALF)))
    s_first = s0 + TIE_W / 2
    s_last = L - DECK_L - TIE_W / 2          # last tie touches the deck, like the originals' long end deck
    if s_last < s_first:
        return []
    n = max(1, int(round((s_last - s_first) / TIE_PITCH)) + 1)
    if n == 1:
        return [s_first]
    return list(np.linspace(s_first, s_last, n))


# ---------------- features ----------------
# Each feature is (x-y polygon, z0, z1): a polygon given in (s, t), mapped through a frame. The piece is
# assembled band by band in height (see build), so every boolean is a 2D one.
def shape(poly, frame):
    return _ccw(frame.map(_densify(poly, frame)))


def mirror_t(poly):
    return [(s, -t) for s, t in poly]


def rails(path):
    L, a, b, c = path.L, RAIL_IN, RAIL_OUT, RAIL_END_CH
    poly = [(0, a + c), (c, a), (L - c, a), (L, a + c), (L, b), (0, b)]
    return [(shape(poly, path), 0, RAIL_H), (shape(mirror_t(poly), path), 0, RAIL_H)]


def webs(path):
    L = path.L
    return [(shape(rect(0, L, WEB_IN, RAIL_IN + 0.01), path), 0, WEB_H),
            (shape(rect(0, L, -RAIL_IN - 0.01, -WEB_IN), path), 0, WEB_H)]


def ties(path):
    return [(shape(rect(c - TIE_W / 2, c + TIE_W / 2, -TIE_HALF, TIE_HALF), path), 0, TIE_H)
            for c in tie_centers(path.L, path.R)]


def end_face_chamfer(frame, s_face, inward):
    """Triangular cutter along the top edge of an end face at s_face, between the rails (so the rail ends
    stay square). inward = +1 when the piece lies at s > s_face (male end), -1 when it lies at s < s_face."""
    c = END_FACE_CH
    # the 45 degree face runs 0.3 past the end face so no cutter edge lies on it (coincident edges leave slivers)
    tri = np.array([(-inward * 0.3, END_H - c - 0.3), (inward * c, END_H), (inward * c, END_H + 1.0),
                    (-inward * 1.0, END_H + 1.0), (-inward * 1.0, END_H - c - 0.3)])
    w = 2 * (RAIL_IN - 0.2)
    m = Manifold.extrude(CrossSection([_ccw(tri).tolist()]), w).translate((0, 0, -w / 2))   # x = s, y = height, z = t
    m = m.rotate((90, 0, 0))                                                                  # x = s, y = -t, z = height
    p = frame.map(np.array([[s_face, 0.0], [s_face + 1.0, 0.0]]))
    ang = math.degrees(math.atan2(p[1, 1] - p[0, 1], p[1, 0] - p[0, 0]))
    return m.rotate((0, 0, ang)).translate((p[0, 0], p[0, 1], 0))


def male_end(path):
    """Last tie, tab plate and the recesses for the other piece's prongs.
    Returns (solids, cuts, 3D solids, 3D cuts); the chamfered block is a 3D solid."""
    start = Path(path.L)                                   # straight frame along the start tangent
    solids = [(shape(rect(0, LAST_TIE_W, -RAIL_OUT + 0.05, RAIL_OUT - 0.05), path), 0, END_H),
              (shape(rect(-PLATE_EAR, 0.5, -PLATE_HALF, PLATE_HALF), path), 0, PLATE_T),
              (shape(rect(-BLOCK_S0 - 0.3, 0.5, -BLOCK_HALF, BLOCK_HALF), path), 0, PLATE_T)]
    lo = prism(rect(-BLOCK_S1, -BLOCK_S0, -BLOCK_HALF, BLOCK_HALF), 0, END_H - BLOCK_CH, path)
    hi = prism(rect(-BLOCK_S1 + BLOCK_CH, -BLOCK_S0 - BLOCK_CH, -BLOCK_HALF + BLOCK_CH, BLOCK_HALF - BLOCK_CH),
               END_H - 0.01, END_H, path)
    cuts = [(shape(rect(-0.2, M_RECESS_L, M_RECESS_T, 40), start), -1, M_RECESS_H),
            (shape(rect(-0.2, M_RECESS_L, -40, -M_RECESS_T), start), -1, M_RECESS_H)]
    return solids, cuts, [Manifold.batch_hull([lo, hi])], [end_face_chamfer(start, 0.0, +1)]


def _arc(cs, ct, r, a0, a1, n=8):
    return [(cs + r * math.cos(math.radians(a)), ct + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]


def prong_outlines(L):
    """One prong (+t side) as (polygon in (s, t), height) pieces. The thin plate runs from the rail ends to the
    tip; the rib runs the full 19 mm along the outer edge; the root inside the piece, from the rail's outer
    face to the rib, is rib height. Rib plus root make the L-shaped raised part seen on the originals."""
    s0, s1 = L - PRONG_BACK, L + PRONG_PAST
    ri, ro = PRONG_TIP_R_IN, PRONG_TIP_R_OUT
    thin = ([(L - 0.3, PRONG_IN), (s1 - ri, PRONG_IN)] + _arc(s1 - ri, PRONG_IN + ri, ri, -90, 0)[1:-1] +
            [(s1, PRONG_IN + ri), (s1, PRONG_RIB_IN + 0.01), (L - 0.3, PRONG_RIB_IN + 0.01)])
    rib = ([(s0, PRONG_RIB_IN), (s1, PRONG_RIB_IN), (s1, PRONG_OUT - ro)] + _arc(s1 - ro, PRONG_OUT - ro, ro, 0, 90)[1:-1] +
           [(s1 - ro, PRONG_OUT), (s0, PRONG_OUT)])
    root = rect(s0, L, RAIL_OUT - 0.1, PRONG_RIB_IN + 0.01)
    return [(thin, PRONG_THIN_H), (rib, PRONG_RIB_H), (root, PRONG_RIB_H)]


def female_end(path):
    """Deck with the bridge, window and recess, plus the prongs. Returns (solids, cuts, 3D solids, 3D cuts)."""
    L = path.L
    solids = [(shape(rect(L - DECK_L - 0.1, L, -RAIL_OUT + 0.05, RAIL_OUT - 0.05), path), 0, END_H)]
    for poly, h in prong_outlines(L):
        solids.append((shape(poly, path), 0, h))
        solids.append((shape(mirror_t(poly), path), 0, h))
    end = EndFrame(path)
    cuts = [(shape(rect(L - WINDOW_S1, L - BRIDGE_L, -WINDOW_HALF, WINDOW_HALF), end), -1, 10),
            (shape(rect(L - F_RECESS_L, L + 0.2, -F_RECESS_HALF, F_RECESS_HALF), end), -1, F_RECESS_H)]
    return solids, cuts, [], [end_face_chamfer(end, L, -1)]


def grain_board(s_lo, s_hi, region, seed, amp):
    """Wood grain for one board whose length runs along t: wavy grooves (polygons in s, t) between s_lo and
    s_hi, clipped to `region` (the board's exposed top in s, t). Neighbouring lines wave nearly in phase so the
    lands between them keep their width; each line breaks off once or twice at random, like real grain."""
    rng = np.random.default_rng(seed)
    t_lo, t_hi = region.bounds[1], region.bounds[3]
    lam, ph = rng.uniform(14, 26), rng.uniform(0, 2 * math.pi)
    lam2, ph2 = rng.uniform(4.5, 8.0), rng.uniform(0, 2 * math.pi)
    a1, a2 = amp * rng.uniform(0.6, 1.0), 0.25 * amp
    half = GRAIN_W / 2
    lo, hi = s_lo + GRAIN_EDGE + half + a1 + a2, s_hi - GRAIN_EDGE - half - a1 - a2
    if hi < lo:
        return []
    n = int(math.floor((hi - lo) / GRAIN_PITCH)) + 1
    offs = (lo + hi) / 2 + GRAIN_PITCH * (np.arange(n) - (n - 1) / 2)
    t = np.arange(t_lo - 1.0, t_hi + 1.0001, 0.35)
    pieces = []
    for k, o in enumerate(offs):
        s = o + a1 * np.sin(2 * math.pi * t / lam + ph + 0.15 * k) + a2 * np.sin(2 * math.pi * t / lam2 + ph2 + 0.9 * k)
        keep = np.ones(len(t), bool)
        breaks = rng.choice([0, 1, 1, 2]) if t_hi - t_lo > 15 else 0      # short boards keep whole lines
        for _ in range(breaks):
            c, w = rng.uniform(t_lo, t_hi), rng.uniform(2.0, 5.0)
            keep &= np.abs(t - c) > w / 2
        idx = np.flatnonzero(keep)
        for run in (np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1) if len(idx) else []):
            if len(run) >= 9:                                   # drop stubs shorter than about 3 mm
                pieces.append(LineString(np.column_stack([s[run], t[run]])).buffer(half, cap_style=1, quad_segs=3))
    if not pieces:
        return []
    g = unary_union(pieces).intersection(region)
    polys = [g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]
    return [list(q.exterior.coords)[:-1] for q in polys if q.area > 0.6]     # no dots left where a rail clips a line


def grain_cuts(path):
    """Groove cuts on the exposed tops of the full ties, the male last tie and the female deck."""
    if not GRAIN:
        return []
    L, g = path.L, GRAIN_RAIL_GAP
    cuts = []

    def add(polys, top):
        cuts.extend((shape(p, path), top - GRAIN_D, top) for p in polys)

    rails_out = lambda s0, s1: unary_union([box(s0 - 1, RAIL_IN - g, s1 + 1, RAIL_OUT + g),
                                            box(s0 - 1, -RAIL_OUT - g, s1 + 1, -RAIL_IN + g)])
    for i, c in enumerate(tie_centers(L, path.R)):
        s0, s1 = c - TIE_W / 2, c + TIE_W / 2
        region = box(s0, -TIE_HALF, s1, TIE_HALF).difference(rails_out(s0, s1))
        add(grain_board(s0, s1, region, seed=1000 + int(round(c * 10)), amp=GRAIN_AMP_TIE), TIE_H)
    # male last tie, kept clear of the chamfer on the end face
    add(grain_board(END_FACE_CH, LAST_TIE_W, box(0, -RAIL_IN + g, LAST_TIE_W, RAIL_IN - g), seed=11,
                    amp=GRAIN_AMP_PLANK), END_H)
    # female deck: the bridge, and the two strips beside the window
    add(grain_board(L - BRIDGE_L, L - END_FACE_CH, box(L - BRIDGE_L, -RAIL_IN + g, L, RAIL_IN - g), seed=12,
                    amp=GRAIN_AMP_PLANK), END_H)
    w = WINDOW_HALF + GRAIN_WINDOW_GAP
    for sg, seed in ((1, 13), (-1, 14)):
        t0, t1 = sorted((sg * w, sg * (RAIL_IN - g)))
        add(grain_board(L - WINDOW_S1, L - BRIDGE_L, box(L - WINDOW_S1, t0, L - BRIDGE_L, t1), seed=seed,
                        amp=GRAIN_AMP_PLANK), END_H)
    return cuts


def build(solids, cuts, solids3d=(), cuts3d=()):
    """Assemble 2.5D features band by band: between consecutive feature heights the cross-section is the 2D
    union of the solids spanning that band minus the cuts spanning it, extruded; the bands are then stacked.
    2D booleans snap near-coincident edges, so features mapped through different frames (arc, start tangent,
    end tangent) leave no sliver triangles."""
    top = max(z1 for _, _, z1 in solids)
    zs = sorted({0.0, top} | {z for _, a, b in solids for z in (a, b)} |
                {min(max(z, 0.0), top) for _, a, b in cuts for z in (a, b)})
    bands = []
    for za, zb in zip(zs[:-1], zs[1:]):
        if zb - za < 1e-6:
            continue
        zm = 0.5 * (za + zb)
        sol = [CrossSection([p.tolist()]) for p, a, b in solids if a < zm < b]
        if not sol:
            continue
        cs = CrossSection.batch_boolean(sol, OpType.Add)
        cu = [CrossSection([p.tolist()]) for p, a, b in cuts if a < zm < b]
        if cu:
            cs = CrossSection.batch_boolean([cs] + cu, OpType.Subtract)
        if not cs.is_empty():
            bands.append(Manifold.extrude(cs, zb - za).translate((0, 0, za)))
    body = union(bands + list(solids3d))
    return diff(body, list(cuts3d))


def piece(path):
    ms, mc, m3, mc3 = male_end(path)
    fs, fc, f3, fc3 = female_end(path)
    body = build(rails(path) + webs(path) + ties(path) + ms + fs, mc + fc + grain_cuts(path), m3 + f3, mc3 + fc3)
    # merge coplanar faces and collapse the zero-length edges left where band walls meet (moves nothing > 1 um)
    return body.as_original().simplify(1e-3)


def straight():
    return piece(Path(STRAIGHT_L))


def curve_path(R=CURVE_R):
    return Path(R * math.radians(CURVE_DEG), R)


def curve(R=CURVE_R):
    return piece(curve_path(R))


def test_piece():
    return piece(Path(TEST_L))


def attach(m, path):
    """Move a piece (male end at the origin, heading +x) onto the female end of `path`."""
    p, ang = path.frame(path.L)
    return m.rotate((0, 0, math.degrees(ang))).translate((p[0], p[1], 0))


if __name__ == "__main__":
    for name, m in (("straight", straight()), ("curve", curve()), ("test", test_piece())):
        b = m.bounding_box()
        print(f"{name:9s} genus {m.genus():3d}  vol {m.volume() / 1000:6.2f} cm3  "
              f"bbox {b[3] - b[0]:.1f} x {b[4] - b[1]:.1f} x {b[5] - b[2]:.1f}  bodies {len(m.decompose())}")
    print("straight ties at", [round(c, 2) for c in tie_centers(STRAIGHT_L)])
    print("curve ties at", [round(c, 2) for c in tie_centers(curve_path().L, CURVE_R)], "L", round(curve_path().L, 2))
