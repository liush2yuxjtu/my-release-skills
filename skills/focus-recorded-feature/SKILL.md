---
name: focus-recorded-feature
description: Create Screen Studio-style smooth zoom and focus MP4/GIF derivatives from immutable full GT recordings. Use for 聚焦录屏, zoom to a feature, focus an existing screen recording, batch feature demos, or 8-second GIFs from verified browser or desktop captures. Plan focus from actual frames, render on Mac mini, preserve source scope/audio/timing, inspect pixels, and verify Drive/Sites delivery when requested.
---

# Focus Recorded Feature

Status: IMPLEMENTED。复用完整 GT，生成聚焦 MP4 和 8 秒 GIF。支持一个功能或一批功能。
由唯一 chatcut-release 入口在有效 feature_shortlist 选择后按需自动调用，或用于已有手动素材任务。明确 plan-only 只规划；不增加录制/剪辑许可 gate，保存技能不启用事件 listener 或公开发布。

固定脚本和验收规则；让 agent 根据真实 UI 决定焦点、节奏和素材区间。

## 1. 锁定 GT 和演示范围

- 先读仓库 `AGENTS.md`、`config/release-policy.json` 和 `config/skills.json`。不要通过模板的 mode 启用占位 pipeline。
- 核实每条 GT 的实际文件、完整 SHA-256、尺寸、FPS、帧数、来源 Release tag/commit/channel 和已有 scope。版本字符串或已合并 PR 不证明功能上线。
- 保留 `operation`、`view`、`entry` 或 `partial` 范围。入口演示不能改写成端到端成功；旧版本 GT 不能证明新版本功能。
- 若没有合适原片，先调用现有 `$ui-demo`，在 Mac mini 按 brief → discover → storyboard → rehearse → record → inspect 录完整 GT。Desktop 必须使用已验证的原生/Electron 路线；不要用 Web 替代。不要覆盖已有技能。
- 原片只读。新录制与已有 GT 分开保存；不得用聚焦片、GIF 或冻结画面替换 GT。

## 2. 用真实画面编排镜头

读取 [计划与时间映射契约](references/focus-contract.md) 和 [交付验收](references/delivery-qa.md)。
将 [焦点计划模板](assets/focus-plan.template.json) 填成实例；按需复用仓库 `templates/recording-TODO.md` 及 `templates/recording-plan.template.json`。

- 为每条原片看全景、主要操作、弹窗、结果及关键转场。根据实际源帧和 runtime marker 填时间与 ROI，不从脚本执行顺序猜秒数。
- 使用「全景 → 操作控件 → 结果/下一步 → 全景」。开始和结尾各保留至少 0.4 秒全景。
- 所有镜头坐标都用解码源帧像素。独立转换窗口坐标、DPR 和裁剪偏移；CameraDriver 不改变 GuiDriver 的点击坐标。
- 为每个关键镜头声明 `required_regions`，包含目标及必要上下文。菜单位置改变后重新观察；不能沿用过期坐标。
- 默认 zoom 1.5–2.5，脚本上限 3。重复相同位置的关键帧表示停留；不同关键帧间用余弦缓动平移和缩放。
- 步骤标签使用实际 UI 名称。它们是编辑标记，不能伪装成捕获的鼠标事件。入口片保留 Entry demo 标识。
- 默认 GIF 选一个真实连续 8 秒区间，包含可见操作和结果。长录制不能直接截前 8 秒。
- 只有明确需要完整短片压到 8 秒时才用 `full-span-retime`；记录源区间映射，保留速度标识。脚本限定 0.5x–2x。结果停留不足时补录或标为 partial，不伪造证明。

## 3. 在 Mac mini 渲染

通过 Mac mini MCP 获取 Darwin、主机名、可用空间及 FFmpeg/ffprobe/Pillow。至少留 10 GiB。
不要从 Work container、MacBook 或 Grokbot 编码或抽帧。Grokbot 用于浏览器 QA；连接器失败时只复用已有 bridge，不重建 SSH/Tailscale 或凭据。

把技能脚本、填写后的计划及需要的 GT 传到已确认的 Mac mini 项目目录。传输前后核对哈希，不传凭据或浏览器 profile。大文件使用已授权文件传输；检查工具输出截断及 offset 单位。

从仓库根运行；在其他目录用解析后的绝对脚本路径：

```bash
python3 skills/focus-recorded-feature/scripts/render_focus.py \
  --plan focus-plan.json --output edits/focus-v1 --dry-run

python3 skills/focus-recorded-feature/scripts/render_focus.py \
  --plan focus-plan.json --output edits/focus-v1 \
  --expected-host "$CONFIRMED_MAC_MINI_HOST"
```

- Dry-run 可在其他主机执行，只核对计划、源文件哈希和路径；不检查媒体、不创建输出。
- 从本次 native preflight 设置 `CONFIRMED_MAC_MINI_HOST`，不能拿任意当前主机绕过限制。
- 非 ASCII 标签显式传 `--font`，确认字体有对应字形。不要安装付费编辑器来完成本流程。
- 新输出目录必须不存在。脚本检查整批输入后再创建目录；拒绝重复 ID、越界、裁掉必要 ROI、缺少全景、哈希不符和已有目录。
- 完整 MP4 保留 GT 视频时长、帧数、FPS 和音频轨道；输出 H.264/yuv420p/faststart。VFR 或偏移时间戳不在本版本支持范围，保留 GT 并准备单独的时间映射。
- GIF 使用 palettegen/paletteuse，8 秒、无限循环；可选 gifsicle 去除重复帧。实际帧数不必等于 FPS×8。
- 输出逐项 MP4、GIF、poster、contact sheet 及 `focus-manifest.json`。批次失败时保留已完成结果与 blocked 清单，换新 edits 目录修正，不覆盖。

## 4. 验收后交付

- 机器检查通过只能报告 `metadata_pass`。脚本始终保留 visual review pending；fixture 始终是 `fixture-only`。
- 把 Mac mini 生成的真实 contact sheets 带回 Work，用 `view_image` 检查所有功能。检查转场、焦点、菜单、文字、标签遮挡、结果及首尾；需要时在 Mac mini 抽更密帧条并试听音频。
- 对失败区间最小修正并另存版本，检查同一区间。记录检查人、时间、图像路径及结论。GIF 超预算时先改叙事或焦点；尺寸/FPS调整后重看文字，不静默降低清晰度。
- 只有文件、像素、来源范围、目标访问和持久保存均通过才标 ready。仅入口或部分证明要保留原 scope。
- 用户请求 Drive/Sites 时按 [交付验收](references/delivery-qa.md) 核实目标文件夹、回读数量/大小/父目录/权限，在原 Sites 提供聚焦与完整 GT 两种视角并用 Grokbot 验收。沿用用户指定 GT 目录，另建衍生目录；不改分享权限。
- 在已授权的 Airtable memory/TODO 中更新实际结果和链接，回读。不要重复创建完成事项；未来 GT 比对 TODO 保留。
- 仅制作素材时，不发送广播、不发表、不改账户配置。报告已完成的文件、真实验证、链接和实际阻塞。

## 验证资源

- `scripts/test_render_focus.py`：计划、几何、范围、不可覆盖及执行主机的确定性测试。
- `evals/trigger.json` 和 `evals/functional.json`：正反触发与任务级评测；保存原始输出。未运行的模型 eval 不计通过。
- [验证记录](evals/verification.json)：本次规则测试、Mac mini 实片/fixture 渲染、像素检查和独立 dry-run 试用的范围与限制。
