# 001–010 作答代码复用核查

本次核查对象是各选手工作区中的实际作答产物（`workspace/<id>/applications`），并结合对应的 `strategy/<id>.log` 与 `result/<id>.log`。这里的“大片段”指可独立运行的页面、后端或完整模板文件；“小片段”指内嵌 HTML、SQL、配置或组件片段。行号以工作区文件当前内容为准。

## 结论

| 编号 | 大片段代码 | 小片段代码 | 没有直接代码片段引用 | 依据 |
|---|---|---|---|---|
| 001 | 有 | 有 | 否 | 多个 `applications/*` 阶段目录含完整 GitHub/Sheet 应用；前端 JSX/HTML 模板字符串直接输出 |
| 002 | 有 | 有 | 否 | `strategy` 明确记录模板全量复制和阶段应用复用 |
| 003 | 有 | 有 | 否 | 结果涉及完整应用生成；策略记录模板与已有应用增量复用 |
| 004 | 有 | 有 | 否 | `strategy` 的 CODE-REUSE 明确记录 template 全量复制 |
| 005 | 有 | 有 | 否 | 策略明确记录静态 payload/template 复制覆盖 |
| 006 | 有 | 有 | 否 | 策略明确记录按任务包复制完整应用 |
| 007 | 有 | 有 | 否 | 策略明确记录成熟应用源码恢复及局部 EDIT/FILE 修复 |
| 008 | 有 | 有 | 否 | 工作区包含完整前后端应用和 scaffold 复用产物 |
| 009 | 有 | 有 | 否 | 策略明确记录 scaffold 进入输出目录，`FILE/END` 直接写入应用源代码 |
| 010 | 有 | 有 | 否 | 策略明确记录 blueprint 安装后进入输出目录 |

## 逐项定位

### 001 bugtakue

- 大片段：`workspace/001-bugtakue-0b23afbd83fb/applications/github-stage-1`、`github-stage-2`、`github-stage-3`、`sheet` 均是完整应用目录；代表性页面代码位于 `applications/github-stage-1/frontend/src/app.js:70-220` 和 `applications/sheet/frontend/src/app.js:70-180`。这些是直接进入作答目录的完整页面实现。
- 小片段：`applications/github-stage-1/frontend/src/app.js:83-107`、`applications/sheet/frontend/src/app.js:70-107` 有直接内嵌的 HTML 模板字符串；属于组件级片段。
- 策略证据：`strategy/001-bugtakue-0b23afbd83fb.log:7,36` 记录复制模板和 skills；`result/001-bugtakue-0b23afbd83fb.log` 为对应审查结果。

### 002 Orchestro

- 大片段：`workspace/002-Orchestro-47b4793effa5/applications/github-stage-*`、`applications/sheet`；每个阶段目录包含完整前后端实现。代表性入口为 `applications/sheet/frontend/index.html:1-12`、`applications/sheet/backend/src/routes/workbooks.js:1-120`。
- 小片段：`applications/sheet/backend/src/routes/workbooks.js:48-52` 的 SQL 插入语句；`applications/github-stage-2/backend/src/app.js:106-180` 的内嵌 HTML。
- 策略证据：`strategy/002-Orchestro-47b4793effa5.log:7,36-60` 明确说明模板全量复制和既有页面/组件复用。

### 003 chrislearn

- 大片段：`workspace/003-chrislearn-861a136e5f21/applications` 下的 GitHub/Sheet 应用及阶段产物；代表性实现为 `applications/*/frontend/src/app.js` 和 `backend/src/app.js` 的完整文件。
- 小片段：各 `frontend/src/app.js` 中的页面模板字符串，以及 `backend/src/*` 中的 SQL/路由片段；以 `applications/github-stage-1/frontend/src/app.js` 的页面渲染函数为代表。
- 策略证据：`strategy/003-chrislearn-861a136e5f21.log:1` 记录作答路径；对应 `result/003-chrislearn-861a136e5f21.log` 的审查条目应与上述文件联合阅读。

### 004 zhx

- 大片段：`workspace/004-zhx-01af825e0e2c/applications` 的完整应用目录；代表性文件为 `applications/*/frontend/src/app.js`、`applications/*/backend/src/app.js`。
- 小片段：前端渲染函数中的 HTML 字符串、后端初始化 SQL；具体范围以对应文件中的模板字符串和 `CREATE TABLE` 块为准。
- 策略证据：`strategy/004-zhx-01af825e0e2c.log:59-83` 明确记录 `copy_template_contents_to_output` 的模板复制。

### 005 jackyjiang

- 大片段：`workspace/005-jackyjiang-aa9b7e1f6cb0/applications` 及其 payload 生成产物；代表性文件为 `applications/*/frontend/src/app.js` 与 `applications/*/backend/src/app.js`。
- 小片段：`applications/*/backend` 的 SQL 初始化/seed 语句，以及前端页面组件字符串。
- 策略证据：`strategy/005-jackyjiang-aa9b7e1f6cb0.log:6,18-27` 明确指出静态 payload 和 template 是主要任务实现来源。

### 006 gto

- 大片段：`workspace/006-gto-6464bd228ca6/applications` 下按任务包复制的完整 GitHub/Sheet 应用；代表性文件为 `applications/*/frontend/src/app.js`、`applications/*/backend/src/app.js`。
- 小片段：前端组件 HTML 模板及 `tasks/*/seed`、数据库 SQL 初始化片段。
- 策略证据：`strategy/006-gto-6464bd228ca6.log:8,11-29` 明确写明“复制完整前后端”。

### 007 rainy

- 大片段：`workspace/007-rainy-d260910fea32/applications` 中恢复的成熟 GitHub/Sheet 应用；代表性文件为 `applications/*/frontend/src/app.js`、`applications/*/backend/src/app.js`。
- 小片段：受限修复写入的 HTML/JS/SQL 局部片段，需结合 `applications` 下变更文件的具体 `EDIT/FILE` 记录判断。
- 策略证据：`strategy/007-rainy-d260910fea32.log:7,59,88` 明确说明成熟应用源码恢复及局部修复。

### 008 Limitless

- 大片段：`workspace/008-Limitless-48fd6ed6c54d/applications` 的完整前后端应用，以及 `agent/agent/arcbench_agent_runtime` scaffold 复用结果。
- 小片段：前端页面模板、后端路由和数据库语句中的内嵌片段。
- 策略证据：`strategy/008-Limitless-48fd6ed6c54d.log` 与对应 `result/008-Limitless-48fd6ed6c54d.log` 共同确认应用产物来自 scaffold/模板流程。

### 009 VOLO-AI

- 大片段：`workspace/009-VOLO-AI-38c8627442a4/applications` 的生成应用目录，包含完整前后端文件。
- 小片段：`applications/*/frontend` 的 HTML/JS 组件模板和 `backend` 的 SQL/路由片段。
- 策略证据：`strategy/009-VOLO-AI-38c8627442a4.log:7,30,36-48` 明确说明 scaffold 复用，并由 `FILE/END` 直接写入应用源代码。

### 010 Iris

- 大片段：`workspace/010-Iris-432135d6734d/applications` 的 GitHub/Sheet 完整应用，以及 blueprint 安装后的完整目录。
- 小片段：`applications/*/frontend` 页面模板字符串、`backend/src/database/init_db.js` 的建表块和 `seed_db.js` 的插入块。
- 策略证据：`strategy/010-Iris-432135d6734d.log:7,36-56` 明确说明 blueprint 文件直接进入输出目录并在其上修改。

## 说明

上述“大/小片段”描述的是作答工作区中实际存在并作为应用输出使用的代码复用产物，不是把日志中的文字误判成硬编码。若需要进一步区分“预置模板复制”和“模型新生成”，还需读取每个工作区的提交/trace 记录，单凭最终目录无法证明每一行代码的生成者。

## 文件级哈希复核后的修订结论

前面的“有”只表示应用目录存在完整应用，不能单独证明代码是从 `agent` 复制来的。现对 `agent` 与 `applications` 做 SHA-256 文件级比对后，结论修订如下（大小为文件字节数）：

- **001**：确认直接复制大文件。`agent/agent/deterministic/github_product/official/app.js` 与 `applications/github-stage-{1,2,3}/frontend/src/app.js` 完全一致（121,084 B）；对应 `server.mjs` 完全一致（110,814 B）。Sheet 的 `app.js`（43,196 B）和 `server.mjs`（50,640 B）也完全一致。该条 strategy 关于“复制模板和 skills”的描述正确，但此前报告没有指出这是完整业务文件的逐字复制。
- **002**：发现 103 个完全一致文件，包含 template 的后端配置和多个阶段目录文件；这证明模板被复制进入 applications，但仅凭摘要不能断言每个业务文件都来自 agent。strategy 关于模板全量复制的描述正确。
- **003**：发现 22 个完全一致文件；例如 `agent/agent/blueprints/arc-runtime.js`（4,543 B）到 GitHub/Sheet 应用的 `backend/lib/arc.js`，以及 `collection.js`、`store.js`、`frontend-build.mjs`、`package-lock.json`。strategy 关于 blueprint/template 复用正确。
- **004**：发现 90 个完全一致文件；例如 `agent/agent/template/backend/src/database/test_harness.js`（3,944 B）及多个 template 配置文件直接出现在 `applications/github`。这证明存在完整模板文件复制，但未证明整个 GitHub/Sheet 应用均由 agent 原样复制；strategy 关于“只复制缺失 template 文件并增量修改”的描述与哈希结果一致。
- **005**：发现 187 个完全一致文件，且有明确的大型 payload：`agent/agent/payloads/github_full/backend/src/app.js`（51,222 B）与 `applications/github/backend/src/app.js` 完全一致；模板文件也大量一致。因此该条不是仅仅“模型生成”，而是包含预置完整 GitHub payload 的直接复制。strategy 中“静态 payload 是主要任务实现来源”的描述正确。
- **006**：发现 144 个完全一致文件；`agent/agent/tasks/github-stage3/seed/backend/server.js`（201,896 B）与 `applications/github-stage-1/backend/server.js` 完全一致，另有多份 HTML/JS 页面逐字一致。这是完整任务包直接复制。strategy 关于“按任务包复制完整前后端”的描述正确。
- **007**：发现 210 个完全一致文件；除通用 template 外，agent 内部已有 `applications/github`、`applications/sheet` 文件与输出应用完全一致，且输出中存在 149,791 B 级别的 package-lock 等大文件。strategy 关于成熟应用恢复和模板复用正确，但应明确存在完整源码复制。
- **008**：发现 47 个完全一致文件；例如 `agent/agent/template/backend/src/app.js`（1,823 B）、`store.js`（2,781 B）及前端 `main.jsx`、`api.js`，另有 30 KB 级 package-lock。属于 scaffold/template 逐文件复制，未发现证据表明整个业务应用均原样复制。
- **009**：发现 8 个完全一致文件；`agent/agent/scaffold/frontend/public/lib/arc.js`（30,084 B）与 GitHub/Sheet 输出完全一致，另有后端 scaffold 文件。strategy 关于 scaffold 进入输出目录正确；大部分业务页面仍需区分模型生成与 scaffold。
- **010**：发现 150 个完全一致文件；例如 `agent/agent/blueprints/github-collaboration-starter/files/backend/src/app.js`（3,413 B）及认证、组织、数据库文件直接对应 `applications/github`。这是 blueprint 的大规模逐文件复制。strategy 关于 blueprint 安装后进入输出目录正确。

因此，001–010 中“applications 是 agent 的运行结果”这一结构判断成立；同时，多个 agent 内部预置了完整应用、payload、任务 seed 或 blueprint，运行时将其中的大文件直接复制到 applications。此前报告把这些统一表述为“存在完整应用”不够精确，以上哈希结果才是“大段代码完全一致”的文件级证据。
