"""Run from repository root: python -m unittest discover -s tests -p 'test_*.py'"""
import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from mesh_pipeline import generate_glb, inspect_glb, parse_glb


class MeshPipelineTests(unittest.TestCase):
    def test_real_cube_glb_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cube.glb"
            path.write_bytes(generate_glb())
            info = inspect_glb(path)
            self.assertEqual(info["triangles"], 12)
            self.assertEqual(info["vertices"], 24)
            self.assertEqual(info["size_m"], [1, 1, 1])
            self.assertTrue(info["uv_present"])
            self.assertEqual(info["texture_count"], 1)
            self.assertEqual(info["image_count"], 1)
            doc, raw = parse_glb(path.read_bytes())
            self.assertTrue(raw.startswith(b"\x00\x00")) # first vertex x=+0.5? see below
            self.assertIn("KHR_materials_unlit", doc["extensionsUsed"])

    def test_reject_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.glb"
            path.write_bytes(generate_glb()[:-1])
            with self.assertRaises(ValueError):
                inspect_glb(path)

    def test_committed_sample_reproducible(self):
        target = ROOT / "docs/assets/test-cube.glb"
        if target.exists():
            self.assertEqual(target.read_bytes(), generate_glb())
            self.assertEqual(inspect_glb(target)["triangles"], 12)


if __name__ == "__main__":
    unittest.main()
