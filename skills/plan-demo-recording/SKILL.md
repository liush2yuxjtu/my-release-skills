---
name: plan-demo-recording
description: "Prepare the real recording brief, discovery, storyboard and rehearsal through ChatCut recording helpers. Default release assets remain image/text."
---

# 录制分镜兼容入口

Status: IMPLEMENTED · Role: compatibility adapter · Canonical: record-full-walkthrough

由唯一 `/chatcut-release` 入口按需读取。保持同一 skills revision、已有人工选择和原发送/保存边界。

默认发布素材为图文；仅本次功能确需操作演示或用户要求时进入录制。读取同 revision 的 [record-production-feature](../record-production-feature/SKILL.md)（已验证 production 单功能）或 [record-full-walkthrough](../record-full-walkthrough/SKILL.md)（beta/整版），然后复用已安装 /ui-demo。

实际填写 `templates/recording-TODO.md`、`templates/recording-plan.template.json` 和 canonical helper 的 brief；执行发现真实 UI → 分镜 → 预演，保存 discovery、storyboard、TODO、typed plan 与 rehearsal。规划不冒充录制。缺真实 build/driver/登录只阻塞录制分支。

分镜基于已选功能、真实语义目标和最终可见结果；不固定历史坐标、端口或剪辑时间。宣传录制须重用唯一 feature_shortlist；不再问录制许可。默认纯屏幕、标准指针、不加解释字幕和 release badge。输出准备证据和真实缺口；plan-only 的 completed_actions 保持空。
