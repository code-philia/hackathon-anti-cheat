# Core Generation Strategy Taxonomy

Use these categories as a coverage checklist, not as mutually exclusive labels.

- `RAG/RETRIEVAL`: indexes, vector or lexical search, task fingerprints, keyword routing, semantic retrieval, file/context selection, and corpus construction. Record the corpus, query, selection rule, and where retrieved material enters generation.
- `PREPARED-KNOWLEDGE`: prompts, skills, checklists, examples, templates, domain rules, and other knowledge prepared before the current task. Distinguish generic guidance from task/domain-specific material.
- `CODE-REUSE`: copying, unpacking, importing, patching, adapting, or asking a model to reuse existing applications, components, snippets, tests, or assets. Distinguish direct reuse from model-mediated adaptation.
- `PROMPT-ORCHESTRATION`: system/user prompt construction, staged agents, decomposition, context compression, role assignment, output constraints, and prompt chaining.
- `MODEL-ROUTING`: model endpoints, roles, fallback/secondary calls, selection logic, parallel calls, and how outputs are combined. Report configuration mechanics without treating model names alone as a strategy.
- `TOOLS/EXECUTION`: filesystem inspection, shell commands, browser/network tools, code generation/editing tools, build or test tools, and safeguards around their use.
- `ITERATION/EVALUATION`: plan-act-review loops, generated tests, build/test feedback, evaluator feedback, retry conditions, self-critique, and stopping rules.
- `STATE/PERSISTENCE`: memory, caches, summaries, artifacts, checkpoints, learned skills, or cross-step/cross-task state.

## Evidence and confidence

For every material strategy, analyze `状态`, `作用`, `输入/知识源`, `选择/检索`, `生成/使用`, and `输出` as separate dimensions. Every dimension must include:

1. `具体说明`: name the concrete mechanism, value, source, behavior, or artifact; do not use a bare generic label.
2. `代码/文档定位`: cite one or more original submission locations as `path:line`. Reusing a location across dimensions is allowed only when that line genuinely supports each dimension.
3. `详细解释`: explain what the cited code/document does, how it supports the concrete statement, and how this dimension connects upstream inputs to downstream generation output.

Use these confidence labels:

- `confirmed`: source and data flow establish the behavior.
- `inferred`: multiple source clues support the behavior, but part of the runtime path is indirect or dynamic.
- `unresolved`: concrete evidence exists, but a necessary file, value, or runtime branch cannot be inspected.

Absence claims must be scoped: write `在已检查的仓库静态内容中未发现` rather than claiming runtime impossibility.

## Synthesis

The summary should answer:

1. What is the repository's primary generation pipeline?
2. What knowledge is prepared, retrieved, or reused?
3. How do prompts, models, and tools cooperate?
4. How does the system evaluate, retry, or refine its work?
5. Which mechanisms are differentiating, and which are ordinary infrastructure?
