# V7 Page/Card 发布流水线 + guanvis-skill 银弹 + 数据集三态硬规则

> **来源**：2026-05-20/21 一次"连锁咖啡 BI 演示拍摄录制"全流程实战沉淀（90 天 / 1200 门店 / 80K 会员 / 20 张表 / 17 个 ETL / 6 个 HTML 应用化看板）。本文件把 6 类高频踩坑一次性写清，避免下一个看板项目再花 2-3 小时绕圈。
>
> **何时读这里**：从零搭 BI v7 实例上的 HTML 应用化看板 / 大批量创建 page+card / CSV 上传后 ETL 写出来数据全错 / Spark SQL 报错搞不清楚为什么。

---

## §1 **关键发现：v7 BI 实例必须用 guanvis-skill 银弹**

### §1.1 现象

直接用 `POST /api/page` + `POST /api/card` + `PUT /api/page/<id>` 这套 v6 思路在 v7 实例上**全部废**：

| 操作 | v7 行为 |
|---|---|
| `POST /api/card` (用 published pgId) | `60004 此操作只能在草稿页面执行` |
| `POST /api/card` (用 draft pgId = `pgId_draft`) | 返回 cdId 但 card 实际未持久化 |
| `PUT /api/page/<draft_id>` 加 meta.layout | layout 写入但 release 后 `cards: []` |
| `POST /api/page/<draft_id>/save '{}'` | 返回 success 但 cards 仍空 |
| `POST /api/page/<pgId>/release` | release 成功但 BI UI 上没有任何 card |

**根因**：v7 用了 draft cdId ↔ published cdId 的双 ID 映射机制，draft cdId 永远不会出现在 published page 里。手撸 API 走不通。

### §1.2 银弹：guancli ≥ 1.0.24 自带 guanvis-skill

```bash
npm install -g @guandata/guancli@latest
guancli install-skill        # 把 guanvis-skill 装到 ~/.agents/skills/
```

一次性获得能力：
- JS DSL：`createCard / createCustomChart / createSelector / createTextCard / createImageCard / createPage`
- `guanvis-skill init <dsId>` 自动生成 schema.js（含 fdId 完整映射）
- `guanvis-skill genid N` 生成合法 24 字符 alphanumeric ID
- `guanvis-skill publish .` **一键** 发布到 BI（内部走 transfer API，绕开 v7 draft/release 复杂度）

### §1.3 完整工程目录骨架（每个 page 一个子目录）

```text
my-dashboards/
├── 01-executive/
│   ├── schema.js              # guanvis-skill init <dsId> 自动生成
│   ├── card_01_html.js        # createCustomChart + DATA_GRID dataView
│   ├── page.js                # createPage + setParentDir + addFullWidthCard
│   └── charts/
│       ├── dashboard.html     # <div id="dash-root"></div> + ECharts loader
│       ├── dashboard.css      # 共享样式（推荐复用 1 份）
│       └── dashboard.js       # 业务渲染 (ECharts setOption)
├── 02-member/
│   └── ... (同上结构)
└── ...
```

### §1.4 一键发布 PoC（5 分钟）

```bash
# 1. 生成 ID
guanvis-skill genid 4         # page / sdk_card / dv1 / dv2

# 2. 写 4 个文件（schema.js / card_01_html.js / page.js / charts/dashboard.{html,css,js}）
# (内容见 §2)

# 3. 一键 publish
cd 01-executive
guanvis-skill publish .
# →  ✓ 01-executive (page)
#    ✓ ExecutiveDashboard (card)
#    ✓ ExecDataView (card)
#    Import finished: 3 succeeded
#    Page ID: <pgId>
#    Moved page <pgId> into dir <parentDirId>
```

打开 `https://<bi-host>/page/<pgId>` 看 BI UI 验证。

> **不要再手撸** `POST /api/card` + `PUT /api/page` + `POST /save` + `POST /release` 这条路径。guanvis-skill 内部走 transfer API（`POST /api/manual/template/transfer` 带 `needIdMapping=false`），所有 v7 draft/release 复杂度都隐藏起来了。

---

## §2 HTML 应用化看板（SDK 子类型）的最小骨架

### §2.1 `card_01_html.js`（custom chart + DATA_GRID dataView）

```javascript
// dataView 0: BI 自动取数喂给 renderChart(data) 的 data[0]
var dv1 = createCard(ChartType.DATA_GRID, "看板数据-日级")
    .setId("u56dfa1e159b55357ac0d6bc")   // guanvis-skill genid 生成
    .bindDataset(DS)
    .addRow(f("业务日期", { granularity: Granularity.DAY }))
    .addMetric(f("总销售", { aggrType: AggrType.SUM }))
    .addMetric(f("会员销售", { aggrType: AggrType.SUM }));

var chart = createCustomChart("我的看板")
    .setId("a938ad9fc26458e4377e90ae")
    .setSubType(CustomChartSubType.SDK)
    .loadContent("charts/dashboard")    // 自动读 dashboard.html/css/js
    .addDataView(dv1);                  // → renderChart(data) 的 data[0]

registerCustomChart(chart.build());
```

### §2.2 `page.js`（page 直接挂这 1 个 custom chart）

```javascript
var page = createPage("01-高层经营驾驶舱")
    .setId("l5b686c77ff07c1e21e49d0a")
    .setParentDir("wbcc12714d05249f4a615f8d")   // 目标目录 dirId
    .setBackgroundColor("#faf7f2")              // 奶白主题（业务用户更友好）
    .setCardMargin(0)
    .addFullWidthCard(0, 22);                   // 整页 1 个模块, h=22 行高

registerPage(page.build());
```

### §2.3 `charts/dashboard.html`

```html
<div id="dash-root">
  <div class="dash-loading">看板加载中...</div>
</div>
<script>loadBuiltinResourceByName('echarts')</script>
```

### §2.4 `charts/dashboard.js`（ECharts 渲染入口）

```javascript
// data[0] = dataView 1 的列数据：[{name:"业务日期",data:[...]}, {name:"总销售",data:[...]}, ...]
function getCol(view, name) {
  for (var i = 0; i < view.length; i++) {
    if (view[i] && view[i].name === name) return view[i];
  }
  return null;
}

function renderChart(data, clickFunc, config) {
  var root = document.getElementById('dash-root');
  if (!data || !data[0]) {
    root.innerHTML = '<div class="dash-loading">No data</div>';
    return;
  }
  // ... 业务渲染 (ECharts.init + setOption)
  var dates = ((getCol(data[0], "业务日期")) || {}).data || [];
  var sales = ((getCol(data[0], "总销售")) || {}).data || [];
  // ...
}

new GDPlugin().init(renderChart);
```

---

## §3 **CSV 三态判断硬规则**（v2 § 12.5 落地标准）

### §3.1 现象

CSV 上传到 BI 后，**散客订单的 `会员ID` 在 BI 中是空字符串 `""` 而非 NULL**。
SQL `WHERE 会员ID IS NOT NULL` 把所有订单都算成会员订单 → 北极星指标 #1 "会员销售占比" = 100%（假数据）。

### §3.2 硬规则

#### STRING 类型字段必须三态判断

```sql
-- ✗ 错：散客 会员ID = '' 全被算成会员
WHERE `会员ID` IS NOT NULL

-- ✓ 对
WHERE `会员ID` IS NOT NULL AND `会员ID` <> ''
```

适用字段类型：所有 STRING / VARCHAR 字段（订单ID / 会员ID / 活动ID / 商品ID / 顾客识别键 等）。

#### DATE / 数字类型字段不能 <> ''

```sql
-- ✗ 错：Spark 严格类型，DATE 不能跟字符串 '' 比较
-- 报错：cannot resolve '`核销日期` <> '''
WHERE `核销日期` IS NOT NULL AND `核销日期` <> ''

-- ✓ 对：DATE / 数字类型空值一定是 NULL，单一态判断
WHERE `核销日期` IS NOT NULL
```

#### Boolean 字段：CSV 解析为字符串 `'TRUE'/'FALSE'`，不是 int 1/0

```sql
-- ✗ 错：永远不匹配，输出空表
WHERE s.`是否90天内新店` = '1'
WHERE s.`是否90天内新店` = 1
WHERE s.`是否90天内新店` = true

-- ✓ 对：CSV 来源的字段值是字符串字面值
WHERE s.`是否90天内新店` = 'TRUE'
```

### §3.3 全局 SQL 后处理 patch（推荐做法）

`compile_payloads.py` 里加一个统一替换层，避免每个 SQL 手工修：

```python
def make_payload(etl_def):
    sql = etl_def["sql"]
    # 三态判断修正 (v2 § 12.5)：仅对 STRING 类型字段
    sql = sql.replace("`会员ID` IS NOT NULL", "(`会员ID` IS NOT NULL AND `会员ID` <> '')")
    sql = sql.replace("`会员ID` IS NULL",     "(`会员ID` IS NULL OR `会员ID` = '')")
    # 注意：日期/数字类型字段不能加 <> ''，会报 Spark 类型不匹配
    # ...
```

---

## §4 Spark SQL 在 BI ETL 里的 4 个硬限制

| # | 限制 | 报错 | 修法 |
|---|---|---|---|
| 1 | **CTE 别名必须英文** | `[PARSE_SYNTAX_ERROR] Syntax error at or near '订'` | `WITH order_agg AS (...)`，字段名仍可中文（反引号包裹） |
| 2 | **Window function 不能嵌套在 aggregate function** | `It is not allowed to use a window function inside an aggregate function` | 先用 CTE 算出 window 结果，外层再 aggregate |
| 3 | **`<> NULL` / `= NULL` 永远 unknown** | 输出 0 行 | `IS NOT NULL` / `IS NULL` |
| 4 | **`WHERE 日期字段 < 'today_field'` 字符串字面量永远不匹配** | 输出 0 行 | `WHERE 日期字段 < date_sub(current_date(), 1)` |

---

## §5 ETL Update 模式：OUTPUT_DATASET 必须带 dsId

### §5.1 现象

ETL 已 execute 过一次（OUTPUT 数据集已创建）。改 SQL 后用 update 模式重写（payload 顶层带 `dataFlowId`）：

```bash
POST /api/etl/direct-save with {..., dataFlowId: <existing>, actions: [...]}
# → {"error": {"status": 1012, "message": "输出数据集目录中存在同名文件，请修改"}}
```

### §5.2 修法

`actions[].dataSource.dsId` 必须显式填入**现有输出数据集的 dsId**，告诉 BI 这是 update 已存在的 ds 而非创建新 ds：

```python
def update_etl(payload_path, dfid, output_name):
    payload = json.loads(payload_path.read_text())
    payload["dataFlowId"] = dfid
    # 查现有输出 ds 的 dsId
    out_dsid = subprocess.run(["guancli", "ds", "search", output_name, "--raw"],
                              capture_output=True, text=True)
    out_dsid = json.loads(out_dsid.stdout)["response"]["contents"][0]["dsId"]
    # 注入到 OUTPUT_DATASET 节点
    for a in payload["actions"]:
        if a.get("type") == "OUTPUT_DATASET":
            a["dataSource"]["dsId"] = out_dsid
            break
    # 然后 POST direct-save
```

---

## §6 数据集上传：BI 无原生 API，必须 UI 手动

### §6.1 现实

`POST /api/data-source`, `/api/data-source/upload`, `/api/data-source/file`, `/api/file/upload`, `/api/excel`, `/api/etl/import-excel` —— **全部失败**（`5001 No static resource` 或 `Method 'POST' is not supported`）。

OPTIONS 探测显示这些 endpoint 只允许 DELETE/GET/HEAD/OPTIONS。

Claude in Chrome 的 `file_upload` 工具有 ≤ 10MB 单次调用 + 必须是 user-shared file 的限制，对 demo 数据集（最大 178MB）也走不通。

### §6.2 最实用方案

用户在 BI UI 上手动上传：
1. **数据准备 → 数据集 → 目标目录 → 新建数据集 → 本地文件 → CSV/Excel → 选文件 → 下一步 → 确认字段类型 → 保存**
2. 单文件 BI 上限 500MB（CSV，可压缩成 zip）

预估时间：
- 12 张表（最大 178MB）：30-45 分钟
- 大表 BI 解析需要 1-2 分钟，期间用户可以并行传下一个

### §6.3 上传清单生成（提升用户效率）

写一个 `inspect_schema.py` 自动输出 `UPLOAD_CHECKLIST.md`，包含：
- 每张表的行数 / 文件大小 / 类型
- 字段名 + 推断类型（date/datetime/int/float/string）+ 样例值
- 重点标注：所有 `*_时间` / `*_日期` / `年月` / `生日` 字段必须确认为 date/datetime（BI 自动识别但有时会错）

---

## §7 数据生成性能优化（pandas + openpyxl）

| 路径 | 性能（50 店 / 90 天 / ~45 万订单）|
|---|---|
| `df.to_excel(engine="openpyxl")` 写大表 | **4-5 分钟 / 100 万行** ⚠️ 极慢 |
| `df.to_csv(encoding="utf-8-sig")` | **2-3 秒 / 100 万行** ✓ 50× 加速 |

**规则**：行数 > 5 万自动转 CSV。Excel 只留维表用。

```python
def save(df, name, force_csv=False, force_xlsx=False):
    if force_xlsx or (not force_csv and len(df) <= 50_000):
        df.to_excel(OUT_DIR / f"{name}.xlsx", index=False, engine="openpyxl")
    else:
        df.to_csv(OUT_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
```

向量化第二原则：避免 Python 循环。1200 店 × 90 天 × ~10 单/天 = 100 万订单，向量化（`np.repeat` 展开 + `np.bincount` 聚合）比逐行 `dict.append + DataFrame()` 快 30 倍。

---

## §8 JOIN 键全局统一命名（避免 ETL 写两套）

### §8.1 反模式

```python
# rename_to_chinese.py 全局映射
COL_MAP = {
    "campaign_id": "活动ID",          # dim_活动主档 里
    "campaign_id": "关联活动ID",      # fact_私域互动 里 ← 后者覆盖前者
    ...
}
```

结果：dim 里叫 `活动ID`、fact 里叫 `关联活动ID`，ETL JOIN 时必须写 `ON dim.\`活动ID\` = fact.\`关联活动ID\``，麻烦且容易错。

### §8.2 正解

JOIN 键在所有表里**同名**，避免 BI ETL JOIN 写两套：

```python
COL_MAP = {
    "campaign_id": "活动ID",          # dim + fact 里都叫 活动ID
    "related_order_id": "订单ID",     # 跟 fact_订单主表.订单ID 同名
    ...
}
```

BI 上 SmartETL 的 JOIN_DATA 节点也能"按同名字段自动联"，无需手工配 predicates。

---

## §9 看板主题色：奶白 / 麻色 > 深色

业务用户（店长 / 区域经理 / 高层）对深色主题（`#0f172a` 等）有强抵触。**默认走奶白**：

```css
body { background: #faf7f2; color: #1f2937; }
.kpi-card { background: #ffffff; border: 1px solid #e5e7eb; box-shadow: 0 1px 2px rgba(15,23,42,0.04); }
.kpi-card::before { background: linear-gradient(90deg, #d97706 0%, #2563eb 100%); }  /* 顶部 3px 暖蓝渐变 */
.chart-card { background: #ffffff; border: 1px solid #e5e7eb; }
```

ECharts 配色：
- 主轴线条 `#2563eb`（深蓝）
- 次轴 `#d97706`（琥珀）/ `#059669`（墨绿）
- 风险标签 `#dc2626`（红）/ `#fbbf24`（黄）/ `#059669`（绿）
- 网格线 `#f3f4f6`（浅灰）

不要用 ECharts `dark` 主题。`echarts.init(el)` 默认就是 light 主题，正合适。

---

## §10 端到端时间预算（真实复盘）

| 阶段 | 实际耗时 |
|---|---|
| 数据生成（20 张表 / 670 万行）| **2 分钟**（向量化 + CSV）|
| 用户上传到 BI（20 张文件）| 30-45 分钟 |
| 17 个 ETL 写入 + 执行（含错误修复）| **15-25 分钟** |
| 6 个 HTML 应用化看板（guanvis-skill）| **3-4 小时**（写代码占大头）|
| 浏览器走查 + 微调 | 30-60 分钟 |
| **总计** | **5-7 小时** |

**关键时间节省**：guanvis-skill 把 v7 page/card 创建从"探 API 2-3 小时还跑不通"压缩到"`publish .` 30 秒"。

---

## §11 反模式与硬约束

| 反模式 | 替代 |
|---|---|
| 手撸 `POST /api/page` + `POST /api/card` + `PUT /api/page/<draft>` 走 v7 草稿流程 | 用 `guanvis-skill publish .` |
| 看板 script 全 hard-code 静态数据 | 用 DATA_GRID dataView，BI 自动取数 |
| 大表用 `df.to_excel(engine="openpyxl")` | 行数 > 5 万自动转 CSV |
| `WHERE 会员ID IS NOT NULL` 直接判断散客 | `WHERE 会员ID IS NOT NULL AND 会员ID <> ''` |
| `WHERE 核销日期 IS NOT NULL AND 核销日期 <> ''` | 日期/数字只能 `IS NOT NULL` 单一态 |
| `WHERE 是否90天内新店 = '1'` | `= 'TRUE'`（CSV 解析的字符串） |
| `WITH 订单汇总 AS (...)` | CTE 别名必须英文 |
| Window function 嵌套在 aggregate function | 先 CTE 算 window，外层 aggregate |
| update ETL 时不带 `dataSource.dsId` | 必须显式填入现有输出 ds 的 dsId |
| 深色主题给业务用户看 | 默认奶白 `#faf7f2` + 暖蓝主色 |
| dim/fact 表 JOIN 键不同名 | 全局统一命名（活动ID / 订单ID / 会员ID）|

---

## §12 完整 demo 工程参考

本次实战完整工程文件（脱敏后）在 maojiebc 的私域：

```text
demo-工程文件/
├── scripts/
│   ├── generate.py              # 20 张表向量化生成
│   ├── inspect_schema.py        # 自动生成 UPLOAD_CHECKLIST.md
│   ├── rename_to_chinese.py     # 英文字段 → 中文（含 JOIN 键统一）
│   └── iterate_helper.py        # 数据集 in-place patch（rename/map/add/drop）
├── etl_payloads/
│   ├── sql_drafts_v3.md         # 17 个 ETL SQL 草图
│   ├── compile_payloads_v3.py   # 编译 17 个 payload + 三态判断后处理
│   ├── apply_v3.py              # 批量 direct-save + execute + 轮询
│   ├── reapply_v3.py            # SQL 改了后 update 模式重跑（含 OUTPUT.dsId 自动注入）
│   ├── fetch_field_aliases.py   # 拉 20 张表的 fdId → 字段名映射
│   └── field_aliases.json       # 缓存
└── dashboards-v3/
    ├── 01-executive/            # 高层经营驾驶舱（4 北极星）
    ├── 02-member/               # 会员私域驾驶舱（RFM 80/20）
    ├── 03-tasks/                # 会员经营任务池（v2 § 9.2）
    ├── 04-store/                # 门店每日指挥台
    ├── 05-campaign/             # 活动权益复盘
    └── 06-experience/           # 体验风险专题
```

**6 个看板** = 6 个独立子目录, 每个目录 `guanvis-skill publish .` 各 30 秒发布。

---

## §13 与 Part C-12 (HTML 应用化看板) 的关系

- **Part C-12 / `part-c-html-dashboard.md`** 是"已经有 page + custom chart 时如何写 HTML 内容 + selector descriptor patch"
- **本文件** 是"从零到 6 个看板上线"的端到端流程，重点在 v7 BI 实例 + guanvis-skill 一键发布

两者互补：先看本文件知道"用 guanvis-skill"，遇到 selector 联动到 custom chart dataView 时再回 C-12 查 descriptor patch 章节。

---

## §14 SmartETL 节点化的两个新坑（2026-05-21 沉淀）

> **来源**：把 6 个 ETL 从"全 SQL 三节点版"改成"花式 SmartETL 节点链"演示版的实战。把 SQL 三节点拆成 8-17 个节点（INPUT / FILTER_ROWS / CALCULATOR / GROUP_BY / JOIN_DATA / SQL_SCRIPT / OUTPUT）时，踩到两个**永远不会出错误日志**的静默坑。两个坑都"看起来正常但数据全错"，是 demo 演示时最致命的。
>
> **何时读这里**：用 `node_group_by()` / `node_join()` 构造 SmartETL 节点，发现输出字段是空值 / 行数爆炸到亿级 / 看板指标显示成 ID 字符串。

### §14.1 **GROUP_BY 节点不支持 STRING 字段的 COUNT / COUNT_DISTINCT**

**现象**：
- 调用 `node_group_by(metric_fields=[("订单ID", "STRING", "COUNT_DISTINCT")])`
- direct-save 返回 success，execute 也 FINISHED
- 但下游 JOIN/CALC 用这个"订单数"字段时，预览数据看到的不是数字 5/8/16，而是 **`O2026022800000065`** 这种**订单 ID 字符串**

**根因**：BI 把请求里的 `aggrType: "COUNT_DISTINCT"` **静默改成 `aggrType: "NUL"`**（用 `guancli fetch GET /api/etl/<dfId>` 反查 zoneData.metric 才能看到），等于没聚合，输出取了原字段第一个值。

```bash
# 验证手段
guancli fetch GET "/api/etl/<dfId>" | jq '.response.actions[] | select(.type=="GROUP_BY") | .zoneData.metric'
# 看 aggrType 是否被改成 "NUL"
```

**修复策略**（按业务语义二选一）：

**A. 业务上唯一的字段** → 前置 CALC 派生 1 + GROUP_BY SUM

```python
# 例：dwd_订单 的 订单ID 业务唯一 → COUNT_DISTINCT(订单ID) == COUNT(*) == SUM(1)
n_calc = node_calculator(idg, n_filter["id"], [
    {"name": "订单计数", "type": "LONG", "expr": "1"},
    # ... 其他派生字段
])
n_calc_keys = {f["name"]: a["key"] for f, a in zip([{"name":"订单计数"}], n_calc["formulas"])}

n_group = node_group_by(idg, n_calc["id"], "dwd_订单",
    row_fields=[("门店ID","STRING"), ("业务日期","DATE")],
    metric_fields=[
        ("订单计数", "LONG", "SUM"),  # = 订单数
        # ...
    ],
    extra_row_keys=n_calc_keys,
)
```

**B. 真去重需求**（同一 key 在源表多次出现）→ **两层 GROUP_BY 模拟去重**

```python
# 例：dwd_会员触达 中同会员可能多次出现 → 必须真去重 COUNT_DISTINCT(会员ID)
# 第一层 GROUP_BY: 把粒度细化到去重字段, 自然去重
n_g1 = node_group_by(idg, n_calc["id"], "dwd_会员触达",
    row_fields=[("活动ID","STRING"), ("会员ID","STRING")],  # 加入会员ID 粒度
    metric_fields=[("查看标志", "LONG", "SUM")],
    extra_row_keys=n_calc_keys,
    name="第一层(活动ID×会员ID)",
)
n_g1_keys = {z["name"]: z["key"] for z in n_g1["zoneData"]["row"] + n_g1["zoneData"]["metric"]}

# CALC: 派生 1 用于第二层 SUM 计数
n_c2 = node_calculator(idg, n_g1["id"], [
    {"name": "会员计数", "type": "LONG", "expr": "1"},
])
n_c2_keys = dict(n_g1_keys); n_c2_keys["会员计数"] = n_c2["formulas"][0]["key"]

# 第二层 GROUP_BY: 粒度滚回, SUM(会员计数) = 去重会员数
n_g2 = node_group_by(idg, n_c2["id"], None,
    row_fields=[("活动ID","STRING")],
    metric_fields=[
        ("会员计数", "LONG", "SUM"),  # = COUNT_DISTINCT(会员ID)
        ("查看标志", "LONG", "SUM"),
    ],
    extra_row_keys=n_c2_keys,
    name="第二层粒度滚回(模拟去重)",
)
```

**C. 实在不想拆节点** → SQL_SCRIPT 旁路 + JOIN 合并主聚合

```python
n_sql_dedup = node_sql(idg, [n_filter["id"]], """
SELECT `门店ID`, `业务日期`, COUNT(DISTINCT `会员ID`) AS `去重会员数`
FROM input1
WHERE `会员ID` IS NOT NULL AND `会员ID` <> ''
GROUP BY `门店ID`, `业务日期`
""".strip(), [("门店ID","STRING"),("业务日期","DATE"),("去重会员数","LONG")])
# 然后 JOIN n_group + n_sql_dedup ⚠注意见 §14.2 多谓词坑
```

### §14.2 **JOIN_DATA 节点不支持多谓词**（只取 predicates[0]）

**现象**：
- 调用 `node_join(predicates=[{"left":"门店ID","right":"门店ID"}, {"left":"业务日期","right":"业务日期"}])`
- 节点 payload 里 `dataFusion.columnFuses[0].predicates` 数组确实有 2 个元素
- direct-save 成功，execute FINISHED
- 但**行数从预期 10 万爆到 900 万**（笛卡尔积）

**根因**：BI JOIN_DATA 节点执行时**只用 `predicates[0]`**（第一个谓词），第二个及之后的全部忽略。等于只 JOIN 了门店ID，每个门店的 N 个日期 × M 个日期 = 笛卡尔积爆炸。

**已试过无效的修复**：
- 加 `"operator": "EQ"` 字段——还是只取第一个
- 拆成两个 `columnFuses`——会被 BI 拒收

**唯一可行修复**：**用 SQL_SCRIPT 节点替代多键 JOIN**

```python
# 多键 JOIN 必须降级 SQL_SCRIPT
n_join_sql = node_sql(idg, [n_group["id"], n_sql_dedup["id"]], """
SELECT
  a.*,
  COALESCE(b.`去重会员数`, 0) AS `去重会员数`
FROM input1 a
LEFT JOIN input2 b ON a.`门店ID` = b.`门店ID` AND a.`业务日期` = b.`业务日期`
""".strip(), [
    ("门店ID","STRING"), ("业务日期","DATE"),
    # ... 复制 a 表所有字段 schema
    ("去重会员数","LONG"),
], name="多键 JOIN 降级 SQL")
```

**JOIN_DATA 仍可用的场景**：单键 JOIN（如 `门店ID = 门店ID` 关联门店主档）依然走 `node_join()`，速度比 SQL 快。

**FULL_OUTER 也踩**：BI JOIN_DATA 的 `joinType` 支持 `LEFT_OUTER / RIGHT_OUTER / INNER`，但 `FULL_OUTER` 节点会被 BI **静默吞掉**（direct-save 返回的 actions 数量比发出去的少 1），下游引用就 `key not found: OpId(...)`。FULL_OUTER 必须 SQL_SCRIPT。

### §14.3 SmartETL builder 函数库参考实现

`smart_etl_builder.py` 工厂函数封装了上述两坑的兼容处理：

```python
def node_group_by(..., metric_fields, ...):
    """⚠ 已知坑: BI GROUP_BY 节点不支持 STRING 字段的 COUNT/COUNT_DISTINCT
       (aggrType 被静默改为 NUL, 输出为空).
       去重计数请用 SQL_SCRIPT 节点旁路或两层 GROUP_BY 模拟,
       非去重计数请前置 CALCULATOR 派生 1 + GROUP_BY SUM.
    """
    for f in metric_fields:
        fname, ftype, aggr = f[0], f[1], f[2]
        # COUNT/COUNT_DISTINCT 输出必为 LONG (即使 BI 还会改成 NUL, 类型先对)
        out_type = "LONG" if aggr in ("COUNT", "COUNT_DISTINCT") else ftype
        if aggr == "AVG": out_type = "DOUBLE"

def node_join(..., predicates, ...):
    """⚠ 已知坑: BI JOIN_DATA 节点只取 predicates[0], 多谓词请用 SQL_SCRIPT 替代;
                 FULL_OUTER joinType 会被静默吞掉, 也必须 SQL_SCRIPT."""
    preds = [{"leftColumn": p["left"], "rightColumn": p["right"]} for p in predicates]
```

### §14.4 6 个 SmartETL 标杆实战节点链（demo 沉淀）

| ETL 名 | 节点数 | 节点链 | 输出行数 | 关键技巧 |
|---|---|---|---|---|
| etl_dws_门店日报 | 10 | F+C+G+S×2+J+C | 105,524 | 多谓词 JOIN 降 SQL |
| etl_dws_会员RFM分层 | 10 | F+C+G+S+J | 69,264 | 派生 1 + SUM 替代 COUNT_DISTINCT |
| etl_dws_私域转化漏斗 | 10 | F+C+G+C+G+J+C | 27,048 | **两层 GROUP_BY 模拟去重** |
| etl_dws_新店爬坡_Comp老店 | 8 | F+C+G+J+C | 105,524 | 派生 1 + SUM |
| etl_dws_员工导购效能 | 8 | F+S+J+C | 7,952 | SQL_SCRIPT 替代 FULL OUTER JOIN |
| etl_ads_活动权益复盘 | 17 | C+G+F+C+G×2+S+J×3+C | 50 | **混合方案集大成**：派生 1 + 两层 GROUP_BY + SQL_SCRIPT(7天内 JOIN) |

**命名规范**：建议 ETL 名末尾加 `(N节点·F+C+G+S+J)` 缩写后缀，方便和 SQL 三节点版（INPUT+SQL+OUTPUT）区分。
- F = FILTER_ROWS, C = CALCULATOR, G = GROUP_BY, J = JOIN_DATA, S = SQL_SCRIPT
- INPUT / OUTPUT 默认省略（每个 ETL 都有）

### §14.5 排查 checklist

跑完 SmartETL execute 后必查（demo 演示前一定要做）：

```bash
# 1. 行数是否预期范围内 (爆炸到亿级 = 多谓词 JOIN 坑)
guancli ds get <output_dsid> --brief | grep 行数

# 2. 预览前 5 行, 重点看 COUNT_DISTINCT 字段是否变成 ID 字符串
guancli ds preview <output_dsid> --limit 5

# 3. 反查 GROUP_BY 节点 aggrType 是否被改 NUL
guancli fetch GET "/api/etl/<dfId>" | jq '.response.actions[] | select(.type=="GROUP_BY") | .zoneData.metric[] | {name, aggrType}'

# 4. JOIN_DATA 节点检查 predicates 数量 (任何 > 1 都是潜在笛卡尔积爆炸)
guancli fetch GET "/api/etl/<dfId>" | jq '.response.actions[] | select(.type=="JOIN_DATA") | .dataFusion.columnFuses[].predicates | length'

# 5. 反查 actions 数量是否等于发出去的 (少 1 = FULL_OUTER 被吞)
guancli fetch GET "/api/etl/<dfId>" | jq '.response.actions | length'
```
