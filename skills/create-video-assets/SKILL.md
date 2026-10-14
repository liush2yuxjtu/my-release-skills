---
name: create-video-assets
description: "Create video derivatives from immutable verified ChatCut recordings using the existing production-feature or walkthrough helpers."
---

# 视频素材兼容入口

Status: IMPLEMENTED · Role: compatibility adapter · Canonical: record-production-feature

由唯一 `/chatcut-release` 入口按需读取。保持同一 skills revision、已有人工选择和原发送/保存边界。

先读 [record-production-feature](../record-production-feature/SKILL.md) 或 [record-full-walkthrough](../record-full-walkthrough/SKILL.md)。有匹配 raw GT 就复用；没有时按需要进入其实际录制流程，缺环境则 blocked。默认图文任务不自动产生视频。

已验证 production 单功能复用 `record-production-feature/scripts/build_feature_media.py --format mp4` 和原 feature manifest；beta/整版复用 walkthrough 的连续 raw/完整 MP4 及其版本、chapter、持久保存验收。真正需要聚焦时再读取 [focus-recorded-feature](../focus-recorded-feature/SKILL.md)，不重写编码器。

raw MP4 不可变，派生 MP4 另存；实际 ffprobe/decode、时长、H.264/yuv420p、hash、帧和音轨检查完成后再交付。编码通过仍保持 visual_review: pending，须检查真实画面和 scope。宣传范围绑定人工已选 IDs；不新增录制审批，不发送、不公开发表。显式 plan-only 不运行编码。
