---
name: preview-release-content
description: "Internal chatcut-release helper to reproduce release text and images inside reference-backed platform mock-up boxes. Use for 邮件或小红书发布效果预览、全平台内容截图、pixel-level platform previews or preview release content. Measure real references, rebuild editable HTML/CSS, render screenshots and compare pixels without publishing, recording video or creating a design system."
---

# 平台图文发布效果预览

Status: IMPLEMENTED · Scope: offline_platform_previews

由唯一 chatcut-release 入口按需加载。把确认后的文字、图片放进平台界面框，让人看到完整发布效果。
默认只做图文，视频留占位。先读根 AGENTS.md、release-policy 和已有决定；发布稿复核有效功能选择。
手动示例复用用户明确内容，不虚构 Release。用户要求先确认文字时，未确认前仅做界面标定和空位稿。
此 helper 不实施或伪造未来的独立文案/最终预览审批。它不发消息、不保存平台草稿、不发表。

## 1. 固定独立参考

读 [预览契约](references/preview-contract.md)。复用已授权真实平台预览、邮件客户端截图或用户给定截图，
先实际查看，再保存来源、时间、客户端/版本、主题、语言、视口、设备像素比、字体、范围及 SHA256。
缺参考时仍制作明确标记 approximate 的稿，fidelity 保持 pending，不宣称像素级复现。
不发测试帖、不新增登录、不改权限。参考不能来自候选模板；fixture 仅用于工具验证。

## 2. 复现平台界面框

从参考量取外框、栏、头像、标题、正文、图片、行距、间距、圆角和按钮，编写该平台具体 HTML/CSS。
不要做新 design system 或装饰性营销卡。先用参考图的同一内容标定，再换已确认的本次文案和真实配图。
参考仅作对照，不能贴整张截图为背景/遮罩，冒充可编辑复现。
[platform-box.html](assets/platform-box.html) 是近似起点，必须按真实参考另存 measured template。
逐平台逐设备保存，邮件记录具体客户端；一个框不代表所有客户端。保留完整文字，长文真实会折叠时
同时导出收起和展开两种状态；不得默默截断。无图显示占位，多图按参考顺序扩展。
不伪造点赞、评论、账号身份或发布成功状态。

## 3. 渲染与像素验证

复用已有 Playwright 环境，Web 浏览器验证优先 Grokbot；不买服务或安装新浏览器。
从本 skill 目录运行，替换所有真实路径：

```bash
node scripts/render_mockup.cjs --manifest /absolute/preview.json --output /absolute/NEW_RENDER
python3 scripts/pixel_diff.py --reference /absolute/reference.png \
  --candidate /absolute/NEW_RENDER/preview.png --output /absolute/NEW_DIFF
```

固定 viewport、DPR、浏览器和字体。渲染器屏蔽 HTTP，等待字体/图片，拒绝溢出和不稳定截图。
像素工具逐像素按原尺寸核对，默认零误差；不缩放、自动对齐、模糊或遮住不同文字图片。
容差必须事前写明固定值和理由，不能看到 FAIL 后调阈值。保留 diff、overlay 和报告；禁止覆盖证据。
PASS 只证明给定 PNG 的像素关系，不能证明独立来源或实际发布。两个生成图/合成图的 PASS 不是平台验收。
旧内容标定通过后换新内容，只能称 mock-up；必须有独立同内容平台截图才能报告发布稿 pixel PASS。

## 4. 检查与交付

查看实际 PNG，核对全文、图片顺序、裁剪、CTA、版本、限制、占位、中文/英文和最长内容。
输出 preview-index.json，每个平台/设备/状态记录文案、图片、模板、参考和截图哈希、比较范围、
实际结果、缺口、content_visual_review 与 human_review（默认 pending）。分别记录像素差异、
内容正确、布局、真实平台预览及发布状态，不能合为一个 PASS。
交付可编辑模板、完整截图、参考/差异/局部放大和报告；复用 handoff-release-pack 准备交接。
发送仅由既有发送 helper 按已授权目的地处理，此 helper 不改目的地。公众号发表由用户完成。

## 验证

运行实际 renderer/pixel CLI，覆盖同内容、单像素改变、尺寸错误、长文和重复目录拒绝。
读 [eval cases](evals/evals.json)，使用项目 verifier 的 platform-content-preview surface 留证。
fixture、单测、真实平台参考、独立 consumer 与模型评测分开；未运行写 not_run。
