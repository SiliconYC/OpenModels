"""#25 honest NO-GO readiness: test real control conversions, never synthesize art."""
import json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/"models/vehicles/land/tiger-i/sprites"
sys.path.insert(0,str(ROOT/"tools/sprites"))
class ProbeEvidence(unittest.TestCase):
    def test_four_locked_angles_and_schema(self):
        from fal_control_probe import SLOTS4,MODES,ENDPOINT
        self.assertEqual(SLOTS4,(0,16,32,48))
        self.assertEqual(len(MODES),3)
        self.assertEqual(ENDPOINT,"fal-ai/sdxl-controlnet-union/image-to-image")
        manifest=json.loads((ASSET/"control/manifest.json").read_text())
        self.assertEqual(manifest["camera"]["type"],"orthographic")
        self.assertEqual(manifest["camera"]["pivot_px"],[256,354])
        for n in SLOTS4:
            self.assertEqual(manifest["frames"][f"{n:03d}"]["theta_deg"],n*5.625)
    def test_prior_fal_api_not_executed_and_no_approved(self):
        p=ASSET/"generated/issue25/request-preflight.json"
        if not p.exists():self.skipTest("dedicated preflight workflow commits inputs")
        d=json.loads(p.read_text())
        self.assertEqual(d["status"],"NOT_EXECUTED")
        self.assertEqual(d["planned_count"],12)
        self.assertEqual(len(d["requests"]),12)
        self.assertTrue(all(x["status"]=="NOT_EXECUTED" for x in d["requests"]))
        # Earlier fal API trial remained unexecuted; later OpenAI imagegen
        # produced real RGB art candidates through a DIFFERENT provider.
        self.assertFalse((ASSET/"generated/issue25/candidates/fal").exists())
        a=ASSET/"generated/issue25/candidates/openai"
        if a.exists():
            m=json.loads((a/"manifest.json").read_text())
            self.assertEqual(m["status"],"REAL_GENERATED_CANDIDATES_UNAPPROVED")
            self.assertFalse(m["controlnet_used"])
            self.assertTrue(all(not rec["approved"] for rec in m["candidates"].values()))
        self.assertFalse((ASSET/"approved").exists())
        self.assertFalse((ASSET/"export").exists())
    def test_real_prepared_inputs(self):
        try:from PIL import Image
        except ImportError:self.skipTest("Pillow only available in dedicated preflight job")
        from prepare_ai_probe import digest
        p=ASSET/"generated/issue25/input-manifest.json"
        if not p.exists():self.skipTest("dedicated preflight workflow commits inputs")
        d=json.loads(p.read_text())
        self.assertEqual(d["status"],"prepared_control_inputs_only_NO_AI_INFERENCE")
        self.assertEqual([int(x) for x in d["slots"]],[0,16,32,48])
        for k,rec in d["slots"].items():
            self.assertEqual(rec["slot"]*5.625,rec["theta_deg"])
            self.assertEqual(set(rec["converted"]),{"edge_rgb","depth_rgb","parts_rgb","subject_mask"})
            for name,item in rec["converted"].items():
                q=ASSET/item["path"]
                self.assertEqual(digest(q),item["sha256"])
                with Image.open(q) as im:
                    im.load()
                    self.assertEqual(im.size,(512,512))
                    self.assertEqual(im.mode,"L" if name=="subject_mask" else "RGB")
                if name=="depth_rgb":
                    with Image.open(ASSET/rec["converted"]["depth_rgb"]["path"]) as depth8:
                        src=Image.open(ASSET/f"control/frames/depth/{k}.png")
                        a=list(depth8.convert("L").getdata())
                        b=[int(x)>>8 for x in src.getdata()]
                        self.assertEqual(a,b)
    def test_provider_payload_actual_three_arms(self):
        try:from PIL import Image
        except ImportError:self.skipTest("Pillow only available in dedicated preflight job")
        p=ASSET/"generated/issue25/input-manifest.json"
        if not p.exists():self.skipTest("dedicated preflight workflow commits inputs")
        from fal_control_probe import job,MODES
        # A local test reference exercises schema ONLY, not approved/commercial style.
        reference=ASSET/"qa/issue25-input-contact-sheet.png"
        a=job(0,MODES[0],reference,False)
        b=job(0,MODES[1],reference,False)
        c=job(0,MODES[2],reference,False)
        self.assertNotIn("canny_image_url",a)
        self.assertIn("image_url",a)
        self.assertIn("canny_image_url",b)
        self.assertNotIn("depth_image_url",b)
        self.assertIn("depth_image_url",c)
        self.assertIn("segmentation_image_url",c)
        self.assertEqual([a["seed"],b["seed"],c["seed"]],[131000]*3)
        self.assertTrue(all(req["format"]=="png" for req in (a,b,c)))
