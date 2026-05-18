# 03 · 营收 KPI 与占比

> 餐饮零售的核心指标卡。**所有 KPI 都按"分子 / 分母"两段看，先盯住分母去重再算分子**。本节是老板汇报口径的高频区，建议直接挂在 majia-guanyuan 的卡片字段里。

## 客单价 AC ⚪

```sql
SUM([去税营业额 NS]) / COUNT(DISTINCT [订单号])
```

**口径**：去税营业额 / 去重订单数

**坑**：
- 分母**必须用 `COUNT(DISTINCT 订单号)`**，写 `COUNT([订单号])` 会把拼单订单的多行重复计入，AC 直接砍半
- 营业额是"去税"还是"含税"必须明示（NS vs GS）

**变体**：

```sql
-- 仅外卖 AC
SUM(IF([业务渠道划分] = 'HD外卖', [去税营业额 NS], NULL))
  / COUNT(IF([业务渠道划分] = 'HD外卖', [订单号], NULL))

-- 仅堂食 AC（同上把 'HD外卖' 换成 'Din堂食'）
```

## 店均日营收 ADS ⚪

```sql
SUM([去税营业额 NS]) / COUNT(DISTINCT [StoreDate])
```

**口径**：去税营业额 / 去重门店日键（= 店天数）

**关键字段**：`StoreDate = CONCAT([StoreID], '_', [businessDate])`，作为门店×日的唯一键。这是餐饮 BI 平台里"分母去重"的标准做法。

```sql
-- 衍生：店天数（StoreDays）
COUNT(DISTINCT [StoreDate])
```

### 店均日营收 - 仅外卖 ADS_HD ⚪

```sql
SUM(IF([业务渠道划分] = 'HD外卖', [去税营业额 NS], 0))
  / COUNT(DISTINCT [StoreDate])
```

**坑**：分子用 `IF(..., 0)` 没问题（SUM 0 不影响结果），但分母**保持总的 StoreDate**——因为"外卖的店均日营收"按"开店天数"分摊，而不是"卖过外卖的天数"。**不要随手把分母也加 IF 过滤**，否则结果会虚高。

## 店均日订单 ADT ⚪

```sql
COUNT(DISTINCT [订单号]) / COUNT(DISTINCT [StoreDate])
```

## 店均日销量 AUD ⚪

```sql
SUM([销量QTY]) / COUNT(DISTINCT [StoreDate])
```

**说明**：销量是商品件数（一单可包含多件），订单是订单笔数。

## Comp 标记 ⚪

```sql
IF([IsComp] = TRUE, 'Y', 'N')
```

**口径**：Comp = 同店可比（Comparable Store），是连锁餐饮看"剔除新店扰动"的核心标记。Comp 老店 = 开业满 1 年的现役老店。

详细判定见 [04 章 · 成长类型](04-channel-and-store.md#成长类型)。

## TC_CRM% / NS_CRM%（会员渗透）🅰️

```sql
-- TC_CRM%（会员订单数 / 总订单数）
COUNT(DISTINCT IF([日用户类型] != '非会员', [订单号], NULL))
  / COUNT(DISTINCT [订单号])

-- NS_CRM%（会员营业额 / 总营业额）
SUM(IF([日用户类型] != '非会员', [去税营业额 NS], 0))
  / SUM([去税营业额 NS])
```

**口径**：CRM% = "会员对总盘子的贡献率"，业务侧最看重的两个数。
- TC_CRM% 看"多少笔订单是会员下的"
- NS_CRM% 看"会员贡献了多少营业额"

**坑**：分母**不要加 IF 过滤**，必须是全量基数。

## 营收 / 订单 / 渠道占比 🅱️

### 堂食营收占比

```sql
IF(
  (SUM([堂食营收]) + SUM([外卖营收])) = 0,
  0,
  SUM([堂食营收]) / (SUM([堂食营收]) + SUM([外卖营收]))
)
```

### 外卖订单占比

```sql
IF(
  (SUM([堂食订单数]) + SUM([外卖订单数])) = 0,
  0,
  SUM([外卖订单数]) / (SUM([堂食订单数]) + SUM([外卖订单数]))
)
```

### 堂食订单占比

```sql
IF(
  (SUM([堂食订单数]) + SUM([外卖订单数])) = 0,
  0,
  SUM([堂食订单数]) / (SUM([堂食订单数]) + SUM([外卖订单数]))
)
```

**为什么要用 IF 兜底分母**：

| 不兜底 | 兜底后 |
|---|---|
| 当筛选条件下没数据时，分母为 0 → SQL 报错 "Division by zero" 或返回 NULL | 当筛选条件下没数据时，返回 0，看板/卡片不会显示空白红叉 |

**适用**：所有"X / (X + Y)" 形式的占比卡片字段。

## 总计 / 累计指标（开窗版）⚪

### 顾客累计消费订单数

```sql
SELECT *,
  COUNT(DISTINCT `订单号`) OVER (PARTITION BY `会员号MemberShipID`) AS `订单数量`
FROM input1;
```

### 顾客累计消费金额

```sql
SELECT *,
  SUM(`去税营业额 NS`) OVER (PARTITION BY `会员号MemberShipID`) AS `累计消费金额`
FROM input1;
```

**特点**：
- 这是"明细行 + 衍生汇总列"模式（不是 GROUP BY 收敛行数）
- 适合下游需要"每条明细订单都带上该会员的累计值"的场景（如打标、客户分群）
- 不能按时间维度做条件聚合，但**可以做时间筛选** —— 例如先 WHERE 当年订单，再 OVER 算"当年累计"

### 顾客累计金额（不分时间）

```sql
SUM([含税营业额 GS]) OVER (PARTITION BY [会员号MemberShipID])
```

## 客单类型（价格分桶）🅰️

```sql
CASE
  WHEN [Gross_sales] < 20  THEN '[0 ,20) 元'
  WHEN [Gross_sales] < 30  THEN '[20,30) 元'
  WHEN [Gross_sales] < 40  THEN '[30,40) 元'
  WHEN [Gross_sales] < 60  THEN '[40,60) 元'
  WHEN [Gross_sales] < 80  THEN '[60,80) 元'
  ELSE                          '[80,+∞) 元'
END
```

**用途**：客单价分布图、客单价×渠道交叉分析。

**坑**：阈值要按你方"实际客单中位数"动态调，低客单品类（咖啡/茶饮）与中高客单品类（正餐/火锅）的区间不同。

## 折扣率 ⚪

```sql
-- 简版（Discount + ALA_Sales 都是 SUM 后的值）
SUM([Discount]) / SUM([ALA_Sales])

-- 完整版（原价 - 含税 = 折让金额）
SUM([原价金额 ALA_Sales] - [含税营业额 GS]) / SUM([原价金额 ALA_Sales])
```

详见 [05 章 · 折扣类型与折扣分桶](05-coupon-and-discount.md#折扣类型)。

## 频次（汇总版）⚪

```sql
COUNT(DISTINCT [订单号]) / COUNT(DISTINCT [会员号MemberShipID])
```

**口径**：会员的"平均消费频次"，等同于 [02 章 · 消费频次-全表均值](02-customer-and-membership.md#消费频次--全表均值卡片字段表达式)，区别在这里分母用 `会员号` 而不是 `顾客标识`（窄口径，只数注册会员）。

## 共消费几笔订单 / 多少钱（顾客明细）⚪

```sql
-- 共消费几笔订单
COUNT([订单日期]) OVER (PARTITION BY [会员号MemberShipID])

-- 共消费多少钱（不能按时间维度，但可以按年筛选后再算）
SUM([含税营业额 GS]) OVER (PARTITION BY [会员号MemberShipID])
```

**坑**：`COUNT(订单日期)` 不去重 = 订单数（一单一行的明细表里成立）；如果是订单-商品明细的"宽表"，必须改为 `COUNT(DISTINCT 订单号)` 否则一单多行会被重复计数。

## 累计人数（注册时序）⚪

```sql
SUM(1) OVER (PARTITION BY 1 ORDER BY [注册时间])
```

**用途**：注册时间序列下的累计注册人数（折线图横轴是注册日期，纵轴是累计数）。

**关键**：`PARTITION BY 1` 意为"不分区"，整张表作一个窗口；`ORDER BY 注册时间` 触发累计语义。

## 折扣率（完整业务版）⚪

```sql
SUM([原价金额 ALA_Sales] - [含税营业额 GS]) / SUM([原价金额 ALA_Sales])
```

**口径解读**：
- 分子 = 原价 - 实收 = 让利金额
- 分母 = 原价
- 结果 = 折扣率（0~1，越高让利越多）

**和 5 章的差异**：

| 文件 | 口径 |
|---|---|
| 本节（03） | 按 SUM 后的差值算，**聚合级折扣率** |
| [05 章 · 折扣类型](05-coupon-and-discount.md#折扣类型) | 按订单级 Disct% 字段分桶，**单笔订单折扣区间** |
