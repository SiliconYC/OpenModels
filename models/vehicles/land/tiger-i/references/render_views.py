#!/usr/bin/env python3
"""Orthographic Tiger I reference SVGs. Standard library only.

Usage: python models/vehicles/land/tiger-i/references/render_views.py
All view geometry is projected from the same geometry.json. Never hand-edit outputs.
"""
from __future__ import annotations
import json
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / "geometry.json").read_text(encoding="utf-8"))
P = D["parts"]
S = D["suspension"]
K = 90.0  # pixels per metre for every projection, no perspective


def point(view, x, y, z):
    if view == "left":
        return (360 + K * x, 386 - K * y)
    if view == "front":
        return (480 - K * z, 386 - K * y)
    if view == "top":
        return (480 + K * z, 590 - K * x)
    raise ValueError(view)


def rect(view, a, b, attrs, component):
    if view == "left":
        q = [point(view, a[0], a[1], 0), point(view, b[0], b[1], 0)]
    elif view == "front":
        q = [point(view, 0, a[1], a[2]), point(view, 0, b[1], b[2])]
    else:
        q = [point(view, a[0], 0, a[2]), point(view, b[0], 0, b[2])]
    x, y = min(p[0] for p in q), min(p[1] for p in q)
    w, h = abs(q[0][0] - q[1][0]), abs(q[0][1] - q[1][1])
    return f'<rect data-part="{component}" x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" {attrs}/>'


def box(view, key, attrs):
    b = P[key]
    return rect(view, [b["x"][0], b["y"][0], b["z"][0]],
                [b["x"][1], b["y"][1], b["z"][1]], attrs, key)


def line(x1, y1, x2, y2, kind="axis"):
    return f'<path class="{kind}" d="M{x1:.2f},{y1:.2f} L{x2:.2f},{y2:.2f}"/>'


def circle(x, y, r, attrs, part):
    return f'<circle data-part="{part}" cx="{x:.3f}" cy="{y:.3f}" r="{r:.3f}" {attrs}/>'


def draw(view):
    if view not in ("left", "front", "top"):
        raise ValueError(view)
    width, height = (1190, 510) if view == "left" else ((960, 510) if view == "front" else (960, 980))
    name = {"left": "LEFT / PORT", "front": "FRONT", "top": "TOP / PLAN"}[view]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'data-scale-px-per-m="{K:g}" data-projection="{view}" role="img" '
        f'aria-label="Tiger I {view} engineering reference">',
        '<style>svg{background:#f5f3ec}text{font-family:monospace;fill:#353d3b}'
        '.title{font-size:22px;font-weight:bold}.note{font-size:13px}'
        '.part{fill:#d5d7ce;stroke:#273b3b;stroke-width:2;stroke-linejoin:round}'
        '.steel{fill:#adb9b2;stroke:#273b3b;stroke-width:2}'
        '.track{fill:#59665f;stroke:#273b3b;stroke-width:3}'
        '.wheel{fill:#d6d5bd;stroke:#293e3b;stroke-width:2}'
        '.axis{fill:none;stroke:#b05c38;stroke-dasharray:7 6;stroke-width:1.5}'
        '.dim{fill:none;stroke:#687977;stroke-width:1;stroke-dasharray:2 4}</style>',
        f'<text class="title" x="42" y="48">TIGER I · EARLY 1943 / {name}</text>',
        '<text class="note" x="42" y="73">SCHEMATIC · 90 px/m · 1:1 COMMON SCALE · METRES</text>',
    ]
    if view == "left":
        out.extend((box(view, "left_track", 'rx="46.8" class="track"'),
                    box(view, "hull", 'class="part"'),
                    box(view, "left_skirt", 'class="steel"')))
        for i, x in enumerate(S["road_wheel_x"]):
            sx, sy = point(view, x, S["wheel_axis_y"], 0)
            out.append(circle(sx, sy, K * S["wheel_radius"], 'class="wheel"', f"wheel-station-{i + 1}"))
            out.append(circle(sx, sy, K * .10, 'class="steel"', "wheel-hub"))
        for key in ("idler_x", "drive_sprocket_x"):
            sx, sy = point(view, S[key], S["wheel_axis_y"], 0)
            out.append(circle(sx, sy, K * S["end_radius"], 'class="steel"', key))
        out.extend((box(view, "turret", 'rx="25" class="part"'),
                    box(view, "gun", 'class="steel"') if "x" in P["gun"] else
                    rect(view, [P["gun"]["breech_x"],P["gun"]["axis_y"]-P["gun"]["outer_radius"],0],
                         [P["gun"]["muzzle_x"],P["gun"]["axis_y"]+P["gun"]["outer_radius"],0],
                         'class="steel"', "gun"),
                    rect(view, [P["cupola"]["centre"][0]-.27, P["turret"]["y"][1], P["cupola"]["centre"][2]-.27],
                         [P["cupola"]["centre"][0]+.27, P["cupola"]["top_y"], P["cupola"]["centre"][2]+.27],
                         'rx="5" class="steel"', "cupola"),
                    line(*point(view,0,0,0),*point(view,0,3.2,0))))
    elif view == "front":
        out.extend((box(view, "left_track", 'class="track"'),
                    box(view, "right_track", 'class="track"'),
                    box(view, "hull", 'class="part"'),
                    box(view, "left_skirt", 'class="steel"'),
                    box(view, "right_skirt", 'class="steel"'),
                    box(view, "turret", 'class="part"')))
        gx, gy = point(view,0,P["gun"]["axis_y"],P["gun"]["axis_z"])
        out.append(circle(gx,gy,K * P["gun"]["outer_radius"],'class="steel"',"gun-muzzle"))
        out.append(circle(gx,gy,K * 0.046,'class="track"',"gun-bore"))
        out.append(box(view,"turret",'fill="none" stroke="#273b3b" stroke-dasharray="5 6"'))
        out.append(rect(view, [0, P["turret"]["y"][1], P["cupola"]["centre"][2]-.27],
                         [0, P["cupola"]["top_y"], P["cupola"]["centre"][2]+.27],
                         'rx="5" class="steel"', "cupola"))
        out.append(line(*point(view,0,0,0),*point(view,0,3.2,0)))
    else:
        out.extend((box(view, "left_track", 'class="track"'),
                    box(view, "right_track", 'class="track"'),
                    box(view, "hull", 'class="part"'),
                    box(view, "left_skirt", 'class="steel"'),
                    box(view, "right_skirt", 'class="steel"'),
                    box(view, "turret", 'rx="22" class="part"')))
        g=P["gun"]
        out.append(rect(view,[g["breech_x"],0,-g["outer_radius"]],
                        [g["muzzle_x"],0,g["outer_radius"]], 'class="steel"',"gun"))
        cx,cy=point(view,P["cupola"]["centre"][0],0,P["cupola"]["centre"][2])
        out.append(circle(cx,cy,K*P["cupola"]["radius"],'class="steel"',"cupola"))
        for n,x in enumerate(S["road_wheel_x"]):
            for z in (-1.411,1.411):
                sx,sy=point(view,x,0,z)
                out.append(line(sx-27,sy,sx+27,sy,"dim"))
        out.append(line(*point(view,-3.158,0,0),*point(view,5.292,0,0)))
    out += [f'<text class="note" x="42" y="{height-40}">X forward · Y up · Z right / centre (0,0,0) = hull midpoint on ground</text>',
            f'<text class="note" x="42" y="{height-19}">Illustrative envelopes are not manufacturing-grade contours; see geometry.json &amp; NOTES.md</text>',
            '</svg>']
    return "\n".join(out)+"\n"


def main():
    for name in ("front","left","top"):
        (HERE / f"{name}.svg").write_text(draw(name),encoding="utf-8")
    print("Generated front.svg, left.svg, top.svg from geometry.json")


if __name__ == "__main__":
    main()
