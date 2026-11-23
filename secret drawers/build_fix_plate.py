'''
Build a one-part reprint 3MF (default: the lower tube) with a support enforcer under the lock pin slot.

The pin slot through the lower tube ceiling is a 112 mm horizontal span when the tube stands on its back
wall; without support Orca lays a 105 mm overhang wall in mid air at z 16.6 and it sags into the slot.
The enforcer box covers only the slot roof, and support_type normal(manual) keeps support everywhere else off.

Usage:
    python -I build_fix_plate.py --out secret_drawers_fixbadprinton1.3mf

Needs trimesh and numpy (conda env marble-run).
'''
import argparse
import json
import os
import zipfile

import numpy as np
import trimesh

import build_project
from build_project import par, proj_over, write_3mf

## support only where an enforcer says so
fix_over = {'enable_support': '1', 'support_type': 'normal(manual)'}


def enforcer_xml(head, oid, box):
    '''3MF mesh object for an axis-aligned box given as [[x0, y0, z0], [x1, y1, z1]].'''
    mesh = trimesh.creation.box(bounds=np.asarray(box))
    vts  = ''.join('<vertex x="%.6f" y="%.6f" z="%.6f"/>' % tuple(v) for v in mesh.vertices)
    tri  = ''.join('<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(f) for f in mesh.faces)
    return (head + '<metadata name="BambuStudio:3mfVersion">1</metadata><resources>'
            '<object id="%d" p:UUID="%08x-81cb-4c03-9d28-80fed5dfa1dc" type="model"><mesh><vertices>%s</vertices>'
            '<triangles>%s</triangles></mesh></object></resources><build/></model>' % (oid, oid, vts, tri))


def add_enforcer(path, box):
    '''add a support enforcer part to object 2 (the only object) of a 3MF written by write_3mf.'''
    oid, fn = 3, '3D/Objects/support_enforcer_3.model'
    with zipfile.ZipFile(path) as z:
        files = {n: z.read(n).decode() for n in z.namelist()}
    head = files['3D/3dmodel.model'].split('<metadata', 1)[0]
    files[fn] = enforcer_xml(head, oid, box)
    comp = ('<component p:path="/%s" objectid="%d" p:UUID="%08x-b206-40ff-9872-83e8017abed1" '
            'transform="1 0 0 0 1 0 0 0 1 0 0 0"/></components>' % (fn, oid, oid))
    files['3D/3dmodel.model'] = files['3D/3dmodel.model'].replace('</components>', comp, 1)
    rel  = ('<Relationship Target="/%s" Id="rel-%d" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>' % (fn, oid + 10))
    files['3D/_rels/3dmodel.model.rels'] = files['3D/_rels/3dmodel.model.rels'].replace('</Relationships>', rel)
    part = ('<part id="%d" subtype="support_enforcer"><metadata key="name" value="slot_roof_enforcer"/>'
            '<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/></part></object>' % oid)
    files['Metadata/model_settings.config'] = files['Metadata/model_settings.config'].replace('</object>', part, 1)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, txt in files.items():
            z.writestr(n, txt)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--src',   default='extracted')
    ap.add_argument('--part',  default='lower_tube')
    ap.add_argument('--out',   default='secret_drawers_fixbadprinton1.3mf')
    ap.add_argument('--base',  default='project_settings_base.json')
    ap.add_argument('--name',  default='fixbadprinton1: lower tube')
    ## [mm] slot roof box in the stl frame: wall x 0-4, slot y 12.7-125.3, flat top 16.3, gable peak 18.3
    ap.add_argument('--box',   default='-0.5,12.0,14.5,4.5,126.0,18.6')
    a = ap.parse_args()

    mesh   = trimesh.load(os.path.join(a.src, a.part + '.stl'))
    ext    = mesh.extents
    x0, y0 = (par['bed'] - ext[0]) / 2.0, (par['bed'] - ext[1]) / 2.0
    proj   = json.load(open(a.base))
    proj.update(proj_over)
    proj.update(fix_over)
    ## orca only applies process keys listed as changed from the system preset
    diff    = proj['different_settings_to_system']
    diff[0] = ';'.join(sorted(set(diff[0].split(';')) | set(fix_over)))

    build_project.plates = {1: (a.name, [(a.part, x0, y0)])}
    write_3mf(a.out, [(a.part, 1, mesh, x0, y0)], 1, par, proj)

    ## enforcer in the object frame, which write_3mf centres on the part's bounding box
    box = np.array([float(v) for v in a.box.split(',')]).reshape(2, 3) - mesh.bounds[0] - ext / 2.0
    add_enforcer(a.out, box)
    print('wrote %s: %s at x %.1f y %.1f, enforcer %s' % (a.out, a.part, x0, y0, a.box))


if __name__ == '__main__':
    main()
