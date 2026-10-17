# Tiger I 1943（#23）——控制幾何審計

**目標不是高精度 3D 成品**：僅為 AI 多向繪製提供真正幾何投影、深度和穩定的部件遮罩。保留原有 `source/build_refined.py` 與 Pages GLB 完全不變。

## 工程來源及信度

- [英國坦克博物館：Tiger Wheels](https://tankmuseum.org/article/tiger-wheels/)：1943 原始輪為 800 mm 橡膠輪，每側 24 枚／8 個軸站×3 層。**1944 年才引進鋼輪**，不可混入。
- [Tiger1.info：Road Wheel Spacing](https://tiger1.info/EN/RoadWheelSpacing.html)：原始軸站距約 515 mm；本控制模型沿用 #19 的 0.515 m 交錯層位。
- [Tiger1.info：Hull dimensions](https://tiger1.info/EN/Hull-dimensions.html)：車體接近垂直的前裝甲、側裙板、履帶外輪廓。
- [Tiger1.info：Turret dimensions](https://tiger1.info/EN/Turret-dimensions.html)：砲塔為前窄後弧的不對稱輪廓，非方盒；仍有實物細節測量的不確定性。
- [坦克博物館：Tiger 131 底盤復原](https://tankmuseum.org/article/tiger-131-hull-suspension-part-ii)：早期底盤懸吊配置。
- 既有幾何三視圖：`references/geometry.json`、`front.svg`、`left.svg`、`top.svg`，本 Issue **未複製外部圖紙**。

核對的尺寸：6.316 m 無砲車體長、8.45 m 含砲全長（不同資料測量約定會有差異）、0.725 m 單側作戰履帶寬、3.547 m 兩側履帶寬、裙板最寬 3.705 m、約 3.00 m 車頂高度。這些數據已存在 `geometry.json`；未把簡化部位當作新測得數據。

## 控制模型

從原 #19 的 Python 幾何生成器提取真正車體裝甲、下車體、圓弧砲塔、砲盾、同軸砲身／雙段制退器、履帶環、裙板、偏置車長塔、8 軸站×3 層／側交錯橡膠輪。以簡單圓柱取代每枚輪的印模，去掉履帶鞋、格柵和裝甲細節，保留幾何遮擋關係。

源：`sprites/build_control.py`；實物：`sprites/control/tiger-i-control.glb` 和 `tiger-i-control.npz`（頂點、三角形、部件類型）；審計：`sprites/control/model-report.json`。

座標：**+X 車頭、+Y 向上、+Z 車右；地面原點 (0,0,0)，繞 +Y 轉向**。攝影機統一正交，俯角 35° 初步鎖定；4 向與斜向基線由同一組真實網格正交渲染（`qa/views/`）檢查。**正式 #24 可在 spec 中凍結相機、比例與 pivot**。

未驗證：砲盾鑄造非對稱量測曲面、制退器氣孔／內腔細節、交錯輪凹面與齒形、履帶節、裙板外緣每節尺度、實車焊線、地面陰影。這些細節可能影響 AI 的近景準確度，但目前不應繼續細化為商業 3D 資產。

重建：

`python -m pip install numpy trimesh Pillow`

`python models/vehicles/land/tiger-i/sprites/build_control.py`

`python tools/sprites/preview_control.py`

本階段的正交截圖是**真實網格 rasterization**，不是可用於商業遊戲的美術圖，也不是 ControlNet 驗證。未清楚判讀的細節不宣稱通過。
