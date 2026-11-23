'''
Build the secret drawers OrcaSlicer project: accent floor liners plus a multi-plate 3MF.

Usage:
    python -I build_project.py --src extracted --out secret_drawers.3mf --liner_dir liners

Needs trimesh, shapely, numpy and mapbox_earcut (conda env marble-run).
'''
import argparse
import json
import os
import zipfile
from xml.sax.saxutils import quoteattr

import numpy as np
import trimesh
from shapely.geometry import Polygon

par = {
    'floor_z'     :    3.0,     # [mm] drawer floor top, section is cut a little above it
    'cut_dz'      :    0.8,     # [mm] height of the section plane above the floor
    'liner_gap'   :    0.4,     # [mm] clearance per side between liner and drawer walls
    'liner_mass'  :   30.0,     # [g] target mass of each liner
    'rho'         :    1.24,    # [g/cm3] pla
    'first_layer' :    0.25,    # [mm] first layer height of the sv06 ace presets
    'layer'       :    0.20,    # [mm] layer height
    'bed'         :  220.0,     # [mm] square bed edge
    'plate_gap'   :    0.2,     # orca logical plate spacing, fraction of bed edge
}

## changes to the base project settings (readme: 3 perimeters, 20 % infill, 0.2 mm layers, brim on the tubes)
proj_over = {'wall_loops': '3', 'sparse_infill_density': '20%', 'layer_height': '0.2', 'brim_type': 'outer_only',
             'brim_width': '4', 'skirt_loops': '0'}

## name, stl, plate (1-based), x0, y0 on the plate [mm]; tubes sit away from x 95-125 (x bar dent)
plates = {
    1: ('base: drawer A + lower tube',  [('lower_tube', 10.0,  35.0), ('drawer_a', 75.0,  38.25)]),
    2: ('base: drawer B + upper tube',  [('upper_tube', 10.0,  35.0), ('drawer_b', 75.0,  41.25)]),
    3: ('accent: dial + cap + pin',     [('dial',       15.0,  15.0), ('cap',     170.0,  30.0),
                                         ('lock_pin',  170.0,  60.0)]),
    4: ('accent: liner A',              [('liner_a',    None,  None)]),
    5: ('accent: liner B',              [('liner_b',    None,  None)]),
}


def liner_poly(mesh, par):
    '''largest interior ring of the drawer section just above the floor, shrunk by the clearance.'''
    sec  = mesh.section(plane_origin=[0, 0, par['floor_z'] + par['cut_dz']], plane_normal=[0, 0, 1])
    rngs = [Polygon(p[:, :2]) for p in sec.discrete]
    rngs = sorted(rngs, key=lambda q: q.area)
    ## the cavity is the largest ring that sits inside the outer wall ring
    cav  = rngs[-2]
    shr  = cav.buffer(-par['liner_gap'])
    ## drop slivers pinched off between the pin boss and the wall
    return max(shr.geoms, key=lambda q: q.area) if shr.geom_type == 'MultiPolygon' else shr


def liner_mesh(mesh, par):
    poly  = liner_poly(mesh, par)
    area  = poly.area / 100.0                                    # [cm2]
    tmass = par['liner_mass'] / (par['rho'] * area) * 10.0       # [mm] thickness for the target mass
    nlay  = max(int(round((tmass - par['first_layer']) / par['layer'])), 1)
    thick = par['first_layer'] + nlay * par['layer']             # [mm] snapped to whole layers
    liner = trimesh.creation.extrude_polygon(poly, thick)
    liner.apply_translation(-liner.bounds[0])
    mass  = thick * area / 10.0 * par['rho']
    return liner, thick, mass


def plate_origin(idx, nplate, par):
    '''orca plate origin for 0-based plate idx (column count rule from PartPlateList).'''
    val  = np.sqrt(nplate)
    cols = int(round(val)) + (1 if val > round(val) else 0)
    step = par['bed'] * (1.0 + par['plate_gap'])
    return (idx % cols) * step, -(idx // cols) * step


def write_3mf(path, objs, nplate, par, proj=None):
    """objs: list of (name, plate, mesh, x0, y0). orca layout: wrapper object with one component per mesh file."""
    ns   = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
            'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
            'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')
    head = '<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" %s>' % ns
    files, res, items, cfg, rels, pl = {}, [], [], [], [], {}
    for i, (name, plate, mesh, x0, y0) in enumerate(objs, start=1):
        mid, wid = 2 * i - 1, 2 * i
        ox, oy   = plate_origin(plate - 1, nplate, par)
        ## orca keeps each object about its bbox centre, so centre the mesh and move the item instead
        ext    = mesh.extents
        verts  = mesh.vertices - mesh.bounds[0] - ext / 2.0
        x0, y0 = x0 + ext[0] / 2.0, y0 + ext[1] / 2.0
        vts    = ''.join('<vertex x="%.6f" y="%.6f" z="%.6f"/>' % tuple(v) for v in verts)
        tri    = ''.join('<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(f) for f in mesh.faces)
        fpath  = '/3D/Objects/%s.stl_%d.model' % (name, wid)
        files[fpath[1:]] = (head + '<metadata name="BambuStudio:3mfVersion">1</metadata><resources>'
                            '<object id="%d" p:UUID="%08x-81cb-4c03-9d28-80fed5dfa1dc" type="model"><mesh><vertices>%s</vertices>'
                            '<triangles>%s</triangles></mesh></object></resources><build/></model>' % (mid, mid, vts, tri))
        rels.append('<Relationship Target="%s" Id="rel-%d" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
                    % (fpath, i + 1))
        res.append('<object id="%d" p:UUID="%08x-61cb-4c03-9d28-80fed5dfa1dc" type="model"><components>'
                   '<component p:path="%s" objectid="%d" p:UUID="%08x-b206-40ff-9872-83e8017abed1" '
                   'transform="1 0 0 0 1 0 0 0 1 0 0 0"/></components></object>' % (wid, wid, fpath, mid, mid))
        items.append('<item objectid="%d" p:UUID="%08x-b1ec-4553-aec9-835e5b724bb4" '
                     'transform="1 0 0 0 1 0 0 0 1 %.6f %.6f %.6f" printable="1"/>'
                     % (wid, wid, ox + x0, oy + y0, ext[2] / 2.0))
        cfg.append('<object id="%d" auto_drop="1"><metadata key="name" value=%s/><metadata key="extruder" value="1"/>'
                   '<part id="%d" subtype="normal_part"><metadata key="name" value=%s/>'
                   '<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>'
                   '<metadata key="source_file" value=%s/><metadata key="source_object_id" value="0"/>'
                   '<metadata key="source_volume_id" value="0"/><metadata key="source_offset_x" value="%.6f"/>'
                   '<metadata key="source_offset_y" value="%.6f"/><metadata key="source_offset_z" value="%.6f"/>'
                   '</part></object>'
                   % (wid, quoteattr(name), mid, quoteattr(name), quoteattr(name + '.stl'),
                      ext[0] / 2.0, ext[1] / 2.0, ext[2] / 2.0))
        pl.setdefault(plate, []).append(wid)
    pcfg = ''
    for p in sorted(pl):
        inst = ''.join('<model_instance><metadata key="object_id" value="%d"/><metadata key="instance_id" value="0"/>'
                       '<metadata key="identify_id" value="%d"/></model_instance>' % (w, 100 + w) for w in pl[p])
        pcfg += ('<plate><metadata key="plater_id" value="%d"/><metadata key="plater_name" value=%s/>'
                 '<metadata key="locked" value="false"/><metadata key="filament_map_mode" value="Auto For Flush"/>'
                 '<metadata key="filament_maps" value="1"/><metadata key="filament_volume_maps" value="0"/>%s</plate>'
                 % (p, quoteattr(plates[p][0]), inst))
    model = (head + '<metadata name="Application">BambuStudio-02.08.01.55</metadata>'
             '<metadata name="BambuStudio:3mfVersion">1</metadata><metadata name="OrcaSlicer">2.5.0</metadata>'
             '<resources>%s</resources><build>%s</build></model>' % (''.join(res), ''.join(items)))
    mset  = '<?xml version="1.0" encoding="UTF-8"?>\n<config>%s%s</config>' % (''.join(cfg), pcfg)
    ctype = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
             '<Default Extension="config" ContentType="text/xml"/></Types>')
    rel0  = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
             '</Relationships>')
    rel1  = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '%s</Relationships>' % ''.join(rels))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ctype)
        z.writestr('_rels/.rels', rel0)
        z.writestr('3D/3dmodel.model', model)
        z.writestr('3D/_rels/3dmodel.model.rels', rel1)
        for fn, txt in files.items():
            z.writestr(fn, txt)
        z.writestr('Metadata/model_settings.config', mset)
        if proj is not None:
            z.writestr('Metadata/project_settings.config', json.dumps(proj, indent=4))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--src',       default='extracted')
    ap.add_argument('--out',       default='secret_drawers.3mf')
    ap.add_argument('--liner_dir', default='liners')
    ap.add_argument('--base',      default='project_settings_base.json')
    a = ap.parse_args()

    os.makedirs(a.liner_dir, exist_ok=True)
    meshes = {}
    for key, src in (('liner_a', 'drawer_a'), ('liner_b', 'drawer_b')):
        liner, thick, mass = liner_mesh(trimesh.load(os.path.join(a.src, src + '.stl')), par)
        liner.export(os.path.join(a.liner_dir, key + '.stl'))
        meshes[key] = liner
        ext = liner.extents
        print('%s: %.1f x %.1f x %.2f mm, %.1f g solid' % (key, ext[0], ext[1], thick, mass))

    objs = []
    for p, (pname, parts) in plates.items():
        for name, x0, y0 in parts:
            mesh = meshes.get(name)
            if mesh is None:
                mesh = trimesh.load(os.path.join(a.src, name + '.stl'))
            if x0 is None:
                x0 = (par['bed'] - mesh.extents[0]) / 2.0
                y0 = (par['bed'] - mesh.extents[1]) / 2.0
            objs.append((name, p, mesh, x0, y0))
    proj = json.load(open(a.base))
    proj.update(proj_over)
    write_3mf(a.out, objs, len(plates), par, proj)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
