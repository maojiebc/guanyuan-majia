---
name: guanyuan-majia
description: 观远 BI（Guandata）全链路操作 — 数据查询/建卡/取数（Part A）、ETL 治理/写入/删除（Part B，含 SmartETL 全链路重写 + 字段使用度审计 + ExecPlan 工程化）、自定义图表 HTML/CSS/JS 注入与排障（Part C）。当用户提到 营业额/门店/会员/订单/建卡/取数/报表/ETL/direct-save/payload_json/自定义图表/观远/Guandata/BI 时使用。马甲业务实战版，60+ ETL 战例、10 类报错手册、Claude Code/OpenClaw/Codex/Hermes 通用。
license: MIT
metadata:
  version: "1.7.3"
  author: "超级马甲 / maojiebc"
  homepage: https://github.com/maojiebc/guanyuan-majia
  openclaw:
    emoji: "📊"
    homepage: https://github.com/maojiebc/guanyuan-majia
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
        package: "@guandata/guancli@^1.0.18"
        bins:
          - guancli
---

# 观远 BI · 马甲专版（V1.7.1）

> **结构说明（V1.5.0 引入 progressive disclosure）**：本文档是**路由层 + 关键规则**，详细操作手册下沉到 `references/`。每个 Part 的入口章节会指出"何时回到 references/ 查全表"。完整章节索引见末尾的 [📚 References 目录](#-references-目录)。

## 🧭 Part 选择

| 你想做 | 走 |
|---|---|
| 查数据、建卡、生成报表、做分析 | **Part A：数据查询与卡片创建** |
| 扫整库 ETL 治理 / 新建/修改/删除 ETL / 字段使用度审计 / 修复 ETL 报错 | **Part B：ETL 治理与写入** |
| 把整条 SmartETL 链改写成 SQL 版 + 页面副本验收 + 差异定位 + 空快照阻塞 | **Part B-17：全链路重写方法论**（拆到 [references/part-b17-fullchain-rewrite.md](references/part-b17-fullchain-rewrite.md)） |
| 30+ 张表批量迁移 / 跨多日工程 / 复杂重构需要项目化追踪 | **B-17.11 ExecPlan 工作法**（同上文件 §11） |
| 自定义图表 HTML/CSS/JS 注入、固定卡片/overlay、payload_json 取数、路由清理 | **Part C：自定义图表开发与排障** |
| 不知道用哪个 | 看 Part B "推荐工作流" 章节，或直接读各 Part 章节末尾的"实战 ID 速查" |

> **作者**：马甲（Part A/B 实证）+ 观远 CTO 张进（Part B-17 SmartETL 改写方法论 + Part C 自定义图表经验）+ OpenAI Codex（V1.2 ExecPlan 规范）
> **版本**：V1.7.0（2026-05-11）· **安装**：`git clone` + `node bin/install.js install`，或 `npx github:maojiebc/guanyuan-majia install`（不依赖 npm registry）· **作用域**：本地私有 BI 实例
> **兼容工具**：Claude Code · OpenClaw · Codex · Hermes (gbrain) · 任何支持 `SKILL.md` frontmatter 的 agent。详见仓库根 [README · 兼容性](README.md#-兼容性--compatibility) 与 [AGENTS.md](AGENTS.md)。

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

> 路径约定：以下命令假定 cwd 是 skill 安装目录。Skill 路径因 agent 工具不同而异（见 [README](README.md) 的兼容性表）：Claude Code 在 `~/.claude/skills/guanyuan-majia/`，OpenClaw 在 `~/.openclaw/skills/guanyuan-majia/`，Codex 在 `~/.codex/skills/guanyuan-majia/`，Hermes 在 `<workspace>/skills/guanyuan-majia/`。所有 Part A 命令都用相对路径 `scripts/guandata.py`，无需修改。

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

## 错误处理

| 状态码 | 处理 |
|--------|------|
| 500 | 终止，服务器问题 |
| 401 | 终止，登录失效 |
| 403 | 终止，无权限 |
| 404 | 终止，资源不存在 |

---

# 🅱️ Part B：ETL 治理与写入（V1.0）

> 基于 `@guandata/guancli@1.0.18` 的实证记录。所有 API 路径、payload 字段、报错信息、治理判断维度均来自真实跑通的请求。覆盖整库治理扫描 + 60+ 张 ETL 创建/重构/修复/删除的实战。
>
> ⚠️ `guanetl-skill` 在 guancli SKILL.md 里被提到，但**没有公开发包**，搜不到、装不上。整套 ETL 写入完全靠 `guancli fetch` 调底层 API。

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

**贡献者原文（不修改，照引）：**

| 文件 | 来源 |
|---|---|
| [etl-rewrite-original.md](references/etl-rewrite-original.md) | CTO 张进 — SmartETL 改写经验未删减原文 |
| [custom-chart-playbook.md](references/custom-chart-playbook.md) | CTO 张进 — 自定义图表排障完整 playbook |
| [execplan-spec.md](references/execplan-spec.md) | OpenAI Codex — ExecPlan 完整规范 |
| [agents-rule.md](references/agents-rule.md) | OpenAI Codex — AGENTS.md 极简调度规则 |

---

## 📋 版本记录

- **V1.5.3** (2026-05-10)：📣 分发可信度与品牌入口修整。
  - `SKILL.md` frontmatter 对齐 Agent Skills 规范：移除顶层 `version`，新增 `license: MIT`，版本号移入 `metadata.version`。
  - `LICENSE` 恢复为标准 MIT 文本，来源与致谢继续放在 `ATTRIBUTIONS.md`。
  - README 增加 GitHub CLI `gh skill`、skills.sh、ClawHub/OpenClaw 安装入口，以及「超级马甲」作者区。
  - 新增 `SECURITY.md` 与 `llms.txt`，说明本地凭据边界、AI/GEO 抓取入口和作者链接。
  - `scripts/guandata.py` 登录函数参数命名调整为 `login_secret`，降低公共 skill registry 的误报概率；观远 API payload 字段不变。
- **V1.5.2** (2026-05-09)：📦 ClawHub 发布准备。
  - `SKILL.md` frontmatter 增加 `metadata.openclaw`，便于 ClawHub / OpenClaw 读取安装依赖与运行要求。
  - README 增加 WorkBuddy / Qoder 兼容标识。
  - `package.json` / `manifest.json` / `SKILL.md` 版本同步到 1.5.2。
- **V1.5.1** (2026-05-09)：🪶 npm 路线精简 — git 唯一 source of truth。
  - 决策：本仓库**不发布到 npm registry**。理由：作为 agent skill，git clone 体验已足够顺，npm publish 是双 source of truth 维护负担（V1.4.0 hand-off 步骤一直没真发，README 命令实际跑会 404，已经踩到一次坑）。
  - 一行装的体验**保留**，入口换两条更稳的路径：
    - `git clone` + `node bin/install.js install`（主推，离线可控）
    - `npx github:maojiebc/guanyuan-majia install`（备选，npx 原生支持 GitHub URL，**不依赖 npm registry**）
  - 删除对外 npm 入口：README 顶部 npm badge 移除，安装段落不再出现 `@supermajia/guanyuan-bi`。
  - **保留** `package.json` / `manifest.json` / `.npmignore` / `bin/install.js` —— 它们是本地 install CLI 的运行时元数据，将来若要再发 npm 不必重写。
  - 同步 bump：`package.json` / `manifest.json` / SKILL.md frontmatter 都升 1.5.1。
- **V1.5.0** (2026-05-09)：🏗️ Progressive Disclosure 架构重构 — 性能不变、内容零损耗，但每次触发省 ~1.2 万 token。
  - **SKILL.md 瘦身**：2087 行（89 KB）→ 913 行（48 KB），减 56%。主文档变成**路由层 + 关键规则 + 决策框架**，详情下沉。
  - **保留在主文档**（agent 触发即载）：Part 选择路由表 + Part A 关键规则 + B-1 API 全图 + B-2 治理扫描决策框架 + B-3/B-5/B-6/B-7 实操步骤（**B-7.0 V1.3.1 删除安全闸完整保留**）+ B-9 10 类报错速查表（一行一条）+ B-10 字段审计 + B-12 经验十条 + B-13 红线 19 条 + B-14 API 速查 + B-15 实战 ID 速查 + B-17 入口指针 + 决策口诀 + Part C 全章节（仅 C-3 拆出）。
  - **拆出到 `references/` 8 个新文件**（按需按 Part 拉取，主文档给出明确指针）：
    - `part-a-commands.md` — Part A 完整命令清单 + 缓存机制 + `--task` 隔离
    - `part-a-cards.md` — 卡片参数 + 26 图表类型 + metric/filters/sorting/字段名/filterType 全格式 + 6 个建卡示例
    - `part-b-errors.md` — Part B 10 类报错的详细方案（每条含触发、根因、修复、回归测试）
    - `part-b-payload.md` — ETL payload schema 深入（节点字段、relativeFieldAlias、位置式 input 索引）
    - `part-b-sdk.md` — v2→v3 批量改造 SDK（transformV2ToV3 7 步）+ 时间窗口缩减实战
    - `part-b17-fullchain-rewrite.md` — B-17 全链路重写方法论全章节（4 件交付 + 8 硬规则 + 5 步工作流 + 三层验收 + 差异追踪 5 步法 + 空快照处理 + ExecPlan 工作法）
    - `part-c-payload-json.md` — C-3 payload_json 排障详解（截断判断 3 步 + 拆列推荐方案 + 实战 case）
    - `guancli-commands.md` — guancli 9 大类命令完整速查（ds / etl / metric / metric_attribution / task / page / card / form / fetch）+ 工具选择决策表
  - **保留在 `references/` 不变**（贡献者原文留档，与马甲蒸馏版区分）：
    - `custom-chart-playbook.md` / `etl-rewrite-original.md`（CTO 张进原文）
    - `execplan-spec.md` / `agents-rule.md`（OpenAI Codex 原文）
  - **同步 bump**：`package.json` / `manifest.json` / npm tarball 都升 1.5.0。
  - 🏗️ **SKILL.md 大瘦身**：主文档从 2087 行 / 89 KB → ~913 行 / ~48 KB（瘦 56%），每次 skill 触发省 ~1.2 万 token。
  - 📦 **拆出 8 个 references/ 文件**（马甲蒸馏版）：part-a-commands / part-a-cards / guancli-commands / part-b-payload（含原 B-8 复用模板）/ part-b-errors / part-b-sdk / part-b17-fullchain-rewrite / part-c-payload-json。每个 references 文件自包含 + 反向链接到主文相关章节。
  - 🎯 **保留主文的章节**（高频/必读/决策框架）：Part 选择表、Part A 关键规则 + 命令骨架 8 条、B-0 工作流、B-1 API 全图、B-2 治理扫描（决策框架）、B-3 建目录、B-4 骨架（详见 references）、B-5 拿真错三步、B-6 校验工具集、B-7 删除拓扑（**含 V1.3.1 安全闸完整保留**）、B-9 速查表（10 类报错 1 行 1 条，详方案见 references）、B-10 字段审计、B-11 SDK 速查、B-12 经验 10 条、B-13 红线（19 条全保留）、B-14 API 速查、B-15 实战 ID、B-17 入口指针 + 决策口诀、Part C 全章节（仅 C-3 拆 references）。
  - 🧹 **description 字段瘦身**：1089 字符 → 约 284 字符（-73%），删除内嵌的 30+ 个函数名/API 路径细节（这些信息的归宿是 SKILL.md 主体，不是 description）。LLM 触发判断更聚焦关键词。
  - ❌ **删除冗余**：原 B-16 / C-10 "触发场景示例"两节删除（重复 description 信息，反 progressive disclosure）。
  - ✏️ **修正 V1.3.1 之前已知小毛病**：原 L28 "操作前必读"标题为空 + L30 立即出现"关键规则"标题这种结构噪声合并清理。
  - ⚠️ **manifest.json 的 `triggers` 字段标记为遗留**：Claude Code/OpenClaw/Codex 三个目标 agent 实际只读 SKILL.md frontmatter `description`，manifest.triggers 维护成本不带来对应收益。本版保留字段不删（避免破坏 schema 期望），但在字段后加注释说明"see SKILL.md description for the single source of truth"。
  - 🔗 **基于 V1.4.0 install CLI**：保留并整合 V1.4.0 引入的 `bin/install.js` 安装器、`package.json` 等基础设施。
- **V1.4.0** (2026-05-09)：🛠️ 添加跨工具 install CLI。
  - 新增 `bin/install.js`（10.9KB Node.js 安装器），三命令：
    - `install [--tool claude-code|openclaw|codex|hermes|all] [--force] [--dry-run]`
    - `list` 列出当前安装情况 + 每个工具的版本
    - `uninstall --tool <name>`（自动备份用户已修改过的 `config.json` 到 `.backup`）
  - 🛡️ 安全约束：
    - **永远不覆盖已存在的 `config.json`**（保留真凭据，再装一次也不丢）
    - 默认跳过已装目标，要 `--force` 才覆盖
    - 排除 `.cache/` / `data/columns_cache/` / `.git/` 不进 tarball（`.npmignore` + `package.json files` 白名单 + dry-run 验证）
  - 📁 新增文件：`package.json` / `bin/install.js` / `.npmignore`（V1.5.1 后明确仅本地用，不 publish）
- **V1.3.1** (2026-05-09)：基于外部代码审查的修复版本（patch release，无新功能）。
  - 🐛 **P1 修复**：SKILL.md L185 附近 ` ```bash ` 代码块未闭合 ——补上关闭 fence，确保后续 Markdown 结构不错位。
  - 🛡️ **P2 安全**：新增 **B-7.0 删除前的硬性安全闸** —— Agent 在执行任何 `DELETE /api/data-source/` 或 `DELETE /api/etl/` 前必须满足四条硬约束（用户逐项明确确认 / 下游引用已切流 / 新链路对账通过 / 批量分批确认）。Agent 默认行为是产出待删清单供用户审阅，永远不主动删除。B-13 红线同步加一条最显眼的"未经用户逐项明确确认，绝不执行任何 DELETE 操作"。
  - 🛡️ **P2 安全**：`scripts/guandata.py` 的 `set_task()` 加输入校验，拒绝包含 `/` `\` `..` 或保留名（`.` / `..`）或超长（>64）的 task 名，封堵 `--task ../../x` 类路径穿越漏洞。回归测试 8 种攻击向量全部 reject，正常中文/字母数字 task 名继续 accept。
  - 📝 **P3 一致性**：frontmatter `description` 里残留的 "V1.1" 字样改为 "V1.3"，跟 `version` 字段对齐。
- **V1.3** (2026-05-09)：工具无关化 — skill 现在不只跑在 Claude Code 上，原生兼容 OpenClaw、Codex、Hermes (gbrain)。
  - 新增 **仓库根 `AGENTS.md`** —— 给 Codex 作项目级指令，给 Hermes 作 resolver 文件，给其他 AGENTS.md-aware 工具（Cursor / Aider 等）作 navigation pointer。
  - 新增 **`manifest.json`** —— 工具无关的 skill 元数据清单，含 compatibility 矩阵、triggers 数组、dependencies、credits 结构化字段。
  - **去硬编码路径**：SKILL.md 里所有 `skills/guandata/...` 旧路径改成相对路径（`scripts/guandata.py` / `config.json` / `.cache/`），脚本现在能在任意 skill 安装目录下运行。删掉 guandata70 残留的 `cat skills/guandata/分析经验.md` 段落（该文件本就不存在）。
  - **README 加 Compatibility 章节** —— 表格列出 4 个已验证工具 + 安装路径 + 入口文件 + 备注。安装命令从单一 Claude Code 路径扩展为四个工具并列。
  - **触发词单独抽到 `manifest.json` 的 `triggers` 数组**，frontmatter description 不变（仍兼容只读 frontmatter 的工具）。
- **V1.2** (2026-05-09)：吸收 OpenAI Codex 的 ExecPlan 规范用于 SmartETL 重写工程化。
  - 新增 **B-17.11 用 ExecPlan 管理重写工程**：何时启用判断 + 三项核心约束（自包含 / 活文档 / 可观察结果锚定）+ SmartETL 改写专用 ExecPlan 骨架（拿去填空，不用从通用模板自己映射）+ 四个活文档章节实战用法（Progress / Surprises & Discoveries / Decision Log / Outcomes & Retrospective）+ 小工程不用 ExecPlan 的判断阈值。
  - 新增 **B-12 ExecPlan 指针**：30+ 张表跨多日工程必须走 ExecPlan，不靠零散 todo。
  - `references/` 新增 `execplan-spec.md`（OpenAI Codex ExecPlan 完整规范）+ `agents-rule.md`（极简调度规则）。
- **V1.1** (2026-05-09)：整合观远 CTO 张进的两份核心经验。
  - 新增 **B-17 全链路重写方法论**（10 节）：4 件交付 + 8 条硬规则 + 5 步标准工作流 + 三层验收（数据集/副本页/卡片级）+ 差异追踪 5 步法 + 空快照处理标准 + ExecPlan/modeling/evidence/sql/raw 标准交付物 + 6 类专属常见坑 + 完成标准。
  - 新增 **Part C 自定义图表开发与排障**（10 节）：renderChart 4 参数 runtime 契约 + data 5 种形态识别 + payload_json 截断判断 3 步 + 拆列推荐方案 + overlay/mask 挂页面根节点 + z-index 基线（8/1/20）+ 懒加载 iframe 处理 + 路由切换销毁规则 + MutationObserver 死循环陷阱 + 复制页 card id 重定位 + 浏览器层级排障清单 + 最终真实浏览器验收 8 项。
- **V1.0** (2026-05-09)：合并 guandata70 数据分析侧 + ETL 治理与写入侧。Part B 整合 60+ 张 ETL 创建/重构/修复实战经验，包括 11 个已实测 endpoint、8 维 ETL 去留判断、4 维字段去留判断、ODS/DIM/DWD/DWS/APP 五层分层、双源字段使用度审计、v2→v3 批量改造 SDK、10 类高频报错修复手册。

## 👤 作者 / 联系

**马甲（@maojiebc）** · 超级马甲

如果这份 skill 帮到你，欢迎在以下任意渠道找我交流踩坑实录、提需求、报 bug，也欢迎勾兑用户运营 / 数据中台 / BI 工程的实战经验：

| 渠道 | 链接 |
|---|---|
| 📧 Email | [m9224@163.com](mailto:m9224@163.com) |
| 🐙 GitHub | [github.com/maojiebc](https://github.com/maojiebc) |
| 🪝 ClawHub | [clawhub.ai/p/maojiebc](https://clawhub.ai/p/maojiebc) |
| 🐦 X | [@maojiebc](https://x.com/maojiebc) |
| 📕 小红书 | [超级马甲](https://xhslink.com/m/4fQMJeHHWKC) |
| 📰 微信公众号 | **超级马甲** |

> 这份 skill 是 14 年用户运营 + 观远 BI 实战 + 60+ 张 ETL 写入实证沉淀出来的，问题/合作随时聊。
