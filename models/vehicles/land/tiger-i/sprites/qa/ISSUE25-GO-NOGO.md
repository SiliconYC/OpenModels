# #25 | Tiger I Controlled AI Probe — 技術查證、權利與阻礙

更新：2026-10-17。**這是未執行 AI 推理的真實工程狀態。** 來源 #23、#24 已合併。嚴禁以灰模、控制 PNG、請求草案或自由文字生圖冒充 ControlNet 的已生成圖片。

## 1. 真正可用的上游能力：資料查證 ≠ 本回合成功推理

| 路線 | 實際 API／能力 | 主要限制 | 權利 |
| --- | --- | --- | --- |
| fal: SDXL ControlNet Union | https://fal.ai/models/fal-ai/sdxl-controlnet-union/image-to-image/api — **image_url 參考底圖，同時 canny_image_url/depth_image_url/segmentation_image_url；各支援 *_preprocess=false**，種子、steps 和 PNG 格式有公開 schema | 必須具備 FAL_KEY、經授權的**單張底圖**、服務實際可用與報價；4 向三組 = 12 次請求，還未嘗試。是否能從三視圖+風格兩份不同參考同時提取身份，不等同於此 endpoint 的單張 image_url。 | 服務頁標示 Commercial use，但需確認服務條款、所用 SDXL 基礎模型及所用聯合 ControlNet 的**各自授權**，並遵守參考素材權利。未作合約級完成判斷。 |
| fal: FLUX.1 dev flux-general | https://fal.ai/models/fal-ai/flux-general/api — 提供參考圖 reference_image_url、IP-Adapter、ControlNetUnion（canny/depth）、LoRA；可規劃更豐富的多條件方案 | ControlNet Union 需明確提供 path 權重及 license；此 endpoint 並非自帶已批准的 Tiger 模型。 | FLUX dev 自託管非商業權重和雲端商業 API **不能混成同一個許可**。需逐模型確認。 |
| Hugging Face Diffusers | https://huggingface.co/docs/diffusers/en/using-diffusers/controlnet 和 https://huggingface.co/docs/diffusers/en/using-diffusers/ip_adapter — 文檔展示 MultiControlNet、IP-Adapter 組合 | 在本回合環境無 CUDA GPU、無可下載權重的網路；本工程不應用普通 GitHub Actions 做大型 GPU 推理。 | SDXL base 1.0 是 OpenRAIL++；ControlNet checkpoint 和 style adapter 亦各自有條款。不能用「開源」籠統代替商用權利。 |

Fal 請求接受 Base64 Data URI／URL；本輪適配器在真正執行時發送經本地 SHA-256 校驗之 PNG 的 data URI，**不要求把控制圖誤發佈成正式 Pages 素材**。

### 16 位深度轉換

#24 原件是固定攝影機可見三角形 z-buffer 的 16-bit PNG，**本輪不覆蓋原件**。若 API 接收 8-bit RGB 深度，採原固定量化範圍從 source uint16 → v >> 8，背景仍 0、全部 4 向固定映射，不做逐幀亮度歸一化。未明確驗證服務端實際對這種深度慣例與亮度尺度的反應。

原有 silhouette 的白色實際分區／輪廓邊界轉 RGB 黑白圖；本工具**沒有**聲稱另行運行 Canny 檢測。分區輸入直接把 stable categorical ID 原色 RGB 映出。黑色背景不是美術透明輸出。

## 2. 實際環境查證與停止原因

- 本回合在執行沙盒測試：沒有 CUDA／nvidia-smi；未發現環境變數 FAL_KEY、REPLICATE_API_TOKEN、HF_TOKEN、STABILITY_API_KEY，**未嘗試猜測任何使用者密鑰**。
- 從容器對 `https://fal.run`、`https://api.replicate.com` 發送普通外連請求，結果均為 DNS resolution 錯誤；**並未發生任何已授權遠端模型呼叫**。
- 尚無經使用者核准的**原創商用美術風格基準單張 PNG**；既有三視圖屬本倉庫幾何示意，不等於商業風格審核通過的輸入。單一參考底圖亦不等於同時輸入三視圖+風格圖。
- 存在供應商端公開 API 定義，不等於已有可呼叫賬戶/商業權利；本回合沒有鎖定 SDXL Union 的真實按張結算價、推理費用或收據，**不得臆測 12 張／64 張成本**。
- 禁止向沒有明確版權的藍圖、商業遊戲原圖或網路圖片發起傳輸。本庫的程序化三視圖是源碼自製，可用作內部控制參考，不代表外部風格圖獲得授權。

## 3. 實際留下的可重現成果

- `tools/sprites/prepare_ai_probe.py`：全量查核 source manifest、SHA 和 camera，實際從 000/016/032/048 的原始 16bit z、RGB part、RGBA edge 控制圖各轉成 **四種服務端輸入**，保存於 `generated/issue25/inputs`；`input-manifest.json` 記錄每張來源與輸出摘要和固定視角。
- `qa/issue25-input-contact-sheet.png`：**僅是實際控制輸入**的比較聯圖，絕非模型候選圖；不作「四方向美術試驗成功」證據。
- `tools/sprites/fal_control_probe.py`：有真實 SDK/HTTP 對應欄位的 API 請求器；預設無網請求、保存 12 條 NOT_EXECUTED 草案。嚴格要求已核定樣圖、API Key、商用條款、逐張計費及總費用上限的明確開關，任何條件缺失直接阻止付費推理。
- 如未來真正請求成功，原圖與 provider request_id、實際 seed、樣圖 SHA、模式與完整 prompt 均保存至 `generated/issue25/candidates/`；**本輪該目錄不存在，因為從未得到 AI 輸出**。
- `tests/test_ai_control_probe.py` 和專用 preflight CI 驗證格式、來源、方向、控制編碼、無混入 approved/export 目錄。

## 4. 四向的預先鎖定對照

- 槽 000、016、032、048 分別對應 0°、90°、180°、270° **車體繞 Y 的偏航**，世界攝影機從頭至尾保持方位 45°、俯角 35°。不得標示四張均是嚴格正側前後視角。
- 三組計畫每槽同一 seed：A `reference_only`（參考圖+文字）；B `reference_edge`（同底圖+真輪廓）；C `reference_edge_depth_parts`（同底圖+輪廓+真深度+分區），僅在服務端確實支援的 schema 下才調用。
- 美術身份鎖定：1943 初期橡膠輪／8.8 cm 長砲雙室制退器、橄欖灰沙色、統一砲塔號 131／相同磨損缺口；絕不採納後期鋼輪。分區語義保留原 6 大類，不能從灰模幻想出未建模的細節。
- 8 向擴展僅在**第一輪四向實際出圖**且經人工及技術初審後才能啟動，不可因本身生成了 64 向幾何而放行。

## 5. Go／No-Go

| 維度 | 判定 | 說明 |
| --- | --- | --- |
| 技術控制 | **未驗證** | 僅可核實 API 有控制參數、本地轉換有效；沒有任何真正推理請求成功 |
| 跨方向一致性 | **未驗證** | 0 幅實際 AI 候選圖，沒有迷彩/編號/幾何的跨向比較 |
| 商業美術品質 | **未驗證** | 0 幅 AI 美術圖；不以控制幾何圖代替 |
| 商用權利 | **未確認** | 服務 Commercial use 宣傳不涵蓋所用所有權重、LoRA、底圖及最終授權 |
| 是否進入 #26 正式 16 向 | **NO-GO** | #25 的真正四向×三組關鍵實驗沒有執行，不因此提前開始 #26 |

**解除阻礙的最低次序**：先獲得可在雲端安全訪問的受控推理帳戶/額度與原創商業風格參考 PNG；確認服務端價格、IP 政策，完成服務側一張輪廓與一張深度/分區真測並留 request_id；再依 000/016/032/048 完整生成 A/B/C 各一張，對照輪廓 IOU、砲管、輪組、號碼與人工美術品質；如果仍一致性不足才探索先繪單張錨圖後用 reference/adapters/局部重繪。**在實際成功前不得宣稱可進 16 向正式製作**。

此處的 No-Go 是對「現在進入正式美術批量生產」的決策，不是斷言 ControlNet 絕不可能做出合格的坦克圖。

## 6. 實際運行的 preflight 驗收補充

- GitHub Actions [#39041211137](https://github.com/SiliconYC/OpenModels/actions/runs/39041211137)：`PREPARED ONLY: 4 headings × 4 images`、`PREFLIGHT ONLY: no remote request`；四個專用單元測試 **4/4 通過**，全部 PNG 為真實 `512×512`、原始來源 SHA 校對。
- 該作業在安全布林檢查中報告 **`Fal API credential configured for this workflow: false`**，表示此倉庫 CI 並無已接通的受控推理憑證（沒有輸出任何 secret 值）。結合 Agent 沙盒無 FAL_KEY、無 CUDA、外連 DNS 失敗，已確認此次會話無法執行真正付費受控模型。
- 遠端分支實際追加 `generated/issue25/inputs/{edge_rgb,depth_rgb,parts_rgb,subject_mask}/` 的 000／016／032／048 PNG，共 **16 份控制輸入**，並有 `generated/issue25/input-manifest.json` 與 `qa/issue25-input-contact-sheet.png`。這些只有**幾何輸入**，不是四張 AI 生成候選。`request-preflight.json` 中 **12 個 planned record 全部 NOT_EXECUTED**，無 request_id 或生成 PNG。
- 聯圖深度 RGB 圖的亮度範圍偏窄，原因是按整組**固定相機 near/far** 映射後分布集中（而非假深度）。進行真正模型試驗時可追加 **對全 64 幀統一求一組 global min/max 的深度增強版本**做 A/B 比較；不得逐幀重新分布而破壞跨向尺度，也不得覆蓋原 16-bit 來源。
- 特別注意：本倉庫的分區色彩為自定義六類 ID，外部 SDXL 供應商的 segmentation 訓練色盤**未核實是否相容**。端點參數存在僅證明能提交分區圖片，**不代表模型知道這六種顏色代表砲塔／砲身等語義**。實際第一輪須先查證模型支援的標籤／色盤映射，再比對「輪廓+深度」與加上分區是否真正增益。
- 另外，指定單一 `image_url` 做圖生圖與同時獨立引入**三視圖和商業風格基準**不是一回事；端點能接受一張參考圖並不能證明身份保持。日後若要採用多參考，須真實確認 IP-Adapter、圖集編碼或其他可重現方法，不得假定三視圖自動被理解。

**停止結論仍為 NO-GO**：四方向真人工美術審核、服務端控制追隨、跨角度身份一致性均不能在不存在生成結果的情況下做成功判定；不能開始 #26。
