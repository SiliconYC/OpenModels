# Tiger I, 1943 early-production: orthographic contract

This is an **original, script-derived engineering silhouette**, not a traced/copyrighted drawing and not a fabrication-grade blueprint. Variant: **Tiger I Ausf. E early 1943**, using Tiger 131 as a general reference. This phase deliberately excludes later all-steel road wheels (February 1944 onward), late cupola, Zimmerit textures and mixed-era details.

## Coordinate and projection
Metres; right-handed Three.js-compatible axes: **+X forward**, **+Y up**, **+Z vehicle's right**; origin at hull length midpoint on ground. Turret yaw is about +Y through approximately (0.315, 2.18, 0); barrel bore is parallel +X at Y=2.43, Z=0; gun recoils toward -X. The turret's centre-of-box and yaw-pivot are not necessarily identical in a final model; this phase uses nominal yaw point [0.315,2.18,0] and requires #5 to refine it.

All three SVGs are strictly orthographic with **90 px/m**. Side: look from -Z, horizontal +X, vertical +Y; front: look from +X, horizontal -Z, vertical +Y; top: look from +Y, horizontal +Z, vertical +X. Shared geometry input: `geometry.json`. Generate from repository root:

`python models/vehicles/land/tiger-i/references/render_views.py`

Validate: `python tests/test_tiger_references.py`.

## Control dimensions and confidence

| Property | Selected value | Status |
|---|---:|---|
| Hull length excluding gun | 6.316 m | Published Tiger 131 figure; check precise measurement conventions |
| Overall with gun pointing forward | 8.450 m | Published overall figure; adopted as envelope |
| Width across combat tracks | 3.547 m | The Tank Museum |
| Width including skirts | 3.705 m | Source's nominal skirt envelope |
| Track width | 0.725 m each | The Tank Museum |
| Maximum height | 3.000 m | Published overall approximate |
| Turret ring diameter | 1.830 m | Secondary published spec, needs factory confirmation |
| Road wheels per side | 24, three overlapping rows at 8 stations | The Tank Museum; SVG shows 8 projected stations rather than fake 24 consecutive wheels |
| Turret box, roof and gun pivot | As in geometry.json | **Provisional** envelope for #5 |

## Source audit

1. The Tank Museum, “Two Widths of Track” (2017): https://tankmuseum.org/article/two-widths-track/ — measured width 3547 mm, 725 mm combat tracks, 24 wheels per side, steel wheels not until 1944.
2. Tiger1.info, “Side skirts”: https://tiger1.info/EN/Side-skirts.html — 3705 mm width over skirts, design-survey context.
3. Tiger1.info, “Dimensions of turret”: https://tiger1.info/EN/Turret-dimensions.html — original factory drawing and Bovington survey provenance; confirms asymmetric turret and explains uncertainties. This *schematic* does not reproduce a measured asymmetrical turret contour.
4. Tiger1.info, “Dimensions of hull”: https://tiger1.info/EN/Hull-dimensions.html — hull design measurement, tolerance context.
5. Tiger 131 general vehicle figures: https://en.wikipedia.org/wiki/Tiger_131 — 6.316 m hull / 8.45 m overall and 3.0 m height. These are secondary overview dimensions, not factory proof.

No third-party image, CAD mesh or technical drawing is copied into the repository. Sources are cited as engineering reference only; link destinations retain their own copyright.

## Explicit limits

- Road wheel **24/side** counts physical overlapping disks, not eight visible outer circles. The plan-view cross marks signify axle stations, not individual wheel faces.
- Flat top/front/side contours simplify mantlet, front armour angles, transmission cover, asymmetric turret, treads, suspension and exhaust; dimensions of these unresolved details **must not be treated as surveyed values**.
- Coordinates are independent of hull length-vs-fender measurement ambiguity. #5 should refine turret axis, upper hull and wheel stagger only with new evidence, preserving the common coordinate frame.
