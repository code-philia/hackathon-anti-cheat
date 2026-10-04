# 031–040 作答代码复用核查

将 `agent/agent.zip` 视为选手提交的智能体，将 `applications/*.zip` 视为运行结果。以下“完全一致”均来自压缩包内文件 SHA-256 相同，且只列出大于 10 KB 的文件。

| 编号 | 文件级结果 | 结论 |
|---|---|---|
| 031 | 15 个一致文件 | 主要是 skills、template、依赖和检查脚本；未确认业务 payload |
| 032 | 18 个一致文件 | 有多个 GitHub 业务路由直接复制 |
| 033 | 19 个一致文件 | 有 Sheet 数据库、路由等大型模板文件直接复制 |
| 034 | 6 个一致文件 | 主要是 template/index.js 和依赖；未确认完整业务 payload |
| 035 | 8 个一致文件 | 主要是 template/index.js 和依赖；未确认完整业务 payload |
| 036 | 15 个一致文件 | 主要是 skills、template、依赖和检查脚本 |
| 037 | 10 个一致文件 | 主要是 template/index.js 和依赖 |
| 038 | 9 个一致文件 | 多个 Sheet 核心业务模块完整复制 |
| 039 | 20 个一致文件 | 主要是 skills、template、测试和依赖 |
| 040 | 10 个一致文件 | 主要是 template/index.js 和依赖 |

## 详细定位

### 031 66大顺

确认 `arc_checkpoint.py`、`arc_traceability.py`、前后端 package-lock 和 `template/scripts/check.py` 等文件复制到多个结果包。没有大段业务 payload 的哈希证据；strategy 应限定为模板/技能复用。

### 032 OUC-SOUND-TEAM

确认 GitHub 业务模块直接复制：`backend/gitlib.js`（10,050 B）、`routes/code.js`（11,035 B）、`routes/issues.js`（14,410 B）、`routes/orgs.js`（10,146 B）、`routes/pulls.js`（19,862 B），以及 31,452 B 的 package-lock。该条存在明确业务代码复用。

### 033 1648557528

确认 Sheet 应用的大型文件直接复制：`backend/src/database/init_db.js`（12,570 B）、`seed_db.js`（31,585 B）、`routes/auth.js`（19,416 B）、`routes/issues.js`（25,361 B）等。该条不是只有通用模板，而是包含完整业务模块。

### 034 能智吗

确认 `template/backend/src/index.js`（20,117 B）和 package-lock 在多个结果包一致。当前证据支持通用模板复制，未确认完整 GitHub/Sheet 业务 payload 原样复制。

### 035 apach

确认多个阶段应用中的 `template/backend/src/index.js`（14,035 B）和 package-lock 一致。应归为模板复制，不能扩大为完整业务应用复制。

### 036 星期3做小三

确认 skills、template package-lock 和 `template/scripts/check.py` 复制。没有大型业务模块完全一致证据。

### 037 Leonard

确认多个阶段中的 `template/backend/src/index.js`（14,035 B）和 package-lock 一致，属于模板级复制。

### 038 强强

确认 Sheet 核心模块逐字复制：`formula-core.js`（25,114 B）、`grid.js`（16,162 B）、`sqlite.js`（15,135 B）、`state.js`（25,203 B）、`routes/workbooks.js`（37,242 B）、`WorkbookDialogs.jsx`（17,485 B）。这是明确的大段业务代码 payload 复制。

### 039 xinyurun

确认 skills、template package-lock、`database-init-contract.test.mjs`（10,262 B）等文件复制；未发现业务主体的大型 payload 完全一致证据。

### 040 chengyuj94

确认多个阶段中的 template `backend/src/index.js`（14,035 B）和 package-lock 一致；当前只能认定模板复制。

## 总体结论

031–040 不能统一说成完整 GitHub/Sheet 应用原样复制。032、033、038 有明确的大型业务模块完全一致，属于 agent 内置业务代码直接进入 applications；031、034–037、039、040 目前主要证明 template/skills/依赖复制。`applications` 仍是智能体运行后的结果，代码来源必须按上述文件级证据区分。
