---
name: record-production-feature
description: Turn one verified product feature into one focused GIF or video, defaulting to production or the explicitly requested preview/build. Use for feature-to-GIF requests, release demo assets, one-feature screen recordings, or 8-second email GIFs. Check tools first, prefer verified recordings, preserve immutable originals/model provenance, inspect delivered frames and playback, and deliver a traceable local/private package. Publish only when requested; never send a broadcast by default.
---

# Record Production Feature

把一个可核实的用户功能，变成一份可追溯的录制素材包。默认核实 production；用户明确要求 beta/PR/preview/Working Alpha 时按该目标核实并标明，不能冒充生产上线。已有明确手动素材任务可直接进入；release 入口的人工 feature IDs 就是范围，不再要求第二次录制许可。显式 plan-only 只准备计划。

默认保留完整 GT 原片，交付完整 MP4 与约 8 秒 GIF；按用户要求只交一种格式也有效。默认在持久工作区交付本地文件，或使用用户指定且已有权限的私有目录。**公开发布、提交代码、建 PR、改分享权限和 bot 消息都不是录制的默认前提。** 用户已明确要求其中某项时，在已有授权范围内完成，不重复索取许可。

先检查工具与访问，再查找匹配的已有素材。默认 pure-screen：不加讲解字幕、发布角标、装饰 callout、旁白、音乐或转场，保留原生应用文字、字幕功能和普通鼠标。章节写 metadata；讲解层仅按用户要求开启。公开脚本、模板和示例不得包含私人路径、账户、凭据、私有 receipts 或客户数据。

## 0. 有界 preflight 与路线选择

在故事调研、下载素材、启动应用或长时间重试前，写 `evidence/preflight.json`：

先运行包内 [preflight.py](scripts/preflight.py)：`python3 scripts/preflight.py --phase encode --format both --execution-route work --project '<actual-project>'`。按实际所需层选择 `record` 或 `verify`、所需格式与 OCR 语言；只检查已有文件时可独立完成 file gate。其 `dependencies-ready` 只说明依赖可用，访问、来源、真实模型与画面仍须分别核实。

1. **范围与交付**：一个 `user_outcome`、产品/版本/真实 UI 语言、所需格式、local/private/public 目标。区分 production、beta、preview，不能互换证明。记录已有发布授权；未给出则 `publication.requested=false`。
2. **包与命令**：确认要用的模板/脚本真实存在，先读 `--help`；检查 Python/Node、FFmpeg/ffprobe、Pillow，以及所需 Playwright/Chromium 和 OCR 语言数据。记录实际版本与缺口，不能把文档命令当作已安装能力。编码前运行 builder `--dry-run`；它不是媒体或模型验收。
3. **访问与来源**：一次检查产品来源、已有素材/manifest/原片、目标 UI 及所需模型授权。使用既有身份；401/403/404、登录墙、缺浏览器和模型额度分别记录，不把访问错误当成对象不存在。不输出凭据，不创建新账户/网络通道。
4. **主机**：记录实际 OS、hostname、工作目录、空间和依赖。新录制默认至少 10 GiB；纯已有文件检查按文件大小说明空间需求。UI/浏览器检查只在所需录制或播放器 gate 执行，不阻塞可独立完成的本地文件检查。
5. **预算与检查点**：初次包/访问/来源诊断默认约 5 分钟，先用一次目录/manifest 批量查询筛选最多 5 个相关候选。正在取得有效证据时可继续；已确认缺原片、模型日志或所需访问时停止等价重试，及时交付 blocked 的分层事实，除非出现新的可用路线。不为固定范围复用做广泛外网研究。模型 take/请求/超时另设硬上限。

选择路线，在 `handoff.json.workflow` 写明：

| 路线 | 条件 | 必做工作 |
|---|---|---|
| `verified-reuse` | 原片/成片匹配功能、请求 channel 的来源、surface、语言、模型来源、格式和尺寸 | 核对源 SHA-256 与请求范围；沿用有效的 SHA 绑定检查，只补缺失/失效的 gate |
| `re-edit` | 可信原片可用，但窗口、尺寸、取景或阅读时间需改 | 保留原片，创建新编辑/源映射；新文件重跑完整媒体 QA |
| `new-recording` | 无匹配素材且真实目标 UI/录制路线可用 | discover → story → storyboard → rehearse → record → inspect |

**快速复用不降低门槛。** 无法读取证据、同名文件、只有 GIF PASS、另一版本/另一 take 的 PASS 都不能继承。完全相同字节与交付范围的 file/player/visual/legibility/cold-reader receipts 可沿用，保留原日期/检查人和 `basis=reused`，不得伪装本次执行。缺某层就补某层，无需重录、重做外网调研或编造新故事。来源、字节、预期文字、语言或交付尺寸变更使相关 gate 失效。用户或产品仓库要求 fresh live gate 时照常执行。

来源身份仍无法建立时，不反复做美化重剪；先交付原样文件检查与缺口。明确的诊断任务可继续修复可追溯的媒体，但来源 gate 保持 pending/blocked，修复不构成上线或模型来源证据。

### 分层报告，不能互相代替

`handoff.json.gates` 分别记录 `production_source`（兼容字段名；核实实际请求的 channel）、`model_source`、`current_environment`、`current_live_e2e`、`file`、`playback`、`visual`、`legibility`、`cold_reader`、`delivery_access`。每层用 `pass | fail | blocked | not-run | not-applicable`，写证据、原因、是否依请求必需及本次/复用依据。

- 缺所请求 channel/model 来源 ⇒ 来源 `blocked`；仍可交真实完成的本地文件检查，不能宣称该目标 ready。已验证的非生产目标可 ready，但只表示该已标明的目标。
- 当前 UI、浏览器、凭据或模型不可用 ⇒ 相关当前 gate `blocked/not-run`；不据此判旧文件损坏，也不把 FFmpeg PASS 写成 live E2E PASS。
- 复用/重剪没有新模型运行 ⇒ 当前摘要写 `operation=reuse/re-edit`、当前 edit run 与原始 source run，`current_live_e2e=not-run`，单独关联已核实原 live 来源，未知不得推断 pass。完整原证据保留历史结果。无需 fresh gate 的历史素材可交付，但明确未重跑 live。
- 未请求公开发布 ⇒ `publication.status=not-requested`；没有 public URL、HTTP 200 或代码提交不阻塞合格 local/private 交付。

## 模型依赖录制：只允许 live 与 captured replay

适用于 production、beta、PR/preview、预演、新录制及已有素材复用，覆盖下游/历史示例允许 scripted 模型的旧约定。

- **禁止 scripted 模型**：不得用手写/生成的预设回复、合成答案 mock API、预填 Assistant/TODO/工具事件制作功能演示。标注 scripted、真实工具、PR 演示或缺凭据都不是例外。浏览器操作脚本、真实输入、独立单元/编码 fixture 可用，但不是模型录制证据；历史 fixture 只保留审计。
- **默认 live**：真实产品 UI 调用已授权的真实模型，由模型决定响应/工具路径。按 [live playbook](playbooks/live-model-recording.md) 冻结初态、等待可观察状态、有界重试并保留所有 take。低温度/seed 不保证相同结果。
- **允许 captured-replay**：仅回放同一产品流程捕获的真实 API 响应，按 [replay playbook](playbooks/captured-model-replay.md) 校验来源、逐步上下文、真实工具结果。不得编辑响应、编造 streaming/tool call、错配请求或静默回退。复用/重剪与重新执行 replay 分别记录。
- **能力与素材分开**：live E2E PASS 只来自实际产品流程，API ping 不算。replay 本次 `current_live_e2e` 固定 `not-run`，原始 live 验收另行关联；surface、commit、输入或工具契约不同的通过不能替素材背书。
- **replay 来源可见**：模型名称或持续可读标签使用 `Recorded model response · real tools`，交付文字同样声明。这是 pure-screen 的必要例外，裁切/缩放不能移除；不可读则 `blocked`。
- 按 [model-execution.md](references/model-execution.md) 绑定 take、原片哈希、逐条调用和独立 live 状态。无模型操作用 `model_execution=null` 加观察依据。无真实模型且无合格 capture 时 `blocked`，不能降级 scripted。

这些 playbook 是规范和证据模板，**不含通用 capture/replay adapter**。先验证项目实际实现，缺失如实报告，不能凭文档声明 replay 已实现。

## 主机与控制能力

- 当前具备依赖的 Cloud / Work 可完成浏览器预演、录制、编码、抽帧和渲染，无需额外许可。遵守用户指定主机；允许云端后，其他主机断连不是停止云端路线的理由。
- 记录真实主机/平台。Darwin 只对 Mac 路线有意义。builder 的 `--execution-route work --expected-host <实测主机名>` 或 `--execution-route mac-mini` 必须与实测一致，不能伪造平台绕过检查。
- 独立浏览器用隔离 profile/工作区。共享 Mac 桌面、原生应用或 CDP 必须先发现并取得该环境已有的机器级锁，排队使用，不抢占、kill 他人进程或删锁文件。独立云端浏览器不依赖 Mac 锁。
- **Mac 锁 CLI、bridge、原生控制与共享 worker 不随本包提供。** 仅在环境已配置并验证时使用；缺失则该路线 `blocked`，可继续已允许的其他路线。私人路径、账户与固定端口不是通用前提。
- 凭据留在授权环境。`ui-demo` 或项目录制器可供发现/录制；先读其实际可用说明并验证能力，不能用 Web 页面替代用户要求的 Desktop UI。

## 1. 核实功能与输入

- 读取所请求 channel 的真实发布/部署/构建记录、tag/source SHA、相关 PR/功能开关及应用版本。默认 production；beta、合并 PR、营销邮件本身不是生产上线证明。
- 官方更新清单、签名包、包内版本及打包 SHA 也可形成相应来源链，不强制 GitHub Release。未知项列出，不编造事件。
- 每功能只对应一个可观察结果，按结果合并相关 PR；不可见重构不单独录 GIF。用无敏感数据的独立演示项目和已授权登录，不修改客户项目。
- 其他 agent 委托用 [delegate-schema.md](references/delegate-schema.md) 与 [模板](assets/delegate.template.yaml)。需要可核实的产品/来源定位与 `user_outcome`；`reply_to`、发布仓库和公共地址不是录制前提。缺来源时保存准备和本地检查、说明 blocker，不盲录或泛发 bot 消息。

## 2. 故事与分镜：按改动规模调研

按 [story-research.md](references/story-research.md) 选研究深度。`verified-reuse` 只做请求/原故事差异检查，保留原 research/story 与评分；无变化时不重做 A/B/C、外网调研或强行重选。小重剪核对素材与目标 beat；新故事才做有界参考/候选比较。用户已选故事是范围约束，无需重新选择或批准；研究可指出证据问题。

- 从真实 UI 发现控件原词、可访问名称、窗口/元素矩形、滚动/弹窗/依赖及动作结果。设计 3–6 个 beat：上下文 → 核心操作 → 状态变化 → 高光结果。
- 每 beat 写入口、鼠标路径、动作、结果、停留、取景和 marker。第一帧有可理解上下文，避免黑屏/空桌面/加载。完整 MP4 默认约 30–90 秒，但以真实证明需要为准。
- GIF 默认连续约 8 秒，参考 1 秒上下文 + 4 秒操作 + **至少 3 秒可读结果**；按 marker 定窗口，不直接取前 8 秒。等待太长时保留完整 MP4，可选更长 GIF 或明确的后段窗口，不伪装等待或遗漏因果。
- 请求、首响应、真实工具、任务结束、结果可读分别打 marker；不依赖固定 sleep、逐字输出或预定工具顺序。不用 replay 证明性能。声音效果用 MP4/音频，GIF 只证明可见操作。
- 默认静态裁切。经验证的外部编辑器可做有目的的平滑镜头，但保留时间线/坐标/源映射。包内 builder **不支持动画镜头、时间压缩或定格扩展**，不得编造参数；外部加速/定格必须披露，不计作新行为/模型证据。
- 写 `shotlist.json`，见 [shot-list-schema.md](references/shot-list-schema.md) 与 [模板](assets/shotlist.template.json)。纯 MP4 将时间明确标为其交付时间线，不伪造 GIF。

## 3. 条件步骤：库存素材与邮件参考

**纯产品 UI 不需要库存片或营销研究。** 仅选定故事需要库存口播/B-roll 时才搜素材，记录作者/来源/许可，不使用参考视频素材。库存搜索/批量评分、邮件抓取集成及其项目脚本**未随本包提供**，先验证环境实现，不假定额外参考文件、Resend 脚本或 Mac worker 存在。缺可选集成不阻塞无此依赖的录制。

- 抠图功能/库存人像选片：选前每候选抽片头/中/尾至少 3 帧，用演示同一工具试抠，替代模型标 proxy。主体/手持物被误删、空洞/碎片、相近色粘连、主体定义不清均失败。失败片不录，存本 run 负例、帧/工具/原因；继续最多 10 个候选，无通过则该依赖 `blocked`，不降门槛。
- 多候选使用同一条件批量施加目标变换，逐项即时存 verdict 后选片。评分必须查看实际帧/contact sheet，不能按文件名猜；高分不能覆盖试抠失败。非抠图记 `clip_test_cutout=not-applicable`，不增加无关工作。
- 任务需要对齐邮件时，使用授权只读工具读取实际 HTML、alt、宽度、链接、媒体 magic 与分页；429 按提示退避。集成缺失时记录限制，可按用户给出的尺寸交付。共用 URL 的点击不能归于 GIF，更不能声称转化因果。默认不发广播。

## 4. 预演、录制与 take 核验

- 新录制先确认语义、控件、状态变化、取景、依赖五项通过；selector PASS 不够。模型预算在预演前确定；预演/正式 take 分开重置并保留失败，不拼接不同 take 的因果链或预填结果。
- 检查真实 UI 语言。ChatCut 发布素材未指定时默认 English；其他产品用目标真实语言。原生中文要求必须录到中文控件/内容，不能以中文字幕替代。每语言独立录前/后证据，CJK 不一律判失败。
- 完整原片写独立 `raw/`，不修改/覆盖/移动 GT。保留目标 channel/discovery/rehearsal 证据，以录制开始为 0 写实际 `elapsed_ms` marker，不从脚本顺序猜。结果连续可读至少 3 秒，写 `proof_interval_s`。
- **每 take 在 keep/discard 前**：按固定时刻（GIF 窗口每 0.5–1 秒加关键 beat）抽帧做 strip，对照分镜/布局，交叉核对点击、结果可见、窗口和镜头时刻。`runs/takes.log` 写 take/verdict/具体原因/证据。未经帧与 timing 核验不得 keep/discard，失败原片保留，不删除来隐藏尝试。
- 常见问题：playhead 未复位、屏幕争用、滚动错位、背景层缺失、UI/时间线不同步、语言不符。只修有证据的根因，新 take/编辑用新目录。
- 按 [media-contract.md](references/media-contract.md)、[feature 模板](assets/feature.template.json)、[cinematography.md](references/cinematography.md) 记录来源、语言、take 核验与相关试抠证据。

## 5. 生成派生素材

在选定主机独立输出目录执行；跨主机只传必要脚本/素材，不传 `.env`、cookie/profile。按 [media-contract.md](references/media-contract.md) 设置 `feature-media/v1` manifest，先 dry-run，再去掉此参数执行：

```bash
python3 scripts/build_feature_media.py \
  --manifest feature.json \
  --output edits/v1 \
  --execution-route work \
  --expected-host '<observed-hostname>' \
  --format both \
  --dry-run
```

- `source.kind=full-recording` 才能产生完整原片 MP4；已有 GIF/短派生片不能变成“完整原片”。`existing-derivative` 保持其来源声明。
- MP4 为 H.264/yuv420p/faststart，保留完整时长/原音频。GIF 默认 520px、12 FPS、无限循环、目标 ≤3 MiB；超预算可尝试 10/8 FPS，不能牺牲文字门槛，失败则报告尺寸/时长取舍。
- builder 拒绝越界区间/crop、阅读时间不足、覆盖 GT/已有输出；保留 SHA。输出为 `demo.mp4`、`feature.gif`、`manifest.json` 和 `input-manifest.json`，预算尝试留在 `attempts/`。
- `--fixture` 仅独立合成编码测试，标 `fixture-only`，不能作为功能/模型证据。脚本/依赖失败属于文件流水线，不是产品 live gate。

## 6. 逐文件检查真实画面

按 [delivered-video-verification.md](references/delivered-video-verification.md) 对每语言、每个实际 MP4/GIF 独立验收，先固定 SHA。GIF PASS 不给完整 MP4 背书；metadata/file PASS 不给视觉或来源背书。

- [verify_delivery.py](scripts/verify_delivery.py)：完整解码、帧/时长/编码/faststart 与匿名全片 sheet。保留 file 层结论；无产品登录也可运行。
- [verify_playback.mjs](scripts/verify_playback.mjs)：匹配的实际 Chromium 完整 MP4 1× 播放到 `ended`，记录掉帧/错误/时钟/SHA。metadata、seek 到末尾、`play()` resolve 或解码均不算全片播放器验收。缺浏览器记 playback `blocked/not-run`，不判文件损坏。
- 实际打开 poster、全片/密集操作帧与 GIF 交付尺寸帧；需要时播放声音。点击前标签可见、指针到达后点击且不遮字，变化真实、上下文完整、无泄露，replay 标签完整，语言声明匹配像素。
- 每完整文件由**未参与制作的新上下文**冷读匿名 16 帧全片 sheet，不给 brief/预期答案/文件名线索，保留原文回答。视频视觉服务不可用时用解码帧/beat 静帧交独立读者，不能跳过或制作者自评 PASS。缺独立读者则 pending，不虚构。
- `qa.json` 记录检查人/时间/SHA/图片、播放器、冷读证据。完全相同文件可沿用可读旧 receipts，保留原日期与 `basis=reused`；新编辑重跑该文件全部 gate。

### 6.1 可读性与故事清晰度（强制）

在**实际交付尺寸**测关键文字，不在母版或 OCR 放大图测。规范见 [legibility-spec.md](references/legibility-spec.md)，脚本 [verify_legibility.py](scripts/verify_legibility.py)。

| 关键文字 | 默认指标 | 最小值 |
|---|---|---|
| hero / 结果标题 | Latin cap height | **16 px** |
| 被操作控件标签 | Latin x-height | **9 px** |
| CTA / 次要结果 | Latin x-height | **7 px** |

- 每项显式给交付像素坐标 `semantic_roi_px` / `measure_roi_px`，token 与字形测量绑定同一 ROI；严格用声明的 beat 帧，不能挑其他时刻较好结果。按真实 GIF delay 映射时间，不假设恒定 FPS；重复文字匹配不唯一时保留 FAIL。
- OCR 安装真实语言数据。正常/反色/放大仅辅助识别，缺依赖/TSV 错误/空结果不是 PASS。Latin cap/x-height 不适用 CJK，另定有依据的整字墨迹高度并看实际笔画。保留 OCR FAIL；独立读者逐字裁定可单列视觉例外，不能改写机器 PASS。
- 16/9/7 是本工作流默认门槛，不宣称 WCAG 像素标准。其他阈值须有依据，不能因失败临时调低。结果达标的**连续可读时间 ≥3 秒**，从镜头稳定且结果可见开始计。
- 特写 ROI 完整，中心偏移宽/高各 ≤10%；点击时控件为主体、指针不遮标签。不够大就调整 ROI/crop/镜头、DPR、落点或交付尺寸，创建新编辑，不靠字幕/加速掩盖。
- 冷读必须复原“可读控件 → 前后变化 → 最终结果/给谁用”，并指出不清楚处。保留 literal answer、独立性、`legibility.json`、标注 strip 与匿名 sheet；自评只能 provisional。

## 7. 本地交付与可选发布

每 run 写 [handoff.json](references/handoff-schema.md)，用 [模板](assets/handoff.template.json) 填实际事实，pending/null 不是通过。附所需 MP4/GIF、poster、manifest、shot list、QA、可分享来源摘要及原片位置；保留 GT/失败历史。私有 receipts 留授权归档，公开仓库只放脱敏摘要。

- **local（默认）**：存持久工作区，实际读取/校验最终字节，给可点击文件链接与 QA/来源说明。不需要 HTTP、功能分支、commit、PR 或公共页面。
- **private**：用已核实的指定私有目标，读取/下载验证所需权限及上传后哈希。无公开链接完全有效，不改分享权限。访问无法验证时仍交本地包并将私有上传 gate 标阻塞。
- **public（仅明确请求）**：完成授权的具体目的地，匿名 GET 核对所发必需 URL、HTTP 200、MIME、非空内容与精确哈希。只发请求格式；请求含 gallery/handoff 页面才验这些页面。发布失败单列 `publication=blocked`，不把本地 QA 改成 FAIL，但整体请求未完成。
- 需要邮件嵌入才生成 `email-block.html`，使用已验证匿名可读 HTTPS 地址；local/private 文件不能伪装公网可嵌入。真实客户端邮件打开验收与只读 HTML/媒体探测分别报告。
- 未请求发信/付款/改权限/广播时停在素材交付，不主动索取额外批准。只在用户明确授权或明确调用的授权工作流内向其他 agent 发消息；否则给可转发文本，不默认调用 bot。
- 用户回复从 handoff 渲染：状态、一个结果、产物链接/内联 GIF、来源/各 QA 层、偏差/阻塞、下一步。复用明确历史原片/本次编辑与未执行 live gate；完整评分/shot list 放文件，按需展示。

## 验收与状态

`ready` 要求所请求 channel/model 来源可核实；语言/范围一致；take/原片 SHA 可追溯；每文件 file、实际播放器（MP4）、像素/可读性、≥3 秒阅读与独立冷读通过；持久保存/所选目标访问通过。适用试抠须通过。复用保留原 receipt，不写成 fresh；非生产目标的 ready 不是生产部署证明。

- `ready`：适用必需 gate 通过，请求交付完成。未请求 publication/fresh live 时明确 `not-requested/not-run`，不算失败。
- `ready-with-notes`：同样通过必需 gate，只有非阻断说明（如历史素材复用）；notes 不能绕过来源/阅读/独立复核或请求的发布失败。
- `needs-visual-review`：文件检查通过，画面/独立阅读未完成，不是成片 ready。
- `blocked`：来源、所需录制/模型/访问或必需 gate 失败/缺失。交付已完成文件和分层证据，说明具体缺口。
- `fixture-only`：独立合成编码测试/历史审计素材，不能作为功能/生产/发送验收。
