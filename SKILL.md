---
name: majia-guanyuan
description: 观远 BI（Guandata）全链路操作 — 数据查询/建卡/取数（Part A）、ETL 治理/写入/删除（Part B，含 SmartETL 全链路重写 + 字段使用度审计 + ExecPlan 工程化）、自定义图表 HTML/CSS/JS 注入与排障（Part C，含 HTML 应用化看板生成 + selector 联动 descriptor patch）、**V7 Page/Card 发布流水线 + 三态硬规则（Part D，V2.1.6 新增：guanvis-skill 一键 publish / CSV 三态判断 / Spark CTE 中文别名坑 / ETL update dsId 注入）**，以及**餐饮 BI 公式实战库**（V2.1.5 新增：60+ SQL 公式 / RFM 8 类营销策略 / AC/ADS/ADT/Comp 营收 KPI / 6 大 ETL 工程范式 / 39 ETL 索引）。当用户提到 营业额/门店/会员/订单/建卡/取数/报表/ETL/direct-save/payload_json/自定义图表/HTML 看板/应用化/更高级/不限标准看板/观远/Guandata/BI/v7 BI/草稿 60004/CSV 散客 100% 假指标/Spark CTE 中文别名/1012 同名文件/guanvis-skill/复购率/客单价/RFM/DWD 宽表/财务双源对账/AC/ADS/Comp 老店 时使用。马甲业务实战版，60+ ETL 战例、10 类报错手册、Claude Code/OpenClaw/Codex/Hermes 通用。
license: MIT
metadata:
  version: "2.1.7"
  author: "超级马甲 / maojiebc"
  homepage: https://github.com/maojiebc/majia-guanyuan
  openclaw:
    emoji: "📊"
    homepage: https://github.com/maojiebc/majia-guanyuan
    os:
      - macos
      - linux
    requires:
      bins:
        - jq
        - bash
      config:
        - config.json
    install:
      - kind: pip
        package: "httpx>=0.20"
      - kind: npm
        package: "@guandata/guancli@^1.0.24"
        bins:
          - guancli
---

# 观远 BI · 马甲专版（V2.1.7）

> **结构说明（V1.5.0 引入 progressive disclosure）**：本文档是**路由层 + 关键规则**，详细操作手册下沉到 `references/`。每个 Part 的入口章节会指出"何时回到 references/ 查全表"。完整章节索引见末尾的 [📚 References 目录](#-references-目录)。

## 🧭 Part 选择

| 你想做 | 走 |
|---|---|
| 查数据、建卡、生成报表、做分析 | **Part A：数据查询与卡片创建** |
| 扫整库 ETL 治理 / 新建/修改/删除 ETL / 字段使用度审计 / 修复 ETL 报错 | **Part B：ETL 治理与写入** |
| 把整条 SmartETL 链改写成 SQL 版 + 页面副本验收 + 差异定位 + 空快照阻塞 | **Part B-17：全链路重写方法论**（拆到 [references/part-b17-fullchain-rewrite.md](references/part-b17-fullchain-rewrite.md)） |
| 30+ 张表批量迁移 / 跨多日工程 / 复杂重构需要项目化追踪 | **B-17.11 ExecPlan 工作法**（同上文件 §11） |
| 自定义图表 HTML/CSS/JS 注入、固定卡片/overlay、payload_json 取数、路由清理 | **Part C：自定义图表开发与排障** |
| 从零生成 HTML 化经营分析应用（用户说"更高级 / 应用化 / 自定义模块 / 最完美 / 不限标准看板"）| **Part C-12：HTML 应用化看板生成**（拆到 [references/part-c-html-dashboard.md](references/part-c-html-dashboard.md)） |
| **v7 BI 实例**上端到端搭多个 HTML 应用看板 / 手撸 `POST /api/page+/api/card` 被 `60004 此操作只能在草稿页面执行` 卡住 / CSV 散客 `会员ID IS NOT NULL` 算出 100% 假指标 / Spark `WITH 中文别名` 报 `PARSE_SYNTAX_ERROR` / ETL update 报 `1012 输出数据集目录中存在同名文件` | **Part D：V7 Page/Card 发布流水线 + 三态硬规则**（V2.1.6 新增，拆到 [references/v7-page-card-publish-pipeline.md](references/v7-page-card-publish-pipeline.md)） |
| 写餐饮业务公式（AC / ADS / 复购率 / 新老客 / 用餐时段 / 留存流失 / RFM / Comp 老店）/ 查字段口径 / 排数据质量坑 / **ETL 工程范式（DWD 宽表 / 双源对账 / 评价 pipeline）** | **餐饮 BI 公式实战库**（[references/restaurant-bi-formulas/README.md](references/restaurant-bi-formulas/README.md)，V2.1.5 蒸馏自两段餐饮连锁 BI 履职 + 39 个生产 ETL，全脱敏） |
| 不知道用哪个 | 看 Part B "推荐工作流" 章节，或直接读各 Part 章节末尾的"实战 ID 速查" |

> **作者**：马甲（Part A/B 实证）+ 观远 CTO 张进（Part B-17 SmartETL 改写方法论 + Part C 自定义图表经验）+ OpenAI Codex（V1.2 ExecPlan 规范）
> **版本**：V2.1.7（2026-05-21）· **环境**：Node ≥20 · **依赖**：`@guandata/guancli@^1.0.24`（V2.1.6 起：1.0.24 自带 `guanvis-skill` 公网分发，`guancli install-skill` 一键装到 `~/.agents/skills/`） · **作用域**：本地私有 BI 实例
> **安装**：`git clone https://github.com/maojiebc/majia-guanyuan.git` + `node bin/install.js install`，或 `npx github:maojiebc/majia-guanyuan install`
> **兼容工具**：Claude Code · OpenClaw · Codex · Hermes (gbrain) · 任何支持 `SKILL.md` frontmatter 的 agent。详见 [README · 兼容性](README.md#-兼容性--compatibility) 与 [AGENTS.md](AGENTS.md)。
>
> 🆕 **V2.0 升级提示**：原名 `guanyuan-majia` 已重命名为 `majia-guanyuan`，对齐马甲家族风格。GitHub repo URL 同步迁至 `maojiebc/majia-guanyuan`（旧地址自动 redirect，老 clone 不影响）。新增命令面与 `@guandata/guancli@1.0.19` 对齐 —— ChatBI 主题问数 (`guancli chatbi`) / SuperApp (`guancli app`) / 多环境 auth (`auth list/use/whoami`) / 连接探测 (`guancli status`)。详见 [CHANGELOG.md](CHANGELOG.md)。
>
> 🆕 **V2.1 升级提示**（2026-05-13）：官方 `@guandata/guanvis-skill@0.1.13` 已通过观远**内网 Nexus 私服**（`https://app.mayidata.com/nexus/repository/guandata-web/`）分发，公网 npm 仍 404；内网员工可让同事下 tarball 走 [references/internal-nexus-install.md](references/internal-nexus-install.md) 的"四步法"装上。本 skill **Part A 的标准 30+ 图表建卡需求优先路由到 `guanvis-skill` 的 JS DSL**（`card_*.js` / `page.js`），本 skill 的 `guandata.py` / `create-card` 保留为 fallback + payload 底层参考，便于无 `guanvis-skill` 的环境继续工作。其他四个兄弟 skill（`guanetl-skill` / `guands-skill` / `guanexport-skill` / `guanadmin-skill`）公网 + 内网均未确认发包，仍走 `guancli fetch` + 本 skill Part B。

---

# 🅰️ Part A：数据查询与卡片创建

## ⚠️ 关键规则

**所有数值计算必须跑代码** — 禁止在思考中直接口算百分比、环比、除法等。

1. **必须提供 pg_id** — 不保存的卡片无法取数据
2. **先查页面权限** — 用 `list-pages --manageable` 找有权限的页面，不用翻 JSON
3. **筛选值按需查** — 只有用了分类筛选（`IN`/`EQ`/`CONTAINS`）才需要 `search-values`；纯日期范围（`BT`）不需要
4. **图表类型限制** — 超出 metric/row/column 上限会返回空数据
5. **必须确认数据范围** — 用户没有明确指定日期范围时，**必须追问**，不要自己假设。例如："你想看哪段时间的数据？" 或提供选项："要看今天、本周还是上月？"

**遇到意外的错误以及得到新的教训立即更新：** 遇到意外的错误立即把它落到 SKILL.md 对应的章节（Part B 报错走 `references/part-b-errors.md`，Part C 走 `references/part-c-payload-json.md` 等）或 ExecPlan 的 `Surprises & Discoveries` 章节（B-17.11）。格式：

```markdown
### [YYYY-MM-DD] 简要标题
- **场景**: 什么情况下遇到的
- **问题**: 发生了什么（含 task error 原文、payload 片段）
- **判断**: 应该怎么做
```

## 基本信息

> 路径约定：以下命令假定 cwd 是 skill 安装目录。Skill 路径因 agent 工具不同而异（见 [README](README.md) 的兼容性表）：Claude Code 在 `~/.claude/skills/majia-guanyuan/`，OpenClaw 在 `~/.openclaw/skills/majia-guanyuan/`，Codex 在 `~/.codex/skills/majia-guanyuan/`，Hermes 在 `<workspace>/skills/majia-guanyuan/`。所有 Part A 命令都用相对路径 `scripts/guandata.py`，无需修改。

- 配置文件: `config.json`（**含明文凭据，已被 .gitignore 排除**）
- 脚本: `scripts/guandata.py`
- 运行环境：Python 3.8+，依赖 `httpx`（`pip install httpx`）

## 配置说明

编辑 `config.json`：

```json
{
  "version": "6",
  "base_url": "https://your-guandata-instance.com:port",
  "domain": "your_domain",
  "login_id": "your_username",
  "password": "<BI_LOGIN_PASSWORD>",
  "default_pg_id": "your_default_page_id",
  "default_folder_id": "your_default_folder_id"
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `version` | ✅ | 观远BI版本：`"6"`（直接保存卡片）或 `"7"`（7.0+ draft/release 机制，自动发布） |
| `base_url` | ✅ | 观远BI服务器地址，如 `https://bi.company.com:8080` |
| `domain` | ✅ | 登录域，通常为 `guanbi`，具体咨询你们的BI管理员 |
| `login_id` / `password` | ✅ | 观远BI登录账号/密码 |
| `default_pg_id` | | 默认页面ID。不传时，`create-and-get` 需手动指定 `pg_id` |
| `default_folder_id` | | 默认文件夹ID。创建新页面时的存放位置 |

**如何获取 pg_id / folder_id**：在观远BI网页打开目标页面，URL 中的 `pgId=xxx` 即为页面ID；文件夹ID在「数据管理」→「目录」中查看。

## 命令骨架（最常用 10 条）

```bash
SCRIPT="python3 scripts/guandata.py"

# 探索
$SCRIPT list-datasets [--columns] [--refresh]    # 数据集（默认走缓存）
$SCRIPT get-columns <ds_id> [--with-calc]        # 字段（含计算字段）
$SCRIPT search-values <ds_id> --name "字段名" --search "关键词"   # 枚举值

# 建卡 / 取数
$SCRIPT create-and-get '<json>'   # 建卡 + 取数（一步到位）
$SCRIPT create-card '<json>'      # 仅建卡
$SCRIPT get-card-data <card_id>   # 取已存在卡片的数据

# 页面 / 卡片管理
$SCRIPT list-pages --manageable   # 有编辑权限的页面（日常用这个）
$SCRIPT delete-cards <pg_id> <card_id1> <card_id2> ...

# 诊断 / 认证
$SCRIPT status                    # 查看配置、token、缓存状态
$SCRIPT set-token <jwt> [--expires 7200]   # 手动设置 JWT（从浏览器复制时用）
```

> **完整命令清单**（含 `--task` 缓存隔离、`create-page` / `release-page` / `get-page-cards`、缓存清理、CSV 缓存使用规范）见 **[references/part-a-commands.md](references/part-a-commands.md)**。

## 写卡片前必读

> 🚦 **V2.1 路由提示**：如果用户的需求是"做销售仪表板 / 加 KPI 卡片 / 柱状图展示门店排名 / 新建区域筛选器联动"等**标准图表/Page 装配** —— **优先用 `guanvis-skill` 的 JS DSL**（`card_*.js` / `selector_*.js` / `page.js` → `pack/publish`），它的 30+ 图表类型覆盖、selector 联动、主题切换、批量发布都比手拼 JSON 顺手。本节的 `create-and-get` / `create-card` 保留作为 **fallback**（无 `guanvis-skill` 的环境）+ **payload 底层参考**（理解 `chart_type` / `metric` / `filters` 字段语义）。`guanvis-skill` 安装见 [references/internal-nexus-install.md](references/internal-nexus-install.md)，触发关键词见其 SKILL 描述。
>
> 反过来，**超出官方组件能力的视觉定制**（双 Y 轴叠加、ECharts 自定义渲染、图例改圆点、tooltip HTML 重写、固定卡片/overlay）走 **Part C**，`guanvis-skill` 不覆盖这些。

`create-and-get` / `create-card` 的 JSON 参数有 13 个字段，2 种格式（metric/filters/sorting/字段名/filterType），26 种 `chart_type`，6 种日期粒度。**写卡前先回到参考表**：

📖 **[references/part-a-cards.md](references/part-a-cards.md)** — 完整参数表 + 26 种图表类型 + metric/filters/sorting/字段名/filterType 全格式 + 6 个建卡示例（指标卡 / 柱状图 / 交叉表 / 多线图 / 组合图 / 气泡图）+ 完整工作流示例 + 自定义公式字段 `custom_fields`。

## guancli 补充：只读探索 + 表单 CRUD

**guandata.py vs guancli 分工**：
- **guandata.py** → 建卡、取数、删卡、发布页面（**写**操作）
- **guancli** → 搜索、探索、ETL/指标/任务/表单（**读**操作 + 表单 CRUD）

**何时用 guancli 替代 list-datasets / list-pages**：
- 库里数据集/页面很多 → `guancli ds search "关键词" --brief` 比全量拉取省 50%+ token
- 想看某 ETL 的 SQL/血缘/节点列表 → `guancli etl get <id> --brief`（`guandata.py` 没有此能力）
- 任务排查 → `guancli task running` / `guancli task get <task_id>`
- 表单 CRUD → `guancli form list/schema/query/add/update/delete`
- 调未封装的 BI API → `guancli fetch <METHOD> <path>`（万能兜底）

📖 **[references/guancli-commands.md](references/guancli-commands.md)** — 9 大类命令完整速查（ds / etl / metric / metric_attribution / task / page / card / form / fetch）+ 工具选择决策表。

## guancli V1.0.21 新能力（V2.0 / V2.1.4 同步）

@guandata/guancli@1.0.21 的命令面比本 skill V1.7 之前覆盖的更广。下列能力是 V2.0 → V2.1.4 陆续对齐的，写到这里只为"路由"，详细命令查 [references/guancli-commands.md](references/guancli-commands.md)：

- **`guancli chatbi`** — ChatBI Public API：`list-theme` / `query`（L1 主题问数）/ `insight`（L2 洞察分析）。
  ⚠️ 2026-05-12 在自有 BI 实例实测后端未部署 `/api/chat/public-api/theme/list-theme`，命令返回 `5001 No static resource`。如果你们 BI 实例升级了 ChatBI 模块就能直接用，命令面查 `guancli chatbi --help`。
- **`guancli app`** — SuperApp 模板：`create`（基于模板创建项目）/ `publish`（发布到平台）。
- **`guancli status`** — 顶层连接状态检查（区别于 `guancli auth status` —— 后者看 token，前者探接口连通）。
- **多环境管理** — 同时管多套 BI 环境（生产 / UAT / 镜像）：
  - `guancli auth login` 交互式登录，token 落盘 `~/Library/Application Support/guancli/config.json`，401 自动重登（无需再写明文密码到 config.json，下个版本计划把 `scripts/guandata.py` 也切到这套 token）
  - `guancli auth list` / `auth use <name>` / `auth modify` / `auth remove` / `auth whoami` / `auth detect-domain` —— 完整 CRUD
  - `guancli --profile <name>` 或 `export GUANCLI_PROFILE=<name>` 临时切

### V2.1.4 新对齐：1.0.20 / 1.0.21 增量（2026-05-15）

- **`guancli metric query` 泛化查询（1.0.20）** —— 一整套"高级指标分析"flag 下放到 CLI 端：`--compare yoy|mom|qoq|wow|dod` + `--compare-value value|rate|rawdata`、`--xtd ytd|qtd|mtd|wtd|dtd`、`--recent 7d|4w|3m`（可配 `--recent-base`）、`--percentage --percentage-dim`、`--rank-top N --rank-dim ... --rank-order asc|desc`、`--last`、兜底 `--adv-calc-json`。等价于在 BI 后台点开"高级计算"面板，**业务侧问"同比/年累计/最近 7 天/各城市占比/Top 10" 现在都能一行命令出数**，不必再去后台建一个新的派生指标实例。命令面与判断表见 [references/guancli-commands.md § metric query 泛化查询](references/guancli-commands.md#v214-起metric-query-泛化查询guancli-1020-新增)。
- **`guancli card preview -f excel`（1.0.20）** —— 新增 Excel 2003 XML 格式导出（重定向 `> out.xls` 直接 Excel 打开），同时把 `--limit` 默认值从 50 抬到 10000、`--sort-asc/desc` 取数下限固定 10000 行；服务端继续截断时命令会拒绝排序避免输出不可信顺序。**业务侧"把这张卡的数据导给我看 / 给我做个报表附件"现在直接 `card preview -f excel` 走通**，不需要再走 guandata.py 的取数 + pandas 落盘组合。
- **错误输出更干净（1.0.21）** —— 1.0.21 修了 CLI 运行时报错附带 `Usage:` / `Available Commands:` 大段帮助信息的 bug，`guancli ... 2>&1 | head -n 5` 这类 Part B 报错速查脚本现在能拿到干净错误，**Part B 报错速查表所有 head 样式提示都更可靠了**。

## 与官方 `guancli` skill 的共存

官方在 2026-05-11 通过 `guancli install-skill` 也分发了一个名为 `guancli` 的 skill，定位**只读分析 + ChatBI + 表单填报 CRUD**；写操作原计划分流到 5 个兄弟 skill（`guanetl-skill / guanvis-skill / guands-skill / guanexport-skill / guanadmin-skill`）。**2026-05-13 实测状态**：

- ✅ **`@guandata/guanvis-skill@0.1.13`** 已通过观远**内网 Nexus 私服** `https://app.mayidata.com/nexus/repository/guandata-web/` 分发（公网 npm 仍 404）。内网员工可走 [references/internal-nexus-install.md](references/internal-nexus-install.md) 的 tarball "四步法" 装上。能力：**30+ 标准图表 JS DSL 建卡 + Page 装配 + selector 联动 + 主题切换 + pack/publish**。
- ❌ `guanetl-skill / guands-skill / guanexport-skill / guanadmin-skill` —— 公网 + 内网均未确认发包。在它们落地之前，ETL 写入、数据集 CRUD、PNG/PDF 导出、SVC SQL 全部继续走 `guancli fetch` + 本 skill 的 Part B 实战手册。

**三件套角色互补**（V2.1 重新定义）：

| skill | 版本 | 主要角色 | 何时触发 |
|---|---|---|---|
| **官方 `guancli`** | 1.0.21 | 只读分析 + 指标泛化查询 + ChatBI L1/L2 + 表单 CRUD + card preview Excel 导出 | 查 ETL/dsId/page/card/血缘、ChatBI 主题问数、表单填报、`metric query` 同比/累计/Top N、`card preview -f excel` 报表导出 |
| **官方 `guanvis-skill`** | 0.1.13（内网 Nexus） | 标准建卡 + Page 装配 | 30+ 标准图表（柱/线/饼/KPI/表格/漏斗/地图/散点等）JS DSL、selector 联动、主题切换 |
| **`majia-guanyuan`**（本 skill） | 2.1.7 | 业务实战 + 高级自定义 + HTML 应用化看板 + **V7 发布流水线** + **餐饮 BI 公式实战库** | ETL 治理写入 / SmartETL 全链路重写 / **Part C HTML/CSS/JS 自定义图表注入与排障** / **Part C-12 HTML 应用化看板生成 + selector 联动 descriptor patch** / payload_json / ExecPlan / 60+ ETL 战例 + 10 类报错手册 / 业务体感与场景模板 / **V2.1.5：餐饮连锁 BI 公式实战库（60+ SQL 公式 + 6 ETL 工程范式 + 39 ETL 索引）** / **V2.1.6：V7 Page/Card 发布流水线 + 三态硬规则（guanvis-skill 一键 publish + CSV 三态 + Spark 中文别名 + ETL update dsId）** |

如果同时启用所有三个 skill，agent 在"分析 ETL 资源"这类只读场景下可能双触发 `guancli` 和 `majia-guanyuan`；想降低歧义建议保留本 skill（命令面更广，已含 guancli 的只读路由），把官方 `guancli` symlink 卸了：`rm ~/.claude/skills/guancli`（仅断 Claude Code 入口，不影响 `~/.agents/skills/guancli/` 真目录与其他 agent 加载）。**`guanvis-skill` 建议保留**——它和本 skill 的 Part A 互补不冲突，路由规则在「写卡片前必读」段已说明。

## 错误处理

| 状态码 | 处理 |
|--------|------|
| 500 | 终止，服务器问题 |
| 401 | 终止，登录失效 |
| 403 | 终止，无权限 |
| 404 | 终止，资源不存在 |

---

# 🅱️ Part B：ETL 治理与写入（V1.0）

> 基于 `@guandata/guancli@1.0.21` 的实证记录。所有 API 路径、payload 字段、报错信息、治理判断维度均来自真实跑通的请求。覆盖整库治理扫描 + 60+ 张 ETL 创建/重构/修复/删除的实战。
>
> ⚠️ 官方 guancli SKILL.md 把 BI 操作拆成 5 个兄弟 skill。**2026-05-13 实测状态**：`guanvis-skill@0.1.13` 已通过观远内网 Nexus 私服分发（公网 npm 仍 404，安装走 [references/internal-nexus-install.md](references/internal-nexus-install.md)），定位标准建卡 + Page 装配，与本 skill Part A 路由互补；其余 4 个（`guanetl-skill` / `guands-skill` / `guanexport-skill` / `guanadmin-skill`）公网 + 内网均未确认发包。**Part B 涉及的 ETL 写入、direct-save、payload_json、execute 全部继续走 `guancli fetch` + 本 skill 的实战手册**，等 `guanetl-skill` 落地后再考虑路由切换。

## B-〇. 推荐工作流（先治理再重建）

```text
1. 治理扫描     ← 批量抓全部 ETL 原始 JSON，分析依赖、循环、复杂度
2. 决策保留     ← 用 8 维 ETL + 4 维字段判断：保留 / 合并 / 降级 / 删除
3. 设计分层     ← 按 ODS/DIM/DWD/DWS/APP 重新分配
4. 字段审计     ← 双源（page + etl）扫字段使用度，确定砍字段范围
5. 新建目录     ← v2 目录与旧目录并行，不动旧链路
6. 写入 ETL     ← 三节点骨架 INPUT→SQL→OUTPUT，本地编译 payload
7. 预览节点     ← etl preview 先看 OUTPUT 节点能不能出数据
8. 执行落表     ← execute + task get 轮询 + 拿 result.error
9. 对账切流     ← 新旧并行验证，下游看板/ETL 逐张迁移
10. 清理旧链路  ← 先 DELETE data-source，再 DELETE etl（顺序不能反）
```

跳过治理直接动手 = 把同样混乱重做一遍。第 1–4 步是写 ETL 之前最值钱的活。

---

## B-1. API 全图（11 个已实测 endpoint）

```text
🔧 写入类（POST）
POST /api/directory                  ← 建目录（dirType=ETL 或 DATA_SET）
POST /api/etl/direct-save --stdin    ← 创建/更新 ETL（payload 有 dataFlowId 即更新）
POST /api/etl/execute                ← 触发执行 {"dataFlowId":"..."} → taskId

📖 读取类（GET）
GET  /api/etl/<id>                   ← ETL 完整定义（含 actions/sql/relativeFieldAlias）
GET  /api/directory/ETL/authorized-tree       ← ETL 目录树
GET  /api/directory/DATA_SET/authorized-tree  ← 数据集目录树
GET  /api/task/<taskId>              ← 任务状态 + 错误详情（关键修 bug 入口）

🗑️ 删除类（DELETE）
DELETE /api/data-source/<dsId>       ← 删数据集（必须先于 etl 删）
DELETE /api/etl/<id>                 ← 删 ETL（输出数据集还在 → 失败）

🔍 探测类（OPTIONS）
OPTIONS /api/<any-path>              ← 返回 Allow 头，反推支持的 method
```

### B-1.1 反推未知 endpoint 的方法

```bash
# 步骤 1：探 method 集合（最高效）
guancli fetch OPTIONS /api/<path>
# Allow: POST,GET,HEAD,DELETE,OPTIONS

# 步骤 2：盲发 POST，根据错误类型判断
# - "No static resource X"               → endpoint 不存在
# - "Request method 'X' is not supported" → endpoint 存在但方法不对
# - "InvalidJSON" / "missing field"       → endpoint 对，body 不对（开始迭代）
# - "ResourceId(...) ResourceNotExist"    → endpoint 模式错误

# 步骤 3：根据错误反推 schema
```

**血泪经验**：BI 内部 endpoint 命名不一致——`data-source`（带连字符）、`dataflow`（无连字符）、`etl`（无连字符）、`directory/ETL`（驼峰大写）混用。靠 OPTIONS 探测比盲发 POST 高效 10 倍。

---

## B-2. 治理扫描：判断 ETL/字段去留

### B-2.1 为什么扫描

观远 BI 用久了的常见症状：核心表互相循环引用、同份业务规则散落多张计算列、维表混入下游经营字段、大量已创建未运行的废弃 ETL、名实不符。**不扫一遍直接动手，重建出来还是一团乱麻。**

### B-2.2 扫描 3 步走

```bash
# Step 1：列出范围
guancli etl tree                                       # 全库
guancli etl search '' -d <PARENT_ETL_DIR_ID> --raw     # 按目录缩范围

# Step 2：批量抓原始定义（--raw 关键，不带就只输出阉割版）
mkdir -p raw
jq -r '.response.contents[].dataFlowId' etl-list.json | while read id; do
  guancli --raw etl get $id > raw/$id.json
done

# Step 3：本地脚本聚合分析
node analyze.mjs raw/ > analysis.json
```

### B-2.3 分析脚本要算的 10 个指标

| 指标 | 怎么算 |
|---|---|
| 输出数据集 | `actions[].type=="OUTPUT_DATASET"` 的 `outputDsName` |
| 上游 ETL 依赖 | `inputs[]` 里 `displayType=="DATAFLOW"` 的，反查归属哪个 ETL |
| 节点数 | `actions.length` |
| Join 数 | `actions[].type=="JOIN_DATA"` 的个数 |
| 计算列数 | `actions[].type=="CALCULATOR"` 的个数 |
| 透传聚合数 | `actions[].type=="GROUP_BY"` 的个数 |
| 长公式数 | CALCULATOR 里 `formulas[].expr.length > N` 的个数 |
| 输出行数/大小 | 输出 ds 的 `rowCount` / `storageSize` |
| 调度方式 | `cron`（`AFTER_REFRESH` / 具体 cron / 无） |
| 状态 | `status`（`FINISHED` / `CREATED` / `FAILED`） |

构建依赖图（节点 = ETL，边 = "本 ETL 输入了另一个 ETL 的输出表"），DFS 三色标记找循环组，计算 fanIn/fanOut。

### B-2.4 ETL 去留判断（8 维）

| 维度 | 信号 | 处置 |
|---|---|---|
| **循环依赖** | 出现在循环组里 | **必拆**：找共同字段抽到 DIM/DWD，让两下游都读它 |
| **状态异常** | `status=CREATED` 且无输出 / 0 次执行 | 删或重建为明确用途 |
| **本地无下游** | 没有任何其他本地 ETL 引用其输出 | 区分两类：① 给看板用 → 标 APP 层；② 没人用 → 删或归档 |
| **节点复杂度** | 节点 > 25、Join > 5、CALCULATOR > 3、长公式 > 0 | **拆**成多段：基础明细 / 规则映射 / 业务汇总 |
| **输出大小** | 单表 > 1GB 或 > 1000 万行 | 检查是否不必要物化；规则计算应集中 |
| **名实不符** | ETL 名跟输出表名差距大 | 改名或废弃 |
| **历史补数** | 名字含"补齐 / 历史 / 月末"等，调度异常 | 移到补数/归档目录，不挂主链 |
| **未调度** | `cron` 为空且不是被其他 ETL 触发 | 确认是否临时/手工 → 标记或删除 |

### B-2.5 字段去留判断（4 维）

| 维度 | 怎么判断 | 处置 |
|---|---|---|
| **下游 ETL 引用** | 在所有下游 ETL 的 SQL/CALCULATOR/SELECT_COLUMNS 里 grep 字段名 | 0 引用 → 候选删 |
| **看板（page）引用** | 看板/卡片是否用了这个字段 | 有 → 不能删 |
| **业务口径** | 字段名是否含业务规则（"是否会员"、"是否新客"） | 这类是规则字段，集中维护到专门的规则映射 ETL |
| **冗余/派生** | 能否从其他字段推导（开业天数 vs 开业日期） | 派生字段尽量在下游算，不在维表物化 |

详细双源审计方法见 **B-10**。

### B-2.6 ODS/DIM/DWD/DWS/APP 分层

| 层 | 放什么 | 关键约束 |
|---|---|---|
| **ODS** | 原始外部表、DB_EXTRACT、手工源表 | 只做轻清洗，不承载业务口径 |
| **DIM** | 门店、会员、日期、支付通道、顾客标识映射 | **稳定、少依赖、可复用，禁止依赖 DWS/APP** |
| **DWD** | 订单明细、券明细、好友明细、评价明细 | 固定主键和时间粒度 |
| **DWS** | 复购、RFM、拉新、蓄水、门店日报 | 从 DWD/DIM 读，**禁止反向被 DIM 引用** |
| **APP** | 看板专用宽表 | **只服务页面，不再作为基础上游** |

调度按层推进 ODS → DIM → DWD → DWS → APP。

**核心反模式**：维表（DIM）混入了下游经营结果字段——比如门店维表里塞了"近 90 天订单数"。这是循环依赖最常见的根源。

### B-2.7 输出物建议

- `analysis.json`：机器可读分析结果（summaries / cycleGroups / highComplexity / nodeTypes）
- `governance-report.md`：人类可读治理报告（核心结论 + 循环组 + 合并主题域 + 清理对象 + 目标架构 + 实施路线）
- `migration-plan.json`：每个旧 ETL → v2 的对应表（score / targetName / status）

---

## B-3. 第一步：新建目录

### B-3.1 不要试这些路径（全部 5001 失败）

```text
POST /api/directory/create
POST /api/directory/ETL/create
POST /api/directory/ETL/add
POST /api/directory/add
GET  /api/directory                  ← Method 'GET' is not supported
GET  /api/etl/tree                   ← ResourceId(tree)/ResourceKind(DataFlow) ResourceNotExist
POST /api/etl/dir                    ← Method 'POST' is not supported
POST /api/resource-atlas/dir         ← 'resourceTypeName missing'
```

合法 `dirType` 只有 **`ETL`** 和 **`DATA_SET`**（不要写 `DATA_PROCESS_ETL` `SMART_ETL` `DATAFLOW` `DATA_FLOW`）。

### B-3.2 正确做法

ETL 树和数据集树是**两棵独立的树**：

```bash
guancli fetch GET /api/directory/ETL/authorized-tree
guancli fetch GET /api/directory/DATA_SET/authorized-tree
```

**分别建**（同名也得建两次）：

```bash
# ETL 目录
guancli fetch POST /api/directory \
  '{"name":"warehouse_v2","parentDirId":"<parent_etl_dir_id>","dirType":"ETL"}'

# 数据集目录
guancli fetch POST /api/directory \
  '{"name":"warehouse_v2","parentDirId":"<parent_ds_dir_id>","dirType":"DATA_SET"}'
```

记住返回的两个 dirId，写 ETL payload 时**两个都要用**：
- ETL 目录 id → ETL 自身的顶层 `parentDirId`
- 数据集目录 id → OUTPUT_DATASET 节点的 `parentDirId` + `dataSource.parentDirId`

---

## B-4. 第二步：构造 ETL payload（速查）

最小骨架 = 3 节点：

```text
INPUT_DATASET → SQL_SCRIPT → OUTPUT_DATASET
```

**最关键的字段坑**（详细见 references）：
- ⚠️ SQL 节点字段名是 **`sql`，不是 `sqlScript`**。写错时 direct-save 不报错，但 SQL 不生效（最隐蔽 bug）。
- ⚠️ SQL 里 `input1/input2/...` 是**位置式索引**对应 `sources[]`，删除 INPUT 节点会让索引前移，**改 input 节点必须同时改 SQL**。
- ⚠️ INPUT_DATASET 的 `relativeFieldAlias` 决定 SQL 里能引用什么字段名，必须读了再写 SQL。
- ⚠️ OUTPUT_DATASET 的 `parentDirId` 是**数据集目录 id**，不是 ETL 目录 id（错填→"保存路径无效"）。

📖 **[references/part-b-payload.md](references/part-b-payload.md)** — 完整 payload 模板（含 dataSource.dirPath）+ 三种节点的字段速查表 + 9 种已知节点类型 + dataFlowId 控制 create vs update + **B-8 复用模板：从扫描到落表的完整 4 阶段脚本**（治理扫描 → 建目录 → 写入执行 → 删除旧链）。

---

## B-5. 第三步：执行 + 拿真实错误

### B-5.1 触发执行（status 字段误导）

```bash
guancli fetch POST /api/etl/execute '{"dataFlowId":"<etl_id>"}'
# => {"taskId":"<task_uuid>","status":"FINISHED"}
```

⚠️ **status 字段误导最坑**：返回的 `status:"FINISHED"` 是**任务触发**结果，不是 ETL 执行结果。

### B-5.2 查任务详情（修 bug 必经路径）

```bash
guancli fetch GET /api/task/<taskId>
# => {"response":{"taskId":"...","status":"FAILED","result":{"error":"..."},"messages":""}}
```

`response.result.error` 才是 BI 引擎给的真实错误（SQL 报错、字段找不到等）。

### B-5.3 错误定位三步走

```bash
# Step 1：触发 execute 拿 taskId
taskId=$(guancli fetch POST /api/etl/execute "{\"dataFlowId\":\"$DFID\"}" \
  | jq -r '.response.taskId')

# Step 2：等几秒再查 task error
sleep 4
guancli fetch GET "/api/task/$taskId" | jq '.response.result.error'

# Step 3：根据 error 类型对照 references/part-b-errors.md 修复手册
```

### B-5.4 异步轮询写法

```bash
TASK_ID="<task_id>"
for i in $(seq 1 30); do
  st=$(guancli task get $TASK_ID --raw | jq -r '.response.status')
  echo "[$i] $st"
  [ "$st" = "FINISHED" ] || [ "$st" = "FAILED" ] && break
  sleep 10
done
```

复杂表给 5 分钟（30×10s）一般够。

---

## B-6. 第四步：校验工具集

```bash
# 1. ETL 视角
guancli etl search <ETL_NAME> -d <ETL_DIR_ID> --raw \
  | jq '.response.contents[0] | {dataFlowId,name,status,lastExecution,outputs}'

# 2. 节点级预览（不用 execute 也能看任意节点输出 — 修 bug 利器）
guancli etl preview <DFID> <NODE_ID> --limit 5 --timeout 120

# 3. 数据集视角
guancli ds search <OUTPUT_DS_NAME> --raw

# 4. 实际数据预览
guancli ds preview <OUTPUT_DSID> --limit 10

# 5. 行列数对账
guancli ds get <OUTPUT_DSID> --brief
```

⚠️ 保存后 OUTPUT 节点 ID 会变成 `id_<ts>_<n>_out`，preview 时用新 id：

```bash
guancli etl get <DFID> --raw \
  | jq -r '.data.actions[] | select(.type=="OUTPUT_DATASET") | .id'
```

---

## B-7. 第五步：删除拓扑

### ⛔ B-7.0 删除前的硬性安全闸（V1.3.1 新增）

**Agent 在执行任何 `DELETE /api/data-source/` 或 `DELETE /api/etl/` 前必须满足以下全部条件，否则拒绝执行：**

1. **用户已逐项明确确认**：列出本次将删除的所有 dsId / etlId（含 ETL 名 + 输出表名 + 路径），用户回复"确认删除"或等价明确指令。**模糊回复（如"嗯"、"可以"、"清理一下"）不算确认。**
2. **下游引用已切流**：通过 `guancli ds get <dsId> --assoc` 或 B-10 双源审计验证目标 ds 的下游 ETL 与看板（page）已切到 v2，无任何活跃引用。
3. **新链路对账通过**：v2 对应 ETL `status:FINISHED`，行数与 v1 差异 <1%，关键字段一致（参考 B-7.3 checklist）。
4. **批量删除分批确认**：单次删除 ≤ 5 张表；超过 5 张必须分批，每批单独走步骤 1。

**Agent 默认行为**：在 ETL 治理 / 重写 / 字段裁剪等任务里，**永远不要主动建议删除**。把待删清单作为 `governance-report.md` / `migration-status.md` 的一节产出给用户审阅，由用户主动指令"删 X / 删这一批"才执行。**新旧并行是默认终态，不是过渡态**——除非用户明确要求收敛。

> 这条闸跟 B-13 红线、B-17.10 完成标准里的"对账确认后再处理旧表"一脉相承。**误删一张被看板用着的 ds，恢复成本高过保留旧链一年。**

### B-7.1 关键约束：先 ds 后 etl

```bash
guancli fetch DELETE /api/etl/<etl_id>
# => {"error":{"status":2002,"message":"输出数据集已存在"}}  ← 失败！
```

正确顺序：

```bash
# Step 1：先删数据集
guancli fetch DELETE /api/data-source/<dsId>

# Step 2：再删 ETL
guancli fetch DELETE /api/etl/<etlId>
```

### B-7.2 数据集 endpoint 反推血泪史

```text
DELETE /api/dataset/<id>     ← No static resource dataset/...
DELETE /api/datasource/<id>  ← No static resource datasource/...
DELETE /api/ds/<id>          ← No static resource ds/...
DELETE /api/dataflow/<id>    ← No static resource dataflow/...
✅ 正确：
DELETE /api/data-source/<id>
```

### B-7.3 删除前 checklist

- [ ] v3 对应 ETL Status = FINISHED
- [ ] v3 输出数据集行数 vs v2 行数（差异 < 1%）
- [ ] v3 输出字段集 = v2 字段集 - 设计砍掉的
- [ ] 看板（page）依赖 v2 数据集的，已先切到 v3
- [ ] 下游 ETL 依赖 v2 输出的，已先切到 v3

---

## B-9. 报错修复手册（10 类真坑 · 速查）

每条只列**触发现象 + 一句根因 + 一句修复方向**；完整修复方案 + SQL 示例 + 升级版坑见 **[references/part-b-errors.md](references/part-b-errors.md)**。

| 坑号 | 触发现象 | 根因 / 修复方向 |
|---|---|---|
| **1** | `请输入ETL名称` / `保存路径无效` | 顶层 `parentDirId` 缺失或填错 → 必须是 `dirType=ETL` 那棵树的 id |
| **2** | 保存成功但 execute 数据为空 | 上游 `inputDsId` 只有读权限没运行权限 → 换有权限的输入或写自包含 ETL |
| **3** | 列名带隐藏 `\n` 找不到字段 | SQL 里要 `` `带换行的原字段名` AS `干净别名` ``；升级版坑：fieldAlias 与 SQL 中换行+空格不一致 |
| **4** | `WHERE field <> NULL` 输出 0 行 | SQL 标准里 `<> NULL` 永远是 unknown → 必须 `IS NOT NULL` / `IS NULL` |
| **5** | `cannot resolve column` | 字段引用与 INPUT_DATASET 的 `relativeFieldAlias` 错位 → 编译时按节点级别名替换 |
| **6** | `Syntax error at or near ';'` | CTE 内 trailing `;` + 中文注释 → 用 regex 去除 `FROM n_id_xxx;` 后的 `;` 与注释 |
| **7** | `AMBIGUOUS_REFERENCE` | FROM/JOIN 同表别名同名 → 改 FROM 别名为 s2，对齐 ON 子句 |
| **8** | `s2.xxx 找不到` | FROM 表错位（自连而非 JOIN 不同表） → 修正 JOIN 目标表 |
| **9** | `NUM_COLUMNS_MISMATCH` | UNION 列数不一致（老引擎自动补 NULL，新引擎严格化） → 手工对齐 SELECT，缺的用 `NULL AS xxx` |
| **10** | 日期比较恒为 false | `WHERE order_date < 'today_field'` 字符串字面量 → 改 `date_sub(current_date(), 1)` |

---

## B-10. 字段使用度审计（双源扫描）

### B-10.1 方法论

字段裁剪不能只看看板（page）—— 下游 ETL 也消费字段。**双源 0 引用**才能安全裁。

```bash
# 1. 拉数据集所有下游
guancli ds get <dsId> --assoc
# 输出 N 个下游：M 个 ETL + K 个 PAGE

# 2. 批量 page get + etl get 落本地
for id in <ids>; do
  guancli page get $id > pages/$id.txt
  guancli etl get $id > etls/$id.txt
done

# 3. 对每个字段做 grep 双源统计
for fld in <field_list>; do
  page_cnt=$(grep -c "$fld" pages/*.txt)
  etl_cnt=$(grep -c "$fld" etls/*.txt)
  if [ "$page_cnt" = "0" ] && [ "$etl_cnt" = "0" ]; then
    echo "🟥 $fld → 真 0 引用，可裁"
  fi
done
```

### B-10.2 实测对照（必看）

```text
某千万级订单明细表：43 字段、5GB
全量扫描：29 page + 14 etl
仅看板抽样：17 个 0 引用候选
双源全扫描：仅 2 个真 0 引用
误删任何一个 → 下游 ETL 跑挂
```

**只看看板会高估 8 倍可裁字段，必须 page+etl 双源。**

---

## B-11. v2 → v3 批量改造 SDK（速查）

`v3_sdk.mjs` 三个核心 API：

```js
transformV2ToV3({ v2PayloadFile, v3Name, removeInputs, newSql, inputMap, description })
pushAndExecute(v3Name, payloadPath)   // direct-save → execute
checkStatus(v3Name)                    // guancli etl search → parse Status
```

`transformV2ToV3` 内部 7 步关键陷阱：**SQL 字段名是 `sql` 不是 `sqlScript`**（最大坑） · 重排节点 ID 时 sources 数组要同步 · 删除 INPUT 后 input 索引重排 · meta 字段要同步更新。

📖 **[references/part-b-sdk.md](references/part-b-sdk.md)** — 完整 7 步实现 + 时间窗口缩减实战（v2 近 3 月 → v3 昨日窗口的 regex 替换样板）。

---

## B-12. 批量迁移工程经验（30+ 表实战）

1. **先治理后写入**：跳过治理直接写 = 把混乱重做一遍。
2. **payload 全部本地生成**：写编译器把每个旧 ETL 的 meta 编译成三段式 payload，存 `payloads/<name>.json`。
3. **分批保存**：一次 5–10 张 direct-save，避免单次失败影响整批。
4. **预览先于执行**：保存完先 `etl preview` 看 OUTPUT 节点能不能出数据；能出来再 execute。
5. **节点 ID 重映射**：保存后 OUTPUT 节点 ID 变成 `id_<ts>_<n>_out`，从 `etl get` 拿新 id。
6. **失败修复就地更新**：改 payload 加 `dataFlowId` 再 POST，不要删了重建。
7. **复用旧 payload**：v2 payload 作为模板，改名+改 SQL+改输入。30 个 ETL 中 22 个用这种方式。
8. **失败定位用 task error**：每个 task 详情里 `result.error` 是真实失败原因，必看。
9. **批量任务异步监控**：`until` 循环 + `etl search | grep -c PROCESSING` 比单 task 轮询效率高。
10. **新旧并行**：v2 链路与 v1 并行，对账无误后再下线 v1。

> 💡 **30+ 张表跨多日的工程必须走 ExecPlan**：不要靠零散 todo + 群消息 + 临时 markdown 来追踪进度。直接走 **B-17.11**（在 [references/part-b17-fullchain-rewrite.md](references/part-b17-fullchain-rewrite.md)）的 ExecPlan 工作法——四个活文档章节（Progress / Surprises & Discoveries / Decision Log / Outcomes & Retrospective）能把治理判断、循环依赖拆法、字段隐藏换行这类"踩坑—修复"轨迹完整落到一份自包含文档里，下一个接手的人不用问任何上下文就能继续。

---

## B-13. ETL 治理与写入红线

- ❌ 不要试 `/api/directory/create` 这类拼凑路径，全部 5001。
- ❌ 不要给 `dirType` 写 `DATA_PROCESS_ETL` `SMART_ETL` `DATAFLOW`，只接受 `ETL` 和 `DATA_SET`。
- ❌ 不要把 `OUTPUT_DATASET.parentDirId` 填成 ETL 目录 id —— 报"保存路径无效"。
- ❌ **不要把 SQL 字段名写成 `sqlScript`**，正确是 `sql`（写错时 direct-save 不报错但 SQL 不生效）。
- ❌ 不要在 SQL 里写 `<> NULL` 或 `= NULL`，用 `IS NOT NULL` / `IS NULL`。
- ❌ 不要假设 INPUT_DATASET 字段名干净 —— 先看 `relativeFieldAlias` 和实际预览。
- ❌ 不要 execute 完就走人 —— `status:FINISHED` 是任务触发结果，不是 ETL 执行结果。要 `GET /api/task/<id>` 拿 `result.error`。
- ❌ 不要假设节点 ID 重排不影响 SQL —— 删除 INPUT_DATASET 后 input 位置式索引会变。
- ❌ **未经用户逐项明确确认，绝不执行任何 DELETE 操作**（含 `/api/data-source/` 和 `/api/etl/`）—— Agent 默认行为是把待删清单产出给用户审阅，由用户明确指令才执行。详见 **B-7.0 删除前的硬性安全闸**。模糊回复（"嗯"、"可以"、"清理一下"）不算确认。
- ❌ 不要为了"清理"删旧 ETL —— 并行做新链路、对账确认后再处理旧表。新旧并行是默认终态，不是过渡态。
- ❌ 不要直接 `DELETE /api/etl/<id>` —— 必须先 `DELETE /api/data-source/<dsId>` 再删 ETL。
- ❌ 不要试 `DELETE /api/dataset/`、`/datasource/`、`/ds/` —— 正确是 `/api/data-source/`（带连字符）。
- ❌ 不要给 INPUT_DATASET 用没有运行权限的 dsId —— 保存能过，执行会拿不到数据。
- ❌ 不要复用 OUTPUT 节点 id 作为 preview 参数 —— 保存后会变成 `id_<ts>_<n>_out`。
- ❌ 不要跳过治理扫描直接重建 —— 不识别循环依赖和重复主题域，重建出来还是一团乱麻。
- ❌ 不要把"是不是被引用"等同于"该不该保留" —— 看板 APP 表常常没下游 ETL，要单独看看板侧。
- ❌ 不要让 DIM 维表依赖 DWS/APP 层 —— 这是循环依赖最常见的根源。
- ❌ 不要只看看板做字段裁剪 —— 实测仅看板会高估 8 倍可裁字段，必须 page+etl 双源。
- ❌ 不要假设老 ETL SQL 写法在新引擎也能跑 —— 5 类历史 bug（trailing `;` / UNION 列差 / 字段名换行+空格 / self-join 别名同名 / 字符串字面量与 DATE 比较）会暴露。
- ❌ 不要忘记 OPTIONS 探测 —— 找未知 endpoint 时比盲发 POST 高效 10 倍。

---

## B-14. ETL 写入侧 API 速查

| 操作 | 方法 | 路径 / 命令 |
|---|---|---|
| 探测 method | OPTIONS | `/api/<any-path>` |
| ETL 目录树 | GET | `/api/directory/ETL/authorized-tree` |
| 数据集目录树 | GET | `/api/directory/DATA_SET/authorized-tree` |
| 建目录 | POST | `/api/directory` body: `{name, parentDirId, dirType}` |
| 抓 ETL 详情 | – | `guancli --raw etl get <id>` |
| 写入 ETL（创建/更新） | POST | `/api/etl/direct-save --stdin` |
| 触发执行 | POST | `/api/etl/execute` body: `{dataFlowId}` |
| 查任务真错误 | GET | `/api/task/<taskId>` → `.response.result.error` |
| 节点级预览 | – | `guancli etl preview <DFID> <node_id>` |
| 删数据集（先） | DELETE | `/api/data-source/<dsId>` |
| 删 ETL（后） | DELETE | `/api/etl/<id>` |

---

## B-15. 实战 ID 速查（模板）

> 跨多日的大型重构（B-17 / 30+ 表）建议在仓库根维护一份本地 ID 速查表，避免每次都用 `guancli` 翻树。下面是模板，把 `<...>` 占位符替换成你自己 BI 实例里的真实 ID。**不要把这份表 commit 到公开仓库。**

| 名称 | ID | 说明 |
|---|---|---|
| 旧 ETL 父目录 | `<v1_etl_dir_id>` | v1 ETL 目录 |
| 旧数据集父目录 | `<v1_ds_dir_id>` | v1 数据集目录 |
| **v2 ETL 目录** | `<v2_etl_dir_id>` | 新建 ETL 落这里 |
| **v2 数据集目录** | `<v2_ds_dir_id>` | OUTPUT_DATASET 落这里 |
| 数据集树根目录 | `<ds_root_id>` | dirPath 第一层 |
| ETL 树根目录 | `<etl_root_id>` | – |
| PoC ETL | `<poc_etl_id>` | 第一个跑通的最小 ETL |
| PoC 输出数据集 | `<poc_output_ds_id>` | 同上输出 |
| PoC 输入数据集 | `<poc_input_ds_id>` | 小表，权限可运行 |

如果上面 ID 失效（被删/改名），用以下命令重新拿：

```bash
guancli fetch GET /api/directory/ETL/authorized-tree | jq '.response | .. | objects | select(.name=="<你的 v2 目录名>")'
guancli fetch GET /api/directory/DATA_SET/authorized-tree | jq '.response | .. | objects | select(.name=="<你的 v2 目录名>")'
```

---

## B-17. 全链路重写方法论（CTO 张进）

> 这套是观远 CTO 张进的 SmartETL 完整改写经验。它跟 B-2 治理扫描互补：B-2 解决"有哪些 ETL 该治理"，B-17 解决"具体重写一条链路时怎么做才不留尾巴"。
>
> **核心区别**：B-17 强调**全链路追到原始源**，不接受只重写最终 ADS。如果用户说"把这条链路重新做一遍" / "替换数据源" / "做副本页验收"，必走 B-17。

📖 **[references/part-b17-fullchain-rewrite.md](references/part-b17-fullchain-rewrite.md)** — 完整方法论 11 节：何时用 B-17 / 4 件交付 / 8 条硬规则 / 5 步标准工作流 / 三层验收（数据集/副本页/卡片级）/ 差异追踪 5 步法 / 空快照处理标准 / 标准交付物清单 / 6 类专属常见坑 / 完成标准 6 项 / **B-17.11 用 ExecPlan 管理重写工程**（含 SmartETL 改写专用 ExecPlan 骨架，拿去直接填空）。

**最简口诀**（10 秒决定要不要进 B-17）：
- 只新建 1 个 SQL 节点数据集 → 走 B-3 ~ B-9，不进 B-17
- 涉及"页面副本验收"或"卡片级数值对账"或"全链路追到原始源" → 必进 B-17
- 30+ 表 / 跨多日 / 循环依赖拆解 → 进 B-17 + 走 B-17.11 ExecPlan

---

# 🆎 Part C：自定义图表开发与排障（V1.1 新增）

> **并行参考（V2.0 标注）**：观远 maintainer wubaoqi 在 2026-04-29 发布了 `@wubaoqi/guan-chart-kit`（React + ECharts 组件库，专为观远 BI 设计）和 `@wubaoqi/guan-chart-kit-usage-skill`（agent-skill，教 SuperApp 接 chart-kit）。两条路线区别：
> - **chart-kit 路线**（wubaoqi）：从零搭新看板，走**组件接入** + npm 依赖管理，适合标准化复用
> - **本 Part C 路线**：在既有卡片上做 HTML/CSS/JS 注入 hack，绕过组件直接改 DOM/data，适合改造既有页面、临时 overlay、固定卡片
>
> 两者互补，按"是新搭还是改造"分流。

> 来源：观远 CTO 张进的自定义图表注入实战经验。涵盖 HTML/CSS/JS 注入、runtime 取数、固定卡片、遮罩层、z-index/stacking context、路由清理，以及任何**必须在真实观远页面里做浏览器验证**的前端问题。

## C-〇. 何时用 Part C

任务涉及观远 BI **自定义图表**的：
- 前端代码（HTML/CSS/JS）
- 运行时取数（`renderChart` 的 `data` 参数解析）
- 页面级 DOM 操作（固定卡片、overlay、mask）
- 浏览器层级问题（z-index、stacking context、pointer-events）
- 路由切换清理、复制页 card id 重定位
- 懒加载导致脚本不执行
- 必须在真实页面验证的问题

不用 Part C 的情况：只是在观远 UI 里点几下做卡片配置，不写代码 → 走 Part A。

## C-1. 快速开始原则（6 条）

1. **要注入 HTML/CSS/JS** → 用「自定义图表」，不用「自定义图表 Lite」
2. **先在真实观远页面复现问题，再改代码**
3. **先确认 live 页实际运行的是哪份脚本**，再判断问题
4. **脚本开始漂移或多次局部修补失效时，优先给完整 JS**，不要继续发零碎 diff
5. **每次结构性修改后回浏览器重新验证**
6. **遇到取数问题，先看 `GDPlugin().init(renderChart)` 的 runtime 入参**，不要先假设它等于 `/api/card/.../data` 的 HTTP 包裹层

## C-2. runtime 契约（必须知道）

观远当前的 runtime 回调签名是：

```javascript
function renderChart(data, clickFunc, config, helpers) {}
```

⚠️ **常见误解**：
- ❌ 把第一个参数 `data` 当 DOM 根节点 —— 错。要自己从 `document.querySelector(...)` 或 `document.body` 获取 DOM。
- ✅ `helpers` 常见为 `{ refreshData, clickFunc }`

`data` 形态多变，常见 5 种：

```javascript
// 形态 1（最常见）
[
  [
    { name: "payload_json", data: ["{...}"] },
    { name: "report_date", data: ["2026-03-18"] }
  ]
]

// 形态 2
[{ name, data }, ...]

// 形态 3
{ chartMain: { columns: [...] } }

// 形态 4
{ response: { viewData: [...] } }

// 形态 5
[{ payload_json, report_date }]
```

**结论**：优先围绕 runtime `data` 写解析逻辑。`/api/card/.../data` 只用于核对证据，不要把它当 callback 结构直接照搬。

## C-3. payload_json 取数排障（速查）

📖 **[references/part-c-payload-json.md](references/part-c-payload-json.md)** — 三种"拿不到 payload"的细分 / 最快判断方式 / `JSON.parse` 硬规则 / 截断错误（`Unterminated string` / `Unexpected end of JSON input`）的判断 / 推荐方案：拆列而非整包 JSON。

**最简结论**：JSON.parse 失败且报截断错时，**优先判断为数据链路把长字符串截断了**，不要继续堆兼容解析逻辑。改数据方案——把整份报告拆成多列（`report_date` / `key_insights_md` / 各 section 列）传给前端，比 runtime 再 `JSON.parse(payload_json)` 稳得多。

## C-4. 固定卡片 / overlay 场景

### C-4.1 保守做法

- ✅ **只移动目标卡片内容**，不要把整页都抽进 overlay
- ✅ overlay 和 mask **挂到当前页面根节点**，**不要挂到 `body`**
  - 挂到 body 的后果：切页后残留 / 与原生浮层打架 / 跟右侧锚点导航层级冲突
- ✅ overlay 的 z-index 要够用，但**不能压过观远原生导航、浮层、工具条**
- ✅ 卡片尺寸变化时，主动派发 `resize`（立即一次 + 延迟几次）让图表重排

### C-4.2 z-index 基线（已验证）

```text
overlay 容器     约 8
mask            约 1
固定卡项        约 20，按需要递减
```

目标：**高于滚动内容，低于观远原生导航、菜单、工具层。**

### C-4.3 让加载器看得到注入卡，但用户不必看到

- 观远自定义图表 iframe **是懒加载的**
- 注入卡放在首屏以下 → 初次进页时脚本可能根本不执行

**可靠做法**：
1. 把注入卡**放在首屏**
2. 查看态视觉隐藏
3. **编辑态恢复可见**（让用户能找到并编辑）

## C-5. 页面生命周期管理

### C-5.1 必须主动销毁注入物的场景

- URL 不再匹配目标 page id
- 进入编辑态
- 切到 `pageRenderType=phoneView`
- 客户端路由离开当前页

**只在目标桌面查看态重建。**

### C-5.2 复制页面后 card id 全变

- 观远复制页面会生成新的 card id
- 继续使用原页面硬编码 id 通常**不会显式报错，只会悄悄失效**
- 复制页一定要重新确认 card id

### C-5.3 MutationObserver 死循环陷阱

- 监听 `body subtree` 后又在回调里改样式 → 容易反复触发，卡死页面
- ✅ 更稳的做法：低频轮询 + 精准 rect 比较

## C-6. 浏览器排障清单

### C-6.1 改代码前先看 live runtime

检查：
- 当前 URL 和 page id
- `window` 上是否已有旧版注入 key
- `__gd_overlay__` 和 `__gd_overlay_mask__` 是否存在
- 页面里是否留有历史实验节点

### C-6.2 找到真正可点击的 DOM

不要把"看到的文本节点"误当成真正交互节点。对右侧锚点导航，真正有用的目标往往是：
- 打开按钮图标
- tab 按钮
- pin 图标

### C-6.3 用 `elementFromPoint` 查层级问题

控件可见但点不动时，查控件中心点命中的真实元素：
- 命中 fixed card 或 overlay 子节点 → 层级问题
- 命中正确控件但还不工作 → 之前点错节点 / 某个祖先禁用了 pointer events

### C-6.4 最终用真实浏览器点击验收

不要只靠 `page.evaluate(... click())`。要用真实浏览器点击，确认：
- tab 切换是否真的生效
- 页面滚动位置是否真的变化
- pin 状态是否真的切换

## C-7. 保留原生浮动 UI

- ❌ 没必要时，**不要重绘或克隆**观远原生浮动控件
- ✅ 优先修 stacking context、pointer-events、opacity，而不是复制一套控件

原生控件不可点时，按这个顺序排查：
1. overlay 是否盖住它
2. mask 是否拦截事件
3. 祖先节点是否被设成 `pointer-events: none`
4. 原控件是否被历史实验隐藏

## C-8. 交付规则

- ✅ 用户要手工粘贴时，**默认给完整 JS**，不给局部片段
- ✅ 如有需要，同时明确给出 HTML / CSS
- ✅ 脚本不稳定时，完整替换优于局部修改
- ✅ 页面已经完全坏掉时，先给最小恢复版救回来：

```javascript
function renderChart() {}
new GDPlugin().init(renderChart);
```

提醒用户执行：**保存 → 发布 → 强刷查看页**。

## C-9. 最终验收清单

最终一定要在真实页面验证：
- [x] 页面加载
- [x] 查询 / 筛选切换
- [x] 滚动
- [x] 左侧栏展开收起
- [x] 路由切页
- [x] 编辑态进出
- [x] 桌面 / 手机态切换
- [x] 原生浮动控件是否仍可见、可点

## C-11. 深度参考资料

遇到复杂的固定卡片 / overlay / 锚点导航问题时，读：

- [references/custom-chart-playbook.md](references/custom-chart-playbook.md) — 张进的完整自定义图表排障手册原文（含固定层与真实布局错位修正、右侧原生导航失效详细处理、elementFromPoint 实战、MutationObserver 死循环深入分析）
- [references/etl-rewrite-original.md](references/etl-rewrite-original.md) — 张进的 SmartETL 改写经验原文（B-17 章节就是基于它整合的，这里是未删减版）

## C-12. HTML 应用化看板生成（V2.1.1 新增）

> **触发**：用户说"更高级 / 更复杂 / 更好 / 应用 / 自定义模块 / 不要限制在标准看板 / 最完美版本 / HTML 看板"——立刻切到这条路线，**不要**按 Part A 的标准 KPI/折线/柱状图套路交付。
>
> **架构**：原生 Page + 原生 selector + HTML SDK 可见层（`createCustomChart().setSubType(CustomChartSubType.SDK).loadContent(...)`）+ DATA_GRID dataView 数据层。后端负责权限/刷新/聚合/筛选，前端负责叙事/布局/SVG-HTML 可视化。
>
> **不能跳的两条坑**（2026-05-14 `app.guandata.com` 上 `<demo-domain>` 实例实测）：
> 1. `guanvis-skill` DSL 的 `.linkToAll()` **不会** 把 selector 联到 custom chart 内部 dataView——必须走 **资源包级 descriptor patch**（不要去调 `/api/card/.../edit/session`，会返回 `60004 此操作只能在草稿页面执行`）。
> 2. `guancli card preview` 的命令面 V2.1 起 **不再有 `--pg-id`**，老写法 `card data <id> --pg-id <pg_id>` 已废弃；同时不同子命令返回根字段不同（`page get → .data`、`card get → .response`），jq 统一写 `.data // .response // .`。

📖 **[references/part-c-html-dashboard.md](references/part-c-html-dashboard.md)** — 完整方法论 15 节：何时切到 HTML 应用看板 / 总体架构 / SDK vs ECHARTS_LITE 决策 / dataView contract / 共享 runtime API / 24 字符 ID 校验 / selector → custom chart dataView 联动补丁 / 12 步 pack-patch-upload 工作流 / 字段粒度后缀兼容（`月份` / `月份 (月)` / `年月`）/ guancli V2.1 命令面（含 `.data // .response` 兼容）/ 四层验收清单 / 12 类常见错误表 / 模板包索引。

🧰 **模板包**：[`templates/html-dashboard/`](templates/html-dashboard/) — `charts/html_common.js` (GDHTML runtime) + `html_base.css` + 2 个起手模块（executive / trend）+ `scripts/patch_selector_linkage.js`（CLI 参数化，弥补 `linkToAll` 联不到 custom chart dataView 的盲区）。

---

# 🆎 Part D：V7 Page/Card 发布流水线 + 三态硬规则（V2.1.6 新增）

> **触发**：用户说"v7 BI 实例上端到端搭多个 HTML 应用看板"，或卡在以下任一报错——立刻进 Part D，**不要** 在 Part A/C 的标准链路上继续挣扎，没用：
> - `POST /api/page` + `POST /api/card` 返回 `60004 此操作只能在草稿页面执行`
> - PUT 草稿页 cdId 后，published page 拿到的 cdId 跟 draft 的不映射，整页拼不出来
> - CSV 散客订单 `会员ID IS NOT NULL` 算出 "会员销售占比 = 100%" 假指标
> - Spark `WITH 订单汇总 AS (...)` 报 `PARSE_SYNTAX_ERROR Syntax error at or near '订'`
> - ETL update 报 `1012 输出数据集目录中存在同名文件，请修改`
> - `dim_是否新店 = '1'` 永远空表（CSV 布尔字段实际是 `'TRUE'/'FALSE'` 字符串）
> - 50 店 / 90 天 / 45 万订单 openpyxl 写 Excel 4-5 分钟
>
> **架构**：v7 BI 的草稿/发布分离机制使**手撸 `/api/page` + `/api/card` 全链路废弃**；银弹是 `guancli ≥ 1.0.24` 自带的 `guanvis-skill` 公网分发，`guancli install-skill && guanvis-skill publish .` 30 秒一键发布整个 page + custom chart + dataView，跳过所有草稿/发布的状态机。配套硬规则：CSV 散客 `会员ID` 是 `""` 不是 NULL（三态判断必须 `IS NOT NULL AND <> ''`）；STRING 字段才能 `<> ''`，日期/数字 Spark 严格类型不行；Spark CTE 别名必须英文；ETL update 必须带 `OUTPUT_DATASET.dataSource.dsId` 否则 1012；数据集上传 BI 无原生 API（`POST /api/data-source/*` 全失败），只能 BI UI 手动 30-45 分钟；大表 pandas 用 `to_csv` 而非 `to_excel`（50 倍速差）。
>
> **不能跳的硬约束**（2026-05-20/21 v7 demo 实战 · 90 天 / 1200 门店 / 80K 会员 / 20 表 / 17 ETL / 6 HTML 看板）：
> 1. **直接手撸 page+card API 全废**：draft cdId ≠ published cdId 不会自动映射回 published page，光走 `POST /api/page` 拼不出来；走 `guanvis-skill publish` 才能跨过状态机。
> 2. **CSV 类型三态硬规则**：STRING 字段可以 `<> ''`，日期/数字字段不能（Spark 严格类型直接报错）；CSV 布尔字段实际是 `'TRUE'/'FALSE'` 字符串而非 int 1/0，`= '1'` 永远空表。

📖 **[references/v7-page-card-publish-pipeline.md](references/v7-page-card-publish-pipeline.md)** — 完整 13 节：v7 草稿/发布机制详解 / HTML 应用看板 SDK 最小骨架（schema.js + card_01_html.js + page.js + charts/dashboard.{html,css,js} 4 文件） / CSV 三态判断硬规则 / Spark SQL 4 个硬限制（中文别名 / 嵌套窗口 / `<> NULL` / 字面量日期）/ ETL update OUTPUT_DATASET dsId 注入脚本（`guancli ds search` 自动查 dsId 注入）/ 数据集上传走 BI UI 手动方案 / pandas to_csv vs to_excel 性能对比 + 向量化 30 倍速差 / JOIN 键全局统一命名（COL_MAP）/ 奶白 `#faf7f2` + 暖蓝 `#2563eb` 主题 / 端到端时间预算（5-7 小时拆解）/ 12 类反模式与硬约束总表 / 工程目录参考结构（scripts/ + etl_payloads/ + dashboards-v3/ 6 子目录）/ 与 Part C-12 的边界关系（C-12 讲已有 page 后怎么写 HTML 内容 + selector patch，本 Part D 讲从零到 6 个看板上线全流程）。

---

## 📚 References 目录

> 本 SKILL.md 主文是路由层；以下 8 个新文件（V1.4.0 引入）+ 4 个原贡献者文件构成完整知识库。详细索引：

**马甲蒸馏版（V1.4.0 新建）：**

| 文件 | 何时读 | 行数 |
|---|---|---|
| [part-a-commands.md](references/part-a-commands.md) | 写卡片、配 `--task` 缓存隔离、清理缓存时 | ~120 |
| [part-a-cards.md](references/part-a-cards.md) | 写 `create-and-get` JSON 前查参数 / 图表类型 / filters / 看示例 | ~240 |
| [guancli-commands.md](references/guancli-commands.md) | 用 guancli 探索 ETL/指标/任务/表单/通用 fetch 时 | ~160 |
| [part-b-payload.md](references/part-b-payload.md) | 写新 ETL payload / 复用 4 阶段脚本时 | ~175 |
| [part-b-errors.md](references/part-b-errors.md) | execute 失败、对照 `task error` 找修复方案时 | ~150 |
| [part-b-sdk.md](references/part-b-sdk.md) | 30+ 表批量改造、写 `transformV2ToV3` 时 | ~60 |
| [part-b17-fullchain-rewrite.md](references/part-b17-fullchain-rewrite.md) | 全链路 SmartETL 重写、副本页验收、ExecPlan 管理时 | ~290 |
| [part-c-payload-json.md](references/part-c-payload-json.md) | runtime 拿不到 payload_json / JSON.parse 失败时 | ~60 |
| [part-c-html-dashboard.md](references/part-c-html-dashboard.md) | 用户说"更高级 / 应用化 / 不限标准看板"，从零生成 HTML 化分析应用时（V2.1.1 新建） | ~360 |
| [v7-page-card-publish-pipeline.md](references/v7-page-card-publish-pipeline.md) | V7 BI 实例端到端搭多个 HTML 看板 / 手撸 page+card API 被 `60004` 草稿页面错误卡住 / CSV 散客 `会员ID IS NOT NULL` 算出 100% 假指标 / Spark `WITH 中文别名` 报错 / ETL update `1012 同名文件` / `dim_是否新店='1'` 永远空表 / openpyxl 写大表 4 分钟（V2.1.6 新建） | ~340 |
| [internal-nexus-install.md](references/internal-nexus-install.md) | 内网同事发来 `guan*-skill` tarball、本地装观远官方私服 skill 时（V2.1 新建） | ~80 |

**餐饮 BI 公式实战库（V2.1.5 新建，去敏蒸馏自两段餐饮连锁 BI 履职 + 39 个生产 ETL）：**

| 文件 | 何时读 | 行数 |
|---|---|---|
| [restaurant-bi-formulas/README.md](references/restaurant-bi-formulas/README.md) | 进入业务公式库的总入口 / 字段词典 / 5 条最常踩坑 | ~90 |
| [restaurant-bi-formulas/01-date-and-time.md](references/restaurant-bi-formulas/01-date-and-time.md) | 写时间范围（T-1 / 本月 / 上月 / 近 N 天 / 时间宏 / 用餐时段 / 跨月对齐） | ~180 |
| [restaurant-bi-formulas/02-customer-and-membership.md](references/restaurant-bi-formulas/02-customer-and-membership.md) | 新老客 / 会员属性 / 消费频次（3 口径）/ 复购（跨天 vs 非跨天）/ 留存流失 / RFM / 注册前后行为 / 90 天复购分桶 | ~350 |
| [restaurant-bi-formulas/03-revenue-kpi.md](references/restaurant-bi-formulas/03-revenue-kpi.md) | AC / ADS / ADT / AUD / Comp / TC_CRM% / NS_CRM% / 营收占比 / 客单分桶 / 累计消费 | ~180 |
| [restaurant-bi-formulas/04-channel-and-store.md](references/restaurant-bi-formulas/04-channel-and-store.md) | 业务渠道（堂食/外卖）/ 订单子渠道大 case / 时效类型 / 搭配类型 / StoreDate / 成长类型 / 注册门店优先级回填 | ~210 |
| [restaurant-bi-formulas/05-coupon-and-discount.md](references/restaurant-bi-formulas/05-coupon-and-discount.md) | 核销率 / 折扣率 / 折扣分桶 / 券类型分流 / 注册第一张券 / 30 日优惠订单比例 | ~110 |
| [restaurant-bi-formulas/06-sql-utils.md](references/restaurant-bi-formulas/06-sql-utils.md) | 字符串拆解 / `explode+split` / `collect_set+concat_ws` / 开窗排名（ROW_NUMBER/RANK/DENSE_RANK）/ 累计窗口 / 多表 LEFT JOIN | ~210 |
| [restaurant-bi-formulas/07-data-quality-traps.md](references/restaurant-bi-formulas/07-data-quality-traps.md) | `NULL vs 0` / 三态判断 / 口径歧义 / 重复字段名 / A↔B↔通用字段对照表 / 日期边界 | ~250 |
| [restaurant-bi-formulas/08-etl-engineering-patterns.md](references/restaurant-bi-formulas/08-etl-engineering-patterns.md) | **ETL 工程范式**：10-CTE DWD 宽表底座 / 轻节点重 SQL vs 重节点轻 SQL 哲学 / 财务双源对账 / POS 系统归一化 / 会员生命周期多输出 / Cohort 日期×门店网格（蒸馏自 39 个 V1 生产 ETL）| ~280 |
| [restaurant-bi-formulas/09-etl-catalog.md](references/restaurant-bi-formulas/09-etl-catalog.md) | **39 个 V1 生产 ETL 索引清单**：按 11 业务域分类（基础维表 / DWD / 会员档案 / 顾客行为 / 财务营收 / 营销目标 / 私域社群 / 活动券 / 评价管理 / 业务标签 / 数据质量）+ 每 ETL 的节点/输入/输出/SQL 速查 + 复用决策表 | ~190 |

> 触发场景："如何算复购率 / 客单价 / 同店增长" / "怎么判新老客" / "用餐时段怎么分桶" / "为什么会员数对不上" / **"我要写 DWD 宽表 / 评价 pipeline / 财务对账"** — 直接进 [restaurant-bi-formulas/README.md](references/restaurant-bi-formulas/README.md) 路由表。和 Part A/B/C 正交（按业务领域分，非按平台操作分）。

**贡献者原文（不修改，照引）：**

| 文件 | 来源 |
|---|---|
| [etl-rewrite-original.md](references/etl-rewrite-original.md) | CTO 张进 — SmartETL 改写经验未删减原文 |
| [custom-chart-playbook.md](references/custom-chart-playbook.md) | CTO 张进 — 自定义图表排障完整 playbook |
| [execplan-spec.md](references/execplan-spec.md) | OpenAI Codex — ExecPlan 完整规范 |
| [agents-rule.md](references/agents-rule.md) | OpenAI Codex — AGENTS.md 极简调度规则 |

---

## 📋 版本记录

**最新：V2.1.7** (2026-05-21) — **路由/触发层强化（docs-only）**。重写 `SKILL.md` frontmatter `description`，把 V2.1.6 Part D（v7 BI / `60004` 草稿 / guanvis-skill / CSV 三态 / Spark CTE 中文别名 / `1012` 同名文件）和 V2.1.5 餐饮 BI 公式库（复购率/客单价/RFM/DWD 宽表/财务对账/AC/ADS/Comp）的触发关键词全列了进来——原描述只覆盖 Part A/B/C，新场景的用户语料根本不路由进来。同时新增 `# 🆎 Part D` stub section（紧跟 Part C 后），结构上对齐 Part A/B/C/C-12 的可见度。修三处 V2.1.6 残留版本错位（主标题 `V2.1.5`→`V2.1.7`、openclaw npm 约束 `^1.0.21`→`^1.0.24`、三件套表 `majia-guanyuan` 行 `2.1.5`→`2.1.7`）。零 references / templates / 命令面改动。

**V2.1.6** (2026-05-21) — **新增 `references/v7-page-card-publish-pipeline.md`：V7 Page/Card 发布流水线 + 三态硬规则**（~340 行）。沉淀自 2026-05-20/21 一次"连锁咖啡 BI 演示拍摄录制"全流程实战（90 天 / 1200 门店 / 80K 会员 / 20 张表 / 17 个 ETL / 6 个 HTML 应用化看板）的 12 大踩坑：① **v7 BI 草稿/发布机制**——`POST /api/page+/api/card` 全失败（`60004 此操作只能在草稿页面执行`），draft cdId ≠ published cdId 导致手撸 API 跑不通；**银弹是 `guancli ≥ 1.0.24` 自带 `guanvis-skill`** 一键 `publish .`；② **CSV 三态判断硬规则**——散客订单 `会员ID` 是空字符串 `""` 而非 NULL，`IS NOT NULL` 把所有订单算成会员订单使北极星 #1 指标 = 100% 假数据，必须 `(会员ID IS NOT NULL AND 会员ID <> '')`；③ **STRING vs DATE 类型边界**——日期/数字字段不能 `<> ''`（Spark 严格类型），只有 STRING 字段能；④ **CSV 布尔字段 = 'TRUE'/'FALSE' 字符串**而非 int 1/0，`= '1'` 永远空表；⑤ **Spark CTE 别名必须英文**——`WITH 订单汇总 AS` 报 `PARSE_SYNTAX_ERROR`；⑥ **Window function 不能嵌套在 aggregate function**；⑦ **ETL update 必须带 `OUTPUT_DATASET.dataSource.dsId`** 否则 `1012 同名文件`；⑧ **数据集上传无原生 API**——所有 `POST /api/data-source/*` 失败，用户必须 BI UI 手动；⑨ **大表用 pandas to_csv 比 to_excel 快 50×**（4 分钟 vs 2 秒）；⑩ **JOIN 键全局统一命名**，避免 dim/fact 用不同名字（活动ID vs 关联活动ID）；⑪ **奶白 #faf7f2 主题 + 暖蓝主色** 业务用户接受度远高于深色；⑫ **HTML 应用看板 SDK + DATA_GRID dataView 最小骨架**（4 文件：schema.js / card_01_html.js / page.js / charts/dashboard.{html,css,js}）。SKILL.md 主路由表新增 Part D 入口，触发关键词："v7 BI 端到端搭看板 / 60004 此操作只能在草稿页面执行 / 会员ID IS NOT NULL 算出 100% / Spark WITH 中文别名 报错 / 1012 输出数据集目录中存在同名文件"。`@guandata/guancli` 依赖版本升级 `^1.0.21` → `^1.0.24`（自带 guanvis-skill 公网分发）。

**V2.1.5** (2026-05-18) — **新增 `references/restaurant-bi-formulas/`：餐饮连锁 BI 公式实战库**（10 个 markdown，2881 行，全脱敏）。蒸馏自两段连续的餐饮 BI 分析师履职 + 39 个生产 ETL，含：① **公式手册**（7 章 60+ SQL）—— 日期时间/顾客会员（RFM 8 类 × 营销策略 + R 阈值多档分级）/营收 KPI（AC/ADS/ADT/Comp/CRM%）/渠道门店（多渠道评价 pipeline）/券折扣/SQL 工具箱/数据质量陷阱；② **6 大 ETL 工程范式**（08 章）—— 10-CTE DWD 宽表底座 / 轻节点重 SQL vs 重节点轻 SQL 工程哲学 / 财务双源对账 / POS 系统识别归一化 / 会员生命周期多输出 / Cohort 日期×门店网格；③ **39 个 V1 生产 ETL 索引清单**（09 章）—— 按 11 业务域分类（基础维表/DWD/会员档案/顾客行为/财务营收/营销目标/私域社群/活动券/评价管理/业务标签/数据质量）+ 每 ETL 节点/输入/输出/SQL 速查 + 复用决策表。SKILL.md 主路由表新增餐饮业务公式入口；frontmatter `version: "2.1.4"` → `"2.1.5"`；纯 docs 增量 + 索引扩充，零 breaking change。

**V2.1.4** (2026-05-15) — 命令面同步 `@guandata/guancli@1.0.21`：① **`metric query` 泛化查询**（1.0.20 新增）完整接入 —— `--compare yoy|mom`、`--xtd ytd|mtd`、`--recent 7d|4w`、`--percentage --percentage-dim`、`--rank-top N --rank-dim`、`--last`、兜底 `--adv-calc-json`，业务侧"同比/累计/最近 N 天/占比/Top N"一行命令出数，命令面与判断表写进 [references/guancli-commands.md](references/guancli-commands.md)；② **`card preview -f excel` 导出**（1.0.20）+ `--limit` 默认抬到 10000 + 排序取数下限 10000；③ **错误输出更干净**（1.0.21），`guancli ... 2>&1 | head` 不再被 Usage 帮助淹没，Part B 报错速查脚本更可靠。manifest 依赖约束 `@guandata/guancli@^1.0.19` → `^1.0.21`；版本与依赖元数据全部对齐。

**V2.1.3** (2026-05-14) — 纯文档 patch：刷新 `docs/architecture.svg` v2.1.x 功能说明图，从 v1.5 时代"三块拼图"升级到 v2.1.x 现实——新增"三件套生态"条带（guancli 1.0.19 / guanvis-skill 0.1.13 / majia-guanyuan 2.1.3）+ Part C-12 HTML 应用化看板 NEW 高亮模块（粉紫渐变 + glow）+ 底部数字校准。同步生成 2880×1840 @2x DPI PNG 渲染产物（`docs/architecture.png`，供 npm/ClawHub 页面 fallback）。`package.json#files` 把 `docs/` 也补进 npm tarball。

**V2.1.2** (2026-05-14) — V2.1.1 的纯打包 hotfix：`package.json#files` 字段补上 `templates/`，让 npm install 的用户也能拿到 `templates/html-dashboard/` 起手模板包（GDHTML runtime + 2 起手模块 + patch_selector_linkage.js）。仅影响 npm 安装路径；GitHub clone / ClawHub install / `gh skill install` 路径在 V2.1.1 就已经包含 templates/。

**V2.1.1** (2026-05-14) — 新增 **Part C-12：HTML 应用化看板生成**（`references/part-c-html-dashboard.md` + `templates/html-dashboard/` 模板包）；用户说"更高级/应用化/不限标准看板"时自动切到 SDK 子类型 + DATA_GRID dataView 数据层架构；附 `patch_selector_linkage.js` 弥补 `guanvis-skill .linkToAll()` 联不到 custom chart 内部 dataView 的盲区。`guancli card preview` 命令面同步纠正（不再有 `--pg-id`），新增 `.data // .response` jq 兼容写法和中文字段 bracket 语法速查。

**V2.1.0** (2026-05-13) — `guanvis-skill@0.1.13` 内网 Nexus 上线，Part A 标准建卡路由优先指向它；新增 `references/internal-nexus-install.md` 内网 tarball 安装手册（含 macOS `com.apple.quarantine` 坑）；与官方 skill 共存表升级为三件套分工。

完整变更历史见 [CHANGELOG.md](CHANGELOG.md) 或 [GitHub Releases](https://github.com/maojiebc/majia-guanyuan/releases)。

## 👤 作者 / 联系

**马甲（@maojiebc）** · 超级马甲

如果这份 skill 帮到你，欢迎在以下任意渠道找我交流踩坑实录、提需求、报 bug，也欢迎切磋用户运营 / 数据中台 / BI 工程的实战经验：

| 渠道 | 链接 |
|---|---|
| 📧 Email | [m9224@163.com](mailto:m9224@163.com) |
| 🐙 GitHub | [github.com/maojiebc](https://github.com/maojiebc) |
| 🪝 ClawHub | [clawhub.ai/p/maojiebc](https://clawhub.ai/p/maojiebc) |
| 🐦 X | [@maojiebc](https://x.com/maojiebc) |
| 📕 小红书 | [超级马甲](https://xhslink.com/m/4fQMJeHHWKC) |
| 📰 微信公众号 | **超级马甲** |

> 这份 skill 是 14 年用户运营 + 观远 BI 实战 + 60+ 张 ETL 写入实证沉淀出来的，问题/合作随时聊。
