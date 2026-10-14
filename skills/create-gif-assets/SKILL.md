---
name: create-gif-assets
description: "Create an eight-second GIF from verified immutable ChatCut raw footage through the shared media helpers, with actual duration and frame QA."
---

# GIF 素材兼容入口

Status: IMPLEMENTED · Role: compatibility adapter · Canonical: record-production-feature

由唯一 `/chatcut-release` 入口按需读取。保持同一 skills revision、已有人工选择和原发送/保存边界。

复用同 revision 的 [record-production-feature](../record-production-feature/SKILL.md) 或 [record-full-walkthrough](../record-full-walkthrough/SKILL.md)；只在本次需要 GIF 时加载。没有真实 raw GT 就按 canonical helper 录制或写 blocked，不以 mock/动画代替产品演示。

production 单功能调用其 `build_feature_media.py --format gif`；walkthrough 调用其 `make_gif_excerpt.py`，使用真实 chapter 内连续 8 秒和至少 3 秒结果停留。需真实聚焦时复用 [focus-recorded-feature](../focus-recorded-feature/SKILL.md)。参数和 host 检查遵循原 CLI，不填历史秒数或默认猜缩放。

保留 raw/hash、marker/chapter、GIF 实际时长/帧数、来源区间、字节预算、poster/contact sheet 和视觉 QA。纯屏幕、标准指针，不默认字幕或版本 badge。编码 metadata PASS 不等于画面可读或功能可用。宣传范围重用唯一人工精选；plan-only 不编码，不发送广播。
