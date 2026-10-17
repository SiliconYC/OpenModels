"""#23 reproducible control-mesh and canonical orthographic views."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=ROOT/"models/vehicles/land/tiger-i/sprites"
class TigerControl(unittest.TestCase):
    def test_geometry_control(self):
        report=json.loads((S/"control/model-report.json").read_text())
        self.assertEqual(report["wheel_count_each_side"],24)
        self.assertEqual(report["wheel_stations_each_side"],8)
        self.assertGreater(report["triangle_count"],1000)
        self.assertLess(report["triangle_count"],12000)
        self.assertLess(report["bounds_m"][0][1],.1)
        self.assertAlmostEqual(report["bounds_m"][1][0],5.292,delta=.1)
        self.assertTrue((S/"control/tiger-i-control.npz").stat().st_size>4000)
        self.assertEqual((S/"control/tiger-i-control.glb").read_bytes()[:4],b"glTF")
        self.assertFalse((S/"control/model-report.json").read_text().find('"UV/textures"')>=0)
    def test_actual_orientations(self):
        report=json.loads((S/"qa/orthographic-review.json").read_text())
        self.assertTrue(report["orthographic"])
        self.assertEqual(len(report["views"]),10)
        for name,record in report["views"].items():
            self.assertGreater(record["opaque_pixels"],1500)
            with (S/"qa/views"/(name+".png")).open("rb") as f:
                self.assertEqual(f.read(8),b"\x89PNG\r\n\x1a\n")
