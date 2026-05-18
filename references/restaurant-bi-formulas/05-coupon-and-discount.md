# 05 · 券与折扣

> 营销活动归因专区。**核心模式**：用 `券号 / 活动编号 / 券类型编号` 三个字段做归因，配合"首张券 / 注册第一张券 / 30 天优惠订单比例"做精细化分析。

## 核销率 ⚪

```sql
COUNT([核券日期]) / COUNT([发券日期])
```

**口径**：分子 = 有核券日期的券数 / 分母 = 已发出的券数 = 核销率。

**变体（卡片字段）**：

```sql
-- 仅数已核销的券数
COUNT(DISTINCT IF([券状态] = '已使用', [券号], NULL))
```

**坑**：分子/分母**不要用同一个字段双重 IF**，否则核销率永远是 1。

## 折扣率（聚合级 vs 单笔级）⚪

### 聚合级折扣率（卡片 KPI）

```sql
-- 简版
SUM([Discount]) / SUM([ALA_Sales])

-- 完整业务版
SUM([原价金额 ALA_Sales] - [含税营业额 GS]) / SUM([原价金额 ALA_Sales])
```

详见 [03 章 · 折扣率](03-revenue-kpi.md#折扣率)。

### 单笔级折扣率（订单字段）

通常预先算好 `Disct%` 字段（在 ETL 阶段），值域 0~1：

```sql
[Disct%] = 1 - [含税营业额 GS] / [原价金额 ALA_Sales]
-- 0 = 没折扣，1 = 全免，0.3 = 打 7 折
```

## 折扣类型（分桶）🅰️ {#折扣类型}

```sql
CASE
  WHEN [Disct%] <= 0   THEN '无优惠'
  WHEN [Disct%] <= 0.1 THEN '(0%,10%]'
  WHEN [Disct%] <= 0.2 THEN '(10%,20%]'
  WHEN [Disct%] <= 0.3 THEN '(20%,30%]'
  WHEN [Disct%] <= 0.5 THEN '(30%,50%]'
  WHEN [Disct%] <  1   THEN '(50%,100%)'
  ELSE                      '免费'
END
```

**口径**：把单笔订单按折扣率分到 7 个桶。
- `'无优惠'`：原价订单（也包括录入异常的负折扣）
- `'(0%, 10%]`、`(10%, 20%]`...：常规折扣力度
- `'(50%, 100%)'`：5 折以下到接近免费
- `'免费'`：100% 减免（券赠送、纠错退款）

**用途**：折扣力度分布饼图、不同折扣区间的订单/营收占比对比。

## 券类型分流（活动归因大 case）🅰️

```sql
CASE
  WHEN [活动编号] = 'XX20220026' THEN '0次客35天未消费V6'
  WHEN [券名] LIKE '%品牌好礼%' THEN '面对面发券'
  WHEN [券类型编号] = '1290700000000084' OR [券类型编号] = '1290700000000199' THEN '面对面发券'
  WHEN [FirstCoupon_typeName] LIKE '%店|饮品买一赠一券%'
    OR [FirstCoupon_typeName] LIKE '%店+1元购暖食%' THEN '新店bogo'
  WHEN [是否会员] = '是会员' AND [添加距离注册] < 0 THEN '老会员'
  ELSE NULL
END
```

**口径**：把上百个活动编号 / 券类型 / 券名归一成几个业务大类（"0 次客唤回"、"面对面发券"、"新店 bogo"、"老会员"）。**绝对值码（如活动编号、券类型编号）和模糊匹配（LIKE 券名）混用**，这是餐饮营销 BI 的常态：活动编号是新系统的，模糊匹配兼容老系统手填数据。

**复用方法**：把上面"活动编号 / 券类型 / 券名"换成你方对应字段，把分类标签按你方营销规则重新设计。

## 注册第一张券 🅰️

```sql
CASE
  WHEN [FirstCoupon_DisDate] = [注册日期]
    THEN [FirstCoupon_typeName]
  ELSE NULL
END
```

**口径**：只有当"首张券的发券日期 = 注册日期"时，才认为这是"注册当天系统自动发的注册礼券"。否则留 NULL（说明首张券是后续运营触发的，不算注册礼券）。

**业务用途**：判断"注册礼券"是否覆盖到所有新会员（注册当天有礼券 → 1，反之 → 0）。

## 会员的第一张券 🅰️

```sql
ROW_NUMBER() OVER (PARTITION BY [dis_cardno] ORDER BY [dis_disDate])
```

**口径**：按会员卡号分组、按发券日期升序排，结果 = 1 的就是"该会员收到的第一张券"。配合 `WHERE rn = 1` 取出首张券明细。

**变体**：
- `ORDER BY [dis_disDate] DESC` 取最新券
- `ORDER BY [dis_disDate], [券面值] DESC` 同日多券取面值最高的

## 过去 30 日优惠订单比例 🅰️

```sql
SELECT
  user_id AS id,
  MAX(distinct_id) AS distinct_id,
  CASE
    WHEN SUM(IF(is_coupon = 1, 1, 0)) / COUNT(is_coupon) = 0    THEN '无使用率'
    WHEN SUM(IF(is_coupon = 1, 1, 0)) / COUNT(is_coupon) <= 0.4 THEN '低使用率'
    WHEN SUM(IF(is_coupon = 1, 1, 0)) / COUNT(is_coupon) <= 0.6 THEN '中使用率'
    ELSE                                                              '高使用率'
  END AS value
FROM events
WHERE event = 'pay_order'
  AND time BETWEEN FROM_TIMESTAMP(days_sub(now(), 30), 'yyyy-MM-dd')
              AND FROM_TIMESTAMP(days_sub(now(), 1),  'yyyy-MM-dd')
GROUP BY user_id;
```

**口径**：分子 = 用券订单数 / 分母 = 全部订单数。

**业务用途**：精细化运营人群分桶，"低使用率人群"是营销重点（券对其敏感）；"高使用率人群"反而要警惕（券依赖症，撤券就流失）。

**坑**：判 NULL 之外，注意 `is_coupon` 字段在不同业务里可能是布尔/0-1/'Y'-'N' 三种类型，按实际转换。

## 券核销卡片表达式 🅱️

简单卡片字段（不用 ETL）：

```sql
-- 已使用券数
COUNT(DISTINCT IF([券状态] = '已使用', [券号], NULL))

-- 已发券数
COUNT(DISTINCT [券号])

-- 核销率
COUNT(DISTINCT IF([券状态] = '已使用', [券号], NULL))
  * 1.0
  / NULLIF(COUNT(DISTINCT [券号]), 0)
```

## 发券时间近 3 个月 ⚪

```sql
SELECT * FROM input1
WHERE input1.`发券日期` >= add_months(concat(substr(current_date(), 1, 7), '-01'), -3);
```

**用途**：分析"近 3 月发券效果"，配合后续按月分桶计算"发券月 → 核销月"的核销时滞。
