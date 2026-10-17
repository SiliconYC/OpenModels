"""Full #24 actual-control-image acceptance, NOT conceptual/mock images."""
import json
import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
S=ROOT/"models/vehicles/land/tiger-i/sprites"
sys.path.insert(0,str(ROOT/"tools/sprites"))
class Controls(unittest.TestCase):
    def test_true_64_orientation_control_images(self):
        from generate_controls import verify,slots
        m=verify(S/"spec.json",64)
        self.assertEqual(len(m["frames"]),64)
        for level,step in ((16,4),(32,2),(64,1)):
            self.assertEqual(slots(level),list(range(0,64,step)))
            self.assertTrue(all(f"{i:03d}" in m["frames"] for i in slots(level)))
        self.assertEqual(m["rotation_target"],"vehicle-only")
        self.assertEqual(m["camera"]["type"],"orthographic")
        self.assertTrue(m["camera"]["fixed"])
        self.assertEqual(m["pivot_px"],[256,354])
        self.assertEqual(m["canvas_px"],[512,512])
    def test_actual_4by4_sheet_mapping(self):
        from PIL import Image
        from generate_controls import slots
        selected=slots(16)
        for channel in ("parts","silhouette","depth"):
            sheet=S/"control/sheets"/f"canonical-16-{channel}.png"
            index=sheet.with_suffix(".json")
            self.assertTrue(sheet.is_file())
            meta=json.loads(index.read_text())
            self.assertTrue(meta["row_major"])
            self.assertEqual([c["slot"] for c in meta["cells"]],selected)
            im=Image.open(sheet);self.assertEqual(im.size,(1024,1024))
            self.assertEqual(meta["tile_px"],256)
        arbitrary=S/"control/sheets/arbitrary-16-parts.json"
        a=json.loads(arbitrary.read_text())
        self.assertEqual([x["slot"] for x in a["cells"]],[1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31])
        self.assertTrue((S/"control/sheets/arbitrary-16-parts.png").is_file())
    def test_geometry_inputs_and_status(self):
        m=json.loads((S/"control/model-report.json").read_text())
        self.assertEqual(m["wheel_count_each_side"],24)
        self.assertLess(m["triangle_count"],12000)
        self.assertFalse((S/"approved").exists())
        self.assertFalse((S/"export/manifest.json").exists())
