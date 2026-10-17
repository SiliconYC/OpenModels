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
        try:
            from generate_controls import verify,slots
        except ModuleNotFoundError as error:
            if error.name in ("numpy","PIL"): self.skipTest("Optional image libs validated by dedicated controls generation CI")
            raise
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
        import numpy as np
        from PIL import Image
        # Consecutive headings are near each other in silhouette space,
        # including the wrap from slot 063 to 000.
        masks=[]
        for i in range(64):
            im=Image.open(S/"control/frames/silhouette"/f"{i:03d}.png")
            masks.append(np.asarray(im)[:,:,3]>0)
        values=[]
        for i in range(64):
            a,b=masks[i],masks[(i+1)%64]
            values.append(float(np.count_nonzero(a&b)/np.count_nonzero(a|b)))
        self.assertGreater(min(values),.65,"Adjacency / loop closure discontinuity")
    def test_actual_4by4_sheet_mapping(self):
        try:
            from PIL import Image
            from generate_controls import slots
        except ModuleNotFoundError as error:
            if error.name in ("numpy","PIL"): self.skipTest("Optional image libs validated by dedicated controls generation CI")
            raise
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

    def test_manifest_index_and_binary_png_signatures_stdlib(self):
        m=json.loads((S/"control/manifest.json").read_text())
        self.assertEqual(m["heading_slots"],64)
        self.assertEqual(m["degrees_per_slot"],5.625)
        self.assertEqual(len(m["frames"]),64)
        self.assertEqual(m["available_levels"],[16,32,64])
        self.assertEqual(m["camera"]["type"],"orthographic")
        self.assertEqual(m["camera"]["fixed"],True)
        for i in range(64):
            rec=m["frames"][f"{i:03d}"]
            self.assertEqual(rec["theta_deg"],i*5.625)
            for channel in ("silhouette","depth","parts"):
                f=S/rec["files"][channel]
                with f.open("rb") as handle:
                    self.assertEqual(handle.read(8),bytes.fromhex("89504e470d0a1a0a"))
    def test_geometry_inputs_and_status(self):
        m=json.loads((S/"control/model-report.json").read_text())
        self.assertEqual(m["wheel_count_each_side"],24)
        self.assertLess(m["triangle_count"],12000)
        self.assertFalse((S/"approved").exists())
        self.assertFalse((S/"export/manifest.json").exists())
