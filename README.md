# Competition Anti-Cheat

本仓库提供 `competition-anti-cheat` skill，用于对竞赛选手的 Agent/代码仓库做静态反作弊审查。

它会结合题目要求与选手仓库，检查以下风险：

- 预置或检索与题目直接相关的模板、代码、测试和领域知识；
- 使用额外的模型地址或 API Key；
- 篡改模型调用量、计费或 token 记录；
- 访问外部网络、测试文件或其他未授权数据；
- 通过提示词、注释或代码干扰反作弊审查；
- 其他可疑行为及无法完整检查的内容。

审查过程只读取题目和选手仓库，不执行选手代码、不安装其依赖，也不访问仓库中提供的 URL。公开且广泛使用、仅用于项目迭代或自测的软件运行时（例如 Playwright 所需的 Chromium/Firefox）不因安装本身判为 `NET-EXTERNAL`；不得借此获取题面实现、评测测试、fixture、预期输出或其他未授权竞赛材料。最终结果以中文日志写入指定位置，并给出 `通过` 或 `作弊` 的初步判决。

模板材料按四个维度分级：知识类型、检索方案、生成方案和泛用估计。完整应用、业务模块以及可直接复用的测试/代码片段，在确认实际复制或模型复用路径后通常为 error；实现逻辑、领域知识和泛用指导在专用性或实际贡献不明确时为 warning；普通跨领域框架基础设施和广泛适用知识通常允许。

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

## 单个 leaderboard ZIP 的完整审计

从仓库根目录运行下面的脚本即可完成“解压 agent、整理 input、创建 output、调用 Codex 和保存审计结果”的完整流程：

```powershell
python tools\run_single_audit.py download\leaderboard-export.zip --overwrite
```

脚本只提取 leaderboard 中的 `agent.zip`，并在 `input/` 下生成纯净 agent 目录；审计结果写入 `output/<leaderboard-name>/audit.log`，Codex 事件写入同目录的 `trace.jsonl`，临时文件写入 `temp/`。需求材料默认使用 `material\arc-bench-web`，也可通过 `--example` 覆盖。

## 批量审计

`tools\run_batch_audit.py` 使用脚本顶部的固定 `ARCHIVES` 列表，串行调用 `run_single_audit.py`。先查看将要处理的 ZIP：

```powershell
python tools\run_batch_audit.py --dry-run
```

确认列表后运行：

```powershell
python tools\run_batch_audit.py
```

脚本不会在运行时自动展开通配符。要审计其他 ZIP，先编辑 `tools\run_batch_audit.py` 中的 `ARCHIVES`。单个审计默认使用 `--overwrite`，会覆盖对应的 `input/`、`output/` 和临时结果。

## 当前审计结果

本工作区的 30 个最新 case 汇总见 [`result/anti-cheat-review-summary.md`](result/anti-cheat-review-summary.md)。汇总报告记录逐 case 判决、error/warning 分类以及模板和网络规则调整后的统计；每个 case 的详细证据仍以 `output/<leaderboard-name>/audit.log` 为准。

## 审计工作区目录

批量审计使用以下目录协作保存原始材料、中间输入和结果：

| 目录 | 用途 | 说明 |
| --- | --- | --- |
| `download/` | 原始 leaderboard 导出 ZIP | 保存平台导出的 `leaderboard-export*.zip`。脚本从 ZIP 中提取选手 agent 和运行元数据；不要把 ZIP 当作题面输入。 |
| `material/` | 题面和授权参考材料 | 默认使用 `material/arc-bench-web`，包含 `requirements.yaml`、reference 资源和题面任务目录。它代表审计允许使用的题面输入。 |
| `input/` | 解压后的选手 agent | `run_single_audit.py` 从 ZIP 提取并整理为 `input/<leaderboard-name>/agent`。审计应以这里的 agent 文件为准，不应直接修改。 |
| `output/` | 每个 case 的审计结果 | 每个选手目录下通常有 `audit.log`、`trace.jsonl` 和临时审计文件；`audit.log` 是最终人工复核依据。 |
| `result/` | 单仓库审计结果或汇总报告 | 保存单模式 `.log`、旧批次结果和 `anti-cheat-review-summary.md` 等人工交付文件。 |
| `benchmark/` | 规则/脚本测试样例 | 用于验证 inspection gap、报告格式等审计工具行为，不是选手提交材料。 |
| `.audit-temp/` | 本地中间脚本和统计文件 | 仅供本地核验使用，通常不应提交到 Git。 |

典型的数据流是：

```text
download/*.zip
    └─ run_single_audit.py
        ├─ input/<leaderboard-name>/agent/   # 解压后的选手 agent
        └─ output/<leaderboard-name>/        # audit.log、trace.jsonl、temp/

material/arc-bench-web/                     # 题面和授权 reference
result/                                      # 单独的结果日志和汇总报告
```

`download/`、`input/` 和 `output/` 可能包含很大的原始数据、选手仓库和运行日志；是否提交它们应根据仓库发布目的决定。提交代码和规则时，通常至少提交 `competition-anti-cheat/`、`tools/`、README 和需要发布的 `result/` 报告，并避免误加入 `.audit-temp/`、`__pycache__/`、临时扫描文件或未打算公开的原始 ZIP。

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
