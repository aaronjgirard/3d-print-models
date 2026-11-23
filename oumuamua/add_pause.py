## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Insert a pause (for a filament swap) at the start of one layer of an
OrcaSlicer G-code sliced with the cli_slice presets, right after the layer
change lines that set CURRENT_LAYER. Rerunning on the same file does nothing.

Usage:
    python3 -I add_pause.py file.gcode --layer 13 [--cmd PAUSE]
'''
import argparse

tag = '; add_pause.py'

def add_pause(path, layer, cmd):
    '''
    Insert the pause command at the start of a layer, in place.

    Args:
        path  (str): G-code file
        layer (int): 1-based layer number (as in SET_PRINT_STATS_INFO CURRENT_LAYER)
        cmd   (str): G-code command(s) to insert, lines split by ';;'

    Returns:
        int: line number of the insertion (0 when already present)
    '''
    with open(path) as fh:
        lin = fh.readlines()
    if any(l.startswith(tag) for l in lin):
        return 0
    key = f'SET_PRINT_STATS_INFO CURRENT_LAYER={layer}'
    idx = next((i for i, l in enumerate(lin) if l.strip() == key), None)
    if idx is None:
        raise ValueError(f'no "{key}" line in {path}')
    zln = next((l for l in reversed(lin[:idx]) if l.startswith(';Z:')), ';Z:?')
    new = [f'{tag}: layer {layer}, {zln.strip()[1:]}\n', 'M117 Change filament\n']
    new += [c.strip() + '\n' for c in cmd.split(';;')]
    lin[idx + 1:idx + 1] = new
    with open(path, 'w') as fh:
        fh.writelines(lin)
    return idx + 2

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('gcode')
    ap.add_argument('--layer', type=int, required=True)
    ap.add_argument('--cmd', default='PAUSE')
    a = ap.parse_args()
    n = add_pause(a.gcode, a.layer, a.cmd)
    print(f'pause inserted at line {n}' if n else 'pause already present, file unchanged')
