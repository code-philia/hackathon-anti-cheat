# Ranking

## 1. 非 TEMPLATE 违规行为：非法获取测试等文件

共 **8 / 50 个榜单条目**命中，每个条目 1 条有效 `[NET-EXTERNAL]` error：

- 均有直接定位、读取、复制、执行或向模型注入平台测试/评分材料的证据。
- 仅探测 `/workspace/tests` 存在性或对象类型的记录已降为 warning，不计入本类。

命中排名：**002、003、010、013、017、022、033、048**。

| 排名 | 条目 | Error | 非法获取行为 |
| ---: | --- | --- | --- |
| 002 | Orchestro | ERROR-003 | 枚举/读取 `/workspace/tests`、`/opt/arcbench/node_modules` 和 `.arc` 平台资料 |
| 003 | chrislearn | ERROR-002 | 读取验收/评分测试，将 spec、helper、端口和失败结果用于生成修复 |
| 010 | Iris | ERROR-003 | 从平台路径读取未授权测试文件 |
| 013 | 奶龙小脚香香喵 | ERROR-003 | 读取评分测试，将原文、端口和测试合同用于生成修复 |
| 017 | MorningW1nd | ERROR-004 | 探测、读取、复制、执行平台测试并用于迭代修复 |
| 022 | Shallow | ERROR-003 | 枚举并读取平台验收测试规格以提取端口 |
| 033 | 1648557528 | ERROR-002 | 定位、读取、复制、执行外部评分测试并回写结果 |
| 048 | AIOS | ERROR-002 | 读取、复制平台验收测试并带入生成/验证流程 |

## 2. TEMPLATE: 预置代码 + 复制粘贴

仅在未命中第 1 类的 **42 个条目**中检索。纳入条件为同一条有效 `[TEMPLATE-DIRECT]` 或 `[TEMPLATE-INDIRECT]` finding 同时包含：

- `知识类型：(1)完整代码实现`
- `生成方案：(1)无模型参与地使用代码`

共命中 **22 / 42 个剩余条目**，对应 **28 条** template error。全部为 `[TEMPLATE-DIRECT]`，没有符合条件的 `[TEMPLATE-INDIRECT]`。

命中排名：**001、005、006、007、011、012、014、018、020、021、025、029、030、031、032、034、036、038、041、045、046、050**。

| 排名 | 条目 | 符合条件的 Error | 检索方式 | 预置并直接使用的内容 |
| ---: | --- | --- | --- | --- |
| 001 | bugtakue | ERROR-001、ERROR-002 | 题面硬编码 | 完整 GitHub 与 Sheet 前后端产品 |
| 005 | jackyjiang | ERROR-001、ERROR-002 | 题面硬编码、关键词硬编码 | 完整 GitHub 与 Sheet 应用 |
| 006 | gto | ERROR-001、ERROR-002 | 题面硬编码 | 完整 GitHub 与 Sheet seed 应用 |
| 007 | rainy | ERROR-001、ERROR-002 | 题面硬编码 | 完整 GitHub 与 Sheet 恢复应用 |
| 011 | sunhao | ERROR-001 | 题面硬编码 | 按公开题面标题选择并复制完整应用 |
| 012 | tyreseluo0630 | ERROR-001 | 全量使用 | 完整 Web 应用 scaffold |
| 014 | Tired | ERROR-001 | 题面硬编码 | 按 requirements 哈希选择完整 GitHub/Sheet 应用 |
| 018 | 2M2 | ERROR-001 | 全量使用 | 完整登录、退出与会话刷新实现 |
| 020 | Liii | ERROR-001、ERROR-002 | 关键词硬编码 | 完整 GitHub 与 Sheet 应用 |
| 021 | bzt | ERROR-002 | 全量使用 | NamedForm、DataTable、EntityCard 等应用级实现 |
| 025 | 排行榜气氛组55 | ERROR-001 | 全量使用 | 完整会话登录、退出及缓存清理模块 |
| 029 | CodeRun | ERROR-001 | 全量使用 | 同时匹配 GitHub 与 Sheet 的完整应用模板 |
| 030 | 5qwq | ERROR-001 | 全量使用 | GitHub 身份与访问客户端实现 |
| 031 | 66大顺 | ERROR-001 | 全量使用 | 会话身份模块及使用合约 |
| 032 | OUC-SOUND-TEAM | ERROR-001、ERROR-002 | 题面硬编码 | 覆盖全部叶子需求的 GitHub 与 Sheet 应用 |
| 034 | 能智吗 | ERROR-001 | 全量使用 | GitHub 每浏览器会话独立种子状态宿主实现 |
| 036 | 星期3做小三 | ERROR-001 | 全量使用 | GitHub 身份会话实现及复用合约 |
| 038 | 强强 | ERROR-001 | 关键词硬编码 | 按领域选择并复制完整 GitHub/Sheet 功能包 |
| 041 | 先提交再说 | ERROR-001 | 全量使用 | 身份会话实现 |
| 045 | nnn45 | ERROR-001 | 全量使用 | 完整认证会话实现 |
| 046 | 删库跑路小分队 | ERROR-001 | 关键词硬编码 | 完整 Sheet reference 应用 |
| 050 | 幻觉工程研究院 | ERROR-001 | 全量使用 | 完整登录会话状态实现 |



## 剩余条目

排除第 1 类的 8 个条目和第 2 类的 22 个条目后，还剩 **20 / 50 个条目**：

**004、008、009、015、016、019、023、024、026、027、028、035、037、039、040、042、043、044、047、049**。

### 剩余条目的 error 情况

- 其中 **18 个条目仍有 error，共 23 条**；全部为 `[TEMPLATE-DIRECT]`。
- 这些 error 主要是应用行为合同、领域规则或验收测试片段进入模型生成/修复流程，没有同时满足第 2 类的“完整代码实现 + 无模型直接使用”。
- **023、047 当前为 0 error，判决为通过**。

| 排名 | 条目 | 有效 error | 简要情况 |
| ---: | --- | --- | --- |
| 004 | zhx | ERROR-001、ERROR-002 | 注入应用功能合同；执行专用 Playwright 检查并用失败结果修复 |
| 008 | Limitless | ERROR-003 | 将两个任务的应用行为契约整体注入生成模型 |
| 009 | VOLO-AI | ERROR-001 | 将 Sheet 表格交互实现细节提供给模型复用 |
| 015 | haiknow | ERROR-001 | 全量注入登录、登出和会话状态实现契约 |
| 016 | KaKa | ERROR-001、ERROR-002 | 使用 GitHub 验收代码修复；注入 GitHub/Sheet 应用合约 |
| 019 | Amazing | ERROR-001 | 向生成与修复提示注入 GitHub/Sheet 应用实现契约 |
| 023 | superz | 无 | 0 error，当前通过 |
| 024 | 00v00 | ERROR-001 | 向编码模型注入登录与会话行为契约 |
| 026 | RyanSanchez | ERROR-002 | 将 GitHub/Sheet 应用契约和验收细节置入系统提示 |
| 027 | 全村的希望 | ERROR-001 | 全量读取并注入 GitHub/Sheet 领域行为契约 |
| 028 | 我要当第一 | ERROR-001 | 将 GitHub 应用功能合同作为模型上下文 |
| 035 | apach | ERROR-001、ERROR-002 | 使用 Sheet 单元格验收代码修复；注入 GitHub 会话实现方案 |
| 037 | Leonard | ERROR-001、ERROR-002 | 注入 GitHub/Sheet 功能契约；用预置验收失败驱动修复 |
| 039 | xinyurun | ERROR-001 | 全量注入 Sheet/GitHub 编辑控件行为契约 |
| 040 | chengyuj94 | ERROR-001 | 向规划、生成和修复提示注入两个任务的应用行为契约 |
| 042 | AFlickerr | ERROR-001 | 向源码生成注入账户、登录、会话和权限合同 |
| 043 | 分支比人多 | ERROR-001 | 向编码模型注入 GitHub/Sheet 组件与功能合同 |
| 044 | nsy | ERROR-001、ERROR-002 | 按题型注入实现合同；用预置验收失败驱动修复 |
| 047 | my67 | 无 | 0 error，当前通过 |
| 049 | JJJ | ERROR-001 | 向每次生成注入 GitHub/Sheet 应用级实现合同 |
