# 01 · 日期与时间

> 餐饮 BI 60% 的 ETL 问题第一步都卡在"时间范围怎么写"。本节按**实时 / T-1 / 用餐时段 / 时间宏 / 跨月对齐**五类罗列，可直接抄。

## 实时日期范围（now 类）⚪

适用于流式刷新表、当日实时看板。`current_date()` 和 `now()` 都按当前服务器时刻取值。

```sql
-- 本月初 / 本月末
SELECT
  DATE_SUB(last_day(add_months(now(),-1)), -1) AS `本月初`,
  last_day(now())                              AS `本月末`,
  DATE_SUB(last_day(add_months(now(),-2)), -1) AS `上月初`,
  last_day(add_months(now(),-1))               AS `上月末`,
  DATE_SUB(last_day(add_months(now(),-3)), -1) AS `上上月初`,
  last_day(add_months(now(),-2))               AS `上上月末`
```

## T-1 日期范围（昨日截止）⚪

最常见的批处理场景。当天的数据还在写入，所以截止昨日，避免读到半天的脏数据。

```sql
SELECT
  TO_DATE(now())                                                                          AS `今日`,
  date_sub(TO_DATE(now()), 1)                                                             AS `昨日_T1`,
  add_months(date_sub(TO_DATE(now()),1), -1)                                              AS `上月昨日_T1`,
  date_add(last_day(add_months(date_sub(TO_DATE(now()),1),-1)), 1)                        AS `本月初_T1`,
  last_day(date_sub(TO_DATE(now()),1))                                                    AS `本月末_T1`,
  date_add(last_day(add_months(date_sub(TO_DATE(now()),1),-2)), 1)                        AS `上月初_T1`,
  last_day(add_months(date_sub(TO_DATE(now()),1),-1))                                     AS `上月末_T1`,
  date_add(last_day(add_months(date_sub(TO_DATE(now()),1),-3)), 1)                        AS `上上月初_T1`,
  last_day(add_months(date_sub(TO_DATE(now()),1),-2))                                     AS `上上月末_T1`
```

**口径**：T-1 系列把 `now()` 替换成 `date_sub(now(),1)` 作为锚点，确保跨月那一天不会跳错。

## 近 N 天 / 近 N 月 / 近 N 周 ⚪

```sql
-- 近 30 天订单（含昨日，不含今日）
SELECT *
FROM input1
WHERE CAST(`订单日期` AS DATE) >= current_date() - INTERVAL 30 DAY
  AND CAST(`订单日期` AS DATE) <= current_date() - INTERVAL 1 DAY;

-- 近 3 个月订单（按当月 1 号往前推 3 个月）
SELECT * FROM input1
WHERE input1.`订单日期` >= add_months(concat(substr(current_date(), 1, 7), '-01'), -3);

-- 本月到昨日
SELECT * FROM input1
WHERE input1.`订单日期` >= add_months(concat(substr(current_date(),1,7),'-01'), 0);

-- 上月到昨日（从上月 1 号到昨天）
SELECT * FROM input1
WHERE input1.`订单日期` >= add_months(concat(substr(current_date(),1,7),'-01'), -1);

-- 仅限昨日数据
SELECT *
FROM input1
WHERE input1.`添加时间` >= date_sub(TO_DATE(now()), 1)
  AND input1.`添加时间` <  TO_DATE(now());

-- 小于等于昨日（含历史所有）🅱️
SELECT *
FROM input1
WHERE CAST(`抽奖日期` AS DATE) <= current_date() - INTERVAL 1 DAY;
```

**坑**：用 `>=` + `<` 而非 `BETWEEN`，避免把"今天 00:00:00 的数据"漏算或重算。

## 增量更新窗口 🅱️

ETL 调度日跑时只更新近 7 天的数据，避免全量重跑。

```sql
SELECT *
FROM tb_order_log
WHERE ORDER_DATE >= CURDATE() - INTERVAL 6 DAY
  AND ORDER_DATE <  CURDATE();
```

**适用**：日跑 ETL 节点，配合下游 OUTPUT_DATASET 增量写入策略。

## 本月已经过去的比例 🅱️

老板汇报场景常用。配合 KPI 用，"本月营收完成率 = 已营收 / (目标 × 本月已过比例)"。

```sql
IF(
  MONTH(DATE_SUB(CURRENT_DATE(), 1)) <> MONTH(CURRENT_DATE()),
  0,
  DAY(DATE_SUB(CURRENT_DATE(), 1)) / DAY(LAST_DAY(CURRENT_DATE()))
)
```

**口径**：
- 月初第一天（昨天还在上月），返回 0
- 否则返回 `已过天数 / 当月总天数`，结果 0~1

## 用餐时段分桶 ⚪

按下单整点（0~23 整数）分早餐 / 午餐 / 下午茶 / 晚餐 / 宵夜。

```sql
-- 字符串版（前置已把 hour 拼成 "6点"/"7点"…）
CASE
  WHEN [下单整点] IN ('6点','7点','8点','9点') THEN '早餐'
  WHEN [下单整点] IN ('10点','11点','12点','13点') THEN '午餐'
  WHEN [下单整点] IN ('14点','15点','16点') THEN '下午茶'
  WHEN [下单整点] IN ('17点','18点','19点','20点') THEN '晚餐'
  WHEN [下单整点] IN ('21点','22点','23点','24点','0点','1点','2点','3点','4点','5点') THEN '宵夜'
  ELSE '其他'
END
```

```sql
-- 数字版（直接传 hour 整数 6/7/8…）
CASE
  WHEN [下单整点] IN ('6','7','8','9') THEN '早餐'
  WHEN [下单整点] IN ('10','11','12','13') THEN '午餐'
  WHEN [下单整点] IN ('14','15','16') THEN '下午茶'
  WHEN [下单整点] IN ('17','18','19','20') THEN '晚餐'
  WHEN [下单整点] IN ('21','22','23','24','1','2','3','4','5') THEN '宵夜'
  ELSE '其他'
END
```

```sql
-- 拼接整点的辅助表达式（卡片字段）
CONCAT(HOUR([下单时间]), '点')
```

**坑**：早 6 ~ 上午 9 点是早餐，但中国本土餐饮品牌很多把"早餐"定义到 10 点之前，按你方实际定义改。

## 月份截取 ⚪

```sql
-- 按月聚合
DATE_TRUNC("month", [report_date])

-- 文本日期转日期（20241101 这种 yyyyMMdd 字符串）
to_date([日期], 'yyyyMMdd')      -- 返回 DATE
to_timestamp([交易日期], 'yyyyMMdd')  -- 返回 TIMESTAMP
```

**适用**：埋点表 / 业务系统导出表里日期字段经常是字符串，落到 ETL 第一步先转成 DATE 再说。

## 日期距离 ⚪

```sql
-- 某门店"统计日期距今天"的窗口表达式
DATEDIFF(MAX([订单日期]) OVER (PARTITION BY [门店编号]), 'today')

-- 顾客"最后一单距今天数"（卡片字段）
GREATEST(
  0,
  DATEDIFF(
    date_sub(CURRENT_DATE, 1),   -- 昨天
    MAX(TO_DATE([订单日期]))
  )
)
```

**口径**：
- `DATEDIFF(a, b)` 返回 `a - b` 的天数差
- `'today'` 是观远 BI 平台关键字，等价于 `current_date()`
- 包 `GREATEST(0, ...)` 防止时差/未来订单导致出现负数

## 时间宏（观远 BI 平台关键字）⚪

**三层花括号 `{{{...}}}` 不可少**。少一个或写两个都会被当字面字符串。

| 时间宏 | 含义 | 示例返回值（假设今天 2026-05-18） |
|---|---|---|
| `{{{yesterday}}}` | 昨天 | `2026-05-17` |
| `{{{today}}}` | 今天 | `2026-05-18` |
| `{{{yesterday - 27 days}}}` | 昨天再往前 27 天 | `2026-04-20` |
| `{{{monday last week - 28 days}}}` | 上周一再往前 28 天（约近 4 周维度起点） | `2026-04-13` |
| `{{{%2025-12-12}}}` | 字面日期注入（前缀 `%`），主要用于占位/默认值 | `2025-12-12` |

**典型用法 — 近 4 周（周维度）**：

```
起点：{{{monday last week - 28 days}}}
终点：{{{yesterday}}}
```

**典型用法 — 近 28 天（日维度，含昨日）**：

```
起点：{{{yesterday - 27 days}}}
终点：{{{yesterday}}}
```

**坑**：
- 时间宏只能放在**筛选器值** / **参数** / **卡片字段引用变量**里，不能放在 SQL 字符串中拼接
- 想在 ETL SQL 里固定日期，用 `'2025-12-12'` 普通字符串即可，不要用 `{{{%...}}}` 语法

## 字段使用度审计

如果想知道这些日期函数在你方 ETL/卡片里被引用了几次（清理废弃节点用），见 majia-guanyuan Part B 的"字段使用度审计 ExecPlan"。
