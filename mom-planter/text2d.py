## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Text to 2D outlines (manifold3d CrossSection), shaped with HarfBuzz so kerning and script joins are right.

All sizes in mm. `text_cs(font, text, cap_height=...)` returns a CrossSection whose baseline is y = 0 and
whose left edge is x = 0 (advance-based), plus its metrics.
"""
import os
import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.varLib import instancer
import manifold3d as m3

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
_cache = {}


def font_path(name, wght=None, extra=None):
    """Path of a static font; variable fonts are instanced at `wght` once and cached on disk."""
    src = os.path.join(FONT_DIR, name)
    if wght is None:
        return src
    out = os.path.join(FONT_DIR, "inst", f"{os.path.splitext(name)[0]}-w{wght}.ttf")
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        f = TTFont(src)
        axes = {"wght": wght}
        if extra:
            axes.update(extra)
        instancer.instantiateVariableFont(f, axes, inplace=True)
        f.save(out)
    return out


class _FlatPen(BasePen):
    """Collects contours as point lists, flattening curves to about `tol` font units."""

    def __init__(self, glyphset, steps=12):
        super().__init__(glyphset)
        self.contours, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = np.array(self.cur[-1], float)
        a, b, c = np.array(p1, float), np.array(p2, float), np.array(p3, float)
        for t in np.linspace(0, 1, self.steps + 1)[1:]:
            q = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * a + 3 * (1 - t) * t ** 2 * b + t ** 3 * c
            self.cur.append(tuple(q))

    def _qCurveToOne(self, p1, p2):
        p0 = np.array(self.cur[-1], float)
        a, b = np.array(p1, float), np.array(p2, float)
        for t in np.linspace(0, 1, self.steps + 1)[1:]:
            q = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * a + t ** 2 * b
            self.cur.append(tuple(q))

    def _closePath(self):
        if len(self.cur) > 2:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


def _load(path):
    if path not in _cache:
        blob = hb.Blob.from_file_path(path)
        face = hb.Face(blob)
        hbfont = hb.Font(face)
        tt = TTFont(path)
        _cache[path] = (hbfont, tt, tt.getGlyphSet(), tt["head"].unitsPerEm)
    return _cache[path]


def cap_height_units(path):
    _, tt, gs, upem = _load(path)
    os2 = tt["OS/2"]
    ch = getattr(os2, "sCapHeight", 0) or 0
    if ch <= 0:                                   # measure the H
        pen = _FlatPen(gs)
        gs[tt.getBestCmap()[ord("H")]].draw(pen)
        ch = max(p[1] for c in pen.contours for p in c)
    return ch


def text_contours(path, text, features=None, letter_spacing=0.0):
    """Contours (font units, baseline y=0) for a line of text, and its advance width."""
    hbfont, tt, gs, upem = _load(path)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, features or {"kern": True, "liga": True, "calt": True})
    order = tt.getGlyphOrder()
    contours, x = [], 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        pen = _FlatPen(gs)
        gs[name].draw(pen)
        dx, dy = x + pos.x_offset, pos.y_offset
        for c in pen.contours:
            contours.append([(px + dx, py + dy) for px, py in c])
        x += pos.x_advance + letter_spacing * upem
    return contours, x


def text_cs(path, text, cap_height=None, size_em=None, letter_spacing=0.0, features=None):
    """CrossSection of a text line in mm. Give cap_height (mm of the font's capital height) or size_em."""
    contours, adv = text_contours(path, text, features, letter_spacing)
    _, _, _, upem = _load(path)
    s = cap_height / cap_height_units(path) if cap_height else size_em / upem
    polys = [np.array(c, float) * s for c in contours]
    cs = m3.CrossSection(polys, m3.FillRule.NonZero)
    return cs, adv * s


def centered(cs, cx=0.0, cy=0.0, by_bounds=True):
    b = cs.bounds()   # (xmin, ymin, xmax, ymax)
    return cs.translate(((cx - (b[0] + b[2]) / 2), (cy - (b[1] + b[3]) / 2)))


def heart_cs(width, n=240):
    """Classic heart curve scaled to `width` mm, centered on its bounding box."""
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    pts = np.c_[x, y]
    pts *= width / (x.max() - x.min())
    cs = m3.CrossSection([pts], m3.FillRule.NonZero)
    return centered(cs)


def cs_polys(cs):
    return [np.asarray(p) for p in cs.to_polygons()]


def min_stroke(cs, step=0.05, limit=5.0):
    """Smallest r such that an inward offset by r removes some island (about half the thinnest stroke)."""
    n0 = len(cs.decompose())
    a0 = cs.area()
    r = step
    while r < limit:
        e = cs.offset(-r, m3.JoinType.Round)
        if e.is_empty() or len(e.decompose()) != n0:
            return r
        r += step
    return limit
