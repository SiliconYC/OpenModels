"""Issue #6: verify *real* exported UV and embedded texture, no painted fakes."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from mesh_pipeline import inspect_glb, parse_glb

ASSET = ROOT / "models/vehicles/land/tiger-i"
SOURCE = ASSET / "source/build_uv.py"
GLB = ASSET / "export/tiger-i-uv.glb"
WEB = ROOT / "docs/assets/tiger-i-uv.glb"
ATLAS = ASSET / "textures/tiger-i-uv-checker.png"
TEMPLATE = ASSET / "textures/tiger-i-uv-template.png"
LAYOUT = ASSET / "textures/uv-layout.json"
REPORT = ASSET / "export/uv-report.json"


class UVTests(unittest.TestCase):
    def test_generator_and_real_export(self):
        for path in (SOURCE, GLB, WEB, ATLAS, TEMPLATE, LAYOUT, REPORT):
            self.assertTrue(path.is_file(), str(path))
        self.assertEqual(GLB.read_bytes(), WEB.read_bytes())
        info = inspect_glb(GLB)
        self.assertTrue(info["uv_present"])
        self.assertGreater(info["texture_count"], 0)
        self.assertEqual(info["triangles"], 1396)
        meta = json.loads(REPORT.read_text("utf-8"))
        self.assertEqual(meta["triangles"], 1396)
        self.assertEqual(meta["mesh_count"], 36)
        self.assertEqual(meta["uv_corners"], 1396 * 3)
        self.assertEqual(meta["atlas_size"], [2048, 2048])
        self.assertEqual(len(meta["atlas_families"]), 16)
        self.assertEqual(sum(x["triangles"] for x in meta["parts"].values()), 1396)
        self.assertGreater(meta["vertices"], 766)  # actual seam splits

    def test_gltf_uv_and_painted_material(self):
        doc, _ = parse_glb(GLB.read_bytes())
        self.assertTrue(doc.get("images"), "real embedded PNG required")
        self.assertTrue(doc.get("textures"), "real glTF texture required")
        self.assertTrue(doc.get("materials"), "real painted material required")
        self.assertTrue(all(
            "TEXCOORD_0" in primitive["attributes"]
            for mesh in doc["meshes"] for primitive in mesh["primitives"]
        ))
        self.assertTrue(any(
            m.get("pbrMetallicRoughness", {}).get("baseColorTexture")
            for m in doc["materials"]
        ))

    def test_atlas_png_dimensions(self):
        import struct
        for path in (ATLAS, TEMPLATE):
            blob = path.read_bytes()
            self.assertEqual(blob[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack_from(">II", blob, 16), (2048, 2048))
        layout = json.loads(LAYOUT.read_text("utf-8"))
        self.assertEqual(len(layout["tiles"]), 16)
        for tile in layout["tiles"]:
            self.assertEqual(len(tile["charts_px"]), 6)
