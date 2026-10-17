# GitHub Pages — OpenModels 双入口静态展厅

静态发布源 **`dev:/docs`**，正式 URL：`https://siliconyc.github.io/OpenModels/`。无后台服务、桌面建模或本地编译依赖。

> **当前是原有 3D 展厅**，新的双入口首页和 2D 播放器由独立 Pages 基础设施 Issue 实施。在真正合并部署并实测前，以下的新路径仅为目标，不得虚报可用。

## 路由与产品定位

- `/OpenModels/`：双入口门户；**多方向图／伪 3D（首要生产路线）**与**历史传统 3D（保留）**。
- `/OpenModels/sprites.html`：通用 N 方向 PNG 浏览器，不依赖精细 3D 网格或 Three.js。
- `/OpenModels/3d.html`：保留当前 Three.js 0.168.0 GLTFLoader + OrbitControls 的真实 GLB 互动功能，原模型/材质/线框、正交与透视、炮塔和炮管动作不可回归。
- 老的 `/OpenModels/?model=tiger-i-uv` 直达链接应兼容跳转到 3D，不能默认为伪 3D。
- 新 PNG 深链形如 `/OpenModels/sprites.html?asset=tiger-i&variant=integrated&level=16&heading=0`；参数只能从可发布目录白名单中选取，不能输入任意 URL。

## N 方向素材通用契约

**权威设计**：[../standards/sprite-viewer-architecture.md](../standards/sprite-viewer-architecture.md)；生产规范：[../standards/n-direction-sprites.md](../standards/n-direction-sprites.md)。

- 一个 `docs/sprites-catalog.json` 资产目录 + 每个资产一个 `manifest.json` + 通用播放器，**不写车型专属页面**。
- 生产源位于 `models/.../sprites/`，但 **Pages 仅发布 `docs/`**：脚本需镜像真实批准的 `export/manifest.json` 和 PNG 到 `docs/assets/sprites/<asset-id>/<variant>/`。
- 同一 64 槽 `000.png…063.png`，16 方向取每4帧、32取每2帧、64取全部；只启用已经完整发布的档位。
- 固定相机、画布、地面 pivot；直接替换 RGBA PNG，支持旋转、触控、透明底检查与 64／128／256 像素 RTS 观看。
- **基础设施先于正式 AI 内容**，应以明确标识的程序化测试 PNG 验证；不要把测试夹具、3D 模型渲染或拼图冒充正式的虎式坦克 N 方向成品。

## 发布验收

检查真正的 Pages 公网地址、HTTP 200、双入口跳转、旧 `?model=` 兼容、3D 正交／透视与 WebGL 互动、2D fixture PNG 真实透明与方向播放/帧索引、手机触控与关键可用性。CI 应精简、按最新提交验收，记录对应 SHA、实际截图和失败项。

原 3D 立方体检查模型为真实 12 三角面带纹理 GLB，不是虎式坦克，也不是伪 3D 方向图；应当在保留区继续可用。
