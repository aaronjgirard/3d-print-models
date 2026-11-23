"""Straight tubes N pitches tall with the fit-ladder connector (config/project.json).

Same body as stl/tubes (OD 29.6, bore 25.6 straight through, 47.3 mm per pitch),
with the current split-ring plug and 45 deg shoulder from parts.add_plug.

Usage:
    python src/tubes.py [--n 1 2] [--pitch 47.3] [--out stl/custom]
"""
import argparse, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts import Piece, POST_OD, POST_ID, cyl, add_plug, export
from project import load_cfg, out_dirs

def tube(n, pitch):
    """Tube n pitches tall: open bore, socket at the bottom, plug on top."""
    h  = n * pitch
    pc = Piece()
    pc.solid.append(cyl(h, POST_OD / 2))
    pc.cut.append(cyl(h + 0.02, POST_ID / 2, z=-0.01))
    add_plug(pc, 0, 0, h)
    return pc.build()

def main():
    cfg  = load_cfg()
    dirs = out_dirs(cfg)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n"    , type=int, nargs="+", default=[1, 2, 3, 4])    # pitches tall
    ap.add_argument("--pitch", type=float, default=cfg["tube_pitch"])       # [mm] body height per pitch
    ap.add_argument("--out"  , default=dirs["custom"])                     # printable STLs
    a = ap.parse_args()
    for n in a.n:
        k = f"tube_{n}_v2"
        t = export(tube(n, a.pitch), f"{a.out}/{k}.stl")
        print(k, "watertight", t.is_watertight, "bodies", len(t.split(only_watertight=False)),
              "extents", np.round(t.extents, 2))

if __name__ == "__main__":
    main()
