---
name: update-release-docs
description: "维护 ChatCut 正式发布文档：核验 production 上线、更新 ChatCut Landing 的版本信息、更新日志和相关产品文档、创建 beta PR，并按配置发布飞书通知。适用于每周或手动发布文档维护，不用于产品代码实现或 beta-only 变更。"
---

# ChatCut Release Docs

Status: IMPLEMENTED · Role: on-demand internal helper

由 chatcut-release 调用时复用已核实的 production 范围、完整 feature matrix 和 feature-selection.json；不再要求人工确认版本或草稿。只准备可回滚内容 PR/预览，不合并或部署。精选项决定宣传优先级；完整已验证功能及必需行为通知仍可沉淀为文档。beta 仅生成隔离草稿，不改正式版本/production Changelog。

入口流程不使用定时维护专属飞书通知授权。若当前任务已有该通知的明确授权，依原规则发送；否则只生成通知草稿并记录 not_sent，不提出第二个人工问题。

把已经正式上线、用户可感知的 ChatCut 变化沉淀到 Landing，让用户和 Agent 能搜索到当前能力、适用端和最低版本。没有足够重要且证据完整的变化时，不制造更新、不创建空 PR，也不发送飞书通知。

这套流程与 `product-help` 的内容维护无关；Landing 英文文档是 Agent 搜索的权威产品信息，Product Help 只是消费者。

## 开始前

1. 确认两个仓库位置，不要假设另一台电脑沿用旧绝对路径：
   - ChatCut 产品仓库：产品实现、production 发布和版本证据，只读使用。
   - `chatcut-landing`：实际修改、提交和开 PR 的仓库。
2. 分别读取仓库的 `AGENTS.md` 或等价开发规则。
3. 拉取最新远端。Landing 一律以最新 `origin/beta` 为目标基线，在隔离 worktree 或独立 checkout 中工作，不碰用户正在使用的主 checkout。
4. 打开 Landing 当前版本、最新 Changelog 和相关普通产品文档，先确定已有记录的截止点。

换机或重新创建定时任务时，先读 [references/transfer-and-automation.md](references/transfer-and-automation.md)。

## 核验正式上线

从 Landing 最新日志之后开始检查：

- 成功完成的 production 部署或正式客户端 / 插件发布；
- 最终合并并实际进入该发布的代码；
- 与代码和部署结果一致的 PR、release 或 workflow 记录。

PR 标题、提交标题、中间讨论和飞书通知只能帮助定位，不能单独证明产品行为。必须交叉检查最终代码和成功发布结果。

只记录已经正式上线且用户能感知的功能或修复。排除 beta-only、已回滚、实验未放量、监控、CI、重构、内部迁移和无用户行为变化的维护工作。证据不足时宁可暂不收录，并在运行结果中列出缺口。

平台和版本判断、内容结构、文案边界详见 [references/content-contract.md](references/content-contract.md)。

## 更新 Landing

有值得记录的变化时：

1. 更新 Current Versions 及其数据源。
2. 新增或补充 Changelog release；按“功能更新 / 问题修复 → 功能模块 → 具体变更”组织。
3. 如果上线内容改变了当前操作方式、能力范围、限制或版本要求，同步修改对应的普通产品文档。
4. 英文文档是 Agent 搜索和读取的权威内容；简体中文页面面向用户本地化，并与当前产品界面术语一致。不要为 Agent 复制第二套页面。
5. 文案只写用户能看到、理解和使用的结果，不写内部维护流程、实现细节或非产品化供应商名称。

页面开头给出本次 Web、Desktop、Agent Plugin 的版本状态。具体条目默认不重复列平台；只有支持范围存在例外时才单独说明。不要在条目下堆重复表格。

## 验证与 PR

按仓库现有脚本运行与改动相称的检查，至少覆盖格式 / lint、完整 build、内部链接和浏览器导航。构建若刷新与任务无关的生成文件，只还原该生成噪声，不覆盖其他人的改动。

使用 `codex/weekly-changelog-YYYY-MM-DD` 分支。创建前检查同一周是否已经有本流程创建的开放 PR；有则更新原 PR，不重复创建。

PR 必须：

- 目标分支为 `beta`；
- 标题和正文使用英文；
- 列出日志日期范围、Current Versions、同步修改的普通产品文档、production 证据、验证结果和可审核的预览链接；
- 明确排除仍为 beta-only 或证据不足的版本；
- 创建后附加到当前任务。

## 飞书交付

基于最新 `origin/beta...PR head` 的最终 diff 生成中文摘要；不要复述迭代过程或已经撤回的内容。优先使用 `$summarize-pr-for-feishu` 和 `$publish-pr-to-feishu-bot`，若目标环境没有这两个 skill，则遵守以下同等约束：

- 默认群：`ChatCut PRs`，以 bot 发送；不要搜索群历史做去重。
- 固定 reviewer：王若帆 Ruofan Wang。
- 固定 cc：Anchor（Fan）。
- 每次发送前通过群成员数据重新确认两人的真实 Feishu identity；不得仅凭显示名猜测，也不得用纯文本 `@` 代替真实 mention。
- 消息首句以 `【辛苦@王若帆 Ruofan Wang review】` 收尾；正文末尾独立一行 `cc：@Anchor`。
- 保留可点击 PR 链接、所有编号、完整的“具体问题 / 具体需求 / 目标”和“这次怎么解决”、边界与验证信息。
- 除非用户明确要求，不附截图。
- 发送后只回读本次 API 返回的 message ID，核对群、bot、正文、链接、reviewer 和 cc mentions；返回 PR、预览、飞书消息链接和 ID。

Fan 已明确授权“定时维护模式”在 PR 检查通过后直接发送上述飞书通知，不需要逐次展示文案或等待确认。此持续授权只适用于按本 skill 配置的定时任务；手动调用或其他用户场景仍遵守当次请求和发布 skill 的确认边界。
