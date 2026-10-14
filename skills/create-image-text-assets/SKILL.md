---
name: create-image-text-assets
description: "Route ChatCut image-text requests to the implemented bilingual social-card generator. Preserve all-candidate review and human-selected promotional scopes."
---

# 图文素材兼容入口

Status: IMPLEMENTED · Role: compatibility adapter · Canonical: create-release-social-cards

由唯一 `/chatcut-release` 入口按需读取。保持同一 skills revision、已有人工选择和原发送/保存边界。

读取同 revision 的 [create-release-social-cards](../create-release-social-cards/SKILL.md)，直接执行其生成、渲染、gallery、PNG 与 ZIP QA 流程。保留全部来源、真实截图/示意标注；缺独立平台参考只能报告 approximate。

- 全量审阅使用 `scope: all-user-aware`；包含 include 和 needs_verification，后者明确待核实。可在唯一精选前准备审阅稿。
- 宣传素材使用 `scope: selected` 和真实 selection 的 scope_hash。`social_cards.py prepare` 必须同时传 `--selection --audit --diff-manifest，Desktop 另传 --context，GitHub 另传 --event`，结合原完整 `--pr-index --feature-matrix` 重算 gate；只渲染明确选择的已验证 IDs。全量矩阵和来源仍存入包，不缩减为精选输入。
- 其余生成参数与 canonical helper 相同。显式 plan-only 返回计划和 completed_actions: []。缺画面可用有标注的示意，不伪造 UI、上线或像素级验收。

旧调用名和目录保留；实际输出采用 social-cards 的已验证包结构，不重复实现图文生成器。
