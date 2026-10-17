#!/usr/bin/env python3
"""Prepare actual #24 orthographic frames as provider-safe RGB control inputs.

No generative model is invoked by this command. Every source PNG is verified
against the source manifest SHA-256 before any conversion. Native 16-bit depth
is never altered: *copies* are mapped to provider RGB8 with fixed global range.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
ASSET=ROOT/"models/vehicles/land/tiger-i/sprites"
SLOTS4=(0,16,32,48)
SLOTS8=(0,8,16,24,32,40,48,56)
CHANNELS=("silhouette","depth","parts")
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(slots=SLOTS4):
    spec=json.loads((ASSET/"spec.json").read_text())
    manifest=json.loads((ASSET/"control/manifest.json").read_text())
    assert manifest["heading_slots"]==64 and manifest["degrees_per_slot"]==5.625
    assert manifest["camera"]==spec["camera"]
    assert manifest["source_spec_sha256"]==digest(ASSET/"spec.json")
    assert (ASSET/spec["model"]).is_file()
    assert manifest["source_model_sha256"]==digest(ASSET/spec["model"])
    assert tuple(spec["camera"]["canvas_px"])==(512,512)
    assert tuple(spec["camera"]["pivot_px"])==(256,354)
    assert len(set(slots))==len(slots) and all(i in range(64) for i in slots)
    output=ASSET/"generated/issue25";inputs=output/"inputs"
    meta={"schema_version":1,"asset_id":"tiger-i","phase":"control-preflight",
          "status":"prepared_control_inputs_only_NO_AI_INFERENCE",
          "source_model_sha256":manifest["source_model_sha256"],
          "source_spec_sha256":manifest["source_spec_sha256"],
          "source_control_manifest_sha256":digest(ASSET/"control/manifest.json"),
          "camera":spec["camera"],"slots":{},"channels":{},
          "depth_conversion":"uint16 camera-space depth → RGB8 by fixed v >> 8; background 0; no per-frame histogram normalization",
          "boundary_conversion":"bright actual #24 silhouette/part-edge pixels → 8-bit black/white edge map; not separately inferred Canny",
          "segmentation_conversion":"original semantic category RGB with transparent pixels composited to RGB black; no semantic relabel",
          "mask_conversion":"source silhouette alpha > 0 → binary L mask; not AI background removal"}
    contact=Image.new("RGB",(512*len(slots),512*3),(20,20,20))
    for col,i in enumerate(slots):
        key=f"{i:03d}";rec=manifest["frames"][key]
        sources={}
        for ch in CHANNELS:
            p=(ASSET/rec["files"][ch]).resolve()
            assert p.is_relative_to(ASSET/"control")
            assert digest(p)==rec["sha256"][ch], (key,ch)
            im=Image.open(p);im.load()
            assert im.size==(512,512)
            sources[ch]=im
        assert sources["depth"].mode in ("I","I;16")
        a=sources["silhouette"].convert("RGBA")
        seg=sources["parts"].convert("RGBA")
        depth=sources["depth"]
        amask=a.getchannel("A").point(lambda x:255 if x else 0)
        assert list(amask.getdata())==list(seg.getchannel("A").point(lambda x:255 if x else 0).getdata())
        zz=depth.getdata()
        assert all((v>0)==(m>0) for v,m in zip(zz,amask.getdata()))
        # Use actual white border vertices from #24, not a new detector.
        whites=a.convert("RGB").getchannel("R")
        edge=Image.new("L",a.size,0)
        edge.putdata([255 if m and r>215 else 0 for r,m in zip(whites.getdata(),amask.getdata())])
        assert edge.getbbox(),f"empty edge condition at {key}"
        dep=Image.new("L",depth.size,0)
        dep.putdata([int(v)>>8 for v in zz])
        assert dep.getextrema()[1]>dep.getextrema()[0]
        images={"edge_rgb":edge.convert("RGB"),
                "depth_rgb":dep.convert("RGB"),
                "parts_rgb":Image.new("RGB",seg.size,(0,0,0)),
                "subject_mask":amask}
        images["parts_rgb"].paste(seg.convert("RGB"),mask=amask)
        record={"slot":i,"theta_deg":i*5.625,"input_sha256":dict(rec["sha256"]),
                "converted":{},"label":"provider_input_NOT_GENERATED_ART"}
        for row,(kind,im) in enumerate(images.items()):
            p=inputs/kind/(key+".png");p.parent.mkdir(parents=True,exist_ok=True)
            im.save(p,optimize=True)
            record["converted"][kind]={"path":p.relative_to(ASSET).as_posix(),
                                       "sha256":digest(p),"mode":im.mode}
            if row<3:contact.paste(im,(col*512,row*512))
        meta["slots"][key]=record
    meta["channels"]={"edge_rgb":"black/white actual geometry boundaries",
                     "depth_rgb":"fixed 16-bit source to 8-bit provider RGB",
                     "parts_rgb":"semantic RGB colors for SDXL ControlNet segmentation",
                     "subject_mask":"actual geometry alpha 0/255"}
    (output/"input-manifest.json").write_text(json.dumps(meta,indent=2)+"\n")
    qa=ASSET/"qa/issue25-input-contact-sheet.png"
    qa.parent.mkdir(parents=True,exist_ok=True)
    contact.save(qa,optimize=True)
    print(f"PREPARED ONLY: {len(slots)} headings × 4 images; no model invoked, no AI outputs.")
    return meta

def main():
    p=argparse.ArgumentParser();p.add_argument("--eight",action="store_true")
    a=p.parse_args();run(SLOTS8 if a.eight else SLOTS4)
if __name__=="__main__":main()
