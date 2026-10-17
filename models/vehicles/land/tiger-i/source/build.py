#!/usr/bin/env python3
"""Reproducible Tiger I early-1943 grey-model builder (Issue #5).

Cloud-only: Python 3.12 + numpy + trimesh. No Blender, no display/GPU.
python models/vehicles/land/tiger-i/source/build.py

All authored geometry uses metres and the #3 geometry.json contract:
+X forward, +Y up, +Z tank right; origin: hull midpoint on ground.
Hulls/track/wheel silhouettes are approximate, *not* measured armour CAD.
"""
from __future__ import annotations

import json
from pathlib import Path
import math
import sys

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[5]
ASSET = ROOT / "models" / "vehicles" / "land" / "tiger-i"
SPEC = json.loads((ASSET / "references" / "geometry.json").read_text("utf-8"))
OUT = ASSET / "export" / "tiger-i-grey.glb"
WEB = ROOT / "docs" / "assets" / "tiger-i-grey.glb"
REPORT = ASSET / "export" / "mesh-report.json"


def mesh(vertices, faces, name, rgb):
    obj = trimesh.Trimesh(vertices=np.array(vertices, dtype=float),
                          faces=np.array(faces, dtype=np.int64), process=False)
    if not np.isfinite(obj.vertices).all() or len(obj.faces) == 0:
        raise ValueError("mesh missing or non-finite: " + name)
    obj.visual.vertex_colors = np.tile(np.array([*rgb,255],dtype=np.uint8),(len(obj.vertices),1))
    return obj


def box(extents, center, name, rgb):
    result = trimesh.creation.box(extents=extents)
    result.apply_translation(center)
    result.visual.vertex_colors = np.tile(np.array([*rgb,255],dtype=np.uint8),(len(result.vertices),1))
    return result


def xz_prism(contour, bottom, top, name, rgb, inset_top=0.0):
    """Flat shaded polyhedral turret deck or armour plate from 2D x,z points."""
    n = len(contour)
    centre = np.mean(np.array(contour, dtype=float), axis=0)
    low = [[x,bottom,z] for x,z in contour]
    high = [[centre[0]+(x-centre[0])*(1-inset_top),top,
             centre[1]+(z-centre[1])*(1-inset_top)] for x,z in contour]
    vertices=low+high
    faces=[]
    # Bottom reversed, top forwards, sides quads. Individual triangles, no fake detail.
    # XZ polygon has +Y pointing opposite the 2D winding;
    # top must face UP, bottom DOWN, side panels must face OUT.
    for i in range(1,n-1):
        faces.append((0,i,i+1))
        faces.append((n,n+i+1,n+i))
    for i in range(n):
        j=(i+1)%n
        faces.extend(((i,n+j,j),(i,n+i,n+j)))
    result=mesh(vertices,faces,name,rgb)
    assert result.face_normals[1][1]>.95, "turret roof normals must point +Y"
    return result


def xy_prism(contour, zlow, zhigh, name, rgb):
    """Extrude silhouette along width Z; +X is forward."""
    n=len(contour)
    vertices=[[x,y,zlow] for x,y in contour]+[[x,y,zhigh] for x,y in contour]
    faces=[]
    for i in range(1,n-1):
        # CCW in XY: low-Z cap faces -Z, high-Z cap faces +Z.
        faces.extend(((0,i+1,i),(n,n+i,n+i+1)))
    for i in range(n):
        j=(i+1)%n
        faces.extend(((i,j,n+j),(i,n+j,n+i)))
    return mesh(vertices,faces,name,rgb)


def track(side):
    """Annular low-poly single-piece continuous track silhouette (not animated links)."""
    x0=2.395
    cy=.685
    def loop(r):
        # Top of front roller, down its nose, across bottom, around rear.
        front=[(x0+r*math.cos(a),cy+r*math.sin(a))
               for a in np.linspace(math.pi/2,-math.pi/2,7)]
        rear=[(-x0+r*math.cos(a),cy+r*math.sin(a))
              for a in np.linspace(-math.pi/2,-3*math.pi/2,7)]
        return front+rear
    outer,inner=loop(.685),loop(.480)
    n=len(outer)
    z0,z1=sorted(((side*1.411)-.3625,(side*1.411)+.3625))
    vertices=[]
    for profile in (outer,inner):
        for z in (z0,z1):
            vertices.extend([[x,y,z] for x,y in profile])
    faces=[]
    # 4 contiguous bands around a hollow belt: outer, right face, inner, left face.
    for i in range(n):
        j=(i+1)%n
        for a,b in ((0,n),(n,3*n),(3*n,2*n),(2*n,0)):
            faces.extend(((a+i,a+j,b+j),(a+i,b+j,b+i)))
    return mesh(vertices,faces,"Track", (64,69,64))


def cylinder_z(radius,width,centre,sections,name,rgb):
    m=trimesh.creation.cylinder(radius=radius,height=width,sections=sections)
    m.apply_translation(centre)
    m.visual.vertex_colors=np.tile(np.array([*rgb,255],dtype=np.uint8),(len(m.vertices),1))
    return m


def tube_x(profiles,sections=12):
    """Low-poly tapered gun tube in local Barrel frame (X is bore / recoil)."""
    verts=[]
    for x,r in profiles:
        for k in range(sections):
            t=2*math.pi*k/sections
            verts.append([x,r*math.sin(t),r*math.cos(t)])
    faces=[]
    for q in range(len(profiles)-1):
        for k in range(sections):
            i=q*sections+k
            j=q*sections+(k+1)%sections
            faces.extend(((i,j,j+sections),(i,j+sections,i+sections)))
    for k in range(1,sections-1):
        faces.extend(((0,k+1,k),((len(profiles)-1)*sections,
                                  (len(profiles)-1)*sections+k,
                                  (len(profiles)-1)*sections+k+1)))
    return mesh(verts,faces,"BarrelTube",(153,158,148))


def translate(x,y,z):
    t=np.eye(4)
    t[:3,3]=[x,y,z]
    return t


def build_scene():
    grey=(165,171,160)
    plate=(153,160,149)
    metal=(117,126,119)
    scene=trimesh.Scene(base_frame="World")
    parts=[]
    # Hull and leaf node: named rigid hierarchy, not baked transforms.
    scene.graph.update(frame_to="Hull",frame_from="World",matrix=np.eye(4))
    def attach(g, node, parent, transform=None):
        scene.add_geometry(g,geom_name=node,node_name=node,parent_node_name=parent,
                           transform=np.eye(4) if transform is None else transform)
        parts.append(node)

    # Lower tub, stepped high rear engine and flatter forward driver's roof.
    outline=[(-3.158,.75),(2.76,.75),(3.158,1.07),(3.158,1.96),
             (2.70,2.13),(-2.82,2.13),(-3.158,1.89)]
    attach(xy_prism(outline,-1.265,1.265,"HullArmour",grey),"HullArmour","Hull")
    attach(box([4.3,.09,2.61],[-.72,2.15,0],"HullDeck",plate),"HullDeck","Hull")
    attach(box([1.57,.10,2.58],[2.22,2.19,0],"Foredeck",grey),"Foredeck","Hull")
    attach(box([1.90,.07,2.62],[-2.19,2.21,0],"EngineDeck",metal),"EngineDeck","Hull")
    for side in (-1,1):
        attach(box([5.72,.09,.35],[0,1.46,side*1.48],"SideSkirt",plate),f"SideSkirt_{side}","Hull")
        attach(track(side),f"Track_{side}","Hull")
        # Main wheel stations only. The three deep overlapping rows from the
        # real Tiger are excluded at this budget; do not claim 24 physical wheels.
        for i,x in enumerate(SPEC["suspension"]["road_wheel_x"]):
            attach(cylinder_z(.36,.13,[x,SPEC['suspension']['wheel_axis_y'],side*1.43],10,"RoadWheel",metal),
                   f"RoadWheel_{side}_{i+1}","Hull")
        for name,x in (("Idler",-2.395),("Sprocket",2.395)):
            attach(cylinder_z(.43,.15,[x,.685,side*1.43],10,name,plate),
                   f"{name}_{side}","Hull")
        # Front tow lug simplified, leave sprocket teeth to future detail stage.
        attach(box([.34,.18,.13],[2.97,.91,side*1.01],"TowLug",metal),
               f"TowLug_{side}","Hull")

    # Turret pivot: nominal xyz from Issue #3, in hull-local metre coordinates.
    px,py,pz=(.315,2.18,0)
    scene.graph.update(frame_to="Turret",frame_from="Hull",matrix=translate(px,py,pz))
    turret_outline=[(-.93,-.27),(-.78,-.72),(-.34,-.96),(.60,-.99),
                    (1.23,-.79),(1.52,-.47),(1.60,0),
                    (1.52,.47),(1.23,.79),(.60,.99),(-.34,.96),(-.78,.72),(-.93,.27)]
    # Authored in world-hull xz then rebased to turret pivot:
    turret_local=[(x-px,z) for x,z in turret_outline]
    attach(xz_prism(turret_local,.01,.57,"TurretShell",grey,inset_top=.06),
           "TurretShell","Turret")
    # Rear stowage bin characteristic early tank silhouette.
    attach(box([.25,.36,1.27],[-1.00-px,.23,0],"TurretStowage",plate),
           "TurretStowage","Turret")
    # Cupola nominal position approximated, located left of bore.
    cup=SPEC["parts"]["cupola"]
    cupmesh=trimesh.creation.cylinder(radius=.24,height=.17,sections=10)
    # Default cylinder Z axis; rotate around X so cupola is truly vertical.
    cupmesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
    cupmesh.apply_translation([-.46-px,.735,-.54])
    cupmesh.visual.vertex_colors=np.tile(np.array([*metal,255],dtype=np.uint8),(len(cupmesh.vertices),1))
    attach(cupmesh,"Cupola","Turret")
    # Barrel pivot relative to Turret; positive X outward, negative X recoil.
    bx=1.65-px
    by=2.43-py
    scene.graph.update(frame_to="Barrel",frame_from="Turret",matrix=translate(bx,by,0))
    attach(tube_x([(0,.14),(.18,.15),(.34,.115),(3.29,.092),(3.49,.12),(3.642,.12)],12),
           "BarrelTube","Barrel")
    attach(box([.16,.28,.34],[3.56,0,0],"MuzzleBrake",plate),
           "MuzzleBrake","Barrel")
    # Mantlet belongs to turret but barrel and muzzle translate independently.
    attach(box([.23,.53,1.08],[1.50-px,.25,0],"Mantlet",metal),
           "Mantlet","Turret")
    return scene,parts


def main():
    scene,parts=build_scene()
    # Real glTF2 GLB generated from named scene graph.
    binary=trimesh.exchange.gltf.export_glb(scene)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    WEB.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_bytes(binary)
    WEB.write_bytes(binary)
    reloaded=trimesh.load(OUT,force="scene")
    assert isinstance(reloaded,trimesh.Scene)
    nodes=set(reloaded.graph.nodes)
    assert {"Hull","Turret","Barrel"}.issubset(nodes), sorted(nodes)
    geom=len(reloaded.geometry)
    tris=sum(len(m.faces) for m in reloaded.geometry.values())
    verts=sum(len(m.vertices) for m in reloaded.geometry.values())
    bounds=np.asarray(reloaded.bounds).round(5)
    assert 800<=tris<=1500, f"tris budget exceeded: {tris}"
    assert abs(float(bounds[0][1]))<.03, "track must physically touch ground y=0"
    assert abs(float(bounds[0][0])+3.158)<.25
    assert abs(float(bounds[1][0])-5.292)<.3
    assert abs(float(bounds[1][1])-3)<.25
    report={
        "asset":"tiger-i-early-1943",
        "phase":"P1 grey-box; deliberately simplified wheels; not a production art asset",
        "export":"models/vehicles/land/tiger-i/export/tiger-i-grey.glb",
        "web":"docs/assets/tiger-i-grey.glb",
        "triangles":int(tris),"vertices":int(verts),
        "mesh_count":int(geom),
        "bounds_xyz_m":bounds.tolist(),
        "size_xyz_m":np.diff(bounds,axis=0)[0].round(5).tolist(),
        "nodes":sorted(nodes),
        "parts":{n:{"triangles":len(m.faces),"vertices":len(m.vertices)}
                 for n,m in reloaded.geometry.items()},
        "articulations":{
            "Turret":{"parent":"Hull","axis":"+Y","pivot_hull_xyz":[.315,2.18,0]},
            "Barrel":{"parent":"Turret","axis":"-X recoil","pivot_turret_xyz":[1.335,.25,0]}
        },
        "nominal_reference":"references/geometry.json",
        "road_wheels_modelled_per_side":8,
        "historical_road_wheels_per_side":24,
        "notes":"Only main visible 8 road wheels/side modelled; interleaved hidden rows omitted pending next LOD; this is not final tracks or measured armour contours.",
        "rebuild_command":"python models/vehicles/land/tiger-i/source/build.py"
    }
    REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
