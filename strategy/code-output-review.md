# 001–050 代码重复片段汇总

本汇总合并以下五份独立报告：

- `code-output-review-001-010.md`
- `code-output-review-011-020.md`
- `code-output-review-021-030.md`
- `code-output-review-031-040.md`
- `code-output-review-041-050.md`

排序依据是 `agent` 与 `applications` 压缩包内文件的 SHA-256 完全一致，按重复文件大小从大到小排列。相同文件在多个阶段结果中出现时合并记录。

## 按重复片段大小排序

| 大小 | 选手 | agent 内文件 | applications 中位置 |
|---:|---|---|---|
| 201,896 B | 006 | `tasks/github-stage3/seed/backend/server.js` | `github-stage-1/backend/server.js` |
| 121,084 B | 001 | `deterministic/github_product/official/app.js` | `github-stage-{1,2,3}/frontend/src/app.js` |
| 110,814 B | 001 | `deterministic/github_product/official/server.mjs` | `github-stage-{1,2,3}/backend/server.mjs` |
| 51,222 B | 005 | `payloads/github_full/backend/src/app.js` | `github/backend/src/app.js` |
| 49,389 B | 020 | `arcagent/github_full/backend/src/routes/repos.js` | GitHub 阶段结果 |
| 41,221 B | 029 | `factory/assets/github/backend/src/pages/work.js` | `github/backend/src/pages/work.js` |
| 40,870 B | 046 | `reference/sheet_app/frontend/src/domain/formula/engine.ts` | `sheet/frontend/src/domain/formula/engine.ts` |
| 37,242 B | 038 | `arc-agent-2.0.0/synth/packs/spreadsheet/backend/src/routes/workbooks.js` | `sheet/backend/src/routes/workbooks.js` |
| 31,585 B | 033 | `template/backend/src/database/seed_db.js` | `sheet/backend/src/database/seed_db.js` |
| 31,265 B | 020 | `arcagent/github_full/backend/src/routes/issues.js` | GitHub 阶段结果 |
| 29,985 B | 046 | `reference/sheet_app/frontend/src/pages/EditorPage.tsx` | `sheet/frontend/src/pages/EditorPage.tsx` |
| 29,743 B | 012 | `scaffold/frontend/public/lib/arc.js` | GitHub/Sheet 阶段结果 |
| 29,193 B | 011 | `github/application/backend/src/m5.js` | `github/backend/src/m5.js` |
| 27,984 B | 多个 | `skills/arcbench-traceability/scripts/arc_traceability.py` | 各阶段 `.codex/.claude/skills` |
| 25,203 B | 038 | `synth/packs/spreadsheet/backend/src/lib/state.js` | `sheet/backend/src/lib/state.js` |
| 25,361 B | 033 | `template/backend/src/routes/issues.js` | `sheet/backend/src/routes/issues.js` |
| 24,156 B | 020 | `arcagent/github_full/backend/src/database/seed_db.js` | GitHub 阶段结果 |
| 23,319 B | 011 | `github/application/backend/src/m3.js` | `github/backend/src/m3.js` |
| 22,677 B | 029 | `factory/assets/github/backend/src/pages/repository.js` | `github/backend/src/pages/repository.js` |
| 22,311 B | 011 | `github/application/backend/src/m4.js` | `github/backend/src/m4.js` |
| 20,972 B | 011 | `github/application/backend/src/m1.js` | `github/backend/src/m1.js` |
| 20,117 B | 034 | `template/backend/src/index.js` | GitHub/Sheet 结果 |
| 19,862 B | 032 | `skills/github-collab-guide/references/backend/routes/pulls.js` | `github/backend/routes/pulls.js` |
| 19,416 B | 033 | `template/backend/src/routes/auth.js` | `sheet/backend/src/routes/auth.js` |
| 17,897 B | 029 | `factory/assets/github/backend/src/pages/repos.js` | `github/backend/src/pages/repos.js` |
| 17,485 B | 038 | `synth/packs/spreadsheet/frontend/src/components/WorkbookDialogs.jsx` | `sheet/frontend/src/components/WorkbookDialogs.jsx` |
| 17,368 B | 013 | `factory/snapshots/github/backend/routes/code.js` | GitHub 结果 |
| 16,794 B | 046 | `reference/sheet_app/frontend/src/contracts/commands.ts` | Sheet 结果 |
| 16,162 B | 038 | `synth/packs/spreadsheet/backend/src/lib/grid.js` | `sheet/backend/src/lib/grid.js` |
| 15,885 B | 013 | `factory/snapshots/github/backend/routes/issues.js` | GitHub 结果 |
| 15,135 B | 038 | `synth/packs/spreadsheet/backend/src/lib/sqlite.js` | `sheet/backend/src/lib/sqlite.js` |
| 14,634 B | 029 | `factory/assets/github/backend/src/pages/settings.js` | `github/backend/src/pages/settings.js` |
| 14,692 B | 020 | `arcagent/github_full/backend/src/database/init_db.js` | GitHub 阶段结果 |
| 14,160 B | 048 | `template/frontend/src/app/formula.js` | GitHub 阶段结果 |
| 14,035 B | 多个 | `template/backend/src/index.js` | 多个阶段结果 |
| 12,879 B | 013 | `factory/scaffold/frontend/src/lib/ui.js` | GitHub 阶段结果 |
| 12,570 B | 033 | `template/backend/src/database/init_db.js` | Sheet 结果 |
| 12,239 B | 038 | `synth/packs/spreadsheet/backend/src/lib/workbook/structure.ts` | Sheet 结果 |
| 12,236 B | 046 | `reference/sheet_app/frontend/src/domain/csv/core.ts` | Sheet 结果 |
| 11,286 B | 029 | `factory/assets/github/backend/src/html.js` | `github/backend/src/html.js` |
| 11,035 B | 032 | `skills/github-collab-guide/references/backend/routes/code.js` | `github/backend/routes/code.js` |
| 10,264 B | 048 | `template/frontend/src/app/ui.jsx` | GitHub 阶段结果 |

## 仅模板、技能或依赖文件重复

以下条目也被五份报告确认，但主要属于通用基础设施，不能单独作为完整业务应用复制证据：

- `arc_checkpoint.py`：10,533 B
- `arc_traceability.py`：26,684–27,984 B
- `template/scripts/check.py`：16,442 B
- 前后端 `package-lock.json`：约 83,040–203,075 B
- 各类 `template/backend/src/index.js`、README、skills 和检查脚本

## 没有大文件级重复证据的选手

014、016、017、026、044、049 当前没有确认的大于 10 KB 的 agent/application 完全一致文件；这不等于没有小文件复制或代码复用，只表示现有哈希核查不足以证明大段代码原样复制。

## 判定说明

`agent` 是选手提交的智能体，`applications` 是智能体运行后的作答结果。表中的重复文件证明预置代码在运行后直接进入作答结果，但不代表每个 applications 目录都由 agent 完整原样复制；模板、技能、依赖和检查脚本应与业务 payload 分开解释。
