# 04 · 渠道与门店

> 餐饮 BI 里"渠道"和"门店生命周期"是两个高频痛点：渠道码十几个变体要归一，门店开关停业要分老中新 Comp/非 Comp。本节给出**业务渠道 → 子渠道 → 时效 → 门店日键 → 成长类型 → 营业天数**的完整套路。

## 业务渠道（一级归类）🅰️

```sql
CASE
  WHEN [Channel] = '03.HomeDelivery' THEN 'HD外卖'
  ELSE                                    'Din堂食'
END
```

**口径**：把上百种渠道码归一成"堂食 / 外卖"两桶，绝大多数老板汇报场景够用。

## 订单子渠道（二级归类，大 case）🅰️

这段是 doc 1 里最复杂的渠道 case，覆盖了**渠道 ID + 订单类型 + 时间分界 + FromType + OrderSource** 五个字段的组合判断。值得作为"渠道归一化"模板单独保留。

```sql
CASE
  /* 2024 跨年的渠道-订单类型重新映射 */
  WHEN [CHANNEL_ID] = 2 AND [OrderType] = 4 AND [businessDate] < '2024-01-01' THEN '微信_外送'
  WHEN [CHANNEL_ID] = 2 AND [OrderType] = 1 AND [businessDate] >= '2024-01-01' THEN '微信_外送'

  WHEN [CHANNEL_ID] = 3 AND [OrderType] = 4 AND [businessDate] < '2024-01-01' THEN '支付宝_外送'
  WHEN [CHANNEL_ID] = 3 AND [OrderType] = 1 AND [businessDate] >= '2024-01-01' THEN '支付宝_外送'

  WHEN [CHANNEL_ID] IN (13, 103001, 103003, 103004) AND [OrderType] = 4 AND [businessDate] < '2024-01-01' THEN 'H5_外送'
  WHEN [CHANNEL_ID] IN (13, 103001, 103003, 103004) AND [OrderType] = 1 AND [businessDate] >= '2024-01-01' THEN 'H5_外送'

  /* 一级渠道码 */
  WHEN [CHANNEL_ID] = 2  THEN '微信_自取'
  WHEN [CHANNEL_ID] = 3  THEN '支付宝_自取'
  WHEN [CHANNEL_ID] = 8  THEN '拼单'
  WHEN [CHANNEL_ID] = 4  THEN '饿了么'
  WHEN [CHANNEL_ID] = 5  THEN '美团'
  WHEN [CHANNEL_ID] = 15 THEN '京东外卖'
  WHEN [CHANNEL_ID] = 6  THEN 'Pad点餐'
  WHEN [CHANNEL_ID] = 7  THEN 'POS'
  WHEN [CHANNEL_ID] = 11 THEN '酒吧'
  WHEN [CHANNEL_ID] = 12 THEN '商米点餐'
  WHEN [CHANNEL_ID] IN (13, 103001, 103003, 103004) THEN 'H5点餐'
  WHEN [CHANNEL_ID] IN (6, 99) THEN 'POS'
  WHEN [OrderSource] != 1600 THEN 'POS'

  /* FromType 二级回退 */
  WHEN [FromType] = 5   THEN '微信_自取'
  WHEN [FromType] = 204 THEN '支付宝_自取'
  WHEN [FromType] = 60  THEN '团购'
  WHEN [FromType] = 403 THEN 'POS'
  WHEN [FromType] = 99  THEN 'POS'
  WHEN [FromType] = 11  THEN 'Pad点餐'
  WHEN [FromType] = 20  THEN '饿了么'
  WHEN [FromType] = 21  THEN '美团'
  WHEN [FromType] = 43  THEN '盒马'
  WHEN [FromType] = 4   THEN '微信_外送'
  WHEN [FromType] = 2   THEN '支付宝_外送'
END
```

**为什么这么长**：
1. 业务系统在 2024-01-01 改了 OrderType 编码（4 → 1），但旧数据保留，必须按业务日期分段处理
2. 同一渠道在不同来源系统的码不一致（CHANNEL_ID 主用，FromType 兜底）
3. 没匹配上的写 `END`（不写 ELSE）= 留 NULL，让下游知道是未识别需要补码

**方法论**：每次业务系统加新渠道、改老编码，**只在 case 链顶部新增 `WHEN ... AND [businessDate] >= '新分界'` 分支，绝不动旧分支**。这样保证历史数据口径稳定。

## 时效类型 ⚪

把"即时单 / 预约单 / 长时效"统一处理 NULL 和空值：

```sql
CASE
  WHEN [订单时效类型_R] IS NULL                   THEN '即时单'
  WHEN LENGTH(TRIM([订单时效类型_R])) = 0         THEN '即时单'
  ELSE [订单时效类型_R]
END
```

**坑**：判 NULL 之外还要判"空字符串 + 全空格"，餐饮系统经常有 `'   '` 这种"看似有值"的脏数据。

## 搭配类型（饮品 / 食品 / 餐 / 甜点）🅰️

```sql
SELECT
  `OrderKey`,
  input1.`union_order_id`,
  input1.`Items`,
  input1.`饮品QTY`,
  input1.`订单内产品数_不含商品`,
  CASE
    WHEN `QTY` = `饮品QTY`                                    THEN '仅饮品'
    WHEN `QTY` = `食品QTY`                                    THEN '仅食品'
    WHEN `饮品QTY` > 0 AND `餐食QTY` > 0                      THEN '饮+餐'
    WHEN `饮品QTY` > 0 AND `甜品QTY` > 0                      THEN '饮+甜点'
    ELSE                                                          '其他'
  END AS `搭配类型`
FROM input1
```

**业务用途**：低客单品类（咖啡/茶饮）经常分析"是否带食品"对客单价的拉动作用。

## StoreDate（门店日键）⚪

```sql
CONCAT([StoreID], '_', [businessDate])
```

**用途**：所有"店均日 X"指标的分母去重单位，详见 [03 章 · ADS/ADT/AUD](03-revenue-kpi.md)。

**约定**：`StoreID` 用门店编号（非门店名），`businessDate` 用 `yyyy-MM-dd` 字符串，下划线分隔保证可读、可拆。

## 加盟类型 🅰️

```sql
IF([门店类型] = '某门店类型', [加盟直营], "")
```

**口径**：只在指定门店类型下展示加盟/直营标签，其他门店类型留空。

**改通用版**：把 `'某门店类型'` 换成你方"需要细分加盟直营的门店类型名"（如"Express 店"、"快取店"、"标准店"等）。

## 截止日期 🅰️

```sql
IF([门店状态] = 'Closed', TO_DATE([停业时间]), DATE_SUB(now(), 1))
```

**口径**：
- 已闭店 → 截至日期 = 停业时间（用于统计该店"历史营业窗口"）
- 在营 → 截至日期 = 昨天（T-1，标准批处理截止）

**用途**：营业天数、Comp 判定、累计指标的"右端点"。

## 成长类型（新店 / Comp 老店 / 次新店 / 非 Comp 老店）🅰️ {#成长类型}

```sql
CASE
  WHEN [停业时间] IS NOT NULL AND CURRENT_DATE() > [停业时间]
    THEN '非Comp计算老店'
  WHEN DATEDIFF(current_date(), [开业时间]) <= 90
    THEN '新店'
  WHEN [IsComp] = TRUE
    THEN 'Comp老店'
  WHEN add_months([开业时间], 12) < [月份]
    THEN '非Comp计算老店'
  ELSE
    '次新店'
END
```

**口径分解**：

| 优先级 | 判定 | 含义 |
|---|---|---|
| 1 | 已停业 | "非 Comp 计算老店"（历史店，不参与同店对比） |
| 2 | 开业 ≤ 90 天 | "新店"（开店扰动期，业绩不稳定，不参与同店对比） |
| 3 | `IsComp = TRUE` | "Comp 老店"（核心同店可比，老板看的就是这条线） |
| 4 | 开业满 12 个月 | "非 Comp 计算老店"（开了一年但因业态调整等原因被人工剔出 Comp） |
| 5 | 兜底 | "次新店"（开业 91 天 ~ 12 个月内，过渡期） |

**业务用途**：
- 同店增长率 = Comp 老店今年 vs Comp 老店去年（**剔除新店扰动**）
- 整体增长率 = 全部门店今年 vs 全部门店去年（含新开闭店扰动）

## 营业天数（累计窗口）🅰️

```sql
SUM([营业]) OVER (
  PARTITION BY [门店]
  ORDER BY [门店], [日期] ASC
  ROWS BETWEEN UNBOUNDED PRECEDING AND 0 FOLLOWING
) AS `营业天数`
```

**口径**：每家门店按日期升序累计"营业标记 = 1"的天数，得到"截至该日的累计营业天数"。

**坑**：`ROWS BETWEEN UNBOUNDED PRECEDING AND 0 FOLLOWING` 等价于 `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`，但前者写法更显式、避免歧义。

## 排序（门店内日期倒序）🅰️

```sql
ROW_NUMBER() OVER (
  PARTITION BY [门店]
  ORDER BY [门店], [日期] DESC
)
```

**用途**：取每家门店最新一日数据时 `WHERE rn = 1`。详见 [06 章 · 开窗排名对比](06-sql-utils.md#开窗排名)。

## 注册门店清洗（优先级回填）🅱️

会员的"归属门店"会因数据源差异有 3 ~ 4 个候选字段（注册门店 / 首单门店 / 最后交易门店），且都可能为空或值为 `'微信小程序'`（虚拟门店）。需要一套**优先级回填**逻辑：

```sql
SELECT
  `用户id`,
  `注册门店编号`, `注册门店名称`, `注册所属分公司`,
  `首单门店编号`, `首单门店名称`, `首单所属分公司`,
  `最后交易门店编号`, `最后交易门店名称`, `最后交易归属分公司`,

  /* 1. 生成【归属门店编号】*/
  CASE
    -- 优先级 1: 注册门店有效
    WHEN `注册门店名称` IS NOT NULL AND `注册门店名称` <> '' AND `注册门店名称` <> '微信小程序'
      THEN `注册门店编号`
    -- 优先级 2: 最后交易门店有效
    WHEN `最后交易门店名称` IS NOT NULL AND `最后交易门店名称` <> '' AND `最后交易门店名称` <> '微信小程序'
      THEN `最后交易门店编号`
    -- 优先级 3: 首单门店有效
    WHEN `首单门店名称` IS NOT NULL AND `首单门店名称` <> '' AND `首单门店名称` <> '微信小程序'
      THEN `首单门店编号`
    -- 兜底：保留原始注册门店编号（哪怕是 NULL 或 '微信小程序'）
    ELSE `注册门店编号`
  END AS `归属门店编号`,

  /* 2. 归属门店名称（结构同上，把"门店编号"换成"门店名称"）*/
  CASE
    WHEN `注册门店名称` IS NOT NULL AND `注册门店名称` <> '' AND `注册门店名称` <> '微信小程序'
      THEN `注册门店名称`
    WHEN `最后交易门店名称` IS NOT NULL AND `最后交易门店名称` <> '' AND `最后交易门店名称` <> '微信小程序'
      THEN `最后交易门店名称`
    WHEN `首单门店名称` IS NOT NULL AND `首单门店名称` <> '' AND `首单门店名称` <> '微信小程序'
      THEN `首单门店名称`
    ELSE `注册门店名称`
  END AS `归属门店名称`,

  /* 3. 归属门店分公司（结构同上）*/
  CASE
    WHEN `注册门店名称` IS NOT NULL AND `注册门店名称` <> '' AND `注册门店名称` <> '微信小程序'
      THEN `注册所属分公司`
    WHEN `最后交易门店名称` IS NOT NULL AND `最后交易门店名称` <> '' AND `最后交易门店名称` <> '微信小程序'
      THEN `最后交易归属分公司`
    WHEN `首单门店名称` IS NOT NULL AND `首单门店名称` <> '' AND `首单门店名称` <> '微信小程序'
      THEN `首单所属分公司`
    ELSE `注册所属分公司`
  END AS `归属门店分公司`

FROM input1;
```

**业务背景**：
- 注册时通过"微信小程序"渠道注册的会员，没有"线下注册门店"概念，需要按"最后交易门店 → 首单门店"回填
- 三个候选字段都为空时只能放弃归属（保留原始 NULL，下游打"未知"标签）

**复用方法**：把 `'微信小程序'` 换成你方的"虚拟渠道名称"（如 `'线上'`、`'APP'`），三个优先级换成你方实际字段。

## 分公司简称 🅱️

```sql
REPLACE([注册所属分公司], "分公司", "")
```

**用途**：把"上海分公司"压缩成"上海"，方便仪表板列名/筛选器/标题展示。

## 日均拉新门店数 🅱️

```sql
COUNT(DISTINCT [StoreDate]) / COUNT(DISTINCT [注册日期])
```

**口径**：去重门店日键 / 去重注册日期 = 每日平均参与拉新的门店数。

**业务用途**：考核拉新活动的"门店覆盖密度"，越高说明全国门店参与度越好。

## 评价分类（情绪 + 标签）🅱️

原始素材里有一段超长正则评价分类 SQL（识别食安/少餐/口味/出品/价格/包装/配送/服务态度 + 情绪打标）。**单独成段，作为附录**，因为太长且业务专属性强（餐饮连锁 B 实战场景）。

**核心方法论**：
1. 先用 `REGEXP_REPLACE` 把评价文本归一化（去标点、去空格、转小写）
2. 用 `CONCAT_WS('|', '关键词1','关键词2',...)` 拼正则
3. 用 `REGEXP_LIKE` 打多个独立标签 flag
4. 用嵌套 CASE WHEN + 否定排除（如 `pos_protect_pat` 保护、`taste_exclude_pat` 反义词排除）做情绪归类

适合"分析师做差评归因 / 情绪打标 / 多渠道评价聚合"场景。

## 多渠道评价整合 Pipeline 🅱️ {#多渠道评价pipeline}

> 餐饮 BI 场景常常要把"美团 / 饿了么 / 大众点评 / 堂食打卡评价" 这 N 个渠道的评价数据拼成一张统一的"评价宽表"，再做情绪打标/差评归因。生产环境下这套通常拆成 **5 个独立 ETL + 1 个总聚合 ETL**，构成完整 pipeline。

### Pipeline 总览

```
原始数据源（按平台分）             单平台清洗 ETL            总聚合 ETL
─────────────────────────         ──────────────         ─────────────
2025 年美团评价 ─┐
2026 年美团评价 ─┴── APPEND_ROWS → 美团评价 ─┐
                                                    │
饿了么评价原始数据 ──────────────→ 饿了么评价 ─┼── APPEND_ROWS
                                                    │       │
堂食打卡评价 + 订单明细 ──── JOIN → 堂食评价 ──┤       ↓
                                                    │   SQL_SCRIPT
美饿外卖评分 ─────────────────→ 美饿外卖评分 ─┘   (评价分类正则)
                                                            ↓
                                                  外卖评价分类—优化（输出）
```

### 关键 Pattern 1：跨年份数据用 APPEND_ROWS 串联

业务系统经常按"年"分表存评价（`2025年美团评价` / `2026年美团评价`），ETL 入口必须先 APPEND_ROWS 合并：

```
节点拓扑：
[INPUT] 2025年美团评价 ─┐
[INPUT] 2026年美团评价 ─┴── [APPEND_ROWS] 行拼接 → ... → [OUTPUT] 美团评价```

**口径**：APPEND_ROWS 要求两源**字段名 + 字段类型完全一致**。如果跨年改过字段名（系统升级），先用 `SELECT * + 重命名` 对齐再拼。

### 关键 Pattern 2：评价图片字段的平台差异

不同平台返回评价图片的格式不同，要做**统一化拆列**（最多 9 张图，拆成 9 个独立列方便落表）：

```sql
-- 美团评价：逗号分隔字符串 → split
SELECT
  `门店编号`,
  `评价日期`,
  `评价内容`,
  `同步时间`,
  element_at(split(`评价图片`, ','), 1) AS `评价图片1`,
  element_at(split(`评价图片`, ','), 2) AS `评价图片2`,
  -- ... 拆到 9 张
  element_at(split(`评价图片`, ','), 9) AS `评价图片9`
FROM input1;
```

```sql
-- 饿了么评价：JSON 数组字符串 → from_json + element_at
WITH t AS (
  SELECT
    `门店编号`,
    `评价日期`,
    `顾客评价`,
    `同步时间`,
    from_json(coalesce(trim(`评价图片`), '[]'), 'array<string>') AS pics
  FROM input1
)
SELECT
  `门店编号`,
  `评价日期`,
  `顾客评价`,
  `同步时间`,
  element_at(pics, 1) AS `评价图片1`,
  element_at(pics, 2) AS `评价图片2`,
  -- ... 拆到 9 张
  element_at(pics, 9) AS `评价图片9`
FROM t;
```

**关键点**：
- 美团用 `split(s, ',')` 把逗号分隔字符串变数组
- 饿了么用 `from_json(s, 'array<string>')` 把 JSON 数组字符串解成 array
- `element_at(arr, N)` 取第 N 个元素，越界返回 NULL（直接落表为空列）
- 饿了么 SQL 多了一层 `coalesce(trim(x), '[]')` 兜底——空字符串/NULL 都先变成空数组，避免 `from_json` 解析失败抛错

### 关键 Pattern 3：堂食评价的"打卡 + 订单"双源 JOIN

堂食评价没有平台级别 API，通常来自**门店打卡 + 订单明细**两个数据源：

```
节点拓扑：
[INPUT] 订单明细 ────┐
                          ├── [JOIN_DATA] 关联数据 → [GROUP_BY] 分组聚合 → [OUTPUT] 堂食评价[INPUT] tb_sign_in_evaluate_log ───┤
                                   │
[INPUT] tb_sign_in_info_detail ─── ┤ (聚合标签)
                                   │
[SQL_SCRIPT] 标签聚合(collect_set) ─┘
```

**核心 SQL（标签聚合）**：

```sql
-- 一个评价主键可能有多个标签，聚合成逗号串
SELECT
  input1.`自增主键`,
  concat_ws(',', collect_set(input1.`标签`)) AS `标签组`
FROM input1
GROUP BY 1;
```

详见 [06 章 · collect_set + concat_ws](06-sql-utils.md#collect_set--concat_ws多行聚一列-) 的通用模式。

### 关键 Pattern 4：总聚合 ETL 把多平台 APPEND 起来再分类

```
节点拓扑：
[INPUT]  美团评价 ──┐
                         │
[INPUT] 饿了么评价 ─┴── [APPEND_ROWS] 行拼接 → [SQL_SCRIPT] 评价分类正则 → [OUTPUT] 外卖评价分类—优化
                                                  ↑
                                                  └ 此处运行 [04 章 · 评价分类](#评价分类情绪--标签-) 那段超长正则 SQL
```

**口径要点**：
1. 多平台合并前必须**字段名对齐**（美团的 `评价内容` vs 饿了么的 `顾客评价` 必须统一成同一字段名）
2. 合并后增加一个 `[平台]` 列（如美团/饿了么），方便分平台分析差评分布
3. 情绪打标 SQL 只跑一次（在 APPEND 之后），避免每个平台维护一套规则

### 全 Pipeline 工程取舍

| 取舍维度 | 选择 | 理由 |
|---|---|---|
| 单 ETL 还是分 ETL？ | **每个平台一个 ETL** | 单平台故障不阻塞其他平台；可独立调度刷新频次 |
| 在哪里做情绪打标？ | **总聚合 ETL** | 单平台 ETL 只做字段对齐和清洗，分类规则集中维护 |
| 跨年数据合并放哪？ | **单平台 ETL 入口** | APPEND_ROWS 越靠前越好，下游 SQL 不感知年份 |
| 图片字段拆几列？ | **9 列** | 经验值（90%+ 评价图片数 ≤ 9 张），超出截断不影响分析 |

### 复用方法

把餐饮连锁 B 的 5 ETL 结构当模板，按你方实际平台数量复制 N 份单平台清洗 ETL，再写一个总聚合 ETL 把它们 APPEND 起来。**每个平台的差异只在"图片字段解析方式 + 字段重命名"，分类规则一份**。
