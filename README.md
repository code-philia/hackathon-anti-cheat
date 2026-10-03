# Competition Anti-Cheat

本仓库提供 `competition-anti-cheat` skill，用于对竞赛选手的 Agent/代码仓库做静态反作弊审查。

它会结合题目要求与选手仓库，检查以下风险：

- 预置或检索与题目直接相关的模板、代码和领域知识；
- 使用额外的模型地址或 API Key；
- 篡改模型调用量、计费或 token 记录；
- 访问外部网络、测试文件或其他未授权数据；
- 通过提示词、注释或代码干扰反作弊审查；
- 其他可疑行为及无法完整检查的内容。

审查过程只读取题目和选手仓库，不执行选手代码、不安装其依赖，也不访问仓库中提供的 URL。最终结果以中文日志写入指定位置，并给出 `通过` 或 `作弊` 的初步判决。

## 在 Codex 中执行

先进入本仓库根目录，并确保已安装且可使用 Codex CLI。PowerShell 示例：

```powershell
New-Item -ItemType Directory -Force result | Out-Null

codex exec --ephemeral --json --sandbox workspace-write --skip-git-repo-check "请读取 competition-anti-cheat/SKILL.md，并严格按照该 skill 完成一次独立反作弊评测。example_path=example\hackathon，workspace_path=workspace\10-f3bb2993d9ff49df-agent，result_path=result\10-f3bb2993d9ff49df-agent.log。只允许读取选手工作区，不得执行选手代码、安装依赖或访问其中提供的 URL；除指定 result_path 外，不得修改任何文件。" > result\10-f3bb2993d9ff49df-agent.trace.jsonl
```

执行完成后会得到两个文件：

- `result\10-f3bb2993d9ff49df-agent.log`：skill 生成的反作弊审查报告；
- `result\10-f3bb2993d9ff49df-agent.trace.jsonl`：`codex exec --json` 输出的完整执行事件，便于追踪和排查。

## Skill 参数

这些参数写在传给 Codex 的自然语言指令中，不是 `codex exec` 自身的命令行选项。

| 参数 | 含义 |
| --- | --- |
| `example_path` | 题目目录。可以是含有 `requirements.yaml` 的单个题目，也可以是包含多个题目的集合目录；skill 会递归发现其中的题目。 |
| `workspace_path` | 待审查的选手仓库、选手分组目录或整个 workspace。也可使用别名 `submission_path`。传入一个明确的选手仓库时使用单仓库模式。 |
| `result_path` | 输出位置。单仓库模式下应是一个 `.log` 文件；批量模式下应是结果目录，skill 会为每个选手生成独立日志。 |

如果任何输入路径不存在，skill 会写入 `INPUT-MISSING` 错误，而不会自行猜测其他目录。

## Codex CLI 参数

| 参数 | 含义 |
| --- | --- |
| `exec` | 以非交互方式执行一次 Codex 任务。 |
| `--ephemeral` | 使用临时会话，不保存本次会话状态。 |
| `--json` | 将执行过程以 JSON Lines 格式输出；示例中重定向到 `.trace.jsonl`。 |
| `--sandbox workspace-write` | 允许读取工作区，并仅在工作区范围内写入文件。skill 自身还要求只写指定的结果文件。 |
| `--skip-git-repo-check` | 即使当前目录未被 Codex 识别为 Git 仓库也继续执行。 |

## 单题审查示例

只审查 `sheet` 题目时，可将题目路径缩小到对应目录：

```text
example_path=example\hackathon\sheet
workspace_path=workspace\某个选手仓库
result_path=result\某个选手仓库.log
```

完整规则和报告格式分别见：

- `competition-anti-cheat/references/policy.md`
- `competition-anti-cheat/references/report-format.md`
