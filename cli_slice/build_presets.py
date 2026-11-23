'''
Build flat OrcaSlicer 2.5.0 printer, process and filament preset JSONs from the
settings stored in a project 3MF, then apply an overrides file.

The 2.5.0 CLI cannot resolve "inherits" against the packed system presets
(.opc), so every preset handed to --load-settings must be complete. The key to
preset ownership comes from Orca's Preset.cpp (keysets.json).

Usage:
    python3 build_presets.py project.3mf [--style tall_thin]
        [--overrides STYLE/overrides.json] [--outdir STYLE]
'''
import argparse
import json
import os
import zipfile

here = os.path.dirname(os.path.abspath(__file__))

## extruder keys live in the printer preset but are not in s_Preset_printer_options
ext_keys = ['deretraction_speed', 'extruder_colour', 'extruder_offset', 'max_layer_height',
            'min_layer_height', 'nozzle_diameter', 'nozzle_volume_type', 'retract_after_wipe',
            'retract_before_wipe', 'retract_length_toolchange', 'retract_lift_above',
            'retract_lift_below', 'retract_restart_extra', 'retract_restart_extra_toolchange',
            'retract_when_changing_layer', 'retraction_length', 'retraction_minimum_travel',
            'retraction_speed', 'wipe', 'wipe_distance', 'z_hop', 'default_filament_profile']
skip     = ('inherits', 'compatible_printers_condition')


def read_project(path):
    '''
    Read Metadata/project_settings.config from a 3MF.

    Args:
        path (str): project 3MF

    Returns:
        dict: full resolved config of the project
    '''
    with zipfile.ZipFile(path) as zf:
        return json.loads(zf.read('Metadata/project_settings.config'))


def split_config(cfg, keysets):
    '''
    Split a full config into machine, process and filament presets.

    Args:
        cfg     (dict): full config from read_project
        keysets (dict): key lists from keysets.json

    Returns:
        dict: {'machine': {...}, 'process': {...}, 'filament': {...}}
    '''
    own   = {'machine' : keysets['printer'] + keysets['machine_limits'] + ext_keys,
             'process' : keysets['print'],
             'filament': keysets['filament']}
    names = {'machine' : cfg['printer_settings_id'],
             'process' : cfg['print_settings_id'],
             'filament': cfg['filament_settings_id'][0]}
    out   = {}
    for typ, keys in own.items():
        pre = {k: cfg[k] for k in keys if k in cfg and k not in skip}
        pre.update({'type': typ, 'from': 'User', 'name': names[typ], 'inherits': ''})
        out[typ] = pre
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project')
    ap.add_argument('--style'    , default='tall_thin')
    ap.add_argument('--overrides', default=None)
    ap.add_argument('--keysets'  , default=os.path.join(here, 'keysets.json'))
    ap.add_argument('--outdir'   , default=None)
    args = ap.parse_args()
    args.outdir    = args.outdir    or os.path.join(here, args.style)
    args.overrides = args.overrides or os.path.join(here, args.style, 'overrides.json')

    keysets = json.load(open(args.keysets))
    pres    = split_config(read_project(args.project), keysets)
    os.makedirs(args.outdir, exist_ok=True)
    if os.path.exists(args.overrides):
        for typ, vals in json.load(open(args.overrides)).items():
            pres[typ].update(vals)

    fnames = {'machine': 'printer.json', 'process': 'process.json', 'filament': 'filament.json'}
    for typ, pre in pres.items():
        out = os.path.join(args.outdir, fnames[typ])
        with open(out, 'w') as fh:
            json.dump(pre, fh, indent=4)
        print(f'{out}: {len(pre)} keys')


if __name__ == '__main__':
    main()
