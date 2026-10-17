#!/usr/bin/env python3
"""Early-1943 Tiger I geometry-control mesh from the existing, audited #19 source.

No textures, UV, detailed reconstruction or Blender. Reuse the existing hull,
authentic early overlapping wheel stations, rounded turret and two-baffle brake.
The unmodified #19 output remains the historical 3D gallery asset.

Run: python models/vehicles/land/tiger-i/sprites/build_control.py
Requires numpy/trimesh; generates real GLB + NPZ triangle positions and semantic IDs.
"""
import importlib.util
import json
from pathlib import Path
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ASSET = HERE.parent
ROOT = HERE.parents[3]
OUT = HERE / "control"
REFINED = ASSET / "source/build_refined.py"
IDS = {"hull":1,"turret":2,"gun":3,"track":4,"wheel":5,"fittings":6}
PALETTE = {"hull":(160,174,160),"turret":(195,193,148),"gun":(225,159,107),
           "track":(82,104,98),"wheel":(130,149,175),"fittings":(173,144,166)}

def category(name):
    if name.startswith(("RoadWheel_","WheelHub_","Sprocket_","Idler_")): return "wheel"
    if name.startswith(("TrackBelt_","TrackShoes_")): return "track"
    if name.startswith(("BarrelTube","Muzzle")): return "gun"
    if name.startswith(("Turret","Mantlet","GunCollar","CommanderCupola","Cupola","LoaderHatch")): return "turret"
    if name.startswith(("Hull","LowerTub","RoofPlate","Sponsons","Nose","RearVertical","SideSkirt","FrontFender")): return "hull"
    return "fittings"

def keep(name):
    # Drop 200 tread shoe solids, wheel hubs, weld slats, bolts and surface ornaments.
    if name.startswith(("TrackShoes_","WheelHub_","SideSkirtJoint_","CoolingGrille",
                       "CupolaVision_","TurretLift_","EngineHinge_","HatchHinge_",
                       "SprocketTeeth_","IdlerTeeth_")): return False
    # Keep only geometry with significant effect on silhouette/occlusion/category.
    prefixes=("HullArmour","LowerTub","RoofPlate","Sponsons","NoseVerticalPlate",
      "NoseRoofTransition","RearVerticalPlate","DriverViewPlate","BowMachinegunBall",
      "SideSkirt_","TrackBelt_","RoadWheel_","Sprocket_","Idler_",
      "FrontFender_","ExhaustSilencer_","ExhaustGuard_",
      "TurretShell","TurretRoof","MantletShield","GunCollar",
      "CommanderCupola","CupolaTop","LoaderHatch","TurretStowage",
      "BarrelTube","MuzzleFirstRing","MuzzleSecondRing","MuzzleExitRing",
      "MuzzleBridge_","TurretRace")
    return name.startswith(prefixes)

def main():
    geo=json.loads((ASSET/"references/geometry.json").read_text())
    assert geo["axes"]["forward"]=="+X" and geo["axes"]["right"]=="+Z"
    assert geo["dimensions"]["road_wheels_per_side"]==24
    spec=importlib.util.spec_from_file_location("tiger_legacy_refined",REFINED)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scene,names=module.build_scene()
    control=trimesh.Scene(base_frame="World")
    vertices=[];faces=[]; ids=[]; parts=[]; total=0
    for node in names:
        if not keep(node):continue
        matrix,gname=scene.graph.get(node)
        mesh=scene.geometry[gname].copy()
        mesh.apply_transform(matrix)
        if node.startswith("RoadWheel_"):
            # Early wheel layer kept, but replace 468-triangle stamp/dish by
            # a 12-section cylinder, without changing station/side/offset.
            center=mesh.bounds.mean(axis=0)
            mesh=trimesh.creation.cylinder(radius=.402,height=.11,sections=12)
            mesh.apply_translation(center)
        if node.startswith(("Sprocket_","Idler_")):
            center=mesh.bounds.mean(axis=0)
            mesh=trimesh.creation.cylinder(radius=.47,height=.15,sections=16)
            mesh.apply_translation(center)
        group=category(node)
        mesh.visual.vertex_colors=np.tile(np.array([*PALETTE[group],255],np.uint8),(len(mesh.vertices),1))
        control.add_geometry(mesh,geom_name=node,node_name=node)
        verts=np.asarray(mesh.vertices,dtype=np.float32)
        triangles=np.asarray(mesh.faces,dtype=np.int32)
        vertices.append(verts); faces.append(triangles+total);total+=len(verts)
        ids.extend([IDS[group]]*len(triangles))
        parts.append({"name":node,"category":group,"triangles":len(triangles)})
    assert sum(p["name"].startswith("RoadWheel_") for p in parts)==48
    assert sum(p["name"].startswith("TrackBelt_") for p in parts)==2
    assert {"MantletShield","BarrelTube","MuzzleFirstRing","MuzzleSecondRing","TurretShell"}.issubset({p["name"] for p in parts})
    out_v=np.concatenate(vertices);out_f=np.concatenate(faces)
    OUT.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(OUT/"tiger-i-control.npz",vertices=out_v,faces=out_f,ids=np.asarray(ids,dtype=np.uint8))
    (OUT/"tiger-i-control.glb").write_bytes(trimesh.exchange.gltf.export_glb(control))
    bounds=np.asarray(control.bounds).round(5).tolist()
    report={"schema_version":1,"asset_id":"tiger-i","variant":"integrated",
      "phase":"control geometry - NOT commercial 3D artwork",
      "reference":"../references/geometry.json","derived_from":"../source/build_refined.py",
      "axes":{"forward":"+X","up":"+Y","right":"+Z"},"ground_pivot_m":[0,0,0],
      "parts":parts,"category_ids":IDS,"triangle_count":len(out_f),
      "vertex_count":len(out_v),"mesh_count":len(parts),"bounds_m":bounds,
      "wheel_count_each_side":24,"wheel_stations_each_side":8,
      "limitations":["Hull and turret proportions not fabrication CAD",
                     "interleaved wheels reduced to cylinder faces",
                     "track tread teeth omitted","cupola/sights simplified",
                     "turret hand-weld detail and precise brake internals omitted"],
      "rebuild_command":"python models/vehicles/land/tiger-i/sprites/build_control.py"}
    (OUT/"model-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    assert bounds[0][1]>=0 and 5.0<bounds[1][0]<5.5 and 2.9<bounds[1][1]<3.2, bounds
    print(json.dumps({k:report[k] for k in ("triangle_count","mesh_count","bounds_m","wheel_count_each_side")}))
    return report

if __name__=="__main__":main()
