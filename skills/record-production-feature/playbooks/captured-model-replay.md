# Captured model response replay

用于已有成功真实模型运行，需要反复调整取景、鼠标与节奏的功能录制。只回放真实 API 响应边界，产品 UI 与工具仍实际执行。优先直接复用/重剪合格 live 原片；重放必须创建独立 take。

本 playbook 不提供 replay adapter。先检查项目是否能捕获和严格匹配真实模型请求/事件；缺失时保留计划并标 `blocked`，不得用脚本模型近似实现。

## 1. 验证 capture 来源

1. 来源必须是按 [live playbook](live-model-recording.md) 在真实产品同一 surface 中完成并通过业务验收的运行；保存原始 run、产品 commit/版本、provider/model、prompt/工具/input/初态指纹、请求响应序列、实际工具结果、时间戳及完整原片哈希。
2. 由已有授权调用捕获实际响应，保留原始事件及顺序。校验原 trace/capture SHA-256，并将脱敏副本与原件分别记哈希；脱敏副本不能用来改写模型实际输出或声称与原件逐字节相同。
3. 录制代码、模型配置、prompt、工具契约、演示输入与起始状态须与来源匹配。影响模型输入或行为的变化需要新 live capture；另一 surface、旧版本验收或提交 hook 的 live 调用不能补作当前素材来源。
4. 手写回复、由 agent 新生成的“示例回答”、返回合成答案的 mock server、预置 Assistant/TODO/工具成功事件，以及把多个 live take 的片段拼成一次对话，均不属于 capture，即使写了 replay 标签也禁止使用。

## 2. 建立严格匹配

- 从 [replay 模板](../assets/model-execution.replay.template.json) 建立当前 `evidence/model-execution.json`，关联原始 live 验收、source trace/capture/raw 哈希与当前 take。当前 `current_live_e2e` 固定为 `not-run`，source live E2E 另记 pass 和原始证据。
- 匹配 provider/model/参数、完整 system/user/history、多模态附件内容、工具 schema、前一步工具结果及顺序。先比较当前请求指纹，再返回该步骤唯一的捕获响应；禁止按“第 N 次调用”单独匹配。
- 回放 adapter 可在模型传输边界拦截请求，但每个返回事件都必须映射到已验证原始 capture；拦截本身不授权编造响应或填充产品状态。
- 只允许预先列出并验证的无语义差异归一化，例如 transport request id、临时时戳或相同演示副本的路径。规则和前后指纹留证据；不能忽略实际任务内容、工具参数、消息顺序或工具执行结果。动态 tool-call ID 如需映射，保持一对一并验证后续结果关联。
- 多步 Agent 的工具实际读取/修改当前演示文件、运行测试并返回结果；逐步与来源核对。不得回放旧工具结果冒充执行；工具失败或结果不匹配时停止后续模型响应，不能强行播放成功结论。
- 严格区分模型响应与工具响应。所有模型响应必须有来源事件映射，包含真实的 tool-call 参数、finish/error/usage 事件；若演示 streaming，必须保留实际 chunk 顺序和相对时间，不能把最终文本人为拆成“生成中”。
- replay 阶段禁止向模型 provider 发新请求，检查实际外发模型请求数为 0。未匹配、缺事件、额外调用、未消费尾部、工具错误或校验失败均使该 take 失败；不静默转 live/scripted，不返回默认成功。

## 3. 在真实产品中预演与录制

1. 恢复匹配的独立演示项目/初态，接入已验证的 adapter，完成原有 discover/rehearse 门禁并验证一个不匹配请求确实会停止。
2. 触发模型动作前，让界面模型名称或持续可读来源标签显示 `Recorded model response · real tools`。来源标签是 pure-screen 的必要例外，必须覆盖最终 MP4/GIF 相关区间；无法做到则 `blocked`。
3. 录制用户输入、真实产品状态、模型回放、真实工具执行与最终结果。为每个请求记录匹配的 source event、指纹、时间、实际工具结果和 outcome；保留本 take 的完整 GT/marker/哈希及失败记录。
4. 默认按源时间间隔回放。若单独调整等待节奏，声明 timing 策略和时间映射并标明压缩；任何 replay 的当前耗时都不作为 live 延迟/性能证明。
5. 基于实际状态做业务断言与帧/timing 检查，结果可读至少 3 秒。匹配成功不能代替当前工具结果和媒体视觉验收。

## 4. 交付与可用范围

- feature、QA、handoff 与公开交付说明都写 `mode=captured-replay`、source live run/版本/surface、当前 replay take、严格匹配结果及 `current_live_e2e=not-run`。来源 live 验收的日期、版本与通过状态保留原意。
- 素材可在来源、匹配、工具、来源标签、业务结果和原有媒体验收都通过后 ready；报告为“真实模型响应回放，真实工具执行”。不能称当前 take 新增真实 API 调用、再次证明自主诊断或通过 fresh live gate。
- crop/zoom/GIF/去讲解字幕均保留来源标签和证据关联；不能将 replay 成片改名为 live。已有历史 scripted/fixture 素材只作审计，不转成 capture。
- 项目自己的 `/verify`、发布和提交约束照常适用；要求新 live E2E 时 replay 无法替代。没有可验证 capture 或匹配失败就交付真实阻塞及已完成部分。
