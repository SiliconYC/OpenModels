#!/usr/bin/env python3
"""Pure-stdlib contract test: python tests/test_tiger_references.py"""
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "models/vehicles/land/tiger-i/references"
d = json.loads((R/"geometry.json").read_text())
p, dims, sus = d["parts"],d["dimensions"],d["suspension"]
def approx(a,b): assert abs(a-b)<1e-8,(a,b)
approx(p["hull"]["x"][1]-p["hull"]["x"][0],dims["hull_length"])
approx(p["gun"]["muzzle_x"]-p["hull"]["x"][0],dims["overall_length_gun_forward"])
approx(p["right_track"]["z"][1]-p["left_track"]["z"][0],dims["operational_track_overall_width"])
approx(p["left_track"]["z"][1]-p["left_track"]["z"][0],dims["operational_track_width"])
approx(p["right_skirt"]["z"][1]-p["left_skirt"]["z"][0],dims["overall_width_with_skirts"])
approx(p["cupola"]["top_y"],dims["height_to_cupola"])
assert len(sus["road_wheel_x"])==dims["road_wheel_stations"]
assert len(sus["road_wheel_x"])*sus["layers_per_station"]==dims["road_wheels_per_side"]
assert d["axes"]["up"]=="+Y" and d["axes"]["forward"]=="+X"
subprocess.run([sys.executable,str(R/"render_views.py")],check=True)
for view in ("left","front","top"):
    root=ET.parse(R/f"{view}.svg").getroot()
    assert root.attrib["data-projection"]==view
    assert root.attrib["data-scale-px-per-m"]=="90"
    components={node.get("data-part") for node in root.iter() if node.get("data-part")}
    assert "hull" in components and "turret" in components
    assert ("gun" if view != "front" else "gun-muzzle") in components
print("PASS: axes, three aligned orthographic SVGs, hull/track/gun envelopes, 8x3 wheel stations")
