## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Put the designer's 3MF on the SV06 ACE bed and slice it with the OrcaSlicer 2.5.0
command line and the presets from make_presets.py.

The plate 3MF is the designer's file with three changes: the object is moved from
the center of a 256 mm Bambu bed to the center of the 220 mm bed, the filament
paint (every face painted "filament 3") is removed so the print uses one filament,
and the Bambu project settings and pictures are left out so that every setting
comes from the presets. The mesh, its size and the designer's support blocker
are untouched.

OrcaSlicer 2.5.0 treats a 3MF without printer settings as laid out on a 200 mm
bed and moves its objects by the difference to the real bed center. The object
is therefore written at --ref-cen (100, 100), and the slice is refused unless it
lands on --bed-cen.

Writes <out>/<name>.gcode and <out>/<name>.3mf (the Orca project, which carries
the sliced plate). Nothing is sent to the printer.

Usage: python slice/plate.py [--src model.3mf] [--orca path] [--out out]
'''
import argparse
import os
import re
import shutil
import subprocess
import zipfile

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)

## parts of the designer's 3mf that go into the plate 3mf
keep_parts = (
    '[Content_Types].xml',
    '3D/3dmodel.model',
    '3D/_rels/3dmodel.model.rels',
    '3D/Objects/object_1.model',
    'Metadata/model_settings.config',
)
rels_text = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
'''
report_keys = (
    '; estimated printing time (normal mode)',
    '; total filament used [g]',
    '; total layers count',
)


def move_to_bed(model, cen):
    '''
    Move the build item of a 3MF model file to the bed center, keeping its height.

    Args:
        model   (str): text of 3D/3dmodel.model
        cen     (tuple): where the object center goes (x, y) [mm]

    Returns:
        str: the model text with the build item moved
    '''
    item = re.search(r'<item [^>]*transform="([^"]+)"', model)
    vals = item.group(1).split()
    assert len(vals) == 12, 'build item transform should have 12 numbers'
    vals[9]  = f'{cen[0]:g}'
    vals[10] = f'{cen[1]:g}'
    return model[:item.start(1)] + ' '.join(vals) + model[item.end(1):]


def build_plate(src, dst, cen):
    '''
    Write the plate 3MF from the designer's 3MF.

    Args:
        src     (str): the designer's 3MF
        dst     (str): the plate 3MF to write
        cen     (tuple): where the object center goes (x, y) [mm]

    Returns:
        int: number of painted faces that were cleared
    '''
    npaint = 0
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        for part in keep_parts:
            data = zin.read(part).decode('utf-8')
            if part == '3D/3dmodel.model':
                data = move_to_bed(data, cen)
            if part == '3D/Objects/object_1.model':
                data, npaint = re.subn(r' paint_color="[^"]*"', '', data)
            if part == 'Metadata/model_settings.config':
                data = re.sub(r'\s*<metadata key="(thumbnail_file|thumbnail_no_light_file|top_file|pick_file)"[^>]*/>', '', data)
            zout.writestr(part, data)
        zout.writestr('_rels/.rels', rels_text)
    return npaint


def slice_plate(orca, plate, presets, out, name, bed_type):
    '''
    Slice the plate 3MF and export the Orca project next to the G-code.

    Args:
        orca        (str): OrcaSlicer binary
        plate       (str): the plate 3MF
        presets     (str): folder with machine.json, process.json and filament.json
        out         (str): output folder
        name        (str): base name of the G-code and project files
        bed_type    (str): Orca bed type

    Returns:
        str: path of the G-code
    '''
    work = os.path.join(out, 'orca_work')
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)
    cmd = [orca, '--slice', '0', '--debug', '2', '--outputdir', work,
           '--load-settings', f'{presets}/machine.json;{presets}/process.json',
           '--load-filaments', f'{presets}/filament.json',
           '--curr-bed-type', bed_type, '--arrange', '0',
           '--export-3mf', name + '.3mf', plate]
    run = subprocess.run(cmd, capture_output=True, text=True, cwd=work)
    if run.stdout or run.stderr:
        print((run.stdout + run.stderr)[-3000:])
    assert run.returncode == 0, 'orcaslicer failed'

    gcode = os.path.join(out, name + '.gcode')
    shutil.move(os.path.join(work, 'plate_1.gcode'), gcode)
    shutil.move(os.path.join(work, name + '.3mf'), os.path.join(out, name + '.3mf'))
    shutil.rmtree(work)
    return gcode


def report(gcode, cen):
    '''
    Print the time, filament and layer count Orca wrote into the G-code and
    confirm the object sits on the bed center.

    Args:
        gcode   (str): path of the G-code
        cen     (tuple): bed center (x, y) [mm]
    '''
    with open(gcode) as fid:
        lines = fid.read().splitlines()
    for key in report_keys:
        print(next(line for line in lines if line.startswith(key)))
    define = next(line for line in lines if line.startswith('EXCLUDE_OBJECT_DEFINE'))
    found  = re.search(r'CENTER=(-?[\d.]+),(-?[\d.]+)', define)
    xcen   = float(found.group(1))
    ycen   = float(found.group(2))
    print(f'object center = {xcen:g}, {ycen:g}')
    assert abs(xcen - cen[0]) < 0.05 and abs(ycen - cen[1]) < 0.05, 'the object is not on the bed center'


def main():
    parser = argparse.ArgumentParser(description='put the sphere on the sv06 ace bed and slice it')
    parser.add_argument('--src',      default=os.path.join(root, 'spiky_twisty_sphere_makerworld.3mf'), help="the designer's 3mf")
    parser.add_argument('--orca',     default='/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer', help='orcaslicer binary')
    parser.add_argument('--presets',  default=here,                                                     help='folder with the preset json files')
    parser.add_argument('--out',      default=os.path.join(root, 'out'),                                help='output folder')
    parser.add_argument('--name',     default='spiky_twisty_sphere',                                    help='base name of the outputs')
    parser.add_argument('--bed-type', default='High Temp Plate',                                        help='orca bed type')
    parser.add_argument('--bed-cen',  default=(110.0, 110.0), type=float, nargs=2,                      help='[mm] bed center x y')
    parser.add_argument('--ref-cen',  default=(100.0, 100.0), type=float, nargs=2,                      help='[mm] bed center orca assumes for a 3mf without printer settings')
    parser.add_argument('--plate-only', action='store_true',                                            help='write the plate 3mf and stop')
    args = parser.parse_args()

    plate  = os.path.join(here, 'plate', args.name + '_plate.3mf')
    npaint = build_plate(args.src, plate, args.ref_cen)
    print(f'wrote {plate} (filament paint cleared on {npaint} faces)')
    if args.plate_only:
        return

    os.makedirs(args.out, exist_ok=True)
    gcode = slice_plate(args.orca, plate, args.presets, args.out, args.name, args.bed_type)
    print('wrote', gcode)
    report(gcode, args.bed_cen)


if __name__ == '__main__':
    main()
