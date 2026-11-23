## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Estimate the print time of a G-code file with Klipper's lookahead planner
(toolhead.py Move, calc_junction and flush, plus the extruder corner limit),
because OrcaSlicer's estimate runs 1.0 to 1.4x low on the SV06 ACE.

Checked 2026-11-12 against four finished prints (printer print_duration):
logo 2.26 vs 2.26 h, Team1 5.14 vs 5.11 h, Kilauea test 1.32 vs 1.31 h,
hhh relief 11.13 vs 11.12 h at 91% of the file.

Usage:
    python3 klipper_time.py FILE.gcode [--limits klipper_limits.json] [--write]
        [--margin 0.05] [--mcr 0.5] [--types] [--pad 0.5]

--write replaces the "; estimated printing time" line and every M73 line with
the Klipper time times (1 + margin), so Moonraker, Mainsail, the phone app and
the printer screen count down from it.

--pad TOL (with --write) adds ";PAD" comment lines where the G-code is thin
for its print time, so the file position (Klipper virtual_sdcard.progress,
the percentage Obico shows) stays within TOL percentage points of the elapsed
time. Rerunning replaces old pad lines; --pad 0 removes them.
'''
import argparse
import bisect
import itertools
import json
import math
import os
import re

here = os.path.dirname(os.path.abspath(__file__))
keys = ('accel', 'vmax', 'mcr', 'scv', 'icv', 'zv', 'za', 'ev', 'ea', 'margin')
pad  = b';PAD '                     # marker of the padding comment lines
padw = 250                          # [bytes] length of a full padding line
orca = b'; orca estimate (normal mode) = '


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('gcode')
    p.add_argument('--limits', default=os.path.join(here, 'klipper_limits.json'))
    p.add_argument('--write',  action='store_true', help='rewrite the time lines in place')
    p.add_argument('--types',  action='store_true', help='print time by feature type')
    p.add_argument('--at',     type=float,          help='also report elapsed time at this file fraction (of the unpadded file)')
    p.add_argument('--pad',    type=float,          help='pad so file progress tracks time to within this many percentage points')
    for k in keys:
        p.add_argument('--' + k, type=float, help='override the limits file')
    a   = p.parse_args()
    lim = json.load(open(a.limits))
    for k in keys:
        if getattr(a, k) is None:
            setattr(a, k, float(lim[k]))
    return a


class Move:
    '''
    One G1 move with the limits Klipper's toolhead would give it.
    '''
    __slots__ = ('d', 'r', 'kin', 'er', 'accel', 'jd', 'cruise2', 'dv2', 'sdv2',
                 'start2', 'smooth2', 't')

    def __init__(s, a, dx, dy, dz, de, v, st):
        d      = math.sqrt(dx*dx + dy*dy + dz*dz)
        s.kin  = d >= 1e-9
        accel  = st['accel']
        if not s.kin:
            d = abs(de); v = min(v, a.ev); accel = min(accel, a.ea)
            s.r = (0., 0., 0.); s.er = 0.
        else:
            s.r = (dx/d, dy/d, dz/d); s.er = de/d
        s.d     = d
        v       = min(v, st['vmax'])
        s.accel = accel
        s.sdv2  = 2.*d*accel*(1. - st['mcr'])
        if s.kin and abs(dz) > 1e-9:
            zr = d/abs(dz)
            v  = min(v, a.zv*zr); s.accel = min(s.accel, a.za*zr)
        s.cruise2 = v*v
        s.dv2     = 2.*d*s.accel
        s.sdv2    = min(s.sdv2, s.dv2)
        s.jd      = st['scv']**2*(math.sqrt(2.) - 1.)/st['accel']
        s.start2  = 0.; s.smooth2 = 0.; s.t = 0.


def junction(a, m, p):
    '''
    Set the highest start speed of move m after move p (Move.calc_junction).

    Args:
        a (Namespace): limits
        m      (Move): this move
        p      (Move): previous move, or None
    '''
    if p is None or not m.kin or not p.kin:
        return
    v2 = min(m.cruise2, p.cruise2, p.start2 + p.dv2)
    dr = m.er - p.er
    if dr:
        v2 = min(v2, (a.icv/abs(dr))**2)
    c  = -(m.r[0]*p.r[0] + m.r[1]*p.r[1] + m.r[2]*p.r[2])
    s2 = math.sqrt(max(.5*(1. - c), 0.))
    c2 = math.sqrt(max(.5*(1. + c), 0.))
    if 1. - s2 > 0. and c2 > 0.:
        rjd = s2/(1. - s2)
        q   = .25*s2/c2
        v2  = min(v2, rjd*m.jd*m.accel, rjd*p.jd*p.accel, m.dv2*q, p.dv2*q)
    m.start2  = v2
    m.smooth2 = min(v2, p.smooth2 + p.sdv2)


def set_time(m, s2, c2, e2):
    '''
    Trapezoid time of move m from its start, cruise and end speeds squared.
    '''
    h  = .5/m.accel
    ad = (c2 - s2)*h; dd = (c2 - e2)*h; cd = m.d - ad - dd
    sv, cv, ev = math.sqrt(s2), math.sqrt(c2), math.sqrt(e2)
    m.t = (ad/((sv + cv)*.5) if ad > 0 else 0.) + cd/cv + (dd/((ev + cv)*.5) if dd > 0 else 0.)


def flush(q):
    '''
    Backward lookahead pass of Klipper's toolhead over the whole queue.
    '''
    delayed = []
    nend2   = nsm2 = peak2 = 0.
    for m in reversed(q):
        reach2 = nend2 + m.dv2
        start2 = min(m.start2, reach2)
        rsm2   = nsm2 + m.sdv2
        sm2    = min(m.smooth2, rsm2)
        if sm2 < rsm2:
            if sm2 + m.sdv2 > nsm2 or delayed:
                peak2 = min(m.cruise2, (sm2 + rsm2)*.5)
                if delayed:
                    mc2 = peak2
                    for dm, ds2, de2 in reversed(delayed):
                        mc2 = min(mc2, ds2)
                        set_time(dm, min(ds2, mc2), mc2, min(de2, mc2))
                    delayed = []
            c2 = min((start2 + reach2)*.5, m.cruise2, peak2)
            set_time(m, min(start2, c2), c2, min(nend2, c2))
        else:
            delayed.append((m, start2, nend2))
        nend2 = start2
        nsm2  = sm2
    for dm, ds2, de2 in delayed:
        c2 = min(dm.cruise2, ds2)
        set_time(dm, min(ds2, c2), c2, min(de2, c2))


num  = r'([-+]?\d*\.?\d+)'
rx   = {k: re.compile(k + num) for k in 'XYZEFSPT'}
rsv  = re.compile(r'(ACCEL|SQUARE_CORNER_VELOCITY|MINIMUM_CRUISE_RATIO|VELOCITY)=' + num)
svk  = {'ACCEL': 'accel', 'VELOCITY': 'vmax', 'SQUARE_CORNER_VELOCITY': 'scv', 'MINIMUM_CRUISE_RATIO': 'mcr'}


def plan(a):
    '''
    Read the G-code and time every move.

    Returns:
        list : moves
        list : byte offset of the end of each move's line (pad lines not counted)
        list : feature type of each move
        int  : file size without pad lines [bytes]
        bytes: orca's own estimate from an earlier --write, or None
    '''
    st   = {'accel': a.accel, 'vmax': a.vmax, 'mcr': a.mcr, 'scv': a.scv}
    pos  = [0., 0., 0., 0.]; absxyz = True; abse = False; f = 1500.
    q    = []; offs = []; typ = []; prev = None; off = 0; cur = 'Custom'; old = None
    with open(a.gcode, 'rb') as fh:
        for raw in fh:
            if raw.startswith(pad):
                continue
            off += len(raw)
            if raw.startswith(orca):
                old = raw[len(orca):].strip()
                continue
            if raw.startswith(b';TYPE:'):
                cur = raw[6:].strip().decode(errors='ignore')
                continue
            ln = raw.split(b';', 1)[0].strip().decode(errors='ignore')
            if not ln:
                continue
            if ln.startswith(('G1 ', 'G0 ')):
                v = {k: float(m.group(1)) for k in 'XYZEF' for m in [rx[k].search(ln)] if m}
                if 'F' in v: f = v['F']
                new = list(pos)
                for i, k in enumerate('XYZ'):
                    if k in v: new[i] = v[k] if absxyz else pos[i] + v[k]
                if 'E' in v: new[3] = v['E'] if abse else pos[3] + v['E']
                dx, dy, dz, de = (new[i] - pos[i] for i in range(4))
                pos = new
                if dx == dy == dz == de == 0.:
                    continue
                m = Move(a, dx, dy, dz, de, f/60., st)
                junction(a, m, prev)
                q.append(m); offs.append(off); typ.append(cur); prev = m
            elif ln.startswith('SET_VELOCITY_LIMIT'):
                for k, val in rsv.findall(ln):
                    st[svk[k]] = float(val)
            elif ln.startswith('M204'):
                ## klipper takes S, else the smaller of P and T
                v = {k: float(m.group(1)) for k in 'SPT' for m in [rx[k].search(ln)] if m}
                if 'S' in v:                  st['accel'] = v['S']
                elif 'P' in v and 'T' in v:   st['accel'] = min(v['P'], v['T'])
            elif ln == 'G90': absxyz = True
            elif ln == 'G91': absxyz = False
            elif ln == 'M82': abse   = True
            elif ln == 'M83': abse   = False
            elif ln.startswith('G92'):
                for i, k in enumerate('XYZE'):
                    m_ = rx[k].search(ln)
                    if m_: pos[i] = float(m_.group(1))
    flush(q)
    return q, offs, typ, off, old


def hms(t):
    '''
    Format seconds the way Orca writes them (Moonraker parses this form).
    '''
    t = int(round(t)); d, t = divmod(t, 86400); h, t = divmod(t, 3600); m, s = divmod(t, 60)
    return (f'{d}d ' if d else '') + (f'{h}h ' if d or h else '') + f'{m}m {s}s'


def pad_plan(offs, cum, size, tol):
    '''
    Padding that keeps the file fraction read (Klipper virtual_sdcard.progress)
    within tol of the elapsed time fraction.

    Padding goes after the move that ends each time step (tol/2 of the print,
    at most 60 s). For a padded size S, the cumulative padding at step j is
    the smallest that brings the file fraction up to the time fraction; S is
    the smallest (bisection) whose worst misfit at any step is within tol.

    Args:
        offs (list) : end offset of each move's line, unpadded [bytes]
        cum  (list) : elapsed time at the end of each move [s]
        size (int)  : unpadded file size [bytes]
        tol  (float): allowed misfit, fraction of the whole print

    Returns:
        dict : {insertion offset: pad bytes inserted there}
        int  : padded file size [bytes]
        float: worst misfit, fraction
    '''
    tot   = cum[-1]
    dt    = min(60., .5*tol*tot)
    xs    = []; fs = []; nxt = dt
    for o, c in zip(offs, cum):
        if c >= nxt:
            xs.append(o); fs.append(c/tot); nxt = c + dt

    def build(s):
        P = 0; ps = []
        for x, fr in zip(xs, fs):
            P = max(P, int(fr*s - x)); ps.append(P)
        sa  = size + P
        err = 0.; prev = 0
        for x, fr, p in zip(xs, fs, ps):
            err = max(err, abs((x + prev)/sa - fr), abs((x + p)/sa - fr)); prev = p
        return ps, sa, err

    ## bisection on the padded size, in log space
    lo, hi = float(size), 50.*size
    if build(hi)[2] > tol:
        lo = hi
    for _ in range(40):
        mid = math.sqrt(lo*hi)
        if build(mid)[2] <= tol: hi = mid
        else:                    lo = mid
    ps, sa, err = build(hi)
    ins  = {}; prev = 0
    for x, p in zip(xs, ps):
        if p > prev:
            ins[x] = p - prev; prev = p
    return ins, sa, err


def pad_lines(n):
    '''n bytes of ";PAD" comment lines.'''
    out = []
    while n > 0:
        w = max(min(n, padw), len(pad) + 1)
        out.append(pad + b'.'*(w - len(pad) - 1) + b'\n'); n -= w
    return b''.join(out)


def rewrite(path, offs, cum, tot, margin, old=None, ins=None):
    '''
    Replace the estimated time line and the M73 lines in place, drop old pad
    lines and insert new ones (ins: {unpadded offset: bytes}).
    '''
    ttot = tot*(1. + margin)
    ins  = ins or {}
    tmp  = path + '.tmp'
    off  = 0
    with open(path, 'rb') as fi, open(tmp, 'wb') as fo:
        for raw in fi:
            if raw.startswith(pad):
                continue
            off += len(raw)
            if raw.startswith(orca):
                continue
            if raw.startswith(b'M73 P'):
                i   = bisect.bisect_right(offs, off) - 1
                el  = cum[i] if i >= 0 else 0.
                pct = min(100, int(100.*el/tot))
                rem = int(math.ceil((tot - el)*(1. + margin)/60.))
                raw = f'M73 P{pct} R{rem}\n'.encode()
            elif raw.startswith(b'; estimated printing time (normal mode) = '):
                prior = old.decode() if old else raw.split(b'= ', 1)[1].strip().decode()
                raw   = f'; estimated printing time (normal mode) = {hms(ttot)}\n'.encode() + orca + prior.encode() + b'\n'
            fo.write(raw)
            if off in ins:
                fo.write(pad_lines(ins[off]))
    os.replace(tmp, path)


def run(a):
    q, offs, typ, size, old = plan(a)
    cum = list(itertools.accumulate(m.t for m in q))
    tot = cum[-1] if cum else 0.
    print(f'klipper estimate: {hms(tot)} ({tot/3600:.2f} h), with {100*a.margin:.0f}% margin {hms(tot*(1 + a.margin))}'
          f'  [mcr {a.mcr:g}, scv {a.scv:g}]')
    if a.at is not None:
        i    = bisect.bisect_right(offs, a.at*size) - 1
        print(f'elapsed at file fraction {a.at:.4f}: {cum[i]/3600:.2f} h')
    ins = {}
    if a.pad and tot > 0:
        ins, sa, err = pad_plan(offs, cum, size, a.pad/100.)
        print(f'padding: {size/1e6:.1f} -> {sa/1e6:.1f} MB ({len(ins)} places); file progress within '
              f'{100*err:.2f} percentage points of elapsed time')
    if a.types:
        by = {}
        for m, t in zip(q, typ):
            by[t] = by.get(t, 0.) + m.t
        for t, s in sorted(by.items(), key=lambda kv: -kv[1]):
            print(f'  {t:28s} {s/3600:6.2f} h  {100*s/tot:5.1f}%')
    if a.write:
        rewrite(a.gcode, offs, cum, tot, a.margin, old, ins)
        print(f'rewrote time lines in {a.gcode}')


if __name__ == '__main__':
    run(parse_args())
