---
name: create-release-social-cards
description: "Create source-backed bilingual ChatCut release social cards, editable templates, a searchable offline review gallery and checked ZIP packages. Use for 同风格图文、全部用户可感知功能卡片、中英双语发布素材、Google Drive 设计交接 or release social card batches. Reuse the approved 1080×1440 style, preserve PR/commit coverage and label footage, illustrations and unverified availability. Prepare review drafts without publishing."
---

# 制作发布图文审阅卡

Status: IMPLEMENTED · Role: on-demand helper for chatcut-release · Scope: review assets

由唯一公开入口 `/chatcut-release` 按需加载；不要求用户另调 helper，也不批量安装。使用同一固定 skills revision 的脚本与兄弟 validator。明确请求全量图文审阅稿时可在人工精选前做可撤销准备；保留唯一 `feature_shortlist`，已匹配的人工选择直接复用，不新增审批。

## 1. 定范围和参考样式

- 读取根 `AGENTS.md`、`config/release-policy.json`、`prompts/router.md`。使用用户已给定的区间；否则按当前入口的版本规则处理。保持真实 Release、workflow source 和手动 Git 区间三种来源身份，不把源码区间伪造为 Release 事件。
- 从完整 `pr-index.json` 与 `feature-matrix.json` 开始。通过 `skills/select-release-features/SKILL.md` 读取正文、diff、重要修复、行为变化、回滚、flag、平台和 backend 部署证据。需要完整 diff 声明时使用项目 `/verify` 的 diff audit。
- 使用 `google-drive` skill 查找用户指定参考包。优先读取原件，不靠文件名推断样式。复用账号，记录实际 folder/file ID、来源链接和读取时间；保留原文件，新输出存独立子目录。历史默认参考与流程见 [references/verified-workflow.md](references/verified-workflow.md)。
- 采用本次指定的 `all-user-aware` 范围时，为矩阵里全部用户变化（feature/fix/performance/behavior 的 include 和 needs_verification）制作审阅稿。所有排除项和未独立审阅的 commit 保留在原矩阵；不能把“来源齐全”写成“功能都没漏”。人工选题仍由已有审阅 skill 执行，不把这些全量卡当作精选或发布许可。

### 已选宣传图文

旧 create-image-text-assets 名称转发到此 helper。全量审阅保持 all-user-aware；宣传图文使用 `scope: selected`、匹配的 scope_hash，features 只含已选且 include 的 IDs。原完整矩阵/源索引不删。prepare 在原参数之外传 `--selection --audit --diff-manifest，Desktop 另传 --context，GitHub 另传 --event`，重新执行 selection gate 并比对原人工决定后才生成。若 selected IDs 为空，不制造宣传封面；保留必要通知的事实文案。fixture 需显式 --fixture，不能升级为真实验收。

## 2. 填双语卡片和界面证据

- 按 [references/card-contract.md](references/card-contract.md) 填写 [assets/social-cards.template.json](assets/social-cards.template.json)。以用户动作、前后行为和收益写标题；保留来源 ID/URL、平台/套餐/上线限制和最小补证动作。没有测量证据就不写提升百分比。
- 使用既有完整 raw GT 或真实截图。下载后核对 manifest 的字节数与 SHA256；逐帧挑选功能实际显示/操作的画面，记录视频链接、时间、frame SHA256、build 和 scope（operation/view/entry/partial）。主音量表、项目库、账户菜单必须正在显示；入口截图不能证明完整结果。
- 新录制调用已有 `/ui-demo` 及录制 skill，保留不可变 raw GT。此图文 skill 不自行录制；缺录屏仍可制作标明 `illustrative-ui` 的审阅示意。用源码核实文字和界面结构；不得用示意图、代码存在或 Desktop 构建成功代替可用性验收。
- 使用 `imagegen` 生成创意封面时记录 `AI-generated-marketing-cover`，只作为营销视觉。精确产品界面与图文排版使用模板代码。封面可用排版模板，不要求每次生成新图。
- 保持浅灰底、ChatCut mark、黑色大标题、灰色副标题、白色圆角功能面板；默认 1080×1440、CN/EN 两份。不要把英文机器直译塞进单行。真实界面只允许忠实裁剪，不改造按钮和结果。
- 要复用本次实际的色轮、字幕、音色卡、账户与导出等专用视觉组件，读取 [历史原样模板](assets/historical-0.5.16-to-0.6.6/snapshot.json) 与其中的 `card-template.js`、81 项双语 `features.json`。它们按字节保存本次真实生成源；素材从原 Drive 包取回。新生成器提供通用起点，按实际用户结果扩展专用组件。历史版本、坐标、标签和统计不能直接套到新 release。

## 3. 生成并验证

从仓库根运行；所有命令中的路径替换为本次真实输入。依赖与完整调用见 [references/card-contract.md](references/card-contract.md)。`prepare` 拒绝覆盖，生成器不下载、不发送、不登录。

```bash
python3 skills/create-release-social-cards/scripts/social_cards.py prepare \
  --manifest /absolute/path/social-cards.json \
  --pr-index /absolute/path/pr-index.json \
  --feature-matrix /absolute/path/feature-matrix.json \
  --media-root /absolute/path/assets \
  --font /absolute/path/NotoSansSC.ttf \
  --font-license /absolute/path/OFL.txt \
  --output /absolute/path/new-social-cards

node skills/create-release-social-cards/scripts/render_cards.cjs /absolute/path/new-social-cards

python3 skills/create-release-social-cards/scripts/social_cards.py finalize \
  --output /absolute/path/new-social-cards
```

- `prepare` 运行现有 feature matrix 校验器，核对完整来源集合、release 上下文、全部用户候选、唯一 ID、双语文案、frame 哈希和字体覆盖；保留未验证状态。
- `render_cards.cjs` 等待字体与图片加载，检查 JS 错误、1080×1440、标题/副标题/面板边界，写 `sources/render-qa.json`。新标题、示意或裁剪必须实际运行。
- `finalize` 重新读取每张 PNG，核对数量、尺寸和哈希；生成自包含 `gallery.html`、预览、两份全量 contact sheet、CSV、完整/CN/EN ZIP 和 CRC 报告。
- 按 [项目验证 surface](../verify-chatcut-release-skill/references/social-cards.md) 操作实际审阅页：搜索 PR、切换语言和筛选、检查来源 anchor、复制文案、下载 PNG，并核对下载字节。链接外部访问另行记录。至少检查一张真实 frame、一张示意、封面、最长中英文标题和多行限制；每张图用 contact sheet 检查，异常项放大复核。文件 PASS 与视觉/内容验收分开。
- 将视觉观察和缺口写入 `sources/visual-review.json`，重新 finalize。模板不自动把视觉审阅标为通过。最终发布前仍需目标版本可用性及人工精选；这里只产审阅稿。

## 4. 交付

- 完整包含可编辑 HTML/CSS/JS、manifest、矩阵、原 source index、双语 PNG、CSV、预览、QA、排除项、待核实项、字体授权及 SHA256SUMS。不要重复打包大型 raw 视频；保留逐项真实链接、GT manifest 和范围。
- 用户要求 Drive 交付时，按 google-drive skill 在原参考目录下建立本次独立目录，上传完整和分语言包；核对 file ID、size、可用校验字段并按连接支持下载复核 SHA256。不修改 sharing，不覆盖原件。链接可访问性和字节校验分别报告。
- 仅保存到仓库不触发 Drive 上传、飞书发送或公开发表。对外动作按已有授权与 handoff skill 处理；保留当前人选 feature/channel 门槛。无需重复询问已经授权的制作/保存工作。
- 输出文件和尺寸检查、来源覆盖、视觉审阅、生产可用性、人工选题、Drive 上传各自状态；未运行就写 not_run，未验证写 pending，禁止合并为一个模糊 PASS。

## 5. 修改后做 functional evals 和 trigger evals

修改说明、模板或生成器时，读取 [references/evaluations.md](references/evaluations.md)。按 Anthropic skill-creator 的「任务 → 独立新旧版运行 → 基于产物评分 → 审阅 → 修订」循环使用 [evals/evals.json](evals/evals.json) 的 3 个 functional 场景；对照使用修改前固定 revision，保留真实产物、trace、断言证据和时间/token，不把脚本单测当作模型评测。

用 [evals/trigger-eval.json](evals/trigger-eval.json) 的 20 条真实表达检查入口是否按需加载本 helper。保持 `allow_implicit_invocation: false`；正例测入口加载，负例覆盖纯文案、录制、审计、飞书消息卡和普通 UI。固定 60/40 train/test，默认每条 3 次，未完成/超时记 BLOCKED，不计为正确未触发。留出集不用来改描述；正式批次与 eval 的合成输入、临时 probe、评分文件分开。
