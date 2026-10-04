# Result Log Contract

Write UTF-8 plain text intended for direct human editing:

```text
反作弊审查：<submission-name>
题面路径：<resolved-example-input-path>
题面范围：<resolved-task-path-1>；<resolved-task-path-2>；...
作答路径：<resolved-submission-path>
审查覆盖：TEMPLATE-DIRECT/TEMPLATE-INDIRECT=已检查；MODEL-EXTERNAL=已检查；MODEL-METER-TAMPER=已检查；NET-EXTERNAL=已检查；AC-INTERFERENCE=已检查；OTHER-SUSPICIOUS/INSPECTION-GAP=已检查
摘要：<N> error(s), <M> warning(s)

[ERROR]
ERROR-001 [RULE-ID] <中文事实描述>
  - <path:line 或精确位置>: <中文证据解释>

[WARNING]
WARNING-001 [RULE-ID] <中文事实描述>
  - <path:line 或精确位置>: <需要人工核查的中文说明>

判决：通过
```

- Always include both sections. Put `无` below an empty section.
- When `example_path` resolves to multiple tasks, include `题面范围` with every resolved task root. For a single task, `题面范围` may be omitted. Findings involving prepared knowledge must identify which task or tasks the knowledge matches.
- Number findings independently and consecutively within each severity.
- Include the exact `审查覆盖` line shown above. It certifies that every listed rule family was inspected after all mechanical leads and relevant explanatory claims were resolved. Do not write this declaration early merely because one error already determines the verdict.
- Keep evidence repository-relative when possible; use resolved paths in the header.
- Prefer Chinese for all narrative content in the final log, including finding summaries, factual explanations, evidence interpretation, applicability analysis, unresolved questions, and the comprehensive judgment. Keep mandated identifiers and keywords such as `ERROR`, `WARNING`, rule IDs, fixed field labels, paths, code symbols, API values, and necessary verbatim source text in their original form. When quoting English source evidence, explain its significance in Chinese instead of switching the surrounding narrative to English.
- Encode the final file as strict UTF-8 and run `scripts/validate_report.py` after its last write. A file is invalid if it contains Unicode replacement characters, private-use characters introduced by broken transcoding, repeated question marks standing in for lost text, or recognizable Chinese mojibake. Repair the text from trustworthy source context and rerun validation; changing only the declared or editor encoding is insufficient after characters have been replaced.
- Every error must have at least one evidence bullet containing an original submission source-code location in `path:line` form. A directory, scanner JSON, generated report, or prose-only runtime observation does not satisfy this requirement. If the behavior constructs a value indirectly, cite the responsible construction line.
- Every `AC-INTERFERENCE` warning about an unverifiable explanatory claim must cite the claim's original `path:line`, summarize the code/data-flow checks performed, and state the unresolved fact requiring human review.
- Every `TEMPLATE-DIRECT` and `TEMPLATE-INDIRECT` error or warning must replace the generic evidence bullets with all five lines below. Use exactly one numbered primary category on each axis. The first three lines each require a detailed explanation and an original source `path:line` location:

```text
  - 知识类型：(1)完整代码实现；说明：<预置了什么知识及其专用程度>；定位：<path:line>
  - 检索方案：(1)针对题面硬编码检索；说明：<如何选择该材料，或为何属于全量使用>；定位：<path:line>
  - 生成方案：(1)无模型参与地使用代码；说明：<该材料如何进入最终作答>；定位：<path:line>
  - 泛用估计：(1)知识仅可用于题面给定的需求；说明：<该泛用等级的依据>
  - 综合判断：<四个维度如何共同支持 error 或 warning；若为 warning，说明尚未解决的问题>
```

  Substitute the appropriate category numbers and exact category labels from the policy. Additional evidence bullets may follow.
- Do not include hidden chain-of-thought. Record findings, evidence, and short adjudication reasons only.
- The final non-empty line must be exactly `判决：通过` or `判决：作弊`.
- At least one error requires `判决：作弊`; warnings alone produce `判决：通过` pending human review.
