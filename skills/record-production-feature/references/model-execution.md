# Model execution evidence contract

模型依赖录制只接受 `live` 与 `captured-replay`。本契约和模板用于填写、逐项核查证据；仓库未实现通用 capture/replay adapter 或自动验证器，不把填了字段当成已经验证。

## Files and identity

- 每个独立 run 保存 `evidence/model-execution.json`，按 [live 模板](../assets/model-execution.live.template.json) 或 [replay 模板](../assets/model-execution.replay.template.json) 填写；所有路径相对该 run 目录。
- `feature.json.model_execution`、QA 与 `handoff.json.model_execution` 保留同一摘要：`mode`、`operation`、`run_id`、`evidence`、`current_live_e2e`、`source_live_e2e`、`disclosure`。`evidence` 指向完整模型证据；公开摘要引用可共享的脱敏版本。
- `operation` 区分 `fresh-recording`、`reuse`、`re-edit`、`replay-recording`。`mode` 描述原片中的模型来源；复用 live 原片仍是 live 来源，不是 captured replay。重剪另记 `edit_run_id`，保留原 `run_id` 与原片哈希。
- 摘要的 `disclosure` 是字符串，逐字保留所引用证据的 `disclosure.label`；完整证据中的 `disclosure` 则是含 label 等字段的对象。feature、QA 与 handoff 使用同一个摘要值，不翻译、扩写或另造标签。交接说明、来源未核验理由和译文写在独立 notes / handoff text，不能覆盖该身份字段。标签或证据不可读取时摘要用 null 并阻塞来源门禁，不补造可通过编码器的值。
- 复用/重剪时，本轮 `current_live_e2e=not-run`。原始完整模型证据保留当时的真实验收结果，不改写历史文件；当前摘要在 `source_live_e2e` 关联已核验的原 run、commit、surface、验收回执及哈希。来源未核验时用 null 并将来源门禁记为 blocked，不能凭 README 主张填 pass。这个摘要与原始运行证据的时间范围不同，必须明确标出。
- 产品本身不涉及模型推理的真实操作可用 `model_execution=null`，在 QA 说明观察到的原因与初态来源。预设模型回复、预填生成结果或伪造调用不能用 null 绕过；不新增“预生成结果”模型演示路线。
- 对每条媒体保留原片路径/哈希与 run/take id；已有 GT 重剪沿用原模型来源并另记编辑 run，不能声称新调用。不同版本、surface 和运行之间的证据不互换。

## Required evidence

| field | meaning |
| --- | --- |
| `schema`, `mode`, `run_id`, `phase` | `feature-model-execution/v1`；两种合法模式；本次运行；rehearse 或 record |
| `product` | 实际 commit、运行版本、surface，与媒体/来源证据一致 |
| `model` | 实际 provider、请求 model、服务披露的 model（未知用 null）、实际参数 |
| `fingerprints` | system/user/history、tools、演示输入与初态的内容指纹；方法和归一化规则可查 |
| `limits` | 录前确定的 take、整轮 live 请求（含预演/重试）、单请求和单 take 超时上限；可知时增加费用限制 |
| `requests`, `markers`, `takes_ledger` | 逐条请求/响应/工具关联、单调时间 marker、所有尝试记录；路径真实存在 |
| `raw` | 本 take 实际原片路径与 SHA-256；中途失败标明 incomplete |
| `outcome` | 业务断言、实际结果和证据；`pending` 不能当 pass |
| `current_live_e2e` | `not-run` / `pass` / `fail` / `blocked`；只有本 take 真实产品 live 流程可 pass；reuse、re-edit 与 replay 固定 not-run |
| `source_live_e2e` | fresh live 用 null；复用/重剪关联已核验的原 live 证据，未核验用 null 并阻塞来源门禁；replay 必须关联已通过的原始 live run、commit、surface 与证据/哈希 |
| `replay` | live 用 null；replay 必须有 source trace/capture/raw 哈希、逐步匹配报告、真实工具记录、网络模型请求数 0、timing 策略 |
| `disclosure` | live 记录实际模式；replay 的可见标签证据及交付文字必须同时存在 |

请求日志至少关联当前 run/take、序号、请求/响应指纹、实际 provider 请求/响应标识（若提供）、状态、耗时、usage（若提供）、工具调用/结果与 source event（replay）。调用数从逐条记录推导，不能直接相信 `liveModel=true` 或手写汇总。模型 usage 未提供或费用未知时如实标 unknown。

live 的可选请求 trace 捕获仅在已有内容披露授权内执行。原始请求、输出和工具结果存于授权归档，公开仓库只放无敏感信息的模板及脱敏摘要；不传凭据、cookie、profile、私人 receipts 或账户标识。脱敏文件单独记哈希，保留与原件的关联。

## Acceptance and delivery

- `current_live_e2e` 与媒体 `status` 是两项独立结论。live 模型成功后仍要做原有文件、像素、保存与访问检查；replay 媒体 ready 不会使当前 live E2E 变为 pass。
- replay source 必须按 live playbook 已验收通过，且与当前产品行为及请求匹配；旧代码、另一 surface 或另一轮提交门禁不能替当前素材补来源。匹配失败、工具失败、来源缺失或标签不可读则该素材 blocked。
- `disclosure` 的 replay 标签在模型动作前及相关 MP4/GIF 中清楚可见，裁切时作为必保留区域。默认文本为 `Recorded model response · real tools`；交付说明同时写“真实模型响应回放，工具真实执行；本次未做 live E2E”。
- 手写或生成的脚本模型、mock API、预填 Assistant/TODO/工具事件均禁止用于功能录制，包括 PR 和预演。编码/单元测试 fixture 独立标记，历史 fixture 原件和纠错记录保留审计，不重新用作功能素材。

## Playbooks

- [Live model recording](../playbooks/live-model-recording.md)
- [Captured model replay](../playbooks/captured-model-replay.md)
