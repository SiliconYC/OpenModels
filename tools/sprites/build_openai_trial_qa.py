#!/usr/bin/env python3
"""Build four real OpenAI candidate & geometry-control QA sheets. Never approve/publish."""
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[2]
ASSET=ROOT/"models/vehicles/land/tiger-i/sprites"
CAND=ASSET/"generated/issue25/candidates/openai"
QA=ASSET/"qa"

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def composite(im,bg="#203036"):
    im=im.convert("RGBA")
    base=Image.new("RGBA",im.size,bg)
    base.alpha_composite(im)
    return base.convert("RGB")

def tile(canvas,im,x,y,w,h,label):
    d=ImageDraw.Draw(canvas)
    d.text((x+12,y+9),label,fill="#f0f1e7")
    thumb=composite(im).resize((w-16,h-38),Image.Resampling.LANCZOS)
    canvas.paste(thumb,(x+8,y+32))

def main():
    meta=json.loads((CAND/"manifest.json").read_text())
    locked=json.loads((ASSET/"control/manifest.json").read_text())
    assert meta["camera_lock_verified"] is False
    assert meta["method"]=="OpenAI hosted image generation (image/reference guided, NOT ControlNet)"
    assert meta["slots"]==[0,16,32,48]
    assert (ASSET/"spec.json").exists()
    source={}
    for slot in meta["slots"]:
        item=meta["candidates"][f"{slot:03d}"]
        assert item["requested_theta_deg"]==slot*5.625
        p=CAND/f"{slot:03d}.png"
        assert p.is_file() and sha(p)==item["sha256"]
        im=Image.open(p);im.load()
        assert im.format=="PNG" and im.mode=="RGB" and im.size==(1254,1254)
        source[slot]=im.copy()
    QA.mkdir(parents=True,exist_ok=True)
    a=Image.new("RGB",(1024,1056),"#162329")
    for i,slot in enumerate(meta["slots"]):
        tile(a,source[slot],(i%2)*512,(i//2)*528,512,528,f"AI CANDIDATE  {slot:03d}  /  {slot*5.625:g} deg")
    a.save(QA/"issue25-openai-four-candidates.jpg",quality=88,optimize=True)
    b=Image.new("RGB",(4*272,2*310),"#162329")
    for col,slot in enumerate(meta["slots"]):
        path=ASSET/locked["frames"][f"{slot:03d}"]["files"]["parts"]
        target=Image.open(path);target.load()
        assert target.mode=="RGBA" and target.size==(512,512)
        tile(b,target,col*272,0,272,310,f"CONTROL {slot:03d}")
        tile(b,source[slot],col*272,310,272,310,f"AI  {slot:03d}  (NOT LOCKED)")
    b.save(QA/"issue25-openai-control-comparison.jpg",quality=88,optimize=True)
    c=Image.new("RGB",(4*290,460),"#162329")
    d=ImageDraw.Draw(c)
    for col,slot in enumerate(meta["slots"]):
        x=col*290+15
        d.text((x,8),f"{slot:03d} · not alpha-transparent",fill="white")
        for row,(size,y) in enumerate(((256,32),(128,315),(64,315))):
            w=source[slot].resize((size,size),Image.Resampling.LANCZOS)
            c.paste(w,(x+(152 if size==64 else 0),y))
    c.save(QA/"issue25-openai-rts-sizes.png",optimize=True)
    print("PASS: FOUR REAL original 1254x1254 OpenAI PNG, fixed slot IDs, no alpha, no art approval")
    print("QA files:",QA/"issue25-openai-four-candidates.jpg",QA/"issue25-openai-control-comparison.jpg",QA/"issue25-openai-rts-sizes.png")
if __name__=="__main__":main()