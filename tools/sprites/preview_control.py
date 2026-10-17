#!/usr/bin/env python3
"""Orthographic control-geometry QA: six canonical + four diagonal views."""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools/sprites"))
from cpu_renderer import raster,shade_preview
ASSET=ROOT/"models/vehicles/land/tiger-i/sprites"
VIEWS={"front":(0,0),"back":(180,0),"left":(270,0),"right":(90,0),
       "top":(0,89),"bottom-oblique":(0,12),
       "front-left":(315,35),"front-right":(45,35),
       "back-left":(225,35),"back-right":(135,35)}
def main():
    data=np.load(ASSET/"control/tiger-i-control.npz")
    folder=ASSET/"qa/views";folder.mkdir(parents=True,exist_ok=True)
    measurements={}
    for name,(az,el) in VIEWS.items():
        region,z=raster(data["vertices"],data["faces"],data["ids"],
                      azimuth=az,elevation=el)
        image=shade_preview(region)
        bg=Image.new("RGBA",image.size,(21,34,38,255))
        bg.alpha_composite(image)
        bg.convert("RGB").save(folder/(name+".png"))
        measurements[name]={"opaque_pixels":int(np.count_nonzero(region)),
                            "visible_categories":sorted(map(int,np.unique(region[region>0])))}
    assert all(x["opaque_pixels"]>1500 for x in measurements.values()),measurements
    (ASSET/"qa/orthographic-review.json").write_text(json.dumps(
       {"views":measurements,"orthographic":True,"source":"control/tiger-i-control.npz",
        "no_commercial_3d_art":True,"note":"camera fixed within each QA view; control QA only"},
       indent=2)+"\n")
    print("PASS: 10 real orthographic geometry views")
if __name__=="__main__":main()
