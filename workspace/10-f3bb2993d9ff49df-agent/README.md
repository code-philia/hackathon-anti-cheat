# ARC-Bench Agent Starter

这个参考 agent 会先初始化一个起步应用，然后让 Codex 逐次实现 `ROOT` 的一个直接子子树。

## 需要修改什么

- `main.py`：Codex agent 的入口。
- `template/`：起步应用。其内容会被直接复制到输出目录。

## 入口契约

ARC-Bench 按如下方式运行你的 agent：

```bash
python3 main.py /path/to/requirements --output-dir /path/to/output --type web
```

输入目录必须包含 `id: ROOT` 的 `requirements.yaml`。ARC-Bench 会在调用 agent 之前先在
`--output-dir` 中准备好权威任务应用（包括所选进化基线）。独立运行时，如果本地存在
`template/` 目录，agent 也会将其复制过去。随后它会把每个 ROOT 直接子子树依次交给 Codex
处理，所有模块都修改同一个输出目录。

捆绑的 `skills/` 目录会被复制到输出项目中的 `.codex/skills/`。Codex 会被告知 skills 的位置，
在需要时可以调用其中的脚本完成运行时进度上报、可追溯性与 git 检查点等操作。
两个开关控制复制与指令注入：前端交互规范默认开启，运行时遥测默认关闭（见下）。

### 前端交互规范（可选，默认开启）

`arcbench-frontend-spec` skill 记录了一份与具体任务无关的前端交互设计规范（可见性一致性、
可访问名唯一、明确的操作反馈）。开启时，Codex 的 developer 指令会要求它在实现任何前端交互
代码前先阅读 `arcbench-frontend-spec/SKILL.md`，并且该 skill 会被复制进输出项目。

通过环境变量 `ARCBENCH_FRONTEND_SPEC` 切换：

- `1`（默认）：注入指令 + 将 skill 复制进产物。
- `0` / `false` / `no` / `off`：不注入指令 + 产物中排除该 skill
  （`skills/` 下的源目录不受影响）。

要彻底卸载，还需删除 `skills/arcbench-frontend-spec/` 目录。

### 运行时遥测（可选，默认关闭）

`arcbench-checkpoint`、`arcbench-runtime-signals`、`arcbench-traceability` 三个 skill 只服务
ARC-Bench 运行时前端的展示（git 检查点、进度上报、可追溯性），不参与也不约束代码生成，
每次调用都会消耗 Codex 的轮次。默认关闭，把模型轮次留给实现本身；需要前端实时进度/追溯
视图时再开启。

通过环境变量 `ARCBENCH_TELEMETRY` 切换：

- `0`（默认）：不注入遥测指令 + 产物中排除这三个 skill
  （`skills/` 下的源目录不受影响）。
- `1` / `true` / `yes` / `on`：注入指令 + 将 skill 复制进产物。

注意：关闭遥测不影响 `.arc/completed_modules.json` 的断点续跑机制（`main.py` 自身维护），
也不影响代码本身。

## 模型变量

runner 会注入：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `MODEL`

Chat Completions 与 Responses 的示例见 `examples/model_calling.py`。

### 视觉参考图分析（可选，默认开启）

需求描述里的参考截图（`![image](./reference/xxx.png)`）会先交给一个独立的
视觉模型转成文本分析，再以 `## Reference image analyses` 段注入每个模块的
prompt，让 Codex 主流程无需多模态主模型也能照着截图实现。

runner 会注入（缺省时逐级回退主模型）：

- `VISUAL_MODEL`（视觉模型，如 `kimi-k3`；缺省回退 `MODEL`）
- `VISUAL_API_KEY`（缺省回退 `OPENAI_API_KEY`）
- `VISUAL_BASE_URL`（缺省回退 `OPENAI_BASE_URL`）

通过环境变量 `ARCBENCH_VISUAL` 切换：

- `1`（默认）：启用视觉分析。实际只在子树引用了图片 **且** 视觉模型配置
  可用时才真正调用；否则打 warning 并继续纯文本 prompt。
- `0` / `false` / `no` / `off`：不注入视觉分析段。

失败优雅降级：图片缺失 / 未配置模型 / API 报错只打 warning 并跳过该图，
Codex 主流程始终以纯文本继续。分析结果缓存在
`<output-dir>/.arc/visual_refs_cache.json`（按文件 mtime+size+prompt 版本
做 key），跨模块复用，避免重复调用。实现见 `visual_refs.py`。

### 执行复杂度档位（可选，默认 L0）

档位控制每个模块 prompt 的"执行复杂度"，在保证平台评测分数不受影响的前提
下省 token。配置方式（优先级从高到低）：

1. 环境变量 `ARCBENCH_EFFORT=0|1|2|3|4`（运行前注入）；
2. `main.py` 文件头部的 `ARCBENCH_EFFORT_DEFAULT` 常量（默认 `0`）。

| 档位 | 测试策略 | 契约 | 预期 token |
|---|---|---|---|
| `L0` (0) | 基线（旧行为） | 完整 9 条自证契约 + 逐条证据罗列 | 最贵 |
| `L1A` (1) | **保留测试**（最保守） | 完整契约 + 结论一行 | 省最少 |
| `L1B` (2) | 禁完整套件，**允许一次 build/tsc**（折中） | 完整契约 + 结论一行 | 省 15–25% |
| `L1C` (3) | **禁跑测试套件**（最激进） | 完整契约 + 结论一行 | 省 15–25% |
| `L2` (4) | 禁跑测试套件 | 四铁律压缩契约（精确可访问名/角色/hover opacity/fixture 限定词） | 省 35–50% |

**L1A / L1B / L1C 只差"测试策略"一个变量**，契约与其余行为约束完全一致，
且按强度递增排列（A 最保守 → C 最激进），适合做对照实验决定长期默认档。
铁律不可删：四条铁律是 P3 用 26 个失败换来的全部根因（见 `CONTRACT.md`），
平台 strict 测试逐字断言，任何档位都保留。实现见 `main.py` 的
`effort_level()`、`effort_label()` 与 `_contract_section()`。

### Token 计量（默认开启）

每次模型调用的用量逐行记入 `<output-dir>/.arc/token-usage.jsonl`（append-only JSONL），
字段：`phase`（`module` / `repair` / `vision`）、`kind`（`model_call` / `turn_total` /
`vision_call`）、`module_id` / `module_index` / `attempt`、`turn_id` / `thread_id`、
`input_tokens`、`cached_input_tokens`（缓存命中读）、`cache_write_input_tokens`、
`output_tokens`、`reasoning_output_tokens`、`total_tokens`，以及 `context_window`。

- 粒度：优先 `thread.turn()` + `TurnHandle.stream()`，**每次模型响应一行**（`last` 口径）；
  若 SDK 不提供该接口则退化为每 turn 一行累计值（`turn_total`，日志会说明原因）。
- 每个模块结束后打印一行 `[codex][usage] module REQ-x: calls=… in=… cached=… (%) out=… …`，
  run 结束再打印 module / repair / vision / run total 汇总与账本路径。
- 交叉校验：每完成一个模块与 run 结束时，把 CLI 的 `rollout-*.jsonl`（含
  `token_usage_record`：response_id + 逐次 + turn/thread 累计）复制到
  `<output-dir>/.arc/codex-rollouts/`（上限 30MB）。该步骤只读 `$CODEX_HOME`，不改变 CLI 行为；
  `ARCBENCH_CODEX_ROLLOUTS=0` 可关闭。
- 计量全程 best-effort：任何写入失败只告警，不打断 run，也不改变给 agent 的提示词。
- 已知边界：usage 是"每次模型响应"的聚合值，拿不到单次工具调用/单个文件的 token；
  `cached_*` 是否非零取决于网关是否回传 `input_tokens_details`。

## 可靠性说明

- 每个 ROOT 模块都在自己独立的 Codex 线程上运行，因此跨模块不会累积对话上下文。
  这避免了 Codex 运行时的远端压缩 v2（remote compaction v2），该特性与
  非 OpenAI 网关不兼容（报错 "remote compaction v2 expected exactly one
  compaction output item"）。
- 模型调用通过自定义 provider（`arcbench`，name != "OpenAI"）指向 `OPENAI_BASE_URL`，
  因此运行时代仍需的压缩会回退到本地摘要路径，而不是走会致命的远端压缩协议。
- 已完成的模块 id 会持久化到 `<output-dir>/.arc/completed_modules.json`；
  重跑时从第一个未完成模块继续，而不是从头再来。
- 如果某个模块因压缩错误失败，会在新线程上重试（最多 3 次）后才宣告本次运行失败。
- `requirements.txt` 将版本固定为 `openai-codex==0.154.0` / `openai-codex-cli-bin==0.154.0`。
