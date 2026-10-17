#!/usr/bin/env python3
"""Issue #25 SDXL ControlNet Union API adapter. No false positive inference.

Default is OFFLINE payload/rights preflight. --execute is impossible without
all of: FAL_KEY, reviewed style reference, explicit commercial-rights approval,
known positive per-image price, explicit budget, and explicit spending flag.

Provider API schema: https://fal.ai/models/fal-ai/sdxl-controlnet-union/image-to-image/api
The *same image-to-image endpoint* and reference image are used for all 3 arms.
Actual returned original images and response IDs are persisted if ever executed.
"""
import argparse,base64,hashlib,json,os,time,urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[2]
ASSET=ROOT/"models/vehicles/land/tiger-i/sprites"
SOURCE=ASSET/"generated/issue25"
ENDPOINT="fal-ai/sdxl-controlnet-union/image-to-image"
MODES=("reference_only","reference_edge","reference_edge_depth_parts")
SLOTS4=(0,16,32,48)
PROMPT=("1943 early Tiger I heavy tank, single integrated vehicle, locked true "
        "orthographic RTS perspective; accurate near-vertical hull, asymmetrical "
        "rounded horseshoe turret and casting mantlet, long 88 mm gun with two "
        "baffle muzzle brake, 24 interleaved rubber road wheels per side. "
        "An original mature premium strategy game 2D illustration: precise "
        "painterly metal materials, restrained sand-olive palette, one consistent "
        "off-white turret number 131, small unique rust nick below the right "
        "turret hatch, same camouflage markings on every view. "
        "Isolated vehicle, no scene, no logo, no ground lettering. "
        "Camera never moves; preserve the supplied geometry projection and ground pivot.")
NEGATIVE=("late Tiger steel wheels, fantasy tank, Panther, Tiger II, extra barrels, "
          "broken sprockets, multiple vehicles, changing tank number, reversed writing, "
          "modern applique armor, invented chassis, cropped barrel, perspective lens, "
          "photographic background, watermarks, captions")
def hash_bytes(data):return hashlib.sha256(data).hexdigest()
def asdata(path):
    return "data:image/png;base64,"+base64.b64encode(Path(path).read_bytes()).decode("ascii")
def job(slot,mode,ref,include_images=False):
    if slot not in range(64) or mode not in MODES:raise ValueError("Invalid slot/mode")
    prepared=json.loads((SOURCE/"input-manifest.json").read_text())
    key=f"{slot:03d}";rec=prepared["slots"][key]
    assert rec["slot"]==slot and rec["theta_deg"]==slot*5.625
    if not ref or Path(ref).suffix.lower() not in (".png",".jpg",".jpeg"):
        raise ValueError("Explicit user-approved style/reference image is required")
    ref=Path(ref)
    if not ref.is_file():raise FileNotFoundError(ref)
    from PIL import Image
    im=Image.open(ref);im.verify()
    parts={}
    for kind,item in rec["converted"].items():
        p=(ASSET/item["path"]).resolve()
        assert p.is_relative_to(SOURCE/"inputs") and hash_bytes(p.read_bytes())==item["sha256"]
        parts[kind]=asdata(p) if include_images else "<data URI of verified "+item["sha256"][:16]+">"
    refurl=asdata(ref) if include_images else "<data URI of verified "+hash_bytes(ref.read_bytes())[:16]+">"
    payload={"prompt":PROMPT,"negative_prompt":NEGATIVE,"image_url":refurl,
             "strength":0.95,"image_size":{"width":512,"height":512},
             "seed":131000+slot,"num_images":1,"num_inference_steps":35,
             "guidance_scale":7.5,"controlnet_conditioning_scale":0.5,
             "enable_safety_checker":True,"expand_prompt":False,"format":"png"}
    if mode!="reference_only":
        payload.update(canny_image_url=parts["edge_rgb"],canny_preprocess=False)
    if mode=="reference_edge_depth_parts":
        payload.update(depth_image_url=parts["depth_rgb"],depth_preprocess=False,
                       segmentation_image_url=parts["parts_rgb"],segmentation_preprocess=False)
    return payload

def report_preflight(slots,ref):
    obj={"status":"NOT_EXECUTED","provider":ENDPOINT,
         "references": {"source":["https://fal.ai/models/fal-ai/sdxl-controlnet-union/image-to-image/api"],
                        "style_image_supplied":bool(ref and Path(ref).is_file())},
         "planned_modes":list(MODES),"planned_slots":list(slots),"planned_count":len(slots)*len(MODES),
         "authentication_available":bool(os.environ.get("FAL_KEY")),
         "exact_price_confirmed":False,"requests":[]}
    for slot in slots:
        for mode in MODES:
            entry={"slot":slot,"mode":mode,"seed":131000+slot,"status":"NOT_EXECUTED"}
            if ref and Path(ref).is_file(): entry["schema_payload"]=job(slot,mode,ref,False)
            else:entry["blocked_by"]="No verified approved reference image"
            obj["requests"].append(entry)
    p=SOURCE/"request-preflight.json";p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2)+"\n")
    print("PREFLIGHT ONLY: no remote request; do not mistake plan for executed image generation.")
    return obj

def remote(payload,token):
    # REST queue protocol. No third-party upload occurs until all gates pass.
    url="https://queue.fal.run/"+ENDPOINT
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),
          headers={"Authorization":"Key "+token,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=90) as r: submitted=json.load(r)
    request_id=submitted["request_id"]
    status_url=submitted["status_url"];result_url=submitted["response_url"]
    for link in (status_url,result_url):
        u=urlparse(link)
        if u.scheme!="https" or u.netloc!="queue.fal.run":
            raise RuntimeError("Provider returned unexpected queue URL")
    for attempt in range(90):
        check=urllib.request.Request(status_url,headers={"Authorization":"Key "+token})
        with urllib.request.urlopen(check,timeout=30) as r:status=json.load(r)
        if status.get("status")=="COMPLETED":break
        if status.get("status")=="FAILED":raise RuntimeError("Remote inference failure")
        time.sleep(2)
    else:raise TimeoutError("Inference polling exceeded 3 min")
    req=urllib.request.Request(result_url,headers={"Authorization":"Key "+token})
    with urllib.request.urlopen(req,timeout=40) as r:record=json.load(r)
    return request_id,record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reference",help="Original user-approved licensed style image")
    p.add_argument("--eight",action="store_true")
    p.add_argument("--execute",action="store_true")
    p.add_argument("--commercial-terms-confirmed",action="store_true")
    p.add_argument("--price-per-image",type=float)
    p.add_argument("--max-total-usd",type=float)
    p.add_argument("--confirm-spend",action="store_true")
    a=p.parse_args();slots=tuple(range(0,64,8)) if a.eight else SLOTS4
    report_preflight(slots,a.reference)
    if not a.execute:return
    # Fail CLOSED. Price must be manually verified, not inferred from other endpoints.
    if not os.environ.get("FAL_KEY"):raise RuntimeError("NO FAL_KEY; zero inference requests")
    if not a.reference or not Path(a.reference).is_file():raise RuntimeError("NO APPROVED STYLE REFERENCE")
    if not a.commercial_terms_confirmed:raise RuntimeError("COMMERCIAL RIGHTS UNCONFIRMED")
    if not a.confirm_spend:raise RuntimeError("SPEND NOT CONFIRMED")
    if not a.price_per_image or a.price_per_image<=0 or not a.max_total_usd:
        raise RuntimeError("PER-IMAGE PRICE OR TOTAL BUDGET UNKNOWN")
    if len(slots)*len(MODES)*a.price_per_image>a.max_total_usd:
        raise RuntimeError("Budget would be exceeded; no API calls")
    # Incremental results for mid-run resumption. Each candidate stays in generated/,
    # never approved/ or export/ without a separate human art acceptance.
    for slot in slots:
        for mode in MODES:
            folder=SOURCE/"candidates"/mode;folder.mkdir(parents=True,exist_ok=True)
            target=folder/f"{slot:03d}.png"
            if target.exists():raise FileExistsError(f"Candidate already exists: {target}")
            payload=job(slot,mode,a.reference,True)
            reqid,response=remote(payload,os.environ["FAL_KEY"])
            files=response.get("images") or []
            if not files:raise ValueError("Provider returned no image")
            imgurl=files[0]["url"]
            if urlparse(imgurl).scheme!="https":raise ValueError("Non-HTTPS image output")
            with urllib.request.urlopen(imgurl,timeout=60) as r:body=r.read(14*1024*1024)
            if not body.startswith(b"\\x89PNG\\r\\n\\x1a\\n"):
                # The API may return JPEG despite PNG request: never rename bytes.
                raise ValueError("Expected genuine PNG, original output not saved")
            from PIL import Image
            import io
            with Image.open(io.BytesIO(body)) as im: im.load();size=im.size;format_name=im.format
            target.write_bytes(body)
            metadata={"status":"EXECUTED_API_RESPONSE","endpoint":ENDPOINT,"request_id":reqid,
                "slot":slot,"theta_deg":slot*5.625,"mode":mode,
                "seed_requested":payload["seed"],"seed_actual":response.get("seed"),
                "image_sha256":hash_bytes(body),"image_dimensions":list(size),
                "image_format":format_name,"prompt":PROMPT,"negative_prompt":NEGATIVE,
                "reference_sha256":hash_bytes(Path(a.reference).read_bytes()),
                "model_version":"fal service model revision not attested",
                "all_conditions_submitted":mode=="reference_edge_depth_parts",
                "actual_condition_weights":"service default shared scalar 0.5"}
            target.with_suffix(".json").write_text(json.dumps(metadata,indent=2)+"\n")
            print("EXECUTED:",mode,slot,reqid)
if __name__=="__main__":main()
