# Tiger I grey model / Issue #5

Builder: `python models/vehicles/land/tiger-i/source/build.py`.

- Deterministic original procedural mesh only; Python 3.12 / numpy / trimesh, fully headless. No Blender, Unity, images or purchased meshes.
- Coordinate contract and variant: `../references/geometry.json`, early-1943 Tiger I Ausf. E. Centre origin at ground beneath mid hull length; +X ahead / +Y upward / +Z right.
- Export paths: `../export/tiger-i-grey.glb` (primary), `../../../../../docs/assets/tiger-i-grey.glb` (web copy), and `../export/mesh-report.json`. The byte-identical web copy is for static Pages only.
- Rigid glTF scene graph `World → Hull → Turret → Barrel`. Yaw turret about hull (.315,2.18,0); barrel local frame pivot from turret (1.335,.25,0). A viewer button rotates Turret in 22.5° steps or moves Barrel -0.22 m along its own +X axis (recoil along -X).
- The model prioritizes RTS small-scale silhouette over interior details. **Eight outer visible road-wheel stations per side**, simplified tracks, no functional tread linkage. 24 overlapping real Tiger wheels per side remain a documented historical note, not inaccurately claimed as complete mesh.
- This is an intermediate *grey model*, no UV painting / finished texture or manufacturing-grade armour details. Commercial finish belongs to later issues, especially #6.
- Validation: `python -m unittest discover -s tests -p 'test_*.py'`; the build itself reimports exported GLB as a true trimesh scene, validates named rigid nodes, dimensions and the target triangle budget.
- The generated mesh-report stores **measured** triangle and vertex counts, bounds, node names and per-mesh data. Never hand-invent these numbers.
- Online release URL (only after Pages deploy succeeds): `https://siliconyc.github.io/OpenModels/docs/?model=tiger-i-grey`, test both actual rendering and independent turret/recoil controls.

## Issue #6: genuine paintable UV and test texture

Run from repository root: `python models/vehicles/land/tiger-i/source/build_uv.py` (Python 3.12, numpy, trimesh, Pillow). This rebuilds the **same 1,396 actual triangles** and node hierarchy, but splits their UV seam corners to 4,188 vertices and embeds the image into a second GLB.

- Input mesh geometry/hierarchy: `source/build.py` (retained and not replaced).
- Paintable RGBA contour template: `../textures/tiger-i-uv-template.png`.
- Rendered checker/part/face-orientation atlas: `../textures/tiger-i-uv-checker.png`.
- Coordinate reference: `../textures/uv-layout.json`; 16 separate paintable part families with six charts each (+X/-X/+Y/-Y/+Z/-Z). Side panels use opposite U directions on left/right to avoid mirrored markings.
- Real textured model and web copy: `../export/tiger-i-uv.glb`, `../../../../../docs/assets/tiger-i-uv.glb`; actual report `../export/uv-report.json`.
- GLB atlas is embedded, not an external URL. Road-wheel instances reuse chart areas; modifying one paints them all by design. Seam vertex duplication is expected; triangle count is unchanged.
- This is a UV **test asset**, not final production livery; artistic texture quality belongs to Issue #7. For continuous production UV islands, improve the generator and regenerate the GLB and template together.
- Pages URL: `https://siliconyc.github.io/OpenModels/?model=tiger-i-uv` after `dev` deployment.
