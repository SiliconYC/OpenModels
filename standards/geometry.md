# OpenModels geometric & web asset contract (v1)

- Units: **metres**. Right-handed, Three.js / glTF compatible frame: +X forward, +Y up, +Z vehicle right.
- Model origin (vehicles): ground beneath longitudinal hull midpoint, not floating at center of bounding box. Test cubes may be centered at (0,0,0).
- Geometry: real glTF 2.0 mesh with indexed triangles (mode 4); position attributes in metres, per-face UV in [0,1], normals and actual material references. Prefer KHR_materials_unlit where art direction needs painted light.
- Rigid actors: separate named glTF nodes for hull, turret, gun, wheels; turret pivot around +Y, gun recoil along local -X. No fake vertices and no screenshot-as-model.
- Metadata: `docs/models.json` provides stable `id`, `title`, `file` relative to **docs/**; do not include origin-absolute paths. `docs/?model=<id>` is the permalink.
- Real model verification: `python tools/mesh_pipeline.py inspect <file.glb>`. Fail on corrupt header/chunks, nonfinite positions, invalid UV range or missing indexed triangle mesh. Inspectors do not substitute for browser visual verification.
- `docs/assets/test-cube.glb` is an engineering smoke test only, not a Tiger model or visual benchmark.
- Never publish a new asset under a production-looking ID unless its actual GLB and source generator are present, and its stage is stated accurately.
