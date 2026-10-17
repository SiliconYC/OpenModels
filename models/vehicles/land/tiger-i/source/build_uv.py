#!/usr/bin/env python3
"""Build true Tiger I UV atlas and textured GLB from Issue #5 geometry.

Reuses source/build.py scene and hierarchy; does not fake geometry or UV.
Cloud Python 3.12 + numpy + trimesh + Pillow, no Blender or GUI.
python models/vehicles/land/tiger-i/source/build_uv.py

Each actual triangle is unshared at UV seams. Within each reusable part category,
faces are projected to one of six nonoverlapping, labelled planar charts. Distinct
parts never overlap in the atlas; repeated wheel stations deliberately reuse UVs.
glTF (0,0) is the upper-left pixel of the image (KHR specification).
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from collections import Counter

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[5]
ASSET = ROOT / "models/vehicles/land/tiger-i"
sys.path.insert(0, str(ASSET / "source"))
from build import build_scene  # noqa: E402

SIZE = 2048
TILES = 4
TILE = SIZE // TILES
PADDING = 10  # pixels of empty atlas chart edge, avoids bilinear bleeding
AXES = ("+X", "-X", "+Y", "-Y", "+Z", "-Z")
TEXTURES = ASSET / "textures"
EXPORT = ASSET / "export"
WEB = ROOT / "docs" / "assets"
ATLAS = TEXTURES / "tiger-i-uv-checker.png"
TEMPLATE = TEXTURES / "tiger-i-uv-template.png"
LAYOUT = TEXTURES / "uv-layout.json"
MODEL = EXPORT / "tiger-i-uv.glb"
WEB_MODEL = WEB / "tiger-i-uv.glb"
REPORT = EXPORT / "uv-report.json"


def family(name: str) -> str:
    # All mirrored/repeated wheel stations share one paintable master chart.
    for prefix in ("RoadWheel", "Track", "SideSkirt", "Idler", "Sprocket", "TowLug"):
        if name.startswith(prefix + "_"):
            return prefix
    return name


def charts(family_index: int):
    tx, ty = family_index % TILES, family_index // TILES
    result = []
    for axis in range(6):
        col, row = axis % 3, axis // 3
        x0 = tx * TILE + col * TILE / 3
        x1 = tx * TILE + (col + 1) * TILE / 3
        y0 = ty * TILE + row * TILE / 2
        y1 = ty * TILE + (row + 1) * TILE / 2
        result.append((x0 + PADDING, y0 + PADDING, x1 - PADDING, y1 - PADDING))
    return result


def face_axis(tri: np.ndarray) -> int:
    n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
    if not np.isfinite(n).all() or np.linalg.norm(n) < 1e-10:
        raise ValueError("degenerate triangle cannot be mapped")
    axis = int(np.argmax(abs(n)))
    return axis * 2 + (0 if n[axis] >= 0 else 1)


def project(points: np.ndarray, face: int) -> np.ndarray:
    # Orient +Z and -Z panels with opposite U so markings cannot appear mirrored
    # when each side is viewed from outside the tank.
    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    if face == 0: return np.column_stack((-z, y))       # from +X
    if face == 1: return np.column_stack(( z, y))       # from -X
    if face == 2: return np.column_stack(( z, x))       # from +Y
    if face == 3: return np.column_stack((-z, x))       # from -Y
    if face == 4: return np.column_stack(( x, y))       # from +Z
    return np.column_stack((-x, y))                     # from -Z


def create_atlases(families):
    checker = Image.new("RGB", (SIZE, SIZE), "#182124")
    template = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(checker)
    outline = ImageDraw.Draw(template)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    for i, part in enumerate(families):
        for axis, chart in enumerate(charts(i)):
            x0, y0, x1, y1 = [int(round(n)) for n in chart]
            # Grid corners/letter orientation remain readable on the actual mesh.
            for yy in range(y0, y1, 16):
                for xx in range(x0, x1, 16):
                    parity = ((xx - x0) // 16 + (yy - y0) // 16) % 2
                    shade = (97, 113, 112) if parity else (163, 176, 163)
                    draw.rectangle((xx, yy, min(xx + 15, x1), min(yy + 15, y1)), fill=shade)
            draw.rectangle((x0, y0, x1, y1), outline="#f0e5be", width=2)
            draw.rectangle((x0 + 2, y0 + 2, x0 + 9, y0 + 9), fill="#ed7753")
            draw.rectangle((x1 - 9, y0 + 2, x1 - 2, y0 + 9), fill="#72dc91")
            draw.rectangle((x0 + 3, y0 + 13, x1 - 3, y0 + 36), fill="#111d20")
            draw.text((x0 + 6, y0 + 16), part[:15], fill="white", font=font)
            draw.text((x0 + 6, y0 + 38), AXES[axis], fill="#ffe3a2", font=font)
            outline.rectangle((x0, y0, x1, y1), outline="#eff0e8", width=2)
            outline.text((x0 + 5, y0 + 15), part[:15] + " " + AXES[axis], fill="#e8ddd0", font=font)
    return checker, template


def unwrap(name, geom, slots):
    # Preserve all original triangles and their winding. Duplicate each corner
    # because projected face charts have real UV seams (no vertex UV conflict).
    faces = np.asarray(geom.faces, dtype=np.int64)
    original = np.asarray(geom.vertices, dtype=np.float64)
    mapped_verts = original[faces].reshape(-1, 3)
    mapped_faces = np.arange(len(mapped_verts), dtype=np.int64).reshape(-1, 3)
    uvs = np.zeros((len(mapped_verts), 2), dtype=np.float64)
    by_axis = Counter()
    projections = [project(original, i) for i in range(6)]
    spans = []
    for coords in projections:
        low = coords.min(axis=0)
        high = coords.max(axis=0)
        spans.append((low, np.maximum(high - low, 1e-7)))
    for t, face in enumerate(faces):
        raw_tri = original[face]
        side = face_axis(raw_tri)
        chart = slots[side]
        projected = project(raw_tri, side)
        low, span = spans[side]
        # Preserve physical U/V aspect. Independent 0..1 normalization would
        # badly stretch the 6-m hull side into a tall narrow chart.
        x0, y0, x1, y1 = chart
        pixel_per_metre = min((x1 - x0) / span[0], (y1 - y0) / span[1])
        offsets = (projected - (low + span * .5)) * pixel_per_metre
        uvs[t * 3:t * 3 + 3, 0] = ((x0 + x1) * .5 + offsets[:, 0]) / SIZE
        # glTF image starts top-left; increasing model-up means decreasing V.
        uvs[t * 3:t * 3 + 3, 1] = ((y0 + y1) * .5 - offsets[:, 1]) / SIZE
        by_axis[AXES[side]] += 1
    if not np.isfinite(uvs).all() or np.any(uvs < 0) or np.any(uvs > 1):
        raise ValueError("UV outside atlas for " + name)
    replacement = trimesh.Trimesh(vertices=mapped_verts, faces=mapped_faces, process=False)
    assert len(replacement.faces) == len(geom.faces)
    return replacement, uvs, dict(by_axis)


def main():
    scene, _ = build_scene()
    original_triangles = sum(len(g.faces) for g in scene.geometry.values())
    original_vertices = sum(len(g.vertices) for g in scene.geometry.values())
    families = sorted({family(name) for name in scene.geometry})
    if len(families) > TILES ** 2:
        raise ValueError("atlas full; increase tile count")
    by_family = {name: i for i, name in enumerate(families)}
    TEXTURES.mkdir(parents=True, exist_ok=True)
    EXPORT.mkdir(parents=True, exist_ok=True)
    WEB.mkdir(parents=True, exist_ok=True)
    atlas, template = create_atlases(families)
    atlas.save(ATLAS, optimize=True)
    template.save(TEMPLATE, optimize=True)
    shared_material = trimesh.visual.material.PBRMaterial(
        name="TigerI_UV_Checker", baseColorTexture=atlas, metallicFactor=0, roughnessFactor=1)
    counts = {}
    for name, geometry in list(scene.geometry.items()):
        result, uv, axes = unwrap(name, geometry, charts(by_family[family(name)]))
        result.visual = trimesh.visual.texture.TextureVisuals(uv=uv, material=shared_material)
        scene.geometry[name] = result
        counts[name] = {"triangles": len(result.faces), "vertices": len(result.vertices),
                        "uv_corners": len(uv), "charts_used": axes, "family": family(name)}
    binary = trimesh.exchange.gltf.export_glb(scene)
    MODEL.write_bytes(binary)
    WEB_MODEL.write_bytes(binary)
    reloaded = trimesh.load(MODEL, force="scene")
    tris = sum(len(m.faces) for m in reloaded.geometry.values())
    verts = sum(len(m.vertices) for m in reloaded.geometry.values())
    if tris != original_triangles:
        raise AssertionError("UV split unexpectedly changed real triangle count")
    assert all(getattr(m.visual, "uv", None) is not None for m in reloaded.geometry.values())
    assert {"Hull", "Turret", "Barrel"}.issubset(reloaded.graph.nodes)
    mapping = {"asset": "tiger-i-early-1943", "texture_size": [SIZE, SIZE],
               "texture_image": "tiger-i-uv-checker.png",
               "template_image": "tiger-i-uv-template.png",
               "tile_count": len(families), "atlas_tile_grid": [TILES, TILES],
               "face_charts_per_tile": list(AXES),
               "uv_strategy": "6 directional non-overlapping charts per reusable mesh family; per-triangle UV seam vertices",
               "paint_note": "All six directional charts for each part are independent. Repeated wheel/track parts reuse the same paint tile.",
               "tiles": [{"part": part, "tile_index": i,
                          "charts_px": {AXES[k]: [round(v, 3) for v in chart]
                                        for k, chart in enumerate(charts(i))}}
                         for i, part in enumerate(families)]}
    LAYOUT.write_text(json.dumps(mapping, indent=2, ensure_ascii=False) + "\n")
    report = {"asset": "tiger-i-early-1943", "phase": "Issue #6 actual painted UV checker",
              "source": "source/build_uv.py", "model": "export/tiger-i-uv.glb",
              "web": "docs/assets/tiger-i-uv.glb", "triangles": tris,
              "vertices": verts, "original_grey_triangles": original_triangles,
              "original_grey_vertices": original_vertices, "mesh_count": len(reloaded.geometry),
              "uv_corners": sum(a["uv_corners"] for a in counts.values()),
              "atlas_size": [SIZE, SIZE], "texture": str(ATLAS.relative_to(ASSET)),
              "atlas_families": families, "parts": counts,
              "topology_note": "Each face corner split for independent chart seam; triangles and hierarchy preserved."}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: report[k] for k in ("triangles", "vertices", "mesh_count",
                                          "uv_corners", "atlas_size", "atlas_families")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
