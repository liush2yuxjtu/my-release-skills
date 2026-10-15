---
name: record-production-feature
description: Turn one verified production feature into one focused GIF or video. Use for feature-to-GIF requests, release demo assets, one-feature screen recordings, 8-second email GIFs, or Resend broadcast demonstration media. Discover the real UI, record on Mac mini through ui-demo, preserve immutable full recordings, create tested MP4/GIF derivatives, inspect actual frames, and prepare a traceable email handoff without sending a broadcast.
---

# Record Production Feature

由唯一 chatcut-release 入口在有效人工 feature_shortlist 选择后按需调用，或用于已有明确手动素材任务。入口的 selected IDs 是范围；不再要求第二次录制许可。显式 plan-only 仅准备计划。完整 full_scope 与 GT 证据保持可追溯。

把一个已在生产环境可用的用户功能，变成一份可追溯的录制素材包。
默认保留完整 GT 原片，并交付完整 MP4 与 8 秒 GIF。用户只要一种格式时，使用 `--format mp4` 或 `--format gif`。

固定验收规则和编码脚本；让 agent 根据真实 UI 决定故事、操作、取景和剪辑区间。

先查找符合版本、功能与画面要求的已有录制；匹配时复用。默认 pure-screen：不加讲解字幕、发布角标、装饰性 callout、旁白、音乐或转场，保留原生应用文字、字幕功能和普通鼠标。章节只写 metadata；讲解层仅按用户明确要求开启。GIF 给内嵌预览，脚本解释用 ELI5，可调项用 Markdown 表格。真实脚本按 `examples/{version_slug}/` 保存；完整录制示例见仓库的 `skills/record-full-walkthrough/examples/0.6.6-to-0.6.7/example.md`。

## 硬性规则 / Hard rules

以下五条在任何录制流程中不可跳过；与下文章节冲突时以本块为准。

1. **英文 UI 强制（每次录制）**：任何录制前必须把应用语言设为 English（ChatCut：头像 → Language → English；`--lang=en` 在 0.6.9 无效）。禁止用中文 UI 录制；项目名、时间线名、素材名也一律用英文。**Pre-flight**：录前通过应用设置或可见英文 UI 文案（如 `Library`、`Effects`、`Export`）用截图/DOM 确认语言；非英文则中止。**Post-check**：扫描 GIF 帧是否出现 CJK UI 文字；若有则整条 take 作废。
2. **保留/丢弃前必须做 take 核验**：每次 take 后，从原片按固定时刻抽帧（例如 GIF 窗口内每 0.5–1s，加上关键 beat），拼成 strip/contact sheet，对照分镜/预期布局，并交叉核对 timing 日志（点击时刻 vs 结果可见时刻 vs GIF 窗口 vs zoom keyframes）。丢弃须写入具体原因，常见包括：playhead 错误（例如点击前已播放导致 playhead 卡在片段末尾——选中前应点标尺等把 playhead 复位到起点）、屏幕被其他任务占用/争抢、视图滚动/错位、背景/backdrop 层缺失、UI 与时间线状态不同步、中文 UI。**未经帧对比 + timing 核验，不得 keep 或 discard**；丢弃的 run 目录用原因命名（如 `runs/B-take2-playhead`），并向 `runs/takes.log` 追加一行（take、verdict、reason、evidence paths）。
3. **批量筛选（选片/多样本验收通用）**：判断一组候选素材是否适合演示/发布时，不要逐条试——对各候选抽短样（片头/片中/片尾），全部放上**同一时间线**，对全体一次性施加目标变换，逐条验收并把 `verdict.json` 立即落盘后再选片。详见 [references/batch-media-screening.md](references/batch-media-screening.md)（AI Portrait Cutout 为首个实作，成功案例见 [references/worked-example-ai-portrait-cutout-v3.md](references/worked-example-ai-portrait-cutout-v3.md)；亦适用于调色/LUT、导出预设、字幕、超分等）。
4. **素材必须先通过试抠图（选片前强制门禁）**：选定任何库存片之前，从候选片抽取 ≥3 张静帧（片头/片中/片尾），用演示中同一背景移除工具做试抠图（ChatCut AI Portrait Cutout 对静帧；若不可行则用可比的人像抠图模型，并注明为 proxy）。仅当主体可干净分离时才继续：无灰对灰/相近色导致主体边缘与背景粘连；无前景或手持物（箱子、衣物、话筒、脚架、道具）被误抠留下空洞或漂浮碎片；无「手持物可能被抠掉」的模糊区域——必须显式裁定何为主体，否则先裁掉这些区域。此门禁高于凌乱度/故事契合打分：高分片若试抠失败，不得作为有效演示素材。教训（2026-10-11）：Pexels 6893155 凌乱度 8.0，但胸前灰衣木箱在实抠中大多被抠掉（空洞 + 漂浮碎片），因当时仅靠肉眼判断 cutout。

   **试抠失败时的强制步骤（不可省略）**：
   1. **立即丢弃该片**：不得录制、不得「先试试看」、不得用凌乱度/故事契合高分抵消失败。
   2. **记为负面样例**：写入技能参考 [references/stock-footage-scoring.md](references/stock-footage-scoring.md) 的 **Negative examples** 列表（clip URL/id、试抠帧、failure mode 如 held object removed / gray-on-gray、evidence path）；同时写入本 run 的 `assets/stock/scoring/report.md` 与 `feature.json` → `clip_test_cutout`（verdict=fail、reasons、frames、tool、evidence）。
   3. **按同一试抠优先标准搜下一候选**：循环直至有片通过；若已试满 N 条候选（默认 **N=10**）仍无通过，**停止并报告 `blocked`**，不得降低门禁、改用肉眼 cutout 评分或跳过试抠。

5. **全机录制锁（每次录制，含预演/抽帧以外所有触碰屏幕或 ChatCut 的步骤）**：本 Mac mini 上所有录制者（GIF 临时任务、公司卡片服务、个人 bridge、shared-recorder worker）共享一把机器级锁 + FIFO 队列（`~/Projects/chatcut-recording-lock`，CLI `~/.local/bin/chatcut-rec-lock`）。共享资源：屏幕/鼠标键盘、ChatCut 应用与默认 profile、CDP 端口 9347/9348/9350。**未持锁不得启动 ChatCut、连接 CDP 或开始录屏。**
   - 录前查看：`chatcut-rec-lock status`（`holder` = 当前持锁者，`queue[].position` 1 = 下一个）。
   - 录制命令一律包一层：`chatcut-rec-lock run --owner gif-job --purpose '<feature>' --ttl 2700 -- node record-xxx.mjs ...`（锁在 wrapper 进程中持有；子进程结束或崩溃即释放；退出码透传；`--wait-timeout N` 超时退出码 75）。
   - 多步长会话（需要跨多条命令持锁）：`chatcut-rec-lock acquire --owner <me> --purpose '<feature>' --ttl 2700` … `chatcut-rec-lock release --owner <me>`；超过 ttl 自动释放。Node 内部用 `withRecordingLock()`（`lock.mjs`）。
   - 排队行为：先到先得（FIFO）；排队时显示位置，不要抢占、不要 kill 别人的 holder 进程、不要直接删 `~/.local/share/chatcut-recording-lock/` 下的文件（死进程的票据/holder 会被自动清理）。若 `status` 显示 `ttl_expired: true` 且 holder 仍在运行，报告给用户而不是强杀。
   - 在 `feature.json` 记录 `recording_lock`：owner、ticket、waited_s、acquired_at/released_at。
   - 完整说明（CLI 子命令、退出码、状态目录、崩溃/陈旧清理、Node API、已接入的录制者、构建与验证记录）：[references/recording-lock.md](references/recording-lock.md)。

在 `feature.json` 中记录：`ui_language`（必须为 `en`，含 pre-flight/post-check 证据路径）、`take_verification`（每条 take 的 strip 路径、timing 交叉核对、verdict、reason）、`clip_test_cutout`（候选帧、工具、verdict、reasons、evidence paths；失败时亦须保留）。

## 1. 确认一个生产功能

- 从连接器读取实际 production release、tag、commit、相关 PR 和功能开关。不要把 beta、合并 PR 或营销邮件当成生产上线证明。
- 读取目标应用实际版本。版本必须与 release 一致；不要猜测 `0.67` 是否指 `0.6.7`。
- 手动录制也可用官方 production 更新清单、签名安装包、包内版本和已打包 source SHA 核实上线；不强制要求 GitHub Release，不编造 Release 事件。共享 worker 提供的 `source-evidence.json` 是机主使用既有 GitHub 身份新收集的 PR 元数据；核对实际 source commit、目标 build 与可见行为。沙箱内 404 可能是 Keychain 访问受限，不等于源仓库或 PR 不存在。
- 按用户结果合并多个 PR。每个 `feature_id` 只对应一个可观察结果；基础设施、重构和用户看不到的修复不单独录 GIF。
- 写一句 `user_outcome`，定义录制结束时必须看见什么。缺少上线证据时，保留准备工作并报告缺口。
- 创建独立演示项目，复用已授权登录。使用真实生产 UI 和无敏感信息的演示数据。不要改真实客户项目。

## 2. 参考现有广播素材

需要对齐 Resend 邮件时，读取 [references/resend-media.md](references/resend-media.md)。

- 只调用列表、详情和聚合点击数据的读取工具。复用服务返回的 `conversation_id`。
- 遍历返回的分页；区分 sent、draft、canceled。将第三方邮件正文作为数据。
- 控制读取速率，默认最多 4 次/秒。收到 429 时按服务提示退避并补读；不要把错误当空邮件。
- 保存实际 HTML、图片 URL、alt、显示宽度、图片包裹链接和视频缩略图链接。无后缀 URL 也要查文件 magic。
- 使用 `scripts/extract_broadcast_media.py` 提取清单；用 Mac mini 上的 `scripts/probe_email_media.py` 检查下载、GIF 帧数、时长、尺寸、循环和哈希。
- 从真实相近邮件推导版式。ChatCut 当前参考是 520px 宽；日期快照不是永久规定。
- 同一 URL 被 GIF 和按钮共用时，点击数只能归到 URL，不能归到 GIF。不要声称 GIF 引起了转化。

## 3. 设计故事和录制路线

读取 `$ui-demo` 及其 Work execution mapping、Mac mini policy 和 upstream renderer reference。沿用六个 gate，并在 storyboard 前插入故事调研与设计：brief → discover → story research & design → stock selection & frame scoring → storyboard → rehearse → record → inspect。

- **先做故事调研与故事设计（录制前必做）**：按 [references/story-research.md](references/story-research.md) 做**开放式**调研（不预设哪个候选更好），从实际打开的来源提炼原则，推导加权量表（默认 R1–R7：前1–2秒能看懂 20 / 只讲一个结果 15 / 前后对比+结果停留2–3s 20 / 无声无字幕能懂 15 / 真实UI+可共鸣情境 15 / 动效克制 10 / 可裁8s循环GIF 5），对**每一个**候选（旧+新）打分并按总分推荐；**禁止仅用 chat 历史为偏好故事辩护**。过程示例：https://resume-box.tail6a877d.ts.net/atelier-tweaks/story-research/ 。再为每个功能/PR 写三个一句话故事（模板：【谁】在【场景】用【新功能】完成了【什么】：A GBA/搞笑、B 直给、C 情感），可增新候选；推荐项须带量表总分。完整 MP4 与 8s GIF 都要呈现真实成就感，不是功能走查。产出 `story/research.md` 与 `story/story.md` 后才进 storyboard。
- 节奏和钩子参考抖音、小红书教程风格：第一秒交代问题或亮出前后对比的钩子，快速进入关键操作，把结果揭晓放在 GIF 区间内；仍保持 pure-screen 默认，不加未要求的字幕或音乐。
- 设计 3–6 个可见 beat（由选中的故事选项映射而来，最后一个 beat 必须是故事的高光成果）：入口与已有状态 → 核心操作 → 状态变化 → 最终结果。
- 发现实际控件、可访问名称、窗口和元素矩形、滚动位置、弹窗、依赖及动作后的结果。
- 使用 UI 原词。每个 beat 写清入口画面、鼠标路径、动作、结果、停留、metadata 章节和取景；讲解字幕仅按用户要求添加。
- 默认完整讲解约 30–90 秒，按任务调节；不要为了时长省略证明。
- 默认 GIF 连续取 8 秒：约 1 秒上下文、4 秒关键操作、3 秒结果。根据原片 marker 选择实际区间，不能直接截前 8 秒。
- 让第一帧提供可理解的上下文，避免黑屏、桌面空白或加载画面。
- 长等待保留在 GT 和完整讲解中。需要时间压缩时，明确标出加速，并生成新的、可追溯编辑时间线；本脚本只支持原片连续区间。
- 声音功能用 MP4 或另附音频样本证明效果；GIF 只证明可见操作。

### 平台路线

- 浏览器 UI：使用 `ui-demo` 的 Playwright 发现、预演和录制流程，匹配 pinned Playwright 与 Chromium。
- ChatCut Desktop：先发现已有原生控制、屏幕捕获或 Electron 录制路线，并验证窗口和实际版本。`ui-demo` 不提供原生控制能力；不要悄悄用 Web 页面替代 Desktop。
- 所有录制、编码、frame extraction 和渲染都在 Mac mini 执行。先确认 Darwin、主机、项目根、至少 10 GiB 空间、FFmpeg、ffprobe 及录制依赖。
- 连接器优先；失败时只用已经建立的 Grokbot → Mac mini bridge。Grokbot 可做 QA，不作为渲染主机。不要新建 SSH、Tailscale 或凭据；不要回退到 Work container 或 MacBook 渲染。
- 缩放依据实测 ROI；默认使用 `gif.crop` 对关键区域取景。需要平滑镜头缩放时，使用已验证的编辑器并保留坐标及时间线；不要声称本 skill 自动复刻 Screen Studio 的点击追踪。

## 4. 素材选择与帧评分

故事设计完成后、预演/录制之前，若故事需要库存口播或 B-roll，按 [references/stock-footage-scoring.md](references/stock-footage-scoring.md) 选片并打分。免费商用素材站为 **Pexels**（https://www.pexels.com，Pexels License）与 **Pixabay**（https://pixabay.com，Pixabay Content License）；用故事场景关键词查视频搜索页，站点会拦截普通 fetch，搜索页用无头浏览器，下载走 `videos.pexels.com` 等直链。

1. 按故事的场景 + 动作在 Pexels / Pixabay 搜索候选片。
2. 下载 3–6 条到 `<project>/assets/stock/`，并写 `sources.md`（URL、作者、许可）。
3. **试抠图门禁（硬性，先于凌乱度打分）**：从每条候选片抽 ≥3 张静帧（片头/片中/片尾），用演示同一工具（ChatCut AI Portrait Cutout 或注明的 proxy）试抠。写入 `feature.json` 的 `clip_test_cutout`。**优先用同一时间线批量筛选**（[references/batch-media-screening.md](references/batch-media-screening.md)）。详见上方「硬性规则」与 [references/stock-footage-scoring.md](references/stock-footage-scoring.md)。
4. **试抠失败处理（硬性，编号执行）**：
   1. 立即丢弃该片——不录制、不「先试试看」。
   2. 记负面样例：更新 `references/stock-footage-scoring.md` 的 Negative examples；并写入本 run `assets/stock/scoring/report.md` + `feature.json` → `clip_test_cutout`（URL/id、frames、failure mode、evidence）。
   3. 用同一试抠优先标准搜下一候选；循环直至通过。已试满默认 **N=10** 仍无通过 → 停止并报告 `blocked`，不得降低门禁。
5. 用 ffmpeg 每 2–3 秒抽一帧（评分用；**仅对试抠通过的片**）。
6. **用视觉模型给拼帧图打分（硬性）**：把每条候选片抽出的帧按时间顺序拼成一张 contact sheet（如 `contact_<id>.jpg`），交给视觉模型读图，按故事要求打 1–10 分并列出画面里看到的物品；分数与依据写入 `scores.csv` / `report.md`，不得凭文件名或缩略图臆测打分。
7. 评估抠图适合度 `good` / `ok` / `poor`（主体对比、头发/边缘、前景遮挡如脚架/道具、贴边裁切、身后走动的人）——**不得替代试抠图门禁**。
8. 仅对试抠通过的片取平均分、排序、选定最佳；记录到 `assets/stock/scoring/`（`frames/`、`scores.csv`、`report.md`、contact sheets、`test-cutout/`）。
9. **选定后才录制。** 若最佳片与故事动作不符（例如不是在说话），必须显式决定：改故事以匹配素材，或继续搜索——不要静默凑合。

## 5. 预演后录制

- 确认语义、选择器、状态变化、取景和依赖五项通过。只验证选择器不算通过。
- 显示鼠标移动和点击，保持文字可读。保留上下文与原生字幕内容；默认无讲解文字层。用户要求的讲解层不得遮住操作或结果。
- 录下完整 GT，写入单独 `raw/`。不修改、替换或移动已有 GT。
- 写 `elapsed_ms` runtime marker；将 0 秒对齐录制开始，不从脚本顺序猜章节时间。
- 让最终结果连续可读至少 3 秒，并记录 `proof_interval_s`。
- **Take 核验（硬性，keep/discard 前必做）**：从原片按固定时刻抽帧拼 strip/contact sheet，对照分镜，并交叉核对 timing 日志；未完成不得 keep/discard。丢弃目录用原因命名（如 `runs/B-take2-playhead`），追加 `runs/takes.log`。详见上方「硬性规则」。
- 保留 production、discovery、rehearsal 和 marker 证据。按 [references/media-contract.md](references/media-contract.md) 填写 `assets/feature.template.json`（含 `ui_language`、`take_verification`、`clip_test_cutout`）。

### 录制呈现要求

按 [references/cinematography.md](references/cinematography.md) 执行，并写入 `feature.json`：

- **界面语言（硬性）**：见上方「硬性规则」——每次录制强制 English UI；`feature.json` 写 `ui_language: en` 及 pre-flight/post-check 证据。ChatCut：头像 → Language → English（`--lang=en` 在 0.6.9 无效）；项目/时间线/素材名用英文。
- **Screen Studio 式后制缩放**：起幅全局全窗；指针到达/双击时 cosine ease-in-out 约 0.6s 缩到约 1.6×（功能卡 + 片段）；处理 toast 处平移/停留约 1.75×；拉回全局并让结果停留 ≥3s。关键帧写入 `feature.json`。采集多为 1280×800，缩放后略软。
- **时间压缩必须标注或避免**：2026-10-11 英文 GIF B 对处理等待做了未标注的 2.5× 加速以塞进 8s——之后必须画面标注（如 `2.5×`），或改用 10–11s GIF / 从点击后起算 8s 窗口。选择记入 `feature.json`。


## 6. 生成派生素材

把所需脚本与 manifest 传到 Mac mini 的独立项目目录；不要传 `.env`、cookie、profile 或凭据。以下命令只在确认的 Mac mini 运行：

```bash
python3 scripts/build_feature_media.py \
  --manifest feature.json \
  --output edits/v1 \
  --expected-host "$CONFIRMED_MAC_MINI_HOST" \
  --format both
```

- 用 `--dry-run` 检查计划，不编码；Work container 可执行此模式。
- 从已连接 Mac mini 的 preflight 设置 `CONFIRMED_MAC_MINI_HOST`；不要用当前任意机器的 hostname 代替。
- `--fixture` 仅用于明确的合成测试；输出标为 `fixture-only`，不能作为生产验收证据。
- 使用 H.264 / yuv420p / faststart MP4，保留完整时长和原音频。
- 默认 GIF 为 520px、12 FPS、无限循环、目标 ≤3 MiB。脚本使用 palettegen / paletteuse，并在超预算时尝试 10 或 8 FPS；不要静默降低文字可读性。
- 拒绝越界剪辑、结果停留不足、越界 crop、覆盖 GT 或已有输出目录。
- 校验原片与派生素材哈希。不要改 GT 来满足验收。

## 7. 检查真实画面

`metadata_pass` 只表示文件检查成功。它不代表视觉通过。

- 将 Mac mini 返回的 poster、完整 contact sheet 和 GIF contact sheet 带回 Work，用 `view_image` 读取并输出图像，检查实际像素。
- 对每次主要操作和章节边界，在 Mac mini 提取更密的 frame strip；必要时播放 MP4，检查声音。
- 检查指针到达目标后才点击、菜单能看见、结果确实变化、上下文完整、没有额外讲解层（若要求添加则用词准确）、没有遮挡或泄露、结果可读 ≥3 秒。
- 核对 take 核验证据：固定时刻 strip、分镜对照、timing 交叉核对、`runs/takes.log`；扫描帧中无中文 UI。
- 按真实 UI 区间验证 presentation、crop 与画面。失败时，只修复有证据的问题，在新的 edits 目录重做并检查同一区间。
- 在 `qa.json` 填写 `visual_review` 的检查人、时间、检查图片路径和结果；保留机器结果，不能自动把状态改成通过。

## 8. 准备交付

- 交付 `demo.mp4`、`feature-8s.gif`、poster、chapters、manifest、QA 和邮件片段，按请求选择格式。
- 保存产物到用户指定、已核实的 Drive 目录；未指定时使用当前持久文件保存流程。查明 folder ID 和权限，不从历史记忆猜目录，也不改分享权限。
- 建议结构：`ChatCut/Releases/<production-tag>/<feature-id>/{raw,edits,evidence}`。保留所有已指定为 GT 的原视频。
- 把 GIF 或 poster 链接到完整视频或功能入口；使用可区分的 `utm_content=<feature-id>-gif` / `-cta`，让后续点击可归到对应入口。
- 将 `email-block.html` 的占位符替换为已验证的实际 HTTPS 地址，并验证匿名 GET、MIME、非空内容、尺寸和发布后哈希。不要把登录页、预览受保护 URL 或未知链接交付成可用素材。
- 不把发信、付款、改权限或凭据包含在素材生成授权中。当前请求未包含这些动作时，停在素材和草稿交付；不要主动发出审批请求。
- 汇报一个功能的用户结果、来源、产物、文件检查、视觉检查、访问检查及实际阻塞。不要称只读抽帧为真实客户端邮箱验收。

## 验收清单（Acceptance checklist）

在标 `ready` 前逐项确认：

- [ ] `ui_language` 为 `en`：录前 pre-flight（设置或可见英文 UI 文案截图/DOM）通过；GIF 帧 post-check 无 CJK UI 文字；项目/时间线/素材名为英文。
- [ ] `take_verification`：每条 take 均有固定时刻抽帧 strip/contact sheet + 分镜对照 + timing 日志交叉核对；keep/discard 均有 verdict 与具体 reason；丢弃目录按原因命名，`runs/takes.log` 已追加。
- [ ] `clip_test_cutout`：选片前对候选片 ≥3 静帧（片头/片中/片尾）用演示同一抠图工具试抠并通过；失败片已立即丢弃（未录制）；已记入 Negative examples + 本 run `report.md`/`feature.json`；按同一标准循环搜下一片；满 N=10 仍无通过则 `blocked`（未降门禁）。
- [ ] 生产证据、文件检查、视觉检查、持久保存和目标访问检查均通过（见下方输出状态）。

## 输出状态

- `ready`：生产证据、文件检查、视觉检查、持久保存和目标访问检查均通过；且 `ui_language=en`、`take_verification` 与 `clip_test_cutout` 硬性规则均满足。
- `needs-visual-review`：编码与文件检查通过，画面尚未验证。
- `blocked`：生产来源、录制路线、窗口权限、登录、空间、依赖阻塞，或英文 UI / take 核验 / 试抠图门禁未通过；交付已完成的准备工作与真实错误。
- `fixture-only`：合成测试素材，禁止用于生产或发送验收。

## 队友共用 Mac mini

需要共用 Mac mini 时，先读取仓库根目录的 `docs/shared-macmini-recorder.md`，使用 `scripts/request_shared_recording.py` 和已有 GitHub 身份提交明确的手动录制任务。Mac mini worker 按本技能与已有 /ui-demo 执行；请求方查询同一 issue、下载校验后的素材或取消。任务访问码不进入仓库，不分享机主凭据。连接验证和 fixture 不能代替本技能的真实版本与画面验收。
