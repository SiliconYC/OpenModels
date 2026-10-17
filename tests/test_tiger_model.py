"""Issue #5 exported GLB integrity and procedural model contract, standard-library only."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from mesh_pipeline import inspect_glb,parse_glb

ASSET=ROOT/"models/vehicles/land/tiger-i"
MODEL=ASSET/"export/tiger-i-grey.glb"
WEB=ROOT/"docs/assets/tiger-i-grey.glb"
REPORT=ASSET/"export/mesh-report.json"


class TigerModelTests(unittest.TestCase):
    def test_real_binary_mesh_and_hierarchy(self):
        if not MODEL.exists():
            self.skipTest("asset generator not yet executed")
        self.assertEqual(MODEL.read_bytes(),WEB.read_bytes())
        a=inspect_glb(MODEL)
        self.assertTrue(800<=a["triangles"]<=1500,a["triangles"])
        self.assertGreater(a["parts"].__len__(),20)
        self.assertEqual(a["texture_count"],0)
        doc,_=parse_glb(MODEL.read_bytes())
        names={n.get("name") for n in doc["nodes"]}
        self.assertTrue({"Hull","Turret","Barrel"}.issubset(names),names)
        self.assertTrue(all(p["triangles"]>0 for p in a["parts"]))
        self.assertEqual(json.loads(REPORT.read_text())["triangles"],a["triangles"])
        self.assertFalse(a["uv_present"])


if __name__=="__main__":
    unittest.main()
