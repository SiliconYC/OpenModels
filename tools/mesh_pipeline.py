#!/usr/bin/env python3
"""Pure-stdlib mesh generation + GLB verification. No Blender, renderer or desktop tools.

python tools/mesh_pipeline.py generate
python tools/mesh_pipeline.py inspect docs/assets/test-cube.glb
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
GLB_MAGIC = b"glTF"
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def png_checker(size=8):
    """Create a genuine 8-bit RGBA PNG, without Pillow."""
    def chunk(label, content):
        return struct.pack(">I", len(content)) + label + content + struct.pack(">I", zlib.crc32(label + content) & 0xffffffff)
    scanlines = bytearray()
    for y in range(size):
        scanlines.append(0)
        for x in range(size):
            light = ((x // 2) + (y // 2)) % 2 == 0
            scanlines.extend((211, 197, 143, 255) if light else (71, 94, 91, 255))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">2I5B", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(scanlines), level=9)) + chunk(b"IEND", b""))


def make_cube():
    """24 actual vertices, six independently UV-mapped faces, 12 triangles."""
    faces = [
        ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
        ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
        ((0, 1, 0), (1, 0, 0), (0, 0, -1)),
        ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
        ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
        ((0, 0, -1), (-1, 0, 0), (0, 1, 0)),
    ]
    corners = [(-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)]
    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
    positions, normals, texcoords, indices = [], [], [], []
    for normal, tangent_u, tangent_v in faces:
        start = len(positions) // 3
        for ((u, v), (tu, tv)) in zip(corners, uvs):
            positions.extend(normal[i] * .5 + tangent_u[i] * u + tangent_v[i] * v for i in range(3))
            normals.extend(normal)
            texcoords.extend((tu, tv))
        indices.extend((start, start + 1, start + 2, start, start + 2, start + 3))
    return positions, normals, texcoords, indices


def generate_glb():
    positions, normals, uvs, indices = make_cube()
    raw = bytearray()
    views = []
    def attach(data, target=None):
        while len(raw) % 4:
            raw.append(0)
        offset = len(raw)
        raw.extend(data)
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        views.append(view)
        return len(views) - 1
    p = attach(struct.pack("<" + "f" * len(positions), *positions), 34962)
    n = attach(struct.pack("<" + "f" * len(normals), *normals), 34962)
    u = attach(struct.pack("<" + "f" * len(uvs), *uvs), 34962)
    i = attach(struct.pack("<" + "H" * len(indices), *indices), 34963)
    im = attach(png_checker())
    gltf = {
        "asset": {"version": "2.0", "generator": "OpenModels stdlib mesh_pipeline.py"},
        "extensionsUsed": ["KHR_materials_unlit"],
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "TEST CUBE / UV", "mesh": 0}],
        "meshes": [{"name": "TEST CUBE / UV", "primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2},
            "indices": 3, "material": 0, "mode": 4
        }]}],
        "materials": [{"name": "UV checker / UNLIT", "doubleSided": False,
                       "pbrMetallicRoughness": {"baseColorTexture": {"index": 0},
                                                "metallicFactor": 0, "roughnessFactor": 1},
                       "extensions": {"KHR_materials_unlit": {}}}],
        "samplers": [{"magFilter": 9728, "minFilter": 9728,
                      "wrapS": 10497, "wrapT": 10497}],
        "textures": [{"sampler": 0, "source": 0}],
        "images": [{"name": "Procedural 8x8 checker", "bufferView": im, "mimeType": "image/png"}],
        "accessors": [
            {"bufferView": p, "componentType": 5126, "count": 24, "type": "VEC3",
             "min": [-.5, -.5, -.5], "max": [.5, .5, .5]},
            {"bufferView": n, "componentType": 5126, "count": 24, "type": "VEC3"},
            {"bufferView": u, "componentType": 5126, "count": 24, "type": "VEC2"},
            {"bufferView": i, "componentType": 5123, "count": 36, "type": "SCALAR"}],
        "bufferViews": views, "buffers": [{"byteLength": len(raw)}],
    }
    j = json.dumps(gltf, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    j += b" " * (-len(j) % 4)
    raw.extend(b"\x00" * (-len(raw) % 4))
    length = 12 + 8 + len(j) + 8 + len(raw)
    return (struct.pack("<4sII", GLB_MAGIC, 2, length) +
            struct.pack("<II", len(j), JSON_CHUNK) + j +
            struct.pack("<II", len(raw), BIN_CHUNK) + raw)


def parse_glb(content):
    if len(content) < 28:
        raise ValueError("GLB too short")
    magic, version, total = struct.unpack_from("<4sII", content)
    if (magic, version, total) != (GLB_MAGIC, 2, len(content)):
        raise ValueError("GLB header / byte length invalid")
    p = 12
    chunks = {}
    while p < total:
        if p + 8 > total:
            raise ValueError("truncated GLB chunk")
        size, kind = struct.unpack_from("<II", content, p)
        p += 8
        if size % 4 or p + size > total or kind in chunks:
            raise ValueError("bad GLB chunk alignment / size / duplicate")
        chunks[kind] = content[p:p + size]
        p += size
    if JSON_CHUNK not in chunks or BIN_CHUNK not in chunks:
        raise ValueError("missing JSON or BIN chunk")
    return json.loads(chunks[JSON_CHUNK]), chunks[BIN_CHUNK]


def inspect_glb(path):
    doc, raw = parse_glb(Path(path).read_bytes())
    if doc.get("asset", {}).get("version") != "2.0":
        raise ValueError("glTF asset not v2")
    if doc["buffers"][0]["byteLength"] > len(raw):
        raise ValueError("declared BIN larger than actual BIN")
    per_part = []
    vertex_total = triangle_total = 0
    found_uv = False
    bbox_min = [math.inf] * 3
    bbox_max = [-math.inf] * 3
    for mesh in doc.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            if primitive.get("mode", 4) != 4:
                raise ValueError("only TRIANGLES supported")
            attrs = primitive["attributes"]
            position = doc["accessors"][attrs["POSITION"]]
            if position["type"] != "VEC3" or position["componentType"] != 5126:
                raise ValueError("unexpected position encoding")
            count = position["count"]
            view = doc["bufferViews"][position["bufferView"]]
            start = view.get("byteOffset", 0) + position.get("byteOffset", 0)
            end = start + count * 12
            if end > view.get("byteOffset", 0) + view["byteLength"]:
                raise ValueError("position accessor extends beyond buffer view")
            triples = list(struct.iter_unpack("<fff", raw[start:end]))
            for values in triples:
                if not all(math.isfinite(x) for x in values):
                    raise ValueError("non-finite vertex")
                for j, x in enumerate(values):
                    bbox_min[j] = min(bbox_min[j], x)
                    bbox_max[j] = max(bbox_max[j], x)
            if "indices" not in primitive:
                raise ValueError("nonindexed primitives forbidden")
            idx = doc["accessors"][primitive["indices"]]
            tris, rem = divmod(idx["count"], 3)
            if rem:
                raise ValueError("indices not divisible by 3")
            uv = "TEXCOORD_0" in attrs
            if uv:
                tex = doc["accessors"][attrs["TEXCOORD_0"]]
                if tex["count"] != count or tex["type"] != "VEC2":
                    raise ValueError("UV vertex count / type mismatch")
                tex_view = doc["bufferViews"][tex["bufferView"]]
                off = tex_view.get("byteOffset", 0) + tex.get("byteOffset", 0)
                if off + count * 8 > tex_view.get("byteOffset", 0) + tex_view["byteLength"]:
                    raise ValueError("UV accessor bounds invalid")
                pairs = list(struct.iter_unpack("<ff", raw[off:off + count * 8]))
                if not all(math.isfinite(a) and math.isfinite(b) and 0 <= a <= 1 and 0 <= b <= 1 for a, b in pairs):
                    raise ValueError("invalid UV range")
            found_uv |= uv
            triangle_total += tris
            vertex_total += count
            per_part.append({"mesh": mesh.get("name", "unnamed"), "vertices": count,
                             "triangles": tris, "has_uv": uv, "material": primitive.get("material")})
    if not per_part:
        raise ValueError("no mesh")
    report = {"model": Path(path).name, "vertices": vertex_total,
              "triangles": triangle_total, "parts": per_part,
              "bounds_min": bbox_min, "bounds_max": bbox_max,
              "size_m": [round(b-a, 6) for a,b in zip(bbox_min,bbox_max)],
              "uv_present": found_uv, "texture_count": len(doc.get("textures", [])),
              "image_count": len(doc.get("images", [])),
              "extensions": doc.get("extensionsUsed", []),
              "rebuild_command": "python tools/mesh_pipeline.py generate",
              "inspection": "python tools/mesh_pipeline.py inspect docs/assets/test-cube.glb"}
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate", "inspect"])
    parser.add_argument("path", nargs="?", type=Path)
    args = parser.parse_args()
    path = args.path or OUT / "test-cube.glb"
    if args.command == "generate":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(generate_glb())
    report = inspect_glb(path)
    if args.command == "generate":
        (path.parent / (path.stem + ".report.json")).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
