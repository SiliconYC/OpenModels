# Tiger I 1943 early production — reference audit (#19)

Only original procedural vertices/triangles are included in the repository. The linked third-party pictures, plans and museum photos are not embedded, downloaded or relicensed.

| Source | Checked geometric constraint | Treatment |
| --- | --- | --- |
| [The Tank Museum: Two Widths of Track](https://tankmuseum.org/article/two-widths-track/) | 725 mm combat tracks; 24 overlapping road wheels/side; wide overall width 3547 mm | 0.725 m belt, 8 axles × 3 real wheel meshes per side |
| [Tiger1.info: RoadWheelSpacing](https://tiger1.info/EN/RoadWheelSpacing.html) | 800 mm rubber rim wheels, interleaving, original 515 mm spacing | 0.804 m diameter; 0.515 m station centers; alternating depth layers (approximate offsets) |
| [Tiger1.info: Hull dimensions](https://tiger1.info/EN/Hull-dimensions.html) | hull mostly slab-sided vertical with projecting sponsons and angled lower bow | separate side sponsons, nose plate, lower tub and rear plate |
| [Tiger1.info: turret dimensions](https://tiger1.info/EN/Turret-dimensions.html) | curved rear turret, asymmetrical forward mantlet | separate curved-contour horseshoe turret, off-centred mantlet |
| [Tiger1.info: hull crew hatches](https://tiger1.info/EN/Hull-crew-hatches.html) | two 560 mm hatches on hull roof, offset ±900 mm | two 570 mm real discs, periscope shrouds |
| [The Tank Museum: Tiger 131 turret restoration](https://tankmuseum.org/article/tiger-131-restoration-turret-part-iii) | turret ring, mantlet, commander cupola etc | preserved rigid Turret and separately recoiling Barrel, visible ring and raised cupola |
| [British 1943 preliminary inspection](https://www.military-references.com/wp-content/uploads/books/tanks/germany/panzer_vi_tiger_ausf_h1/Preliminary_Report_No_19_Pz_Kw_VI_Tiger_1943.pdf) | 8.8 cm gun and dual-baffle muzzle brake | two separate 3D baffles and structural bridge pieces, replacing block at muzzle |

## Interpretation / limitations

- This is a geometry-focused *visual re-model*, not a dimensional manufacturing CAD reconstruction. Exact weld profiles, sprocket pitch, suspension arms, precise wheel stamping and exhaust guards remain approximations.
- Wheels are now 24 per side in real geometry, instead of earlier 8/side. Tread shoes use 100 procedural pieces per side for readable detail, rather than claiming an exact historical count.
- The original #5 grey GLB and #6 UV demo remain in the gallery as regression baselines. New sources are `source/build_refined.py` and `source/build_refined_uv.py`.
- No textures/meshes were copied from external sources. Refined checker is an actual editable atlas, not a production camouflage texture.

Source verification: 2026-10-17.