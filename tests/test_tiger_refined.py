"""No fake preview: actual GLB geometry and UV of Tiger early-production #19."""
from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from mesh_pipeline import inspect_glb,parse_glb

ASSET=ROOT/"models/vehicles/land/tiger-i"
OUT=ASSET/"export"
WEB=ROOT/"docs/assets"

class TigerRefinedTests(unittest.TestCase):
    def test_real_detailed_geometry_and_articulations(self):
        model=OUT/"tiger-i-refined-grey.glb"
        assert model.exists(), "Cloud generator must commit real GLB"
        self.assertEqual(model.read_bytes(),(WEB/model.name).read_bytes())
        measured=inspect_glb(model)
        self.assertGreater(measured["triangles"],6000)
        self.assertGreater(measured["parts"].__len__(),100)
        raw,_=parse_glb(model.read_bytes())
        names={n.get("name") for n in raw["nodes"]}
        self.assertTrue({"Hull","Turret","Barrel","TurretShell","MantletShield",
                        "MuzzleExitRing","TrackShoes_-1","TrackShoes_1"}.issubset(names))
        self.assertEqual(sum(n.startswith("RoadWheel_") for n in names),48)
        self.assertEqual(sum(n.startswith("SprocketTeeth_") for n in names),2)
        self.assertEqual(sum(n.startswith("TrackBelt_") for n in names),2)
        report=json.loads((OUT/"refined-mesh-report.json").read_text())
        self.assertEqual(measured["triangles"],report["triangles"])
        self.assertEqual(report["road_wheels_per_side"],24)
        self.assertEqual(report["track_shoes_per_side"],100)
        self.assertLessEqual(report["bounds_xyz_m"][0][1],.08)

    def test_true_refined_uv_material_and_seams(self):
        glb=OUT/"tiger-i-refined-uv.glb"
        self.assertTrue(glb.exists())
        self.assertEqual(glb.read_bytes(),(WEB/glb.name).read_bytes())
        stats=inspect_glb(glb)
        self.assertTrue(stats["uv_present"])
        self.assertGreater(stats["texture_count"],0)
        meta=json.loads((OUT/"refined-uv-report.json").read_text())
        grey=json.loads((OUT/"refined-mesh-report.json").read_text())
        self.assertEqual(stats["triangles"],grey["triangles"])
        self.assertEqual(meta["triangles"],grey["triangles"])
        self.assertEqual(meta["uv_corners"],grey["triangles"]*3)
        self.assertEqual(meta["atlas_size"],[4096,4096])
        self.assertGreater(stats["vertices"],grey["vertices"])
        doc,_=parse_glb(glb.read_bytes())
        self.assertTrue(doc["images"] and doc["textures"] and doc["materials"])
        self.assertTrue(all("TEXCOORD_0" in p["attributes"]
                            for g in doc["meshes"] for p in g["primitives"]))
        png=ASSET/"textures/tiger-i-refined-checker.png"
        tmpl=ASSET/"textures/tiger-i-refined-uv-template.png"
        import struct
        for file in (png,tmpl):
            b=file.read_bytes()
            self.assertEqual(b[:8],b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack_from(">II",b,16),(4096,4096))
