# Strategy Log Contract

Write strict UTF-8 plain text:

```text
核心策略分析：<submission-name>
题面路径：<resolved-example-input-path>
题面范围：<resolved-task-path-1>；<resolved-task-path-2>；...
作答路径：<resolved-submission-path>
分析覆盖：RAG/RETRIEVAL=已检查；PREPARED-KNOWLEDGE=已检查；CODE-REUSE=已检查；PROMPT-ORCHESTRATION=已检查；MODEL-ROUTING=已检查；TOOLS/EXECUTION=已检查；ITERATION/EVALUATION=已检查；STATE/PERSISTENCE=已检查

[核心结论]
<用简洁中文概括端到端生成策略、最关键机制，以及 RAG 与代码复用结论>

[策略清单]
STRATEGY-001 [RAG/RETRIEVAL] <策略名称或事实>
  - 状态：
    1. 具体说明：<confirmed|inferred|unresolved，以及具体判定内容>
    2. 代码/文档定位：<submission-relative-path:line；可列多个位置>
    3. 详细解释：<哪些静态证据使该策略得到确认、推断或仍未解决>
  - 作用：
    1. 具体说明：<该机制具体解决的任务或生成环节>
    2. 代码/文档定位：<submission-relative-path:line；可列多个位置>
    3. 详细解释：<代码如何实现该作用，以及它在完整生成链路中的意义>
  - 输入/知识源：
    1. 具体说明：<具体文件、语料、模板、题面、运行时数据或其他来源>
    2. 代码/文档定位：<submission-relative-path:line；可列多个位置>
    3. 详细解释：<来源的内容、载入方式、数据形态及其为何构成该策略的输入>
  - 选择/检索：
    1. 具体说明：<具体查询、匹配、路由、排序或全量使用机制；无检索时说明实际选择机制>
    2. 代码/文档定位：<submission-relative-path:line；可列多个位置>
    3. 详细解释：<选择条件、执行步骤、命中结果以及结果如何传给下一环节>
  - 生成/使用：
    1. 具体说明：<具体的提示词注入、复制、修改、拼接、工具调用或模型生成方式>
    2. 代码/文档定位：<submission-relative-path:line；可列多个位置>
    3. 详细解释：<输入材料如何被处理并影响生成、代码修改或最终作答>
  - 输出：
    1. 具体说明：<具体产物、文件、补丁、提示词上下文、评估结果或状态>
    2. 代码/文档定位：<submission-relative-path:line；可列多个位置>
    3. 详细解释：<输出在哪里产生、由谁消费，以及它对最终作品的贡献>

[未发现或未解决]
- <覆盖项>：在已检查的仓库静态内容中未发现；或说明具体未解决点。
分析完成
```

- Keep all four sections and the exact `分析覆盖` line.
- `题面范围` may be omitted for a single discovered task; include every task for a collection.
- Number strategies consecutively. Use the closest primary taxonomy label; mention additional categories in the text rather than duplicating the same mechanism.
- Every one of the six dimensions (`状态`, `作用`, `输入/知识源`, `选择/检索`, `生成/使用`, `输出`) must contain all three numbered parts: `具体说明`, `代码/文档定位`, and `详细解释`.
- Every dimension requires original submission `path:line` evidence. A directory, generated scanner output, or an uncited repository-wide assertion is not a valid location.
- `具体说明` must identify the actual mechanism or artifact. Bare phrases such as `生成页面`, `组件库`, `关键词选择`, `模型生成`, or `输出代码` are invalid.
- `详细解释` must interpret the cited location and trace its relationship to the preceding or following generation stage. Do not merely restate `具体说明`.
- Explicitly state the RAG and code-reuse result in `[核心结论]` or `[未发现或未解决]`.
- Do not include a cheating/pass verdict, hidden chain-of-thought, or unsupported claims.
- The final non-empty line must be `分析完成`.
