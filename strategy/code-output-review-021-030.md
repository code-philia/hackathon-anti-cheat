# 021–030 作答代码复用核查

这里将 `agent/agent.zip` 视为选手提交的智能体，将 `applications/*.zip` 视为该智能体运行后的作答结果。完全一致依据压缩包内文件的 SHA-256 相同判断；只把大于 10 KB 的一致文件列为“大段代码证据”。

| 编号 | 文件级复用结论 | 大段完全一致证据 | strategy 论述核对 |
|---|---|---|---|
| 021 | 仅确认 skill 文件复制 | `arcbench-frontend-spec/SKILL.md` 23,735 B，复制到三个结果包 | 应表述为预置 skill 注入，不能称完整应用复制 |
| 022 | 仅确认 scaffold 依赖复制 | `scaffold/minimal-web/frontend/package-lock.json` 112,769 B，复制到两个阶段包 | 应表述为 scaffold/template 复用 |
| 023 | 仅确认 template/skills 复制 | checkpoint、traceability、两个 package-lock、`template/scripts/check.py` | 不能据此称完整业务应用原样复制 |
| 024 | 仅确认 template/skills 复制 | checkpoint、traceability、两个 package-lock、`check.py` | strategy 的模板复用结论成立 |
| 025 | 仅确认 template/skills 复制 | checkpoint、traceability、两个 package-lock、`check.py` | 未发现完整业务 payload 的大文件证据 |
| 026 | 未发现大于 10 KB 的完全一致文件 | 无 | 不能声称完整代码由 agent 直接复制 |
| 027 | 仅确认 template/skills 复制 | checkpoint、traceability、两个 package-lock、`check.py` | 需避免把模板复制扩大为应用全量复制 |
| 028 | 仅确认 template/skills 复制 | checkpoint、traceability、两个 package-lock、`check.py` | 同上 |
| 029 | 确认完整 GitHub 业务模块复制 | `factory/assets/github/backend/src/pages/work.js` 41,221 B；`repository.js` 22,677 B；`repos.js` 17,897 B；`settings.js` 14,634 B；`html.js` 11,286 B | strategy 应明确 factory assets 是应用业务源码来源 |
| 030 | 仅确认 template/skills 复制 | checkpoint、traceability、两个 package-lock、`check.py` | 未发现完整业务 payload 的大文件证据 |

## 逐项说明

### 021 bzt

`agent` 与结果压缩包之间只确认 3 个大文件级一致项，均为 `arcbench-frontend-spec/SKILL.md`。这证明 skill 被带入结果，不证明 GitHub/Sheet 完整业务源码从 agent 原样复制。若 strategy 只说预置规则/skill 参与生成，则正确。

### 022 Shallow

确认 `scaffold/minimal-web/frontend/package-lock.json` 在两个阶段结果中逐字一致。该证据支持 scaffold 复制；当前没有完整业务文件的哈希证据。

### 023 superz

确认 20 个一致文件，主要是 arcbench skills、template package-lock 和检查脚本。应将结论限定为模板与技能复制，不能推断完整 GitHub/Sheet 应用原样复制。

### 024 00v00

确认 15 个一致文件，类型与 023 相同，属于模板、依赖和运行技能复制。业务应用主体没有大文件级完全一致证据。

### 025 排行榜气氛组

确认 25 个一致文件，仍集中在 skills、template 和 package-lock。结果目录存在完整应用，但文件比对不能证明其业务代码全部来自 agent 内置副本。

### 026 RyanSanchez

没有发现大于 10 KB 的 agent/application 完全一致文件。该结果不能支持“完整应用直接复制”的说法；需结合 trace 判断模型生成或小文件复制。

### 027 全村的希望

确认 20 个一致文件，主要为 template/skills。应保留“模板复用”表述，删除“完整业务应用复制”的推断。

### 028 我要当第一

确认 20 个一致文件，主要为 template/skills。与 027 相同，业务主体没有大文件完全一致证据。

### 029 CodeRun

确认 14 个一致文件，其中存在明确的大型 GitHub 业务模块：`work.js` 41,221 B、`repository.js` 22,677 B、`repos.js` 17,897 B、`settings.js` 14,634 B、`html.js` 11,286 B。该条可以认定 factory 内置的完整 GitHub 页面/业务模块直接进入 `applications/github.zip`。

### 030 5qwq

确认 25 个一致文件，主要为 skills、template、package-lock 和检查脚本；没有大型业务 payload 的一致证据。

## 总体修订

021–030 不能统一归类为“完整 GitHub/Sheet 应用由 agent 原样复制”。文件级证据显示：021–025、027–028、030 主要是模板/技能/依赖复制；026 没有确认的大文件一致；029 明确存在多个完整 GitHub 业务模块逐字复制。`applications` 始终是智能体运行后的作答结果，但结果中代码的具体来源必须按上述哈希证据区分。
