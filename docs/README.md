# GitHub Pages — OpenModels model viewer

Static website source: `dev:/docs`. Visit `https://siliconyc.github.io/OpenModels/?model=test-cube` **only after** Pages has actually been enabled and deployed. Until then this is a target URL, not an acceptance claim.

- Import maps pin Three.js **0.168.0** and OrbitControls + GLTFLoader to the same CDN version. Online access to jsDelivr is required; site has no local build or server.
- Click/touch orbit, right click/two fingers pan, wheel/pinch zoom; orthographic front/left/top/oblique, reset, grey, original textured and real wireframe.
- `models.json` contains the only permitted selectable IDs: a query string never becomes an arbitrary remote URL.
- `file` paths are relative to `docs/`, ensuring repository GitHub Pages subpath support.
- The checkerboard test GLB is a real indexed 12-triangle cube, 24 vertices, embedded PNG UV texture, `KHR_materials_unlit`. **It is not a Tiger model**.
- Build `python tools/mesh_pipeline.py generate` and validate `python -m unittest discover -s tests`.
- To publish: repository Settings → Pages → Build and deployment → **Deploy from a branch** → **dev /docs** → Save. This is an administrator action, *not* automatic through content pushes.
- Production acceptance must additionally verify published HTTP 200 for both `/OpenModels/` and `/OpenModels/assets/test-cube.glb`, see GLB rendered in WebGL, and manually test all pointer and UI controls on actual mobile/desktop browsers.
