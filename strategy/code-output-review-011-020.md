# 011–020 作答代码复用核查

核查对象为 `workspace/011`–`workspace/020` 中的实际作答目录，并与对应的 `strategy/*.log`、`result/*.log` 对照。大片段指完整应用/完整前后端文件；小片段指页面 HTML、组件模板、SQL、seed 或配置块。

| 编号 | 大片段代码 | 小片段代码 | 结论依据 |
|---|---|---|---|
| 011 | 有 | 有 | 哈希清单直接复制预构建 Sheet/GitHub 应用；策略行 8、37–51 |
| 012 | 有 | 有 | scaffold/template 生成完整前后端；策略行 8、21–27 |
| 013 | 有 | 有 | deterministic canvas 复制 official GitHub/Sheet 文件；策略行 7、36–52 |
| 014 | 有 | 有 | 工作区包含完整应用阶段产物；结合对应 result 与应用目录核对 |
| 015 | 有 | 有 | 明确复用 local template、skills 和 workspace artifacts；策略行 58、110 |
| 016 | 有 | 有 | 通用模板复制并在阶段应用上适配；策略行 7、60、213 |
| 017 | 有 | 有 | 生成器输出 frontend/backend 文件；小任务允许 tiny HTML/codegen 模板；策略行 8、41–61 |
| 018 | 有 | 有 | 控制器复制 template、skills 并生成应用源代码；策略行 7、32、36–38 |
| 019 | 有 | 有 | 模板复制、产品契约和阶段记忆进入生成上下文；策略行 7、88–92 |
| 020 | 有 | 有 | `copytree` 复制预置完整模板并走关键词快速路径；策略行 5、34 |

## 逐项定位

### 011 sunhao

- 大片段：`workspace/011-sunhao-e19423e68321/applications/github`、`applications/sheet`，是按哈希清单恢复的完整前后端应用。
- 小片段：上述应用中的 `frontend` 页面模板、`backend` 路由/数据库初始化和 seed 文件；这些属于大片段中的组件级直接复用。
- 证据：`strategy/011-sunhao-e19423e68321.log:8,37-51` 明确写明“直接复用完整前后端文件”。

### 012 tyreseluo0630

- 大片段：`workspace/012-tyreseluo0630-75216a25af14/applications/github*`、`applications/sheet`，由 scaffold/template 进入输出目录。
- 小片段：`frontend` 的 HTML/JS 组件模板、`backend` 的 SQL/seed 块；结合 `result/012-tyreseluo0630-75216a25af14.log` 的生成/修复记录核对。
- 证据：`strategy/012-tyreseluo0630-75216a25af14.log:8,21-27`。

### 013 奶龙小脚香香喵

- 大片段：`workspace/013-奶龙小脚香香喵-063c27c8b27c/applications` 中的 GitHub/Sheet 完整应用，以及 deterministic 官方实现。
- 小片段：`agent/agent/deterministic/*_product/official` 中的页面渲染模板和后端固定数据/路由片段。
- 证据：`strategy/013-奶龙小脚香香喵-063c27c8b27c.log:7,36-52`。

### 014 Tired

- 大片段：`workspace/014-Tired-81126f2cb60f/applications` 的完整应用阶段目录；按最终应用文件与 `result/014-Tired-81126f2cb60f.log` 的输出记录核对。
- 小片段：应用 `frontend` 中的内嵌 HTML/组件字符串和 `backend` 中的 SQL/配置块。
- 证据：对应 `strategy/014-Tired-81126f2cb60f.log` 的 CODE-REUSE/PREPARED-KNOWLEDGE 条目。

### 015 haiknow

- 大片段：`workspace/015-haiknow-bcc80ee75a90/applications` 的完整前后端应用和模板产物。
- 小片段：模板中的页面组件、路由、数据库初始化和 seed 片段。
- 证据：`strategy/015-haiknow-bcc80ee75a90.log:58,110` 明确写明复用本地 template、skills 和增量工作区产物。

### 016 KaKa

- 大片段：`workspace/016-KaKa-450dbb130f66/applications` 的阶段应用和通用模板文件。
- 小片段：阶段应用的前端模板、后端 SQL/路由局部；压缩包与最终应用需按 result 记录进一步区分。
- 证据：`strategy/016-KaKa-450dbb130f66.log:7,60,213`。

### 017 MorningW1nd

- 大片段：`workspace/017-MorningW1nd-c0de05637c2b/applications` 中生成的 frontend/backend 文件。
- 小片段：tiny HTML、单响应文件块、组件模板和验证所需的局部文件。
- 证据：`strategy/017-MorningW1nd-c0de05637c2b.log:8,41-61`；策略明确说明模板不会作为最终页面整体输出，但其内容进入生成上下文。

### 018 2M2

- 大片段：`workspace/018-2M2-a95fed7eca51/applications` 的应用源代码和模块提交快照。
- 小片段：模板页面、skills 生成的 contract/acceptance 片段，以及后端 SQL/配置块。
- 证据：`strategy/018-2M2-a95fed7eca51.log:7,32,36-38`。

### 019 Amazing

- 大片段：`workspace/019-Amazing-faa1a2b02cf8/applications` 的完整应用文件；FILE/EDIT 协议写入的最终应用属于直接输出产物。
- 小片段：应用中的 HTML/JS 组件、SQL 和路由局部。
- 证据：`strategy/019-Amazing-faa1a2b02cf8.log:7,88-92`。

### 020 Liii

- 大片段：`workspace/020-Liii-8df71b56b920/applications/github*`、`applications/sheet`，由预置模板 `copytree` 复制形成。
- 小片段：模板中的页面 HTML、组件字符串、数据库初始化/seed 片段。
- 证据：`strategy/020-Liii-8df71b56b920.log:5,9,34`。

## 文件级哈希复核后的修订结论

011–020 的后半段工作区以 `agent/agent.zip` 和 `applications/*.zip` 保存，因此按压缩包内文件逐项计算 SHA-256。完全一致表示 agent 压缩包内的文件在 applications 压缩包中逐字出现。

- **011**：28 个大于 5 KB 的文件完全一致，包括 `backend/src/m1.js`（20,972 B）、`m2.js`（14,862 B）、`m3.js`（23,319 B）、`m4.js`（22,311 B）、`m5.js`（29,193 B）。预构建 GitHub 应用的大量业务文件直接进入 `applications/github.zip`。
- **012**：`scaffold/frontend/public/lib/arc.js`（29,743 B）在 GitHub 三个阶段、GitHub 主包和 Sheet 包中完全一致。确认 scaffold 复制，不能据此断言完整业务应用原样复制。
- **013**：28 个文件完全一致，包括 `factory/snapshots/github/backend/routes/code.js`（17,368 B）、`routes/issues.js`（15,885 B）和 scaffold 的 `ui.js`（12,879 B）。deterministic/factory 快照中的业务模块被直接复制。
- **014**：当前压缩包哈希比对没有得到可确认的大文件交集，不能把“存在完整应用”改写为“完整代码由 agent 原样复制”。
- **015**：55 个文件完全一致，包括 `arc_traceability.py`（27,984 B）和前后端 package-lock（149,791 B、178,360 B）。确认 template 与 bundled skills 直接带入 applications，不等于全部业务代码原样复制。
- **016**：没有得到完全一致的大文件交集，只能确认模板复制和阶段应用适配路径。
- **017**：没有得到完全一致的大文件交集；当前证据支持按需求节点生成 frontend/backend 文件，不能证明完整应用来自 agent 副本。
- **018**：42 个文件完全一致，包括 skills 脚本、template README、前后端 package-lock 和状态 README。确认模板/skills 复制，未据此认定全部业务文件原样复制。
- **019**：9 个文件完全一致；`template/backend/src/index.js`（14,035 B）和前端 package-lock 在多个阶段应用中逐字一致。确认模板复制，业务主体仍无完全复制证据。
- **020**：104 个文件完全一致，包括 `arcagent/github_full/backend/src/database/init_db.js`（14,692 B）、`seed_db.js`（24,156 B）、`routes/issues.js`（31,265 B）、`routes/repos.js`（49,389 B）。agent 内置的 `github_full` 是完整业务 payload，多个大文件直接进入阶段应用。

## 判定边界

这里记录的是实际作答目录中的代码复用和输出产物，不把日志中出现的文件路径或函数名误判为代码。最终目录只能证明代码确实进入作答结果；若要进一步判定某段代码是预置复制、模型生成还是后续修复写入，需要继续对照各自的 trace/提交快照。
