# Issue #24：64 方向真實幾何控制圖（非正式美術）

**此階段交付：固定相機真正正交投影與 64×3 張真實單幀 PNG，可直接交給 #25 Agent 輸入受控 AI 實驗。** 不修改既有 #32 Pages 播放器，亦不把控制條件偽裝成已通過的 AI 美術。

資料與投影契約：**唯一規格是 spec.json**。引用 #23 已提交的 control/tiger-i-control.npz 三角形，+X 車頭、+Y 上、+Z 車右，模型繞全車地面原點 (0,0,0) 的 +Y 軸旋轉。攝影機世界方位 45°、仰角 35°，**不隨車輛轉動**。固定 512×512 畫布、47 px/m、pivot [256,354]，不進行逐幀裁切或置中。全局 64 槽從 000.png 到 063.png，i 槽角度 = 5.625° × i；16 向每 4 槽、32 向每 2 槽。

真實遮擋由 CPU 三角形光柵化的 **Z-buffer** 完成，每個像素依相機 Z 最近三角形計算 ID 和深度。深度使用原始 16 位 PNG，背景 0，前景將固定 [-12,12] 米視線深度線性編碼成 [1,65535]，越近越亮。可顯示用灰階縮圖不能替代 16 位原始深度，亦不能假裝是物體貼圖亮度。

每個槽位的正式控制條件由三份檔案構成：

- control/frames/silhouette/000.png 等：RGBA 輪廓、可見部件邊界。
- control/frames/depth/000.png 等：16 位真正幾何深度。
- control/frames/parts/000.png 等：RGBA 部件分區（1 車體、2 砲塔、3 砲身、4 履帶、5 輪組、6 附件；0 背景）。

單幀檔名不因檔位重編。control/manifest.json 記錄全部方向、來源雜湊、每張圖雜湊、幀號與相機參數；**它不是** Pages 正式美術的 export/manifest.json。

## 重現與驗收

從倉庫根目錄：

1. python -m pip install numpy trimesh Pillow
2. python models/vehicles/land/tiger-i/sprites/build_control.py
3. python tools/sprites/generate_controls.py generate --spec models/vehicles/land/tiger-i/sprites/spec.json --level 64
4. python tools/sprites/generate_controls.py verify --spec models/vehicles/land/tiger-i/sprites/spec.json --level 64
5. python tools/sprites/generate_controls.py sheet --spec models/vehicles/land/tiger-i/sprites/spec.json --channel parts --tile 256 --name canonical-16-parts

亦可將 --level 設 16、32，或以 --slots 指定任意 16 個合法、不可重複的全局方向，按行優先拼出 4×4；不改變原始檔位編號。已包含 canonical-16-silhouette、canonical-16-depth、canonical-16-parts，以及 arbitrary-16-parts 等完整圖集與 JSON 對映。注意圖集中的深度僅供視覺審查，單張原始深度維持 16bit。

**客觀驗收**：64×3 檔 PNG 全部可解碼，尺寸和 alpha／深度背景一致，64 個輪廓雜湊互異，16/32/64 真實子集一致，每幀有可解釋非均勻相機深度、相同攝影機和 pivot。真實前、後、左右／斜向由 #23 QA 和本次 64 向圖集判讀。

**限制**：#23 控制模型特意省略準確鑄造砲盾曲率、履帶逐節、輪子凹面與制退器內部孔洞；#24 不可能從不存在的幾何控制出這些細節。進入 #25 前僅代表幾何控制條件已準備好，不代表實際多條件 AI ControlNet 推理或商業品質已通過。

## 實際提交後的測量（#24）

64 槽各三張控制圖已由 PR 的生成器實際重建：一共 **192 張 512×512 PNG**，另有 4 份 4×4 PNG 圖集及 JSON 索引。確認 0 號槽 = 0°，63 號槽 = 354.375°；輪廓幀 SHA 不重複、各槽遮擋標籤與 16bit 深度對齊，所有 16／32 子檔位因完整包含於 64 檔而同樣標示可用。**正式美術 PNG 仍為零。**

技術狀態：就可交付 AI 控制輸入而言已準備好進入 #25；就證明 AI 實際遵循控制、跨角度細節正確而言未驗證，須由 #25 做真模型推理小樣。機械結構仍欠精確的履帶鞋、車輪印模、砲盾不對稱鑄造曲面及制退器穿孔，不可由控制圖自行假設存在。
