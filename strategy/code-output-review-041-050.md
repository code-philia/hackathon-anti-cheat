# 041–050 作答代码复用核查

`agent/agent.zip` 是提交的智能体，`applications/*.zip` 是运行结果。以下完全一致结论来自压缩包内文件 SHA-256 比对，仅列出大于 10 KB 的一致文件。

| 编号 | 文件级结果 | 结论 |
|---|---|---|
| 041 | 9 个一致文件 | skills、template、依赖和检查脚本复制；未确认业务 payload |
| 042 | 10 个一致文件 | template/index.js 和依赖复制；未确认业务 payload |
| 043 | 15 个一致文件 | skills、template、依赖和检查脚本复制 |
| 044 | 0 个一致文件 | 没有确认的大文件直接复制证据 |
| 045 | 10 个一致文件 | skills、template、依赖和检查脚本复制 |
| 046 | 6 个一致文件 | Sheet 业务模块直接复制 |
| 047 | 10 个一致文件 | skills、template、依赖和检查脚本复制 |
| 048 | 7 个一致文件 | Sheet 公式和 UI 模块直接复制 |
| 049 | 0 个一致文件 | 没有确认的大文件直接复制证据 |
| 050 | 10 个一致文件 | skills、template、依赖和检查脚本复制 |

## 详细定位

### 041 先提交再说

确认 `arc_checkpoint.py`（10,533 B）、`arc_traceability.py`（27,984 B）、前端 package-lock（178,360 B）和 `template/scripts/check.py`（16,442 B）复制到 GitHub/Sheet 结果。未确认完整业务 payload。

### 042 AFlickerr

确认多个阶段中的 `template/backend/src/index.js`（14,035 B）和 package-lock（83,040 B）一致。属于 template 复制，不能据此认定完整应用原样复制。

### 043 分支比人多

确认 skills、前后端 package-lock 和 `template/scripts/check.py` 复制。当前没有大型业务模块完全一致证据。

### 044 nsy

没有发现大于 10 KB 的 agent/application 完全一致文件。不能声称完整业务代码由 agent 直接复制；需结合 trace 判断生成或小文件复制。

### 045 nnn45

确认 skills、template package-lock 和检查脚本复制；没有完整业务 payload 的哈希证据。

### 046 删库跑路小分队

确认 Sheet 业务模块直接复制：`frontend/src/contracts/commands.ts`（16,794 B）、`domain/csv/core.ts`（12,236 B）、`domain/formula/engine.ts`（40,870 B）、`domain/workbook/structure.ts`（12,239 B）、`pages/EditorPage.tsx`（29,985 B）。这是明确的大段 Sheet 业务代码复用。

### 047 my67

确认 skills、template package-lock 和检查脚本复制；未确认大段业务 payload。

### 048 AIOS

确认 Sheet 相关模板模块直接复制：`frontend/src/app/formula.js`（14,160 B）和 `frontend/src/app/ui.jsx`（10,264 B），均出现在三个阶段结果中。这是组件级/业务模块级直接复制。

### 049 JJJ

没有发现大于 10 KB 的 agent/application 完全一致文件。当前不能证明完整业务代码由 agent 直接复制。

### 050 幻觉工程研究院

确认 skills、template package-lock 和检查脚本复制；没有大型业务 payload 的完全一致证据。

## 总体结论

041–050 不能统一归类为完整 GitHub/Sheet 应用原样复制。046 明确复制了多个大型 Sheet 业务模块，048 明确复制了公式和 UI 模块；其余多数条目只确认了 skills、template、依赖或检查脚本复制；044、049 没有确认的大文件一致证据。`applications` 仍是智能体运行后的作答结果，代码来源应按文件级哈希证据区分。
