---
name: guanyuan-majia
description: 观远 BI（马甲专版 V1.1）— 数据查询/建卡/取数 + ETL 治理/写入/删除 + 自定义图表开发 全链路。Part A：用 guandata.py 做数据获取与分析（list-datasets / get-columns / search-values / create-and-get / create-card / get-card-data / delete-cards / create-page / release-page / list-pages）+ guancli 只读探索（ds/etl/page/card/metric/task/form/fetch）。Part B：用 guancli 做 ETL 治理与写入全链路（POST /api/directory ETL/DATA_SET 双树建目录、POST /api/etl/direct-save create+update 同接口、POST /api/etl/execute、GET /api/task 拿真实错误、DELETE /api/data-source 先于 DELETE /api/etl、批量扫描判断 ETL/字段去留、ODS/DIM/DWD/DWS/APP 五层分层、字段使用度双源审计、v2→v3 批量改造 SDK、CTO 张进的 SmartETL 全链路重写方法论：全链路追到原始源/旧资产只读/新链只允许 SQL 节点/双层结构+数值验收/副本页卡片级验收/差异追踪 5 步法/空快照处理标准/ExecPlan+modeling+evidence 交付物），10 类高频报错修复。Part C：自定义图表 HTML/CSS/JS 注入开发与排障（renderChart 4 参数 runtime 契约、payload_json 截断判断、固定卡片/overlay/z-index/stacking context、复制页 card id 重定位、懒加载 iframe、路由切换销毁注入物、live 浏览器验收、payload_json 拆列方案）。触发词：查数据、做图表、看报表、营业额、门店、会员、订单、分析、建卡、取数、删卡、ETL 治理、循环依赖、字段使用度、新建 ETL、修改 ETL、direct-save、ETL 报错、execute 失败、批量迁移 ETL、SmartETL 改写、全链路重写、副本页验收、差异追踪、空快照、自定义图表、HTML 注入、JS 注入、payload_json、overlay、固定卡片、z-index、看 BI HTTP API。
version: "1.3"
---

# 观远 BI · 马甲专版（V1.3）

## 🧭 Part 选择

| 你想做 | 走 |
|---|---|
| 查数据、建卡、生成报表、做分析 | **Part A：数据查询与卡片创建** |
| 扫整库 ETL 治理 / 新建/修改/删除 ETL / 字段使用度审计 / 修复 ETL 报错 | **Part B：ETL 治理与写入** |
| 把整条 SmartETL 链改写成 SQL 版 + 页面副本验收 + 差异定位 + 空快照阻塞 | **Part B-17：全链路重写方法论** |
| 30+ 张表批量迁移 / 跨多日工程 / 复杂重构需要项目化追踪 | **Part B-17.11：ExecPlan 工作法**（V1.2 新增） |
| 自定义图表 HTML/CSS/JS 注入、固定卡片/overlay、payload_json 取数、路由清理 | **Part C：自定义图表开发与排障** |
| 不知道用哪个 | 看 Part B "推荐工作流" 章节，或直接读章节末尾的"实战 ID 速查" |

> **作者**：马甲（Part A/B 实证）+ 观远 CTO 张进（Part B-17 SmartETL 改写方法论 + Part C 自定义图表经验）+ OpenAI Codex（V1.2 ExecPlan 规范）
> **版本**：V1.3（2026-05-09）· **作用域**：本地私有 BI 实例
> **兼容工具**：Claude Code · OpenClaw · Codex · Hermes (gbrain) · 任何支持 `SKILL.md` frontmatter 的 agent。详见仓库根 [README · 兼容性](README.md#-兼容性--compatibility) 与 [AGENTS.md](AGENTS.md)。

---

# 🅰️ Part A：数据查询与卡片创建

## 🔴 操作前必读（不可跳过）

## ⚠️ 关键规则

**所有数值计算必须跑代码** — 禁止在思考中直接口算百分比、环比、除法等。
1. **必须提供 pg_id** — 不保存的卡片无法取数据
2. **先查页面权限** — 用 `list-pages --manageable` 找有权限的页面，不用翻 JSON
3. **筛选值按需查** — 只有用了分类筛选（`IN`/`EQ`/`CONTAINS`）才需要 `search-values`；纯日期范围（`BT`）不需要
4. **图表类型限制** — 超出 metric/row/column 上限会返回空数据
5. **必须确认数据范围** — 用户没有明确指定日期范围时，**必须追问**，不要自己假设。例如："你想看哪段时间的数据？" 或提供选项："要看今天、本周还是上月？"



**遇到意外的错误以及得到新的教训立即更新：** 遇到意外的错误立即把它落到 SKILL.md 对应的章节（Part B 报错走 B-9，Part C 走 C-3 等）或 ExecPlan 的 `Surprises & Discoveries` 章节（B-17.11）。格式：
```markdown
### [YYYY-MM-DD] 简要标题
- **场景**: 什么情况下遇到的
- **问题**: 发生了什么（含 task error 原文、payload 片段）
- **判断**: 应该怎么做
```

## 基本信息

> 路径约定：以下命令假定 cwd 是 skill 安装目录。Skill 路径因 agent 工具不同而异（见仓库根 [README](README.md) 的兼容性表）：Claude Code 在 `~/.claude/skills/guanyuan-majia/`，OpenClaw 在 `~/.openclaw/skills/guanyuan-majia/`，Codex 在 `~/.codex/skills/guanyuan-majia/`，Hermes 在 `<workspace>/skills/guanyuan-majia/`。所有 Part A 命令都用相对路径 `scripts/guandata.py`，无需修改。

- 配置文件: `config.json`（**含明文凭据，已被 .gitignore 排除**）
- 脚本: `scripts/guandata.py`

## 运行环境
- **Python 3.8+**
- **依赖库**: `httpx`（`pip install httpx`）
- 凭据存储在 `config.json` 中（明文），仅供本地使用，切勿提交到公开仓库

## 配置说明

编辑 `config.json`：

```json
{
  "version": "6",
  "base_url": "https://your-guandata-instance.com:port",
  "domain": "your_domain",
  "login_id": "your_username",
  "password": "your_password",
  "default_pg_id": "your_default_page_id",
  "default_folder_id": "your_default_folder_id"
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `version` | ✅ | 观远BI版本：`"6"` 或 `"7"`。<br>• `"6"`：观远BI 6.x，直接保存卡片<br>• `"7"`：观远BI 7.0+，使用 draft/release 机制（创建卡片后自动发布页面） |
| `base_url` | ✅ | 观远BI服务器地址，如 `https://bi.company.com:8080` |
| `domain` | ✅ | 登录域，通常为 `guanbi`，具体咨询你们的BI管理员 |
| `login_id` | ✅ | 观远BI登录账号 |
| `password` | ✅ | 观远BI登录密码 |
| `default_pg_id` | | 默认页面ID。不传时，`create-and-get` 需手动指定 `pg_id`；传入后可省略 |
| `default_folder_id` | | 默认文件夹ID。创建新页面时的存放位置 |

### 如何获取 pg_id / folder_id

1. 在观远BI网页打开目标页面，URL 中的 `pgId=xxx` 即为页面ID
2. 文件夹ID在观远BI「数据管理」→「目录」中查看

## 核心命令

```bash
SCRIPT="python3 scripts/guandata.py"

# 查数据集（默认读本地缓存）
$SCRIPT list-datasets
$SCRIPT list-datasets --columns   # 同时显示每个数据集的字段
$SCRIPT list-datasets --refresh   # 强制刷新缓存（数据源有变更时用）

# 查字段（默认读本地缓存，自动包含计算字段）
$SCRIPT get-columns <ds_id>             # 输出原始字段 + 计算字段
$SCRIPT get-columns <ds_id> --refresh   # 强制刷新缓存
$SCRIPT get-columns <ds_id> --with-calc # 同时显示计算字段（公式字段）

# 查枚举值（筛选前必查，避免值不存在）
# fd_id 从 get-columns 输出第二列拿
$SCRIPT search-values <ds_id> <fd_id> --search "关键词"
$SCRIPT search-values <ds_id> --name "门店名称" --search "某门店"  # 用字段名代替 fd_id

# 建卡+取数（一步到位）
$SCRIPT create-and-get '{"name":"卡片名","ds_id":"数据集ID","chart_type":"SINGLE_VALUE","pg_id":"页面ID","metric":[{"name":"会员id","aggr":"CNT_DISTINCT"}],"filters":[{"name":"营业日期","op":"BT","value":["2026-02-01","2026-02-28"]}]}'
$SCRIPT create-and-get '{...}' --limit 200   # 限制返回200行数据（默认500行上限）

# 建卡+取数（组合图，metric_additional 传折线叠加数据）
$SCRIPT create-and-get '{"name":"达成率趋势","ds_id":"数据集ID","chart_type":"STACKED_COLUMN_WITH_LINE","pg_id":"页面ID","metric":[{"name":"营业额","aggr":"SUM"}],"metric_additional":[{"name":"人数","aggr":"SUM"}],"row":["营业日期(月)"],"column":["销售类型"],"filters":[...]}'

# 仅建卡（不取数）
$SCRIPT create-card '{...}'

# 取卡片数据（含筛选条件）
$SCRIPT get-card-data <card_id>

# 列页面
$SCRIPT list-pages
$SCRIPT list-pages --manageable  # 只显示有编辑权限的页面（日常用这个）

# 注意：list-datasets 默认显示父文件夹ID
# 输出格式示例：
#   数据集名称
#     ID: 数据集ID  |  行数  列数  |  状态
#     父文件夹ID: 父文件夹ID
#     描述: 描述信息
#     路径: 目录路径

# 创建页面
$SCRIPT create-page "页面名称"
$SCRIPT create-page "页面名称" --parent-dir "目录ID" --desc "描述"

# 获取页面卡片列表
$SCRIPT get-page-cards <pg_id>

# 批量删除卡片（需要 pg_id）
$SCRIPT delete-cards <pg_id> <card_id1> <card_id2> ...
```

## 💾 数据缓存机制
**`create-and-get`、`get-card-data` 命令都会自动将数据保存到本地 CSV 缓存文件。**

输出末尾会显示缓存路径：`📁 缓存: .cache/data/xxx.csv`

### 缓存目录结构

```
.cache/
├── data/                   # 数据查询缓存（CSV），默认共享目录
├── datasets/               # 数据集列表缓存（JSON）
├── columns/                # 字段列表缓存（JSON）
└── tasks/                  # 按任务隔离的缓存（使用 --task 参数时）
    └── {task_name}/
        ├── data/
        ├── datasets/
        └── columns/
```

### 按任务隔离缓存（--task）

不同任务的缓存混在一起时，用 `--task` 参数按任务名分组。**`--task` 放在子命令前面：**

```bash
# 堂食分析任务 → .cache/tasks/堂食分析/data/
$SCRIPT --task "品类分析" create-and-get '{"name":"品类","ds_id":"<dataset_id>",...}'

# 查字段也隔离
$SCRIPT --task "会员分析" get-columns <dataset_id>
```

不加 `--task` 时，缓存仍在默认的 `.cache/data/` 共享目录。

### 缓存清理

当缓存占用过多空间或数据过期时，需要清理缓存：

```bash
# 清理所有数据查询缓存（保留最近7天）
find .cache/data -name "*.csv" -mtime +7 -delete

# 清理所有缓存（彻底清空）
rm -rf .cache/*



### 缓存文件格式

CSV，首行为表头，后续行为数据。用 Excel / pandas / csv 模块直接读即可。

### 大模型使用规范

**当拿到取数结果后，必须用缓存文件处理数据，不要把大量数据塞进上下文。**

正确做法：
```python
import csv
# 1. 从输出中提取缓存路径
# 2. 用代码读取缓存
with open('.cache/data/xxx.csv', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    headers = next(reader)
    rows = list(reader)
# headers[j] 是第 j 列的字段名
# rows[i][j] 是第 i 行第 j 列的值（字符串）
```

## create-and-get / create-card 参数说明

`create-and-get` 和 `create-card` 共用以下参数格式：

| 参数 | 必填 | 类型 | 说明 | 类比 SQL |
|------|------|------|------|----------|
| `name` | ✅ | string | 卡片名称 | - |
| `ds_id` | ✅ | string | 数据集 ID（用 `list-datasets` 查） | `FROM 表` |
| `chart_type` | ✅ | string | 图表类型（见下方速查表） | - |
| `pg_id` | ✅ | string | 保存到的页面 ID（用 `list-pages --manageable` 找） | - |
| `row` | | list | 行维度（分组依据） | `GROUP BY` |
| `column` | | list | 列维度（横向拆列） | 交叉表列头 |
| `metric` | | list | 数值（要算的指标） | `SUM/AVG/COUNT` |
| `metric_additional` | | list | 叠加数值（组合图专用：柱+线的线） | - |
| `color_by` | | list | 颜色分组（气泡图/散点图） | - |
| `size_by` | | list | 气泡大小（气泡图专用） | - |
| `filters` | | list | 筛选条件 | `WHERE` |
| `sorting` | | list | 排序 | `ORDER BY` |
| `custom_fields` | | list | 自定义公式字段（动态创建计算列） | `SELECT ... , SUM(x)/SUM(y) AS 别名` |

举例说明：
```json
{
  "row": ["城市"],                        // 按城市分行
  "column": ["渠道类型"],              // 堂食/外卖拆成两列
  "metric": [{"name": "销售额", "aggr": "SUM"}],  // 每格填营业额总和
  "filters": [{"name": "营业日期", "op": "BT", "value": ["2026-01-01", "2026-02-28"]}],  // 只看1-2月
  "sorting": [{"name": "销售额", "order": "DESC"}]  // 按营业额降序排
}
// 等价于: SELECT 城市, 渠道类型, SUM(销售额) FROM 表 WHERE 营业日期 BETWEEN ... GROUP BY 城市, 渠道类型 ORDER BY SUM(销售额) DESC
```

### 自定义公式字段（custom_fields）

在创建卡片时动态添加计算字段，无需提前在观远界面建好：

```bash
$SCRIPT create-and-get '{
  "name": "成本率分析",
  "ds_id": "数据集ID",
  "chart_type": "GROUPED_COLUMN",
  "pg_id": "页面ID",
  "row": ["门店名称"],
  "metric": [
    {"name": "销售额", "aggr": "SUM"},
    {"name": "成本率"}
  ],
  "custom_fields": [
    {"name": "成本率", "fdType": "DOUBLE", "formula": "SUM([实付金额])/SUM([销售额])*100"}
  ],
  "filters": [{"name": "营业日期", "op": "BT", "value": ["2026-01-01", "2026-02-28"]}]
}'
```

**参数格式**：

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | 新字段名称 |
| `fdType` | ✅ | 数据类型：`DOUBLE`（数值）、`STRING`（文本）等 |
| `formula` | ✅ | 公式表达式，用 `[字段名]` 引用字段，支持 `SUM()`/`AVG()` 等聚合 |

**注意**：
- 公式里的字段名必须是数据集中已存在的字段
- 创建后该字段可直接在 `metric`/`row` 中引用（和其他字段一样），如果公式已经聚合无需再写 `aggr`
- 仅 `create-and-get` 和 `create-card` 支持此参数


## 图表类型速查（26种）

| 类型 | metric | row | column | metric_additional | color_by | size_by | 备注 |
|------|:------:|:---:|:------:|:-----------------:|:--------:|:-------:|------|
| `SINGLE_VALUE` | 1 | 0 | 0 | 0 | 0 | 0 | 指标卡（单值） |
| `KPI_CARD` | n | 0 | 0 | 0 | 0 | 0 | 指标卡（带阈值样式） |
| `BASIC_COLUMN` | 1 | n | 0 | 0 | 0 | 0 | 柱状图 |
| `GROUPED_COLUMN` | n | n | 1 | 0 | 0 | 0 | 簇状柱状图 |
| `STACKED_COLUMN` | n | n | 1 | 0 | 0 | 0 | 堆积柱状图 |
| `PERCENT_STACKED_COLUMN` | n | n | 1 | 0 | 0 | 0 | 百分比堆积柱状图 |
| `WATERFALL_COLUMN` | 1 | n | 0 | 0 | 0 | 0 | 瀑布图 |
| `BULLET_COLUMN` | 2 | n | 0 | 0 | 0 | 0 | 子弹图 |
| `BASIC_BAR` | 1 | n | 0 | 0 | 0 | 0 | 条形图 |
| `BASIC_LINE` | 1 | n | 0 | 0 | 0 | 0 | 折线图 |
| `MULTI_LINE` | n | n | 1 | 0 | 0 | 0 | 多条折线图 |
| `STACKED_AREA` | n | 1 | 1 | 0 | 0 | 0 | 堆积面积图 |
| `PERCENT_STACKED_AREA` | n | 1 | 1 | 0 | 0 | 0 | 百分比堆积面积图 |
| `STACKED_COLUMN_WITH_LINE` | n | 1 | 1 | 1 | 0 | 0 | metric=柱子, metric_additional=折线 |
| `GROUPED_COLUMN_WITH_LINE` | n | 1 | 1 | 1 | 0 | 0 | metric=柱子, metric_additional=折线 |
| `STACKED_COLUMN_WITH_SYMBOL` | n | 1 | 1 | 1 | 0 | 0 | metric=柱子, metric_additional=标记 |
| `GROUPED_COLUMN_WITH_SYMBOL` | n | 1 | 1 | 1 | 0 | 0 | metric=柱子, metric_additional=标记 |
| `PIE` | 1 | 1 | 0 | 0 | 0 | 0 | 饼图 |
| `TREE_MAP` | 1 | n | 0 | 0 | 0 | 0 | 矩形树图 |
| `FUNNEL` | n | 0 | 0 | 0 | 0 | 0 | 漏斗图 |
| `HEAT_MAP` | 1 | 1 | 1 | 0 | 0 | 0 | 热力图 |
| `MULTIDIMENSIONAL_SANKEY` | 1 | n | 0 | 0 | 0 | 0 | 多维桑基图 |
| `PIVOT_TABLE` | n | n | n | 0 | 0 | 0 | 交叉表 |
| `WORD_CLOUD` | 1 | 1 | 0 | 0 | 0 | 0 | 词云 |
| `BASIC_BUBBLE` | 2 | n | 0 | 0 | 1 | 1 |气泡图 x=metric[0], y=metric[1] |
| `BASIC_SCATTER_PLOT` | 2 | 1 | 0 | 0 | 1 | 0 | 散点图  x=metric[0], y=metric[1]|

> `n` = 不限数量, `0` = 不支持, `2` = 最大2个


## metric 格式

```json
{"name": "销售额", "aggr": "SUM"}                         // SUM

{"name": "订单编码", "aggr": "CNT_DISTINCT", "alias": "订单数"}  // 指定聚合

{"name": "桌单价"}                           // 自定义字段如果在formula的计算公式中已聚合的情况下，就不再需要 aggr了
```

聚合方式: `SUM` / `AVG` / `MAX` / `MIN` / `CNT` / `CNT_DISTINCT`

## filters 格式

```json
// 维度筛选（WHERE）
{"name": "城市", "op": "IN", "value": ["上海市", "南京市"]}

// 日期范围
{"name": "营业日期", "op": "BT", "value": ["2026-01-01", "2026-02-28"]}

// 度量筛选（HAVING，聚合后过滤）
{"name": "销售额", "op": "GT", "value": ["1000000"]}
```

## sorting 格式

```json
// 单字段排序
[{"name": "销售额", "order": "DESC"}]
[{"name": "门店编号", "order": "ASC"}]

// 多字段排序
[{"name": "城市", "order": "ASC"}, {"name": "销售额", "order": "DESC"}]
```

## 字段名格式

`row`、`column`、`metric.name`、`filters.name`、`sorting.name`、`color_by.name`、`size_by.name` 都用字段名。

**普通字段** — 直接写平台上的字段名：
```json
"row": ["城市"]
"metric": [{"name": "销售额", "aggr": "SUM"}]
"filters": [{"name": "门店名称", "op": "EQ", "value": ["某门店"]}]
```

**日期子字段** — `字段名(粒度)`，自动按时间维度拆分：

| 写法 | 效果 | 示例输出 |
|------|------|----------|
| `"营业日期(年)"` | 按年汇总 | 2025 |
| `"营业日期(季度)"` | 按季度汇总 | 2025年第4季度 |
| `"营业日期(月)"` | 按月汇总 | 2025-11 |
| `"营业日期(周)"` | 按周汇总 | 2025年第44周 |
| `"营业日期(星期)"` | 按星期几汇总 | 星期六 |

```json
"row": ["营业日期(月)"]   // 按月看趋势
"filters": [{"name": "营业日期(年)", "op": "IN", "value": ["2026"]}]  // 筛选2026年
```

## filterType 速查

| 类型 | 含义 | 示例 |
|------|------|------|
| `EQ` | 等于 | `["A品牌"]` |
| `NE` | 不等于 | `["闭店"]` |
| `IN` | 在列表中 | `["上海市","北京市"]` |
| `NI` | 不在列表中 (Not In) | `["闭店","未开业"]` |
| `BT` | 范围 | `["2025-01-01","2025-12-31"]` |
| `GT` | 大于 | `["100"]` |
| `GE` | 大于等于 | `["100"]` |
| `LT` | 小于 | `["100"]` |
| `LE` | 小于等于 | `["100"]` |
| `CONTAINS` | 包含 | `["万达"]` |
| `IS_NULL` | 为空 | `[]` |
| `NOT_NULL` | 不为空 | `[]` |

## 建卡示例

**示例0：汇总值（row 为空） — 拿总计不拆维度**
```bash
# row=[] 不分组，直接返回汇总值，不会截断
$SCRIPT create-and-get '{"name":"汇总","ds_id":"<dataset_id>","chart_type":"BASIC_COLUMN","pg_id":"<page_id>","row":[],"metric":[{"name":"销售额","aggr":"SUM"}],"filters":[{"name":"日结日期","op":"BT","value":["2026-03-16","2026-03-22"]}]}'
# 输出: 销售额: 313230258.42
# 卡片保留供复核，用户要求清理时再 delete-cards
```

**示例1：指标卡 — 2月消费会员数**
```bash
$SCRIPT create-and-get '{"name":"2月消费会员数","ds_id":"<dataset_id>","chart_type":"SINGLE_VALUE","pg_id":"页面ID","metric":[{"name":"会员id","aggr":"CNT_DISTINCT"}],"filters":[{"name":"营业日期","op":"BT","value":["2026-02-01","2026-02-28"]}]}'
# 输出: 会员id: 252335
```

**示例2：柱状图 — 各城市销售额（按营业额降序）**
```bash
$SCRIPT create-and-get '{"name":"各城市销售额","ds_id":"<dataset_id>","chart_type":"BASIC_COLUMN","pg_id":"页面ID","row":["城市"],"metric":[{"name":"销售额","aggr":"SUM"}],"filters":[{"name":"营业日期","op":"BT","value":["2026-01-01","2026-02-28"]}],"sorting":[{"name":"销售额","order":"DESC"}]}'
# 输出: 销售额: ['2323360', '8483271', ...]  维度: ['南京市', '南通市', ...]
```

**示例3：交叉表 — 各城市×月份营业额（按城市+月份排序）**
```bash
$SCRIPT create-and-get '{"name":"城市×月份营业额","ds_id":"<dataset_id>","chart_type":"PIVOT_TABLE","pg_id":"页面ID","row":["城市"],"column":["营业日期(月)"],"metric":[{"name":"销售额","aggr":"SUM"}],"filters":[{"name":"营业日期","op":"BT","value":["2025-01-01","2026-02-28"]}],"sorting":[{"name":"城市","order":"ASC"},{"name":"营业日期(月)","order":"ASC"}]}'
# 输出: [城市 ,月份 ,销售额].....['上海','2025-01','123232323'],['上海','2025-02','1230232333'].....
# 排序: 先按城市名正序，再按月份正序
```

**示例4：多条折线图 — 各渠道月趋势**
```bash
$SCRIPT create-and-get '{"name":"渠道月趋势","ds_id":"<dataset_id>","chart_type":"MULTI_LINE","pg_id":"页面ID","row":["营业日期(月)"],"column":["渠道类型"],"metric":[{"name":"销售额","aggr":"SUM"}],"filters":[{"name":"营业日期","op":"BT","value":["2025-01-01","2026-02-28"]}]}'
```

**示例5：组合图（柱+线） — 营业额柱状+消费人数折线**
```bash
$SCRIPT create-and-get '{"name":"营业额与客户数","ds_id":"<dataset_id>","chart_type":"STACKED_COLUMN_WITH_LINE","pg_id":"页面ID","row":["营业日期(月)"],"column":["渠道类型"],"metric":[{"name":"销售额","aggr":"SUM"}],"metric_additional":[{"name":"客户数","aggr":"SUM"}],"filters":[{"name":"营业日期","op":"BT","value":["2026-01-01","2026-02-28"]}]}'
```

**示例6：气泡图 — 各门店营业额vs实收金额（按城市着色，气泡大小=客户数）**
```bash
$SCRIPT create-and-get '{"name":"门店气泡图","ds_id":"<dataset_id>","chart_type":"BASIC_BUBBLE","pg_id":"页面ID","row":["城市","门店"],"metric":[{"name":"销售额","aggr":"SUM"},{"name":"实收金额","aggr":"SUM"}],"size_by":[{"name":"客户数","aggr":"SUM"}],"color_by":[{"name":"城市"}],"filters":[{"name":"营业日期","op":"BT","value":["2026-01-01","2026-02-28"]}]}'
# row=维度标签, metric[0]=x, metric[1]=y, color_by=颜色分组, size_by=气泡大小
```

## 完整工作流示例

**需求：做一张「2026年2月各城市外卖销售类型销售额 TOP10」交叉表**

```bash
# Step 1: 通过表id查字段，确认可用字段
$SCRIPT get-columns <dataset_id>
# → 确认: 城市(DIM), 销售额(METRIC), 渠道类型(DIM), 营业日期(DATE)

# Step 2: 查枚举值（因为用了 IN/EQ 筛选，必须查）
$SCRIPT search-values <dataset_id> --name "渠道类型" --search "外卖"
# → 确认值是 "外卖"

# Step 3: 建交叉表，自动取数
$SCRIPT create-and-get '{"name":"2月外卖各城市销售额","ds_id":"<dataset_id>","chart_type":"PIVOT_TABLE","pg_id":"<page_id>","row":["城市"],"column":["渠道类型"],"metric":[{"name":"销售额","aggr":"SUM"}],"filters":[{"name":"营业日期","op":"BT","value":["2026-02-01","2026-02-28"]},{"name":"渠道类型","op":"EQ","value":["外卖"]}],"sorting":[{"name":"销售额","order":"DESC"}]}'
```

> 💡 如果只做日期或数值筛选（无分类筛选），跳过 Step 2，两步搞定。



## guancli 补充命令（只读探索 + 省 token）

guancli 是观远官方 CLI（`npm install -g @guandata/guancli`），与 guandata.py **互补**：
- **guandata.py** → 建卡、取数、删卡、发布页面（写操作）
- **guancli** → 搜索、探索、ETL/指标/任务/表单（读操作 + 表单CRUD）

**全局 flag**：
- `--brief` — 省 token 模式（输出缩减 50%+），探索阶段必用
- `-f csv` / `-f json` / `-f table` — 切换输出格式
- `--raw` — 原始 JSON（调试用）

### 数据集探索（替代 list-datasets）

```bash
# 搜索数据集（比 list-datasets 全量拉取快得多）
guancli ds search "会员"
guancli ds search "会员" --brief        # 省 token

# 数据集目录树
guancli ds tree
guancli ds tree --brief

# 数据集详情（字段列表 + 元信息）
guancli ds get <ds_id>
guancli ds get <ds_id> --brief          # 1894 字符 vs 完整 7468 字符

# 预览数据（自动精简列，干净表格）
guancli ds preview <ds_id> --limit 10
guancli ds preview <ds_id> --limit 10 -f csv   # CSV 格式
```

### ETL 探索（guandata.py 无此能力）

```bash
# 搜索 ETL
guancli etl search "会员"
guancli etl search "会员" --brief

# ETL 目录树
guancli etl tree

# ETL 详情（节点列表、SQL、血缘）
guancli etl get <etl_id>
guancli etl get <etl_id> --brief        # 省略 Malloy/血缘/公式细节

# 预览 ETL 节点数据
guancli etl preview <etl_id> --node <node_id> --limit 10
```

### 指标平台（guandata.py 无此能力）

```bash
# 搜索指标
guancli metric search "营业额"

# 指标目录树
guancli metric tree

# 指标详情
guancli metric get <metric_id>

# 查询指标数据
guancli metric query <metric_id>
```

### 指标归因分析（guandata.py 无此能力）

```bash
# 搜索指标树
guancli metric_attribution search "营业额"

# 指标树详情
guancli metric_attribution get <tree_id>

# 查询贡献数据
guancli metric_attribution query <tree_id>
```

### 任务监控（guandata.py 无此能力）

```bash
# 查看运行中任务
guancli task running

# 任务历史
guancli task history

# 任务详情
guancli task get <task_id>
guancli task detail <task_id>
```

### 页面 & 卡片探索

```bash
# 搜索页面（替代 list-pages 全量拉取）
guancli page search "门店"

# 页面详情（卡片列表 + 布局）
guancli page get <pg_id>
guancli page get <pg_id> --brief

# 卡片元信息（数据集、类型、筛选条件）
guancli card get <card_id>

# 预览卡片数据
guancli card preview <card_id>
```

### 表单填报 CRUD

```bash
# 列出表单
guancli form list
guancli form list --tree              # 显示目录结构

# 查看表单字段结构
guancli form schema <form_id>

# 查询表单数据
guancli form query <form_id>
guancli form query <form_id> -f csv   # CSV 格式

# 插入数据
guancli form add <form_id> '{"字段1":"值1","字段2":"值2"}'

# 更新数据
guancli form update <form_id> <record_id> '{"字段1":"新值"}'

# 删除数据
guancli form delete <form_id> <record_id>
```

### 通用 API 调用（万能兜底）

```bash
# GET 请求
guancli fetch GET /api/health

# POST 请求
guancli fetch POST /api/resource '{"key":"value"}'

# stdin 传大 body
echo '{"large":"json"}' | guancli fetch POST /api/some-endpoint --stdin

# 上传文件
guancli fetch POST /api/import/upload-files/CSV --upload file0=/path/to/data.csv
```

### 工具选择决策表

| 场景 | 用什么 | 原因 |
|---|---|---|
| 建卡+取数、数据分析 | `guandata.py create-and-get` | guancli 不支持写操作 |
| 删卡/发布页面 | `guandata.py delete-cards / release-page` | 同上 |
| 搜索数据集/页面/ETL | `guancli xx search` | 比全量拉取快，省 token |
| 查 ETL 结构/SQL/血缘 | `guancli etl get` | guandata.py 无此能力 |
| 查指标平台 | `guancli metric` | guandata.py 无此能力 |
| 任务排查 | `guancli task` | guandata.py 无此能力 |
| 快速预览数据 | `guancli ds preview` | 自动精简列，输出干净 |
| 表单 CRUD | `guancli form` | guandata.py 无此能力 |
| 调未封装的 API | `guancli fetch` | 万能兜底 |

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

## B-4. 第二步：构造 ETL payload

### B-4.1 反推 schema

```bash
guancli --raw etl get <旧ETL_id> > old.json
jq '.data.actions[] | {id,name,type,sources,inputDsId,outputDsName,parentDirId,sql,dataSource,relativeFieldAlias}' old.json
```

### B-4.2 最小骨架：3 节点

```text
INPUT_DATASET → SQL_SCRIPT → OUTPUT_DATASET
```

### B-4.3 完整 payload 模板

```json
{
  "name": "dim_store_master_v2",
  "parentDirId": "<etl_dir_id>",
  "actions": [
    {
      "id": "id_1778227328970_1",
      "name": "input_source",
      "type": "INPUT_DATASET",
      "sources": [],
      "inputDsId": "<source_ds_id>"
    },
    {
      "id": "id_1778227328970_2",
      "name": "transform",
      "type": "SQL_SCRIPT",
      "sources": ["id_1778227328970_1"],
      "sql": "SELECT DISTINCT\n  `store_code` AS `store_id`,\n  `store_name` AS `store_name`\nFROM input1\nWHERE `store_code` IS NOT NULL;"
    },
    {
      "id": "id_1778227328970_3",
      "name": "dim_store_master_v2",
      "type": "OUTPUT_DATASET",
      "sources": ["id_1778227328970_2"],
      "outputDsName": "dim_store_master_v2",
      "parentDirId": "<ds_dir_id>",
      "dataSource": {
        "created": false,
        "name": "dim_store_master_v2",
        "parentDirName": "warehouse_v2",
        "parentDirId": "<ds_dir_id>",
        "dirPath": [
          { "dirId": "<root_dir_id>", "dirName": "Root" },
          { "dirId": "<parent_ds_dir_id>", "dirName": "ParentDB" },
          { "dirId": "<ds_dir_id>", "dirName": "warehouse_v2" }
        ]
      }
    }
  ]
}
```

### B-4.4 节点字段速查（含踩坑标注）

| 字段 | INPUT_DATASET | SQL_SCRIPT | OUTPUT_DATASET |
|---|---|---|---|
| `id` | 必填 | 必填 | 必填 |
| `type` | `"INPUT_DATASET"` | `"SQL_SCRIPT"` | `"OUTPUT_DATASET"` |
| `sources` | `[]` | 上游节点 id 数组 | 上游节点 id 数组 |
| `inputDsId` | **必填** | null | null |
| `sql` | null | **必填**，字段名是 `sql` ⚠️ **不是 `sqlScript`** | null |
| `outputDsName` | null | null | **必填** |
| `parentDirId` | null | null | **数据集目录 id** |
| `dataSource` | null | null | 必填，含 dirPath、parentDirId |
| `relativeFieldAlias` | **关键**：fieldHash → 字段名映射 | null | null |
| `displayType` | DATAFLOW / CLICKHOUSE / MYSQL / FEISHU_SPREADSHEET | null | DATAFLOW |
| `cascadeUpdateEnabled` | true/false | null | null |

⚠️ **`sql` vs `sqlScript` 字段名最大坑**：写错时 direct-save 不报错（接受任意字段），但 SQL 不生效——BI 落库后看到的还是老 SQL。这个 bug 极隐蔽，必须用正确字段名 `sql`。

### B-4.5 SQL 节点的位置式 input 索引（必须警惕）

```text
SQL 里 input1 = sources[0] 对应的 INPUT_DATASET
SQL 里 input2 = sources[1] 对应的 INPUT_DATASET
... (位置式索引，不是按 ID)
```

**关键陷阱**：删除某个 INPUT_DATASET 节点（去循环依赖时常见），其余 input 索引会**自动往前补**：原 input3 变成 input2，原 input5 变成 input3。**改 input 节点必须同时改 SQL！**

### B-4.6 已知支持的节点类型

```text
INPUT_DATASET     上游输入
SQL_SCRIPT        Spark SQL（推荐）
OUTPUT_DATASET    输出数据集
FILTER_ROWS       行筛选（看 .filterConditions）
JOIN_DATA         多表 join（看 .dataFusion）
GROUP_BY          分组聚合（看 .zoneData.metric）
CALCULATOR        计算字段（看 .formulas[].expr）
SELECT_COLUMNS    选列
APPEND_ROWS       纵向合并 / UNION
```

**实战推荐**：把所有非 SQL 节点全部编译成单条 SQL_SCRIPT，三节点结构最简单可控。

### B-4.7 dataFlowId 控制 create vs update

```bash
# 新建：payload 顶层不带 dataFlowId
guancli fetch POST /api/etl/direct-save --stdin < payload.json
# => {"result":"ok","response":{"success":true,"dataFlowId":"<new_id>"}}

# 更新：payload 顶层加 "dataFlowId":"<existing_id>"
guancli fetch POST /api/etl/direct-save --stdin < payload-updated.json
```

create 和 update 是**同一个接口**。SQL 改错直接改 payload 加 `dataFlowId` 再 POST，**不要**删了重建。

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

# Step 3：根据 error 类型对照 B-9 修复手册
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

## B-8. 复用模板：从扫描到落表

```bash
# === 阶段一：治理扫描 ===
PARENT_DIR="<父ETL目录id>"
guancli etl search '' -d $PARENT_DIR --raw > etl-list.json

mkdir -p raw
jq -r '.response.contents[].dataFlowId' etl-list.json | while read id; do
  guancli --raw etl get $id > raw/$id.json
done

node analyze.mjs raw/ > analysis.json
# 人工 review → migration-plan.json

# === 阶段二：建目录 ===
NEW_DIR_NAME="warehouse_v2"
PARENT_ETL_DIR="<父ETL目录id>"
PARENT_DS_DIR="<父数据集目录id>"

ETL_DIR=$(guancli fetch POST /api/directory \
  "{\"name\":\"$NEW_DIR_NAME\",\"parentDirId\":\"$PARENT_ETL_DIR\",\"dirType\":\"ETL\"}" \
  | jq -r '.response.dirId')

DS_DIR=$(guancli fetch POST /api/directory \
  "{\"name\":\"$NEW_DIR_NAME\",\"parentDirId\":\"$PARENT_DS_DIR\",\"dirType\":\"DATA_SET\"}" \
  | jq -r '.response.dirId')

# === 阶段三：写入 + 执行（每张 v2 表循环） ===
TARGET_NAME="<输出表名>"
DFID=$(guancli fetch POST /api/etl/direct-save --stdin < payload.json \
  | jq -r '.response.dataFlowId')

# 节点预览（成功再 execute）
NODE_OUT=$(guancli etl get $DFID --raw \
  | jq -r '.data.actions[] | select(.type=="OUTPUT_DATASET") | .id')
guancli etl preview $DFID $NODE_OUT --limit 5 --timeout 120

TASK=$(guancli fetch POST /api/etl/execute "{\"dataFlowId\":\"$DFID\"}" \
  | jq -r '.response.taskId')

until [ "$(guancli task get $TASK --raw | jq -r '.response.status')" != "RUNNING" ]; do
  sleep 10
done

# 失败定位
guancli fetch GET "/api/task/$TASK" | jq '.response.result.error'

# 成功验证
guancli ds search $TARGET_NAME --raw \
  | jq '.response.contents[0] | {dsId,name,rowCount,colCount}'

# === 阶段四：删除旧链路（确认 v2 对账无误后） ===
guancli fetch DELETE /api/data-source/<v1_dsId>
guancli fetch DELETE /api/etl/<v1_etlId>
```

---

## B-9. 报错修复手册（10 类真坑）

### 坑 1：`请输入ETL名称` / `保存路径无效`

```bash
$ printf '{}' | guancli fetch POST /api/etl/direct-save --stdin
=> 请输入ETL名称
$ printf '{"name":"x","actions":[]}' | guancli fetch POST /api/etl/direct-save --stdin
=> 保存路径无效
```

**根因**：顶层 `parentDirId` 缺失或填错（必须是 `dirType=ETL` 那棵树的 id）。

**修复**：先建好 ETL 目录拿到 id，写到 payload 顶层。

---

### 坑 2：保存成功但 execute 数据为空（上游运行权限不足）

**现象**：写入返回 `{success:true}`，execute 也返回 ok，但输出表始终为空。

**根因**：`INPUT_DATASET.inputDsId` 当前账号只有"读权限"没有"运行权限"。

**修复**：
1. 换一个账号确实能运行的输入表
2. 写自包含 ETL：`SELECT explode(sequence(...))` 或 `VALUES(...)` 直接生成数据

---

### 坑 3：上游字段名带隐藏 `\n`（含升级版）

**现象**：列名显示成两行，但 SQL 引用永远查不到。

**修复（基础版）**：编译 SQL 时 `` `带换行的原字段名` AS `干净别名` ``，下游用别名。

**升级版坑**：v2 SQL 里字段名实际是 `` `field\n  ` ``（换行 + 2 空格），但 fieldAlias 是 `` `field\n` ``（仅换行）——**两边不一致**。BI 老引擎容错跑得通，重生节点 ID 后挂了。

**修复**：把 SQL 里 `` `field\n  ` `` 改成 `` `field\n` `` 对齐 fieldAlias。

---

### 坑 4：`<> NULL` 把所有行过滤光

**现象**：旧"非空筛选"节点编译成 `WHERE field <> NULL`，输出 0 行。

**根因**：SQL 标准里 `<> NULL` 永远是 `unknown`。

**修复**：编译器 `FILTER_ROWS` → SQL 强制规则：
- "非空" → `IS NOT NULL`
- "为空" → `IS NULL`

---

### 坑 5：字段引用与 relativeFieldAlias 错位

**现象**：SQL 引用 `t.id`，但 INPUT_DATASET 在 `relativeFieldAlias` 里映射成了 `coupon_id`。`cannot resolve column`。

**修复**：编译 payload 时**必须读 INPUT_DATASET 的 `relativeFieldAlias`**，把 SQL 里所有原字段名替换成节点级别名。

---

### 坑 6：CTE 内 `;` + 中文注释

**现象**：

```text
[PARSE_SYNTAX_ERROR] Syntax error at or near ';'.(line 196, pos 24)
== SQL ==
... FROM n_id_xxx;  -- 请将这里替换为您的源数据表名 ...
```

**修复**：

```js
fixed = sql.replace(/(\s+FROM\s+n_id_\w+);(\s*--[^\n]*)?/g, "$1");
fixed = fixed.replace(/;\s*--[^\n]*/g, "");
```

---

### 坑 7：FROM/JOIN 同表别名同名

**现象**：

```sql
FROM n_id_aaa s1
  LEFT JOIN n_id_aaa s1 ON s2.`field_a` = s1.`field_a`
-- 错误: AMBIGUOUS_REFERENCE Reference s1.`field_a` is ambiguous
```

**修复**：把 FROM 别名改成 s2，对齐 ON 子句：

```sql
FROM n_id_bbb s2
LEFT JOIN n_id_aaa s1 ON s2.`field_a` = s1.`field_a`
```

---

### 坑 8：FROM 表错位（自连而非 JOIN 不同表）

**现象**：

```sql
FROM n_id_aaa s1
  LEFT JOIN n_id_aaa s1 ON s2.`key` = s1.`key`
-- 错误: s2.`some_field` 找不到
```

但 SELECT 用 `s2.specific_field` —— 说明 v2 SQL 写错表。

**修复**：

```sql
FROM n_id_aaa s1
LEFT JOIN n_id_ccc s2 ON s2.`key` = s1.`key`
```

---

### 坑 9：UNION 列数不匹配

**现象**：

```text
[NUM_COLUMNS_MISMATCH] UNION can only be performed on inputs with the same number of columns,
but the first input has 35 columns and the second input has 36 columns.
```

**根因**：BI 老引擎对 UNION 列差异自动补 NULL，重生节点 ID 后严格化。

**修复（彻底）**：手工把两侧 SELECT 列表对齐，缺的字段用 `NULL AS xxx` 补。

---

### 坑 10：日期字段 vs 字符串字面量混淆

**现象**：

```sql
SELECT *, current_date() AS `today_field` FROM ...
WHERE `order_date` < 'today_field'   -- ❌ 字符串字面量，恒为 false
```

**修复**：

```sql
WHERE `order_date` = date_sub(current_date(), 1)
```

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

## B-11. v2 → v3 批量改造 SDK

### B-11.1 SDK 核心 API

```js
// v3_sdk.mjs
export function transformV2ToV3({
  v2PayloadFile,    // 旧 payload 路径
  v3Name,           // 新 ETL 名
  removeInputs = [],// 要移除的 INPUT_DATASET id（去循环依赖）
  newSql = null,    // 重写 SQL（null = 沿用原 SQL）
  inputMap = {},    // v1/v2 dsId → v3 dsId 替换
  description = "",
}) { ... }

export function pushAndExecute(v3Name, payloadPath) {
  // POST /api/etl/direct-save → POST /api/etl/execute
}

export function checkStatus(v3Name) {
  // guancli etl search → parse Status
}
```

### B-11.2 transformV2ToV3 内部 7 步

```text
1. 读 v2 payload JSON
2. 过滤掉 removeInputs 列表中的 INPUT_DATASET 节点
3. 替换 inputMap 中的 inputDsId（v1/v2 → v3）
4. 重新生成所有节点 ID（避免冲突），同步重映射 sources 数组
5. 改 OUTPUT_DATASET 的 outputDsName + parentDirId
6. 如有 newSql，覆盖 SQL_SCRIPT 节点的 `sql` 字段
7. 顶层换 name + parentDirId + dirPath + description
   + 更新 meta = JSON.stringify(actions)
```

### B-11.3 关键陷阱（必读）

```text
- SQL 字段名是 `sql`，不是 `sqlScript`！（最大坑）
- 重排节点 ID 时 sources 数组要同步映射
- 删除 INPUT_DATASET 后剩余 input 索引重排（input1..N），SQL 可能要同步改
- meta 字段也要更新（meta = JSON.stringify(actions)）
- description 改了不影响行为，但便于追溯
```

### B-11.4 时间窗口缩减实战

v2 是近 3 个月窗口（千万级），v3 改昨日窗口（验证沙盒）：

```js
let sql = v2_sql.replace(
  /add_months\(concat\(substr\(current_date\(\)\s*,1,7\),'-01'\),-3\)/g,
  "date_sub(current_date(), 1)",
);
sql = sql.replace(
  /WHERE\s+`order_date`\s*<\s*'today'/g,
  "WHERE `order_date` = date_sub(current_date(), 1)",
);
```

**结果**：v3 跑出 ~50 万行（与业务预期 60 万级别误差 8%）。

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

> 💡 **30+ 张表跨多日的工程必须走 ExecPlan**：不要靠零散 todo + 群消息 + 临时 markdown 来追踪进度。直接走 **B-17.11** 的 ExecPlan 工作法——四个活文档章节（Progress / Surprises & Discoveries / Decision Log / Outcomes & Retrospective）能把治理判断、循环依赖拆法、字段隐藏换行这类"踩坑—修复"轨迹完整落到一份自包含文档里，下一个接手的人不用问任何上下文就能继续。

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
- ❌ 不要为了"清理"删旧 ETL —— 并行做新链路、对账确认后再处理旧表。
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

## B-15. 实战 ID 速查（马甲业务侧）

| 名称 | ID | 说明 |
|---|---|---|
| 旧 ETL 父目录（v1 会员数据库） | `<v1_etl_dir_id>` | v1 ETL 目录 |
| 旧数据集父目录（马甲的会员数据库） | `<v1_ds_dir_id>` | v1 数据集目录 |
| **v2 ETL 目录**（会员数仓_v2） | `<v2_etl_dir_id>` | 新建 ETL 落这里 |
| **v2 数据集目录**（会员数仓_v2） | `<v2_ds_dir_id>` | OUTPUT_DATASET 落这里 |
| 数据集树根目录 | `<ds_root_id>` | dirPath 第一层 |
| ETL 树根目录 | `<etl_root_id>` | – |
| PoC ETL（dim_store_name_map_v2） | `<poc_etl_id>` | 第一个跑通的最小 ETL |
| PoC 输出数据集 | `<poc_output_ds_id>` | 同上输出 |
| PoC 输入数据集（一个编号多个名字） | `<poc_input_ds_id>` | 593 行小表，权限可运行 |

如果上面 ID 失效（被删/改名），用以下命令重新拿：

```bash
guancli fetch GET /api/directory/ETL/authorized-tree | jq '.response | .. | objects | select(.name=="会员数仓_v2")'
guancli fetch GET /api/directory/DATA_SET/authorized-tree | jq '.response | .. | objects | select(.name=="会员数仓_v2")'
```

---

## B-16. 触发场景示例

**治理类：**
- "帮我扫一遍我们 BI 的 ETL，看哪些可以删 / 合并 / 重建"
- "ETL 之间有没有循环依赖"
- "这些字段还在被使用吗"
- "怎么判断一个 ETL 应该归哪一层"
- "我们 BI 的字段冗余情况怎么样"

**写入类：**
- "帮我在观远 BI 上新建一个 ETL"
- "我有一份 SQL，想做成 ETL 跑出来"
- "guancli 怎么 POST /api/etl/direct-save"
- "Guandata 怎么批量重建 ETL"
- "观远 BI 新建目录的 API 是什么"

**报错类：**
- "direct-save 报错 保存路径无效 / 请输入ETL名称"
- "ETL 保存了但 execute 没数据 / 输出 0 行"
- "ETL 字段引用报 cannot resolve column"
- "task FAILED 怎么看真实错误"
- "ETL 删除失败 输出数据集已存在"
- "UNION columns mismatch 怎么修"
- "Spark SQL syntax error at ;"

---

## B-17. 全链路重写方法论（CTO 张进）

> 这套是观远 CTO 张进的 SmartETL 完整改写经验。它跟 B-2 治理扫描互补：B-2 解决"有哪些 ETL 该治理"，B-17 解决"具体重写一条链路时怎么做才不留尾巴"。
>
> **核心区别**：B-17 强调**全链路追到原始源**，不接受只重写最终 ADS。如果用户说"把这条链路重新做一遍" / "替换数据源" / "做副本页验收"，必走 B-17。

### B-17.1 何时用 B-17

- 用户明确要把已有 SmartETL **完整**改写成 SQL 版 SmartETL
- 目标不仅是重建数据集，还包括**页面副本替换**和**卡片级验收**
- 需要把旧 ETL 当作只读参考，重新梳理页面、数据集、ETL DAG、源数据
- 需要判断差异到底来自页面配置、执行快照时点、还是某一层数据链
- 需要处理"上游空快照，但链路定义仍要重写完"的场景

如果用户只是新建一个 SQL 节点数据集，不涉及旧链迁移、页面替换和链路审计 → 走 B-3 ~ B-9，不用 B-17。

### B-17.2 4 件交付（缺一不可）

交付不是"SQL 能跑"这么简单，必须同时满足：

1. 旧链所有参与本次范围的 ETL 加工都被新 SQL 链替代
2. 新链只依赖原始表/表单/文件/系统内置表或本轮新 SQL 中间层，**不再依赖旧 ETL 数据集**
3. 新数据集能挂到页面副本上，且**卡片结果可与原页比对**
4. 对无法验收的部分，必须把阻塞点上推到真正的空源或权限/平台问题，**不能含糊写成"已完成"**

### B-17.3 8 条硬规则

- ✅ **全链路重写**：不能只改最终 ADS，必须继续上追，直到原始源
- ✅ **旧资产只读**：旧文档、旧 ETL、旧数据集只作为参考，不作为本轮交付对象
- ✅ **新结果放新目录**：用子目录隔离新旧对象，正式对象名保持业务原名
- ✅ **新 SmartETL 只允许 SQL 节点**：不要混回可视化清洗节点（FILTER_ROWS、JOIN_DATA、CALCULATOR 等）
- ✅ **SQL 输入只引用 input1/input2**：不要赌平台按对象名解析。引用顺序对应 `sources[]` 数组顺序
- ✅ **双层验收**：结构验收（字段、行列规模、依赖关系、是否 FINISHED）+ 数值验收（与原数据集或页面卡片对齐）
- ✅ **空快照不是"完成"**：原始源为空时只能写"新链已重写完成，但数值验收硬阻塞"
- ✅ **页面验收只看副本页**：不直接改原页

### B-17.4 标准工作流（5 步）

#### Step 1. 锁定范围和命名

明确：
- 正式页面、正式数据集、排除范围
- 本轮新 ETL 目录和新数据集目录
- 建 ExecPlan，写清：正式范围 / 只读历史 / 命名规则 / 暂停条件 / 验收标准

#### Step 2. 从页面往下重新拉血缘

**不要从 ETL 往上推**。从页面卡片清单重新盘点：
- 卡片绑定的数据集
- selector / 参数卡
- 页面默认筛选器
- 页面运行时 payload

对每个正式数据集，拉数据集详情和 ETL DAG。标注每个输入是：
- 原始源
- 旧 ETL 数据集
- 系统表
- 当前页面不在范围内的旁路输入

#### Step 3. 严格判断"是否已经到原始源"

判断口径很严格：

- ✅ 表单、Excel、ADLS、数据库物理表、系统内置时间表 → **可以视为源**
- ❌ 输入是 `DATAFLOW` 且背后还有 ETL → **没到底，必须继续追**
- ❌ 不要因为名字叫 `清洗_*`、`ods_*`、`report_*` 就误判成源

#### Step 4. 重建顺序：上游先，下游后

按"最上游老 ETL 先重写，再往下游收口"推进：

```text
1. 先重写被多个下游复用的清洗层 / 中间层
2. 再重写共享中间 ADS
3. 最后重跑最终消费 ADS
4. 最后再做页面副本切换
```

避免反复改下游输入。

#### Step 5. 每个对象的重建模板

每个待重建对象固定记录：

- 原 ETL 定义文件
- 目标输出 selector
- 目标输出名称
- 结构对齐参考的 schema 数据集
- 需要替换成"本轮新数据集"的输入 override

**自动从 ETL JSON 编译 SQL 时的特殊坑**：
- `split(col, ']')[1]` 这类**数组下标不能误识别成字段引用**
- 分组维度重名时要去重
- 空公式列表不能生成非法 `select`
- 列名里如果带**换行或特殊字符**，最终 SQL 拼接不能破坏原标识符

### B-17.5 三层验收方法

#### 数据集验收

每新建一层至少检查：
- 新 ETL 是否 `FINISHED`
- 新数据集是否**真实物化**（不是只保存了草稿 ETL）
- 行数、列数是否与旧对象一致
- 关键字段名是否一致

**结构不一致先修这一层，不要急着看页面。**

结构一致但页面不一致，优先检查：
- 上下游执行时点
- 页面筛选是否真正作用到卡片
- selector 是否还绑定旧 ds

#### 副本页验收

**只换副本页**，原页保持不动。副本页先替换图表卡，再检查 selector 卡。

⚠️ **不要默认相信页面首屏渲染**——副本页常出现两类假差异：
- selector 还挂旧数据集
- 页面默认时间筛选器没真正传到卡片

#### 卡片级验收法（推荐）

```text
1. 先抓原页运行时 payload
2. 把副本卡切到新数据集
3. 用原页真实 payload 去重放副本卡片
4. 这样可以把"页面联动问题"和"数据链问题"拆开
```

### B-17.6 差异追踪 5 步法

当页面只剩 1~2 张卡不一致时，**不要盲改 SQL**，按下面顺序压缩范围：

```text
1. 先对比新旧最终数据集的键集合
2. 再对比有差异的字段（不要一次看全表）
3. 把差异收缩到少量记录
4. 沿链路往上追，看差异最早出现在哪一层
5. 对该层再看：
   - SQL 定义是否不同
   - 执行时间是否落后于上游
```

**关键经验**：很多"SQL 错了"的假象，实际是因为新链吃到了**更早的快照**。如果定义相同但时点落后，先补跑最近一层上游，再补跑下游。

### B-17.7 空快照处理（不能写"已完成"）

如果上游是空的：

```text
1. 继续把链路定义完整重写到源头
2. 如平台允许，物化出新的空数据集
3. 在文档里明确写：
   - 根阻塞源是谁
   - 当前行列规模是多少
   - 哪些下游因此为空
4. 结论只能写成：
   "全链路 SQL 重写完成"
   "数值验收硬阻塞"

❌ 不能写成"已完成对齐"
```

### B-17.8 标准交付物清单

```text
output/<restart_tag>/
  ExecPlan.md              ← 范围、命名、暂停条件、验收标准
  modeling.md              ← 每个对象的建模决策、依赖关系、字段对齐
  evidence.md              ← 验收证据：行列数、键集合差异、卡片对比
  sql/<object_name>/       ← 每个对象的完整 SQL（可独立复跑）
  raw/                     ← ETL 保存前定义、执行结果、页面运行时 payload
```

### B-17.9 B-17 特有的常见坑

| 坑 | 表现 | 修复 |
|---|---|---|
| 把旧 `DATAFLOW` 当源头 | 只重写了半条链 | 严格按 B-17.3 判断"是否到原始源" |
| 只保存 ETL 没执行 | 误以为已经有新数据集 | 检查数据集是否物化、状态是否 FINISHED |
| 卡换了新 ds，selector 还在用旧 ds | 副本页假差异 | 卡片 + selector **都要换** |
| 时间筛选器没真正生效 | 直接拿页面数字做结论 | 抓原页 runtime payload 重放 |
| 看到少量差异就修 SQL | 没先检查执行时点 | 走 B-17.6 五步压缩 |
| 上游空快照时为了"有东西看"接受降级结果 | 文档写成"已完成对齐" | 必须按 B-17.7 写"硬阻塞" |

### B-17.10 完成标准（同时满足才能说"替换成功"）

- [x] 新链已追到原始源，不再依赖旧 ETL 数据集
- [x] 新 SmartETL 全部是 SQL 节点
- [x] 目标数据集已**真实物化**并运行成功
- [x] 页面副本已切到新数据集
- [x] 非阻塞范围内，**卡片级**结果与原页一致
- [x] 阻塞范围内，根因已被定位到真实空源或平台限制，**并明确留证**

### B-17.11 用 ExecPlan 管理重写工程（V1.2 新增）

> 借自 OpenAI Codex 的 ExecPlan 规范（[references/execplan-spec.md](references/execplan-spec.md)）。这套方法论的精髓：**让一个完全没上下文的新人，仅凭 ExecPlan 文档本身就能端到端继续这项重写工作。** SmartETL 全链路重写动辄跨多日、跨几十张表、涉及循环依赖拆解和副本页验收，正是 ExecPlan 的最佳适用场景。

**何时启用**：当本次重写工作满足以下任一条件，就开 ExecPlan：

- 涉及 5 张以上 ETL 重建
- 跨工作日（不能一次性收口）
- 包含循环依赖拆解（一动牵动多张表）
- 需要副本页 + 卡片级验收
- 上游存在空快照需要写明硬阻塞

**核心约束**（来自 ExecPlan 规范，照抄）：

- **自包含**：ExecPlan 不依赖任何外部上下文。读者只有当前工作树和这份文档。
- **活文档**：每个停顿点都要更新 Progress / Surprises / Decision Log，**不是事后补**。
- **可观察结果锚定**：验收标准写"卡片 X 在副本页用原 payload 重放，上海 2 月营业额与原页一致到分"，不写"代码层面满足某个定义"。这条跟 B-17.7"空快照不能写已完成对齐"是同一个原则的两种表达。

**SmartETL 改写专用 ExecPlan 骨架**（拿去直接填空，不用从通用模板自己映射）：

```text
# SmartETL 全链路重写 · <项目代号>

本 ExecPlan 按 references/execplan-spec.md 维护，必须保持 Progress /
Surprises & Discoveries / Decision Log / Outcomes & Retrospective 始终为最新。

## Purpose / Big Picture

这次重写完成后，<业务方> 在 <副本页 URL> 上看到的 <卡片清单> 全部由
新 SQL 链 v2 数据集驱动，不再依赖任何旧 ETL；<指定卡片> 与原页数值
一致，差异 < 1%；<空快照阻塞表> 已明确根因留证。

## 范围 / 命名 / 验收（B-17.1 锁定项）

- 正式范围：<页面 ID> · 数据集 N 个 · ETL N 个
- 旧资产只读：<旧目录路径>，绝不修改
- v2 落地：ETL 目录 <NEW_ETL_DIR_ID> · 数据集目录 <NEW_DS_DIR_ID>
- 命名：dwd_xxx_v2 / dws_xxx_v2 / dim_xxx_v2，业务原名挂在 description
- 暂停条件：上游空快照 / 平台限制 / 副本页卡片 > 3 张数值偏差
- 验收：B-17.10 六项必须全勾

## Progress

- [ ] (待时间戳) 治理扫描完成（依赖图 / 循环组 / 复杂度 → analysis.json）
- [ ] (待时间戳) 第一批 5 张 ETL 写入 + 节点预览通过
- [ ] (待时间戳) 第一批 execute 落表 + ds preview 验数
- [ ] (待时间戳) 副本页卡片切换 + payload 重放对账
- [ ] ...（每张表、每次预览、每次 execute、每张卡片对账都拆条目）

## Surprises & Discoveries

- Observation: <字段名带隐藏换行 / <> NULL 把行过滤光 / SQL 字段名是 sql 不是 sqlScript / ...>
  Evidence: <task error 摘录 / preview 0 行截图 / payload 片段>

## Decision Log

- Decision: 把"门店信息_v1"降回纯 DIM，经营状态字段迁到 dws_store_operating_status
  Rationale: 该表处于 5 张表循环依赖中心，不拆循环就一直反向依赖订单明细
  Date/Author: 2026-XX-XX / <你>

## Plan of Work

按 B-17.4 的 5 步推进：锁范围 → 拉血缘 → 判断到原始源 → 重建顺序（上游先）
→ 每对象重建模板。先写最上游清洗层 v2，再共享中间 ADS，再最终消费 ADS，
最后副本页切换。

## Concrete Steps

每张表的具体命令、payload 路径、dataFlowId、taskId、节点 OUTPUT id（带 _out 后缀）
落到这里，方便接手人原样复跑。

## Validation and Acceptance

- 数据集层：guancli ds get <dsId> --brief 看行列数与旧对象差异 < 1%
- 卡片层：抓原页 runtime payload，副本卡切新 ds 重放，<指定卡片> 数值一致
- 空快照层：明确写"全链路 SQL 重写完成，<根阻塞源> 数值验收硬阻塞"

## Outcomes & Retrospective

每完成一个里程碑写一段：完成什么 / 还剩什么 / 经验是什么。最终对账后写
完整复盘：v1→v2 对齐了 N 张，硬阻塞 M 张，下游看板已切流 K 张。
```

**四个活文档章节怎么用**（关键）：

| 章节 | 实战用法 |
|---|---|
| **Progress** | 每张表的 direct-save / preview / execute / 验数四步都拆条目，时间戳记到分钟。失败的也写"已完成：写入；剩余：execute 报权限错"。30+ 张表的 Progress 应该有 100+ 条。 |
| **Surprises & Discoveries** | B-17.6 差异追踪每一步的发现都进这里。字段隐藏换行、`<> NULL`、relativeFieldAlias 错位、上游运行权限不足、UNION 列差——每个都附 task error 原文摘录或 preview 截图作 evidence。 |
| **Decision Log** | "为什么把门店信息降回 DIM"、"为什么放弃 v2 直留改 SQL 重写"、"为什么 dws_finance_order 不拆"。判断比代码更值钱，写清 Rationale 让接手人理解，不用反复决策。 |
| **Outcomes & Retrospective** | 单张表跑通 = 一段小复盘；批次完成 = 中复盘；整套链路对账完 = 总复盘。"v1→v2 对齐了 27 张，硬阻塞 3 张（根因都是 ODS 空快照），下游看板切流 8 张" 这种结论必须落地。 |

**小工程别用 ExecPlan**：单张表新建、单条 SQL 修复、单个报错排查——直接照 B-1~B-9 走，开 ExecPlan 是负担。判断阈值看 B-17.11 顶部"何时启用"。

**深度参考**：完整 ExecPlan 规范见 [references/execplan-spec.md](references/execplan-spec.md)；OpenAI Codex 的 AGENTS.md 极简版调度规则见 [references/agents-rule.md](references/agents-rule.md)。

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

`data` 形态多变，常见 4 种：

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

## C-3. payload_json 取数排障（实战重灾区）

### C-3.1 三种"拿不到 payload"的细分

```text
1. runtime 里根本没有 payload_json     → 数据集没出 / 卡片配置错
2. payload_json 在，但没被正确解包      → 解析逻辑问题
3. payload_json 在，但字符串本身已损坏  → 数据链路截断
```

### C-3.2 最快判断方式

- 卡片里临时输出 `data/config/helpers` 摘要
- 抓 live 页 iframe 的 `window.PR_REPORT_CONTEXT`
- 抓浏览器里真实发出的 `/api/card/.../data` 请求和响应

### C-3.3 payload_json 硬规则

```javascript
JSON.parse(payload_json)  // 这才是最终判断标准
```

如果报：
- `Unterminated string`
- `Unexpected end of JSON input`
- 其他明显截断类错误

**优先判断为"数据链路把长字符串截断了"，不是图表 JS 自身问题。**

这种情况下：
- ❌ 不要继续堆兼容解析逻辑
- ❌ 不要再试图用更多递归去"猜"
- ✅ **优先改数据方案**

### C-3.4 超长字符串的实战结论

实战观察：live 页 runtime 明明有 `payload_json` 列，但里面的 JSON 字符串中途被截断 → `JSON.parse` 失败。

页面表现：
- 有 `report_date`
- 标题能出来
- 正文和 sections 都空
- 或直接显示 `Unable to resolve payload_json`

### C-3.5 推荐方案：拆列，不是整包 JSON

不要把整份报告压成一个超长 `payload_json` 字段过图表数据链路。**拆成多列**：

```text
report_date
send_window
key_insights_md
safety_intro_md
productivity_intro_md
service_intro_md
quality_intro_md
... 各 section 对应的明细列 / 明细子表
```

让前端直接读拆列后的字段，比 runtime 再 `JSON.parse(payload_json)` 稳得多。

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

## C-10. 触发场景示例

- "自定义图表脚本不执行"
- "payload_json 解析失败 / Unterminated string"
- "固定卡片在副本页错位"
- "复制页面后图表不出来"
- "切页后 overlay 没消失"
- "右侧导航被遮住点不动"
- "iframe 懒加载怎么处理"
- "renderChart 第一个参数到底是啥"

## C-11. 深度参考资料

遇到复杂的固定卡片 / overlay / 锚点导航问题时，读：

- [references/custom-chart-playbook.md](references/custom-chart-playbook.md) — 张进的完整自定义图表排障手册原文（含固定层与真实布局错位修正、右侧原生导航失效详细处理、elementFromPoint 实战、MutationObserver 死循环深入分析）
- [references/etl-rewrite-original.md](references/etl-rewrite-original.md) — 张进的 SmartETL 改写经验原文（B-17 章节就是基于它整合的，这里是未删减版）

---

## 📋 版本记录

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
