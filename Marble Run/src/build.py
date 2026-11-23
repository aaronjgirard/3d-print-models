## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Build every generated piece into stl/custom (previews into preview).

Each piece script runs in its own process because stand.py and parts.py set
different global circle resolutions in manifold3d.

Usage:
    python src/build.py [stand] [bucket_v2] [pieces] [tubes] [refit] [cascade]
'''
import argparse
import os
import subprocess
import sys

here    = os.path.dirname(os.path.abspath(__file__))
scripts = ['stand', 'bucket_v2', 'pieces', 'tubes', 'refit', 'cascade']


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('which', nargs='*', default=scripts)
    a = ap.parse_args()
    bad = set(a.which) - set(scripts)
    if bad:
        ap.error(f'unknown script(s) {sorted(bad)}, choose from {scripts}')
    for s in a.which:
        print(f'== {s}')
        subprocess.run([sys.executable, os.path.join(here, s + '.py')], check=True)


if __name__ == '__main__':
    main()
