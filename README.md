# guanyuan-majia · 观远 BI 马甲专版 Skill

> Claude Code Skill for **观远 BI / Guandata** — 数据查询 / ETL 治理与写入 / 自定义图表开发，**全栈三合一**。
> 60+ 张 ETL 创建/重构/修复 + 治理扫描 + 自定义图表注入排障的真实战场记录。

[![Skill Version](https://img.shields.io/badge/skill-v1.2-blue)](./SKILL.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-orange)](https://docs.claude.com/en/docs/claude-code/skills)
[![BI](https://img.shields.io/badge/Guandata-BI_6.x_/_7.x-purple)](https://www.guandata.com/)

**[English README](README.en.md)** · 中文文档 ↓

---

## 概述

本 Skill 整合了观远 BI 的三大类操作能力到**一份 Claude Code Skill** 里，让 AI 既能日常查数据出报表，又能做严肃的 ETL 治理与写入，还能处理自定义图表的前端注入排障。

| Part | 能力 | 触发场景 |
|---|---|---|
| 🅰️ **A** | 数据查询与卡片创建 | "查 2 月各城市营业额" / "做一张交叉表" / "删掉这张卡片" |
| 🅱️ **B** | ETL 治理与写入 | "扫一遍 ETL 看哪些可以删" / "建一个 ETL" / "direct-save 报错怎么修" |
| 🅱️ **B-17** | 全链路重写方法论 | "把这条 SmartETL 链整个改成 SQL 版" / "副本页验收 / 卡片级对比" |
| 🆎 **C** | 自定义图表开发与排障 | "payload_json 解析失败" / "固定卡片错位" / "overlay 切页残留" |

---

## ✨ 效果

### 数据分析侧（Part A）

- ✅ 26 种图表类型一键建卡 + 取数（柱状图、折线图、交叉表、组合图、气泡图……）
- ✅ 自定义公式字段（动态 `SUM(x)/SUM(y)*100` 类计算列，无需提前在 BI 界面建好）
- ✅ 多表 / 多页面 / 多字段缓存机制（按任务隔离 `--task` 名）
- ✅ 26 种聚合 + 13 种筛选操作符 + 6 种日期粒度（年/季/月/周/日/星期）
- ✅ 自动处理观远 7.0+ 的 draft-release 机制

### ETL 治理写入侧（Part B）

- ✅ **11 个已实测 BI HTTP API endpoint**（POST/GET/DELETE/OPTIONS 全覆盖）
- ✅ **批量治理扫描**：构建依赖图 → 检测循环依赖 → 计算复杂度 → 8 维 ETL + 4 维字段去留判断
- ✅ **ODS/DIM/DWD/DWS/APP 五层架构**重组指引
- ✅ **字段使用度双源审计**（page + etl 双源 grep，避免**仅看板会高估 8 倍可裁字段**）
- ✅ **POST /api/etl/direct-save** create + update 同接口的完整 payload schema
- ✅ **task error 真错误定位**（`status:FINISHED` 是任务触发结果，真错误在 `GET /api/task/<id>.response.result.error`）
- ✅ **删除拓扑**：`DELETE /api/data-source/` 必须先于 `DELETE /api/etl/`
- ✅ **v2→v3 批量改造 SDK**：`transformV2ToV3()` 7 步重写 + 节点 ID 重映射
- ✅ **CTO 张进的全链路重写方法论**：4 件交付 + 8 条硬规则 + 5 步标准工作流 + 三层验收 + 差异追踪 5 步法 + 空快照处理标准

### 自定义图表侧（Part C）

- ✅ **`renderChart` 4 参数 runtime 契约**详解（不是把第一个参数当 DOM 根节点）
- ✅ **5 种 `data` 形态**识别
- ✅ **payload_json 截断判断 3 步**（`Unterminated string` → 优先改数据方案，不堆兼容逻辑）
- ✅ **拆列推荐方案**（替代单字段长 JSON）
- ✅ **z-index 基线**（容器 8 / mask 1 / 固定卡 20）
- ✅ **生命周期管理**（URL 不匹配/编辑态/phoneView/路由离开 → 销毁注入物）
- ✅ **MutationObserver 死循环陷阱**（用低频轮询 + 精准 rect 比较替代）
- ✅ **复制页 card id 重定位**（不会显式报错，只会悄悄失效）
- ✅ **真实浏览器验收 8 项**

### 报错修复手册

- 🔧 **10 类 ETL 高频报错**：`请输入ETL名称` / `保存路径无效` / 上游运行权限不足 / 字段隐藏换行 / `<> NULL` / relativeFieldAlias 错位 / CTE 内 `;` / self-join 别名同名 / UNION 列差 / 字符串字面量与 DATE 比较

---

## ✅ 适合 / ❌ 不适合

### ✅ 适合

- 在观远 BI（Guandata 6.x / 7.x）上做日常数据分析、出报表
- 做 ETL 治理（识别循环依赖、判断字段去留、重新分层）
- 批量重建 ETL（30+ 张 v2→v3 改造）
- 做副本页验收 / 卡片级对比 / 差异追踪
- 自定义图表 HTML/CSS/JS 注入开发与排障
- 不会写代码但想让 AI 帮你完成上面这些事

### ❌ 不适合

- 用其他 BI 平台（Tableau / Power BI / Superset）—— 本 skill 只针对**观远 BI / Guandata**
- 完全不允许调用底层 HTTP API 的合规环境
- 没有 BI 账号 + 写权限（Part B 写入需要 ETL 创建权限 + 数据集运行权限）

---

## 📦 安装

### 方式 1：克隆到 Claude Code skills 目录（推荐）

```bash
cd ~/.claude/skills
git clone https://github.com/maojiebc/guanyuan-majia.git
cd guanyuan-majia
cp config.example.json config.json
# 编辑 config.json 填入 BI 凭据
vim config.json
```

### 方式 2：手动放置到任意 skill 加载路径

```bash
git clone https://github.com/maojiebc/guanyuan-majia.git
# 放到任何 Claude Code 会扫描的 skill 目录，例如：
mv guanyuan-majia /path/to/your/skills/
```

### 依赖

```bash
# Python 依赖（Part A）
pip install httpx

# guancli（Part B/C 必需）
npm install -g @guandata/guancli
guancli auth login   # 配置 BI 登录
```

---

## ⚙️ 配置

把 `config.example.json` 复制为 `config.json` 后填入真实凭据：

```json
{
  "version": "6",
  "base_url": "https://your-bi-instance.example.com/",
  "domain": "guanbi",
  "login_id": "your_username@example.com",
  "password": "your_password_here",
  "default_pg_id": "your_default_page_id",
  "default_folder_id": "your_default_folder_id"
}
```

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `version` | ✅ | `"6"`（观远 BI 6.x）或 `"7"`（观远 BI 7.0+，支持 draft/release） |
| `base_url` | ✅ | BI 实例地址，如 `https://bi.company.com:8080` |
| `domain` | ✅ | 登录域，通常为 `guanbi`（具体咨询 BI 管理员） |
| `login_id` | ✅ | BI 登录账号 |
| `password` | ✅ | BI 登录密码（**明文，仅供本地使用，已被 .gitignore 排除**） |
| `default_pg_id` | | 默认页面 ID（建卡时不传 `pg_id` 用这个） |
| `default_folder_id` | | 默认文件夹 ID（创建新页面时使用） |

> ⚠️ `config.json` 已被 `.gitignore` 排除，**不会被 commit 到仓库**。但请仍然小心保管，不要在公开环境分享。

---

## 🚀 快速开始

### Part A：建卡取数（数据分析）

```bash
SCRIPT="python3 ~/.claude/skills/guanyuan-majia/scripts/guandata.py"

# 1. 列数据集
$SCRIPT list-datasets

# 2. 看字段
$SCRIPT get-columns <ds_id>

# 3. 一步建卡 + 取数
$SCRIPT create-and-get '{
  "name": "2 月各城市营业额",
  "ds_id": "<dataset_id>",
  "chart_type": "BASIC_COLUMN",
  "pg_id": "<page_id>",
  "row": ["城市"],
  "metric": [{"name": "毛营业额", "aggr": "SUM"}],
  "filters": [{"name": "营业日期", "op": "BT", "value": ["2026-02-01", "2026-02-28"]}],
  "sorting": [{"name": "毛营业额", "order": "DESC"}]
}'
```

### Part B：建 ETL（数据建模）

```bash
# 1. 治理扫描
guancli etl tree
guancli --raw etl get <id> > raw/<id>.json
# 本地脚本分析依赖图、循环组、复杂度 → analysis.json + governance-report.md

# 2. 建 v2 目录（ETL + DATA_SET 各一个）
guancli fetch POST /api/directory \
  '{"name":"warehouse_v2","parentDirId":"<父>","dirType":"ETL"}'
guancli fetch POST /api/directory \
  '{"name":"warehouse_v2","parentDirId":"<父>","dirType":"DATA_SET"}'

# 3. 写入 + 执行
guancli fetch POST /api/etl/direct-save --stdin < payload.json
guancli fetch POST /api/etl/execute '{"dataFlowId":"<id>"}'

# 4. 失败定位（关键！别只看 status:FINISHED）
guancli fetch GET /api/task/<taskId> | jq '.response.result.error'
```

### Part C：自定义图表（前端排障）

```javascript
// 观远 runtime 真实签名（不是把第一个参数当 DOM 根节点！）
function renderChart(data, clickFunc, config, helpers) {
  // data 常见形态：
  // [[ {name:"payload_json",data:["{...}"]}, {name:"report_date",data:["2026-03-18"]} ]]

  // 关键：如果 JSON.parse(payload_json) 报 Unterminated string
  //  → 优先判断为"数据链路截断"，改数据方案（拆列），不堆前端兼容逻辑
}

new GDPlugin().init(renderChart);
```

---

## 📁 目录结构

```text
guanyuan-majia/
├── SKILL.md                          # AI 读的主文档（Part A + B + C，1968 行）
├── README.md                         # 本文件（中文）
├── README.en.md                      # English README
├── ATTRIBUTIONS.md                   # 致谢与来源
├── LICENSE                           # MIT
├── config.example.json               # 配置模板（公开版）
├── config.json                       # 你的真实凭据（gitignore 排除，不会 commit）
├── .gitignore
├── scripts/
│   ├── guandata.py                   # Part A 主脚本（建卡 / 取数 / 删卡 / 发布页面）
│   └── zonedata_builder/             # zoneData 构建模块
└── references/                       # 深度参考资料
    ├── custom-chart-playbook.md      # CTO 张进自定义图表完整排障手册原文
    ├── etl-rewrite-original.md       # CTO 张进 SmartETL 改写经验原文
    ├── execplan-spec.md              # OpenAI Codex ExecPlan 规范（V1.2 新增）
    └── agents-rule.md                # OpenAI Codex 极简调度规则（V1.2 新增）
```

---

## 🎯 何时用 Part A / B / C

| 用户需求 | 走 |
|---|---|
| "查一下 2 月各城市营业额" | A |
| "做一张交叉表给我" | A |
| "删掉这张卡片" | A |
| "扫一遍 BI 的 ETL 看哪些可以删" | B |
| "ETL 之间有循环依赖怎么办" | B |
| "帮我新建一个 ETL" | B |
| "direct-save 报错怎么修" | B |
| "字段使用度审计" | B |
| "把这条 SmartETL 链整个改成 SQL 版" | **B-17** |
| "做副本页验收 / 卡片级对比" | **B-17** |
| "上游空快照怎么写结论" | **B-17** |
| "差异定位到底在 SQL 还是执行时点" | **B-17** |
| "30+ 表跨多日工程怎么管 / 给我 ExecPlan 骨架" | **B-17.11** |
| "自定义图表脚本不执行 / payload_json 报错" | **C** |
| "固定卡片错位 / overlay 切页残留" | **C** |
| "renderChart 第一个参数到底是啥" | **C** |

---

## ❤️ 致谢与来源

本 skill 站在多个前辈项目和经验贡献者的肩膀上，详细致谢见 [ATTRIBUTIONS.md](./ATTRIBUTIONS.md)：

- **[guandata-bi @ ClawHub](https://clawhub.ai/skills/guandata-bi)** — 观远 BI 通用版 skill，本项目最早的灵感来源
- **[zhengyuhe123/guandata](https://github.com/zhengyuhe123/guandata)** — guandata 原始 GitHub 项目
- **小小郑3号 · guandata70** — 观远 7.0+ 适配版（draft/release 机制），本项目 Part A 的直接前身
- **观远 BI CTO 张进** — Part B-17（SmartETL 全链路重写方法论）+ Part C（自定义图表开发与排障）的核心经验贡献者
- **OpenAI Codex** — V1.2 引入的 [ExecPlan 规范](./references/execplan-spec.md)（自包含活文档 + 四章节项目管理结构），用于 30+ 张表跨多日 SmartETL 重写工程的项目化追踪
- **马甲（@maojiebc）** — Part A/B 实战整合与 60+ 张 ETL 写入实证记录

> 没有 ClawHub / 张进 / 小小郑3号 / OpenAI Codex 的开源精神，这份 skill 不可能存在。

---

## 📋 版本记录

完整变更历史见 [SKILL.md 末尾的版本记录](./SKILL.md#-版本记录)。

- **V1.2** (2026-05-09) — 吸收 OpenAI Codex 的 ExecPlan 规范，新增 B-17.11 用 ExecPlan 管理重写工程（SmartETL 改写专用骨架 + 四个活文档章节实战用法）+ B-12 工程化指针；`references/` 加 execplan-spec.md + agents-rule.md
- **V1.1** (2026-05-09) — 整合 CTO 张进的两份经验：B-17 全链路重写方法论 + Part C 自定义图表
- **V1.0** (2026-05-09) — 重命名 `guandata70` → `guanyuan-majia`，新增 Part B：ETL 治理与写入完整指南
- **V0.x** (2026-03-30) — guandata70 初版（小小郑3号），适配观远 BI 7.0+

---

## 🤝 贡献

欢迎 issue 和 PR：

- 🐛 发现报错没在手册里的：欢迎提交 issue 描述报错信息 + payload + 真实错误（`/api/task/<id>.response.result.error`）
- 📝 你跑通了新的 BI HTTP API endpoint：欢迎补充到 Part B 的 API 全图
- 🎨 自定义图表新场景：欢迎补充到 Part C
- 📚 文档优化、翻译、错别字修正：直接 PR

---

## 📄 License

[MIT](./LICENSE) © 2026 [maojiebc](https://github.com/maojiebc) and contributors.

本 skill 基于他人开源工作整合而成，详细 attribution 见 [ATTRIBUTIONS.md](./ATTRIBUTIONS.md)。
