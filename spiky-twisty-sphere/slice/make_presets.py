## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Write the OrcaSlicer presets for the spiky twisty sphere in basic PLA: the stock
Sovol SV06 ACE presets from OrcaSlicer 2.5.0 (flattened by fetch_profiles.py) with
the changes below. The stock value of each setting is in its comment; "same" marks
a value that already matches stock and is written out so the preset says it.

Usage: python slice/make_presets.py [--stock slice/stock] [--out slice]
'''
import argparse
import json
import os

here = os.path.dirname(os.path.abspath(__file__))

## stock preset files written by fetch_profiles.py
stock_files = {
    'machine'  : 'flat_machine_Sovol_SV06_ACE_0.4_nozzle.json',
    'process'  : 'flat_process_0.20mm_Standard_atSovol_SV06_ACE.json',
    'filament' : 'flat_filament_Generic_PLA_atSovol_SV06_ACE.json',
}
preset_names = {
    'process'  : '0.20mm Spiky sphere @Sovol SV06 ACE',
    'filament' : 'Basic PLA @Sovol SV06 ACE',
}

## standing changes (sv06-ace-print-settings skill)
proc_std = {
    'top_solid_infill_flow_ratio' : '1',            # 0.8
    'sparse_infill_pattern'       : 'gyroid',       # crosshatch
    'top_shell_layers'            : '5',            # 3
    'top_shell_thickness'         : '1',            # [mm] 0.8
    'bottom_shell_layers'         : '4',            # 3
    'outer_wall_speed'            : '100',          # [mm/s] 200
    'inner_wall_speed'            : '180',          # [mm/s] 270
    'sparse_infill_speed'         : '200',          # [mm/s] 300
    'internal_solid_infill_speed' : '180',          # [mm/s] 200
    'top_surface_speed'           : '80',           # [mm/s] 200
    'default_acceleration'        : '5000',         # [mm/s2] 10000
    'outer_wall_acceleration'     : '3000',         # [mm/s2] 6000
    'inner_wall_acceleration'     : '5000',         # [mm/s2] 8000
    'top_surface_acceleration'    : '3000',         # [mm/s2] 6000
    'enable_prime_tower'          : '0',            # 1
}

## this model: walls and infill as in the designer's profile, plain surface patterns
proc_mdl = {
    'wall_loops'                  : '2',            # same
    'sparse_infill_density'       : '15%',          # 10%
    'top_surface_pattern'         : 'monotonicline',    # same
    'bottom_surface_pattern'      : 'monotonic',        # same
}

## supports carried over from the designer's 3mf (Metadata/project_settings.config,
## bambu studio 2.5.0.66). bambu's "tree_organic" style is "organic" in orca, and
## bambu's organic trees read tree_support_branch_angle, _distance and _diameter
## where orca reads the keys ending in _organic. the support blocker cube that
## keeps supports off everything above 22.7 mm rides along in the plate 3mf
## (plate.py). support speeds stay at the ace stock 80 mm/s.
## one value differs from the designer's: the first layer gap is 0.5 mm, not 0.2,
## see proc_gap below
proc_sup = {
    'enable_support'                       : '1',                       # 0
    'support_type'                         : 'tree(auto)',              # normal(auto)
    'support_style'                        : 'organic',                 # snug
    'support_threshold_angle'              : '30',                      # [deg] 20
    'support_on_build_plate_only'          : '0',                       # same
    'support_critical_regions_only'        : '1',                       # 0
    'support_remove_small_overhang'        : '1',                       # same
    'support_top_z_distance'               : '0.26',                    # [mm] 0.2
    'support_bottom_z_distance'            : '0.2',                     # [mm] same
    'support_interface_top_layers'         : '3',                       # 2
    'support_interface_bottom_layers'      : '2',                       # -1, same as top
    'support_interface_pattern'            : 'rectilinear_interlaced',  # auto
    'support_interface_spacing'            : '0.1',                     # [mm] 0.5
    'support_base_pattern'                 : 'default',                 # rectilinear
    'support_base_pattern_spacing'         : '2.5',                     # [mm] same
    'support_object_xy_distance'           : '0.35',                    # [mm] same
    'support_line_width'                   : '0.42',                    # [mm] 0.45
    'tree_support_branch_angle_organic'    : '45',                      # [deg] 40
    'tree_support_branch_distance_organic' : '5',                       # [mm] 1
    'tree_support_branch_diameter_organic' : '2',                       # [mm] same
    'tree_support_branch_diameter_angle'   : '5',                       # [deg] same
}

## first layer clearances, set so that nothing is printed in the gaps between the
## 15 segments (check.py on each trial slice):
## - stock brim (auto, 0 mm gap): brim lines run down every 0.5 mm gap and join
##   the segments on the first layer
## - the designer's brim (outer only, 5 mm, 0.2 mm gap): the radial gaps are clear,
##   but brim rings fill the hole on the axis and brim lines sit in slots under
##   1 mm wide between a segment and its neighbor's spike tips. the support pad
##   surrounds the base anyway, so the brim is off
## - the designer's 0.2 mm first layer support gap leaves support lines in the
##   same slots; 0.5 mm, the clearance the segments have from each other, clears them
proc_gap = {
    'brim_type'                      : 'no_brim',   # auto_brim
    'support_object_first_layer_gap' : '0.5',       # [mm] 0.2
}

## basic pla
fila_chg = {
    'nozzle_temperature_initial_layer' : ['220'],   # [C] 235
    'nozzle_temperature'               : ['210'],   # [C] same
    'filament_max_volumetric_speed'    : ['18'],    # [mm3/s] 21
    'fan_min_speed'                    : ['80'],    # [%] 50
    'fan_max_speed'                    : ['100'],   # [%] 80
}


def load_stock(stock, kind):
    '''
    Read one flattened stock preset.

    Args:
        stock   (str): folder holding the flattened stock presets
        kind    (str): 'machine', 'process' or 'filament'

    Returns:
        dict: the preset
    '''
    with open(os.path.join(stock, stock_files[kind])) as fid:
        return json.load(fid)


def make_presets(stock, out):
    '''
    Apply the changes to the stock presets and write machine.json, process.json,
    filament.json and changes_from_stock.json.

    Args:
        stock   (str): folder holding the flattened stock presets
        out     (str): folder the presets are written to

    Returns:
        dict: the changes, by preset kind
    '''
    proc_chg = {**proc_std, **proc_mdl, **proc_sup, **proc_gap}

    process = load_stock(stock, 'process')
    process.update(proc_chg)
    process['name']              = preset_names['process']
    process['print_settings_id'] = preset_names['process']
    process['from']              = 'User'

    filament = load_stock(stock, 'filament')
    filament.update(fila_chg)
    filament['name']                 = preset_names['filament']
    filament['filament_settings_id'] = [preset_names['filament']]
    filament['from']                 = 'User'

    machine = load_stock(stock, 'machine')
    machine['printer_settings_id'] = machine['name']

    os.makedirs(out, exist_ok=True)
    for name, preset in (('machine', machine), ('process', process), ('filament', filament)):
        with open(os.path.join(out, name + '.json'), 'w') as fid:
            json.dump(preset, fid, indent=1, sort_keys=True)

    changes = {'process': proc_chg, 'filament': fila_chg}
    with open(os.path.join(out, 'changes_from_stock.json'), 'w') as fid:
        json.dump(changes, fid, indent=1)
    return changes


def main():
    parser = argparse.ArgumentParser(description='write the sphere presets from the stock sv06 ace presets')
    parser.add_argument('--stock', default=os.path.join(here, 'stock'), help='flattened stock presets folder')
    parser.add_argument('--out',   default=here,                        help='folder the presets are written to')
    args = parser.parse_args()

    changes = make_presets(args.stock, args.out)
    nproc   = len(changes['process'])
    nfila   = len(changes['filament'])
    print(f'wrote presets to {args.out} ({nproc} process and {nfila} filament settings set)')


if __name__ == '__main__':
    main()
