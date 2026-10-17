# GitHub Pages — 双入口与 PNG 播放器（Issue #32）

首选发布源：**`dev:/docs`**；历史 Pages 仍可能实际以 `dev:/root` 发布：根目录提供双入口首页及 `sprites.html`、`3d.html` 兼容跳转，两个配置都能使用。公开网站：<https://siliconyc.github.io/OpenModels/>。

- **`/`**：双入口首页。主入口为多方向图／伪 3D，次入口为保留的传统 3D。
- **`/sprites.html`**：统一 Canvas 2D RGBA 方向播放器，纯 2D，无 Three.js。支持 16／32／64 已完整档位、固定锚点、透明棋盘、64／128／256 像素与鼠标／触控。
- **`/3d.html`**：保留 GLTFLoader、OrbitControls、真正正交／透视、六视向、材质／灰模／线框、炮塔与炮管控制。
- **`/?model=tiger-i-uv`**：旧深链自动进入 `3d.html?model=tiger-i-uv`；其他旧模型 ID 保留；`/docs/?model=...` 提供兼容重定向。
- **`/sprites.html?asset=fixture-compass&variant=integrated&level=64&heading=0`**：fixture 深链。参数通过目录/manifest 白名单解析，不拼用户路径。

## 数据源、发布与校验

`tools/sprites/assets.json` 是**发布目录配置**。每项需有唯一 ID、variant、发布状态、展示名；真实发布项提供源 `export` 目录。正式资产将使用 `models/.../sprites/export/`；测试夹具仅位于 `tests/fixtures/sprites/`。

`tools/sprites/publish.mjs` 会校验 manifest、完整档位、000–063 全局槽号、RGBA 解码、alpha、CRC、路径与源文件，然后**按字节**复制到 `docs/assets/sprites/<asset-id>/<variant>/`，生成 `docs/sprites-catalog.json`。镜像检查对所有 PNG 校验 SHA-256，不允许手改发布副本。

从仓库根目录运行：

```sh
node tools/sprites/generate_fixture.mjs --check
node tools/sprites/publish.mjs --check
node --test tests/test_sprites.mjs
```

重新生成 fixture 用 `node tools/sprites/generate_fixture.mjs`，然后运行 `node tools/sprites/publish.mjs` 发布。发布源 manifest 和 docs manifest 相同；不要手动修改 docs 镜像。

**fixture-compass** 是纯程序生成、64 槽方向不对称图案的真实 RGBA PNG，画布 96×96、统一 pivot [48,56]。完整 16/32/64 档位均可测试。**它不是 Tiger I、也不是正式美术**。正式虎式资产在目录标记为 planned，尚不可播放。

## 验收

`tests/test_sprites.mjs` 验证目录、64 全局槽、真实文件和可重建性；`tests/acceptance-sprites.mjs` 在 Chromium 验证桌面／移动首页、真实 PNG 播放、切档、透明背景、方向拖动与触控、坏帧反馈、旧 3D GLB、正交／透视及深链。PR 浏览器测试使用相同的 `/OpenModels/` 路径本地部署；合并 `dev` 后 `pages-smoke.yml` 等待 Pages 真正更新并对公网进行相同浏览器验收，保存截图。

架构规范：[../standards/sprite-viewer-architecture.md](../standards/sprite-viewer-architecture.md)。**基础设施可验收不等于正式 AI 美术可验收**。
