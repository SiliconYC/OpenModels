#!/usr/bin/env python3
"""Reproducible genuine UV atlas for detailed early Tiger geometry.

Atlas generation shares tested six-direction chart math with build_uv.py,
but has a separate 8x8 atlas so original Issue #6 assets are retained as a
baseline. No downloaded image is presented as a model or UV diagram.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import trimesh
from PIL import Image

import build_uv as uv
from build_refined import build_scene, ASSET, WEB, EXPORT

uv.SIZE = 4096
uv.TILES = 8
uv.TILE = 512
uv.PADDING = 12

ATLAS=ASSET / "textures/tiger-i-refined-checker.png"
TEMPLATE=ASSET / "textures/tiger-i-refined-uv-template.png"
LAYOUT=ASSET / "textures/refined-uv-layout.json"
MODEL=EXPORT / "tiger-i-refined-uv.glb"
WEB_MODEL=WEB / "tiger-i-refined-uv.glb"
REPORT=EXPORT / "refined-uv-report.json"


def family(name):
    for prefix in (
        "RoadWheel", "WheelHub", "TrackBelt", "TrackShoes", "Sprocket",
        "SprocketTeeth", "Idler", "IdlerTeeth", "CrewHatch",
        "HatchPeriscopeCover", "HatchHinge", "SideSkirtJoint", "SideSkirt",
        "TowEye", "FrontFender", "ExhaustSilencer", "ExhaustTip",
        "ExhaustGuard", "CoolingGrilleFrame", "CoolingGrilleSlats",
        "EngineHinge", "CupolaVision", "TurretBinBracket", "TurretLift",
        "MuzzleBridge"
    ):
        if name.startswith(prefix+"_"):
            return prefix
    return name


def main():
    scene,_=build_scene()
    total=sum(len(m.faces) for m in scene.geometry.values())
    families=sorted({family(name) for name in scene.geometry})
    if len(families)>uv.TILES**2:
        raise ValueError("Too many chart families: "+repr(families))
    slots={part:i for i,part in enumerate(families)}
    (ASSET / "textures").mkdir(exist_ok=True)
    EXPORT.mkdir(exist_ok=True)
    WEB.mkdir(exist_ok=True)
    checker,template=uv.create_atlases(families)
    checker.save(ATLAS,optimize=True)
    template.save(TEMPLATE,optimize=True)
    shared=trimesh.visual.material.PBRMaterial(
        name="TigerI_Refined_UV_Debug",baseColorTexture=checker,
        metallicFactor=0.0,roughnessFactor=1.0)
    parts={}
    for name,g in list(scene.geometry.items()):
        mapped,coords,axes=uv.unwrap(name,g,uv.charts(slots[family(name)]))
        mapped.visual=trimesh.visual.texture.TextureVisuals(uv=coords,material=shared)
        scene.geometry[name]=mapped
        parts[name]={"triangles":len(mapped.faces),"family":family(name),
                     "uv_corners":len(coords),"orientation_charts":axes}
    binary=trimesh.exchange.gltf.export_glb(scene)
    MODEL.write_bytes(binary)
    WEB_MODEL.write_bytes(binary)
    reloaded=trimesh.load(MODEL,force="scene")
    tris=sum(len(m.faces) for m in reloaded.geometry.values())
    verts=sum(len(m.vertices) for m in reloaded.geometry.values())
    assert tris==total
    assert all(getattr(m.visual,"uv",None) is not None for m in reloaded.geometry.values())
    assert {"Hull","Turret","Barrel"}.issubset(reloaded.graph.nodes)
    layout={"atlas_size":[4096,4096],"texture":"tiger-i-refined-checker.png",
            "template":"tiger-i-refined-uv-template.png",
            "tile_grid":[8,8],"tiles":[{"part":fam,"charts_px":{
                uv.AXES[j]:list(chart) for j,chart in enumerate(uv.charts(i))}
                } for i,fam in enumerate(families)],
            "strategy":"Independent six-way aspect-preserving planar charts per part family, actual UV on every triangle; repeated wheels and tread shoes use shared atlas paint region."}
    LAYOUT.write_text(json.dumps(layout,ensure_ascii=False,indent=2)+"\n")
    report={"asset":"tiger-i-refined-early-1943",
            "phase":"detailed geometric UV test (not final camo)",
            "model":"export/tiger-i-refined-uv.glb",
            "source":"source/build_refined_uv.py",
            "triangles":tris,"vertices":verts,"mesh_count":len(reloaded.geometry),
            "uv_corners":sum(p["uv_corners"] for p in parts.values()),
            "atlas_size":[4096,4096],"atlas_families":families,
            "parts":parts,"bounds_xyz_m":reloaded.bounds.tolist()}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in
        ("triangles","vertices","mesh_count","uv_corners","atlas_size")},ensure_ascii=False))


if __name__=="__main__":
    main()
