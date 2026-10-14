---
name: record-full-walkthrough
description: Internal recording helper for chatcut-release or an explicit manual recording. Find and reuse verified existing recordings first; otherwise record pure-screen beta/production walkthroughs with installed ui-demo on Mac mini after the entry's feature selection. Preserve immutable raw MP4, rehearse real desktop UI, derive chapters from markers, inspect frames and save full MP4/8-second GIF plus versioned scripts. Explicit plan-only tasks do not record.
---

# Record Full Walkthrough

Status: IMPLEMENTED — entry_or_manual recording; explicit plan-only tasks only prepare plans.

把一个已核实的版本区间录成完整 MP4，并按请求从同一原片剪出连续 8 秒 GIF。
固定证据、验收和编码规则；让 agent 根据实际 UI 决定功能顺序、操作、取景和区间。

## 录制与交付偏好

- 先找已有录制。按用户指定范围搜索可访问的 ChatGPT 会话、已保存素材及脚本；核对时间、版本、范围、画面和哈希。匹配时复用，不为预览或讲解脚本重录。会话搜索能力不可用时明确实际检索范围，不能声称查遍全部聊天。
- 默认 `pure-screen`：不加讲解字幕、发布角标、标题卡、装饰性 callout、旁白、音乐或转场；保留原生应用界面、文字与普通鼠标。应用自己的字幕编辑/字幕轨属于演示内容，不能因“去掉字幕”而删掉它们。章节写入 metadata，不烧进画面。仅按用户明确要求开启讲解层。
- 需要去掉讲解层时，优先使用已有干净原片重新导出。若只有烧录字幕的成片，说明缺少干净源；用户明确要求不重录时交付现有来源和缺口。不要用裁掉原生 UI、模糊或生成式修补伪造纯屏幕。
- 交付 GIF 时给可直接看的内嵌预览与下载链接。用户要讲解脚本时，用 ELI5 说明：Bash 启动脚本，Playwright/原生 API 完成固定步骤，FFmpeg 导出素材；区分实际保存的脚本与 agent 临时操作。可调整项用 Markdown 表格列出当前值、修改位置和所需复验。
- 将实际录制脚本、分镜、复现命令和小型证据放在本技能的 `examples/{version_slug}/`，从 SKILL.md 链接。大媒体与 raw frames 留在已核实归档，不打包凭据、profile 或访问码。版本示例不作为下一次任务的默认项目、端口、坐标或剪辑秒数。

## 1. 区分规划与执行

- 先读仓库 `AGENTS.md`、`config/release-policy.json`、`config/skills.json`。
- 合成 planning eval 和明确“只规划”任务只返回 `status: placeholder`、`missing_inputs`、`todo`、`planned_outputs`、空 `completed_actions`。不运行录制或编码。
- 唯一 chatcut-release 入口已记录有效人工功能选择时，自动执行该范围，不再请求录制许可；独立明确录制请求也可执行。默认 agent_orchestrated 允许入口调用；plan builder 本身仍不录制。
- 读取执行环境已安装的 `/ui-demo` 及其 Work mapping、Mac mini policy 和 renderer reference。按 `brief → discover → storyboard → rehearse → record → inspect` 六个 gate 执行。
- 缺少真实 build、登录、可用驱动或渲染主机时，完成不依赖它们的准备并报告 `blocked` 与真实错误。

## 2. 核实版本与用户范围

- 根据实际发布包、更新清单、包内版本和已打包源 commit 核实 base/head、渠道与平台。保留下载地址、发布时间、安装包校验和及签名证据。
- 对手动版本区间，使用已验证的发布证据。不要要求先有 GitHub Release；也不要把正式安装包、PR merge 或 workflow success 编造为 GitHub Release 事件。
- 保留用户输入的原始版本标签。仅在证据明确时记录映射，如 `0.66 → 0.67` 对应实际 `0.6.6 → 0.6.7`；不要泛化此映射。
- 区分 workflow 的 `head_sha` 与真正打包的 source SHA。只用已核实的打包源 commit 比较 commits/PR。
- 按已安装的 `select-release-features` 或功能矩阵确定全部用户可感知结果。合并同一结果的多个 PR；标记内部改动、未上线功能和无法验证的项。
- 独立完整 walkthrough 覆盖任务中的全部可演示结果。由入口调用时以 feature-selection.json 的人工重点为录制范围，并保留完整功能矩阵；为每个入选可演示结果导出一份 GIF，不用 agent 推荐替换人工选择。
- 创建独立演示项目或可恢复副本。标明本地测试字幕、form、资产等 fixture；不把手工测试数据写成真实翻译、Agent 生成或付费请求的证据。

## 3. 发现 UI 与编写分镜

读取 [desktop-and-timing.md](references/desktop-and-timing.md)，再填 [recording-brief.template.json](assets/recording-brief.template.json)。

- 使用仓库 `templates/recording-TODO.md` 和 `templates/recording-plan.template.json`；逐步记录入口、目标、实测矩形、动作、状态断言、停留、镜头主体、保留上下文及 metadata 章节。讲解字幕仅在用户要求时填写。
- ChatCut Desktop 优先连接已验证的 Electron 页面和现有原生 API。确认 app 路径、版本、窗口与 CDP 端口；不要录成 Web mock。
- 捕获区须包含当前功能的入口、动作和结果。每次布局、菜单或 Inspector 改变后重新量取矩形。
- 安排可见鼠标移动、点击和真实拖动；选择状态必须能看见。程序直接改数据只可用来准备 fixture，不可替代录制中的用户操作。
- 用真实 UI 词语写分镜与章节；若用户要求讲解字幕，同样使用 UI 原词。给多选、字幕独立编辑等行为安排能排除歧义的对比。
- 默认 full MP4 保留完整应用画面。GIF 可按实测 ROI 裁切；只有生成并检查真实镜头动画后才能称为平滑 zoom。
- 保留必要上下文和至少 3 秒可读结果。普通光标不得挡住操作或结果；默认没有讲解字幕或可见章节角标。

## 4. 预演与录制

- 在 Mac mini 检查主机、磁盘、FFmpeg、ffprobe、应用及 pinned Playwright。Electron attach 不要求启动另外一个 Chromium。
- 通过 `/ui-demo` 的已核实 renderer wrapper 运行预演、录制、编码和抽帧。Work container 只编写脚本、做离线检查和读取返回图片。
- 每次预演和重录都先检查并恢复起始状态：选择项、checkbox、编辑文本、undo 状态、特效参数、布局和播放头。不要盲目 toggle 或依赖上一轮留下的状态。
- 预演须证明语义、选择器、状态变化、完整取景、依赖和 fixture 重置均通过。仅找到控件不算通过。
- 用当前操作真实演示处理过程。预先处理好的结果须注明；若把 video 演示改成 image，同步修改分镜、章节与范围，以及用户要求的讲解层。
- 将每次原始完整录制保存到独立 `raw/<attempt>/`，记录 SHA256、时长、尺寸、原声音轨及实际路径。保留所有已指定为 GT 的视频；派生物不能覆盖、改写或替换原片。
- 录制开始时设时间零点，记录单调时钟的 `elapsed_ms`、UI 状态与 frame 时间。完成文件后才生成 chapters。
- 若 Electron 使用时间戳帧序列，先在 Mac mini 按实际帧间隔组装完整 raw MP4；再从 raw 生成展示 MP4。不把帧数除以名义 FPS 当成原始录制时长。
- 完整展示 MP4 用 H.264、`yuv420p`、`faststart`；验证实际 pixel format，必要时显式转换 full/limited range。保留声音功能所需音频；无音轨的 GIF 不证明声音效果。

## 5. 剪出精确 8 秒 GIF

- 根据原片 marker 和实际像素选连续区间；不要固定截前 8 秒或硬编码上一版的秒数。
- 区间包含上下文、核心动作及至少 3 秒结果，且不跨入另一功能章节。用原片时间坐标记录 excerpt、proof 与 ROI。
- 默认 960px、12 FPS、无限循环；邮件规格按已核实的目标版式调整，常用 520px。不要为了体积静默缩到文字无法读。
- 使用 [make_gif_excerpt.py](scripts/make_gif_excerpt.py) 生成 8 秒 MP4、GIF、poster 和 contact sheet。先 `--dry-run` 验证计划；只有确认的 Mac mini 可实际编码。

```bash
# 在 /ui-demo renderer wrapper 内、确认的 Mac mini 上运行；从本次 marker 填入数值。
python3 skills/record-full-walkthrough/scripts/make_gif_excerpt.py \
  --source /absolute/run/raw/attempt-01/full.mp4 \
  --start ACTUAL_MARKER_SECONDS --chapter-end ACTUAL_CHAPTER_END_SECONDS \
  --proof-start ACTUAL_PROOF_SECONDS --proof-end ACTUAL_PROOF_END_SECONDS \
  --crop X,Y,WIDTH,HEIGHT --width 960 --fps 12 \
  --expected-host CONFIRMED_MAC_MINI_HOST --output /absolute/run/edits/v1
```

- `--dry-run` 不调用 FFmpeg 或创建输出；它不能核实媒体尺寸与时长。`--fixture` 只标记合成编码测试，不可用作真实产品验收。
- 检查 GIF 的实际 Graphic Control Extension 延时总和为 800 centiseconds、帧数为 `8 × fps`、循环为 0。脚本只修正一帧内的编码取整误差，不靠长时间冻结最后一帧凑时长。
- 输出目录已存在、区间越界、proof 不足、ROI 越界、超出体积预算或 GT 哈希变化时，拒绝通过；保留失败日志。

## 6. 检查与保存

- 在 Mac mini 用 ffprobe 检查完整 MP4 与 excerpt；抽完整 contact sheet、所有主要交互的密集 frame strip、每个章节边界和 GIF 序列。
- 返回并查看实际图片；检查空白帧、裁切、菜单、遮挡、术语、鼠标、状态变化及至少 3 秒结果。`metadata_pass` 不能代替视觉通过。
- 对 `pure-screen` 检查真实像素没有讲解字幕、发布角标或其他额外文字层；无 subtitle stream 不代表没有烧录文字。保留原生字幕演示。另记录 presentation 与 `textOverlays: false`。
- 将视觉结论另存 `qa.json`，包含检查人、时间、被检查文件 SHA256、图片路径和结果。编码脚本只返回 `visual_review: pending`。
- 遇到连接器输出上限时，用有界图片和二进制分块返回；验证每块长度及整文件 SHA256。不要把截断图片当成应用空白或视觉通过。
- 保存 full MP4、GIF、excerpt MP4、poster、chapters、manifest、QA、脚本与 evidence。用户指定 Drive 时核实目录 ID 和实际上传文件；未指定时使用当前持久保存能力。
- raw GT 使用已核实的归档位置，保留路径、ID、哈希和存储回执。未完成持久保存时，不写 `ready`。
- 完成持久保存和文件校验后交付文件链接。不要把录制授权扩大为发送广播、发表社交内容或修改线上 docs。

## 输出状态

| 状态 | 依据 |
| --- | --- |
| `placeholder` | plan-only 任务；只有准备计划 |
| `blocked` | 缺少真实证据、环境、驱动、依赖或保存能力 |
| `needs-visual-review` | 文件验证成功，实际像素尚未检查 |
| `fixture-only` | 合成编码或 UI fixture 测试，不能冒充产品验收 |
| `ready` | 版本与范围、真实录制、文件与视觉 QA、持久保存及交付均通过 |

遇到与 0.6.6 → 0.6.7 相似的版本定位、测试素材和 UI 行为时，读取 [verified-release-example.md](references/verified-release-example.md)。复用验证方法，不复用项目 ID、选择器、坐标、端口或剪辑秒数。

本次纯屏幕录制的实际脚本见 [examples/0.6.6-to-0.6.7/example.md](examples/0.6.6-to-0.6.7/example.md)。包含 bootstrap、可重复预演/录制、原生 bridge、编码与离线检查；该示例锁定历史演示副本，不会自动创建新客户项目或发出 Agent 请求。

## 队友共用 Mac mini

需要共用 Mac mini 时，先读取仓库根目录的 `docs/shared-macmini-recorder.md`，使用 `scripts/request_shared_recording.py` 和已有 GitHub 身份提交明确的手动录制任务。Mac mini worker 按本技能与已有 /ui-demo 执行；请求方查询同一 issue、下载校验后的素材或取消。任务访问码不进入仓库，不分享机主凭据。连接验证和 fixture 不能代替本技能的真实版本与画面验收。
