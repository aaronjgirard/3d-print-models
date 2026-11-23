## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Build flat OrcaSlicer 2.5.0 printer, process and filament preset JSONs from the
config block Orca writes at the end of every G-code, then apply an overrides
file. Use it to re-slice a new model with exactly the settings of a print that
came out well.

Key ownership and value types (list or scalar) come from a set of flat template
presets (default: tall_thin). Keys missing from the G-code keep the template
value and are reported. Output goes to the style subfolder, and that folder's
overrides.json is applied.

Usage:
    python presets_from_gcode.py good_print.gcode [--style relief]
        [--overrides STYLE/overrides.json] [--templates tall_thin] [--outdir STYLE]
'''
import argparse
import json
import os

here   = os.path.dirname(os.path.abspath(__file__))
fnames = {'machine': 'printer.json', 'process': 'process.json', 'filament': 'filament.json'}
meta   = ('type', 'from', 'name', 'inherits')
ids    = {'machine': 'printer_settings_id', 'process': 'print_settings_id', 'filament': 'filament_settings_id'}


def read_config_block(path):
    '''
    Read the key = value pairs between CONFIG_BLOCK_START and CONFIG_BLOCK_END.

    Args:
        path (str): G-code from OrcaSlicer

    Returns:
        dict: raw string values keyed by setting name
    '''
    cfg, inside = {}, False
    with open(path, errors='replace') as fh:
        for line in fh:
            if line.startswith('; CONFIG_BLOCK_START'):
                inside = True
            elif line.startswith('; CONFIG_BLOCK_END'):
                break
            elif inside and ' = ' in line:
                key, val = line[2:].rstrip('\n').split(' = ', 1)
                cfg[key]  = val
    if not cfg:
        raise ValueError(f'no config block in {path}')
    return cfg


def unescape(s):
    '''
    Undo Orca's c-style escaping (\\n, \\r, \\t, \\\\, \\").

    Args:
        s (str): escaped string

    Returns:
        str: plain string
    '''
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 'r': '\r', 't': '\t'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def split_quoted(s):
    '''
    Split a ;-separated list of c-style quoted strings.

    Args:
        s (str): e.g. "a";"b"

    Returns:
        list: unescaped strings
    '''
    out, cur, quoted, i = [], [], False, 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            cur.append(s[i:i + 2])
            i += 2
            continue
        if c == '"':
            quoted = not quoted
        elif c == ';' and not quoted:
            out.append(unescape(''.join(cur)))
            cur = []
        else:
            cur.append(c)
        i += 1
    out.append(unescape(''.join(cur)))
    return out


def convert(val, tmpl):
    '''
    Convert a raw config-block value to the type of the template value.

    Args:
        val  (str)       : raw value from the G-code
        tmpl (str | list): template value

    Returns:
        str | list: typed value
    '''
    if not isinstance(tmpl, list):
        return unescape(val)
    if val == '':
        return []
    if val.startswith('"') or ';' in val:
        return split_quoted(val)
    return val.split(',')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('gcode')
    ap.add_argument('--style'    , default='relief')
    ap.add_argument('--overrides', default=None)
    ap.add_argument('--templates', default=os.path.join(here, 'tall_thin'))
    ap.add_argument('--outdir'   , default=None)
    args = ap.parse_args()
    args.outdir    = args.outdir    or os.path.join(here, args.style)
    args.overrides = args.overrides or os.path.join(here, args.style, 'overrides.json')

    cfg  = read_config_block(args.gcode)
    over = json.load(open(args.overrides)) if os.path.exists(args.overrides) else {}
    os.makedirs(args.outdir, exist_ok=True)
    for typ, fname in fnames.items():
        tmpl    = json.load(open(os.path.join(args.templates, fname)))
        pre     = {k: convert(cfg[k], v) if k in cfg else v for k, v in tmpl.items() if k not in meta}
        missing = [k for k in tmpl if k not in meta and k not in cfg]
        name    = convert(cfg[ids[typ]], [''])[0]
        pre.update({'type': typ, 'from': 'User', 'name': name, 'inherits': ''})
        pre.update(over.get(typ, {}))
        out     = os.path.join(args.outdir, fname)
        with open(out, 'w') as fh:
            json.dump(pre, fh, indent=4)
        print(f'{out}: {len(pre)} keys, "{name}", kept template value for {missing or "none"}')


if __name__ == '__main__':
    main()
