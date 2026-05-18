# 02 · 顾客与会员

> 餐饮 BI 一半以上业务围绕"顾客"展开：会员 vs 非会员、新客 vs 老客、首单 vs 复购、留存 vs 流失。本节按**顾客标识 → 频次 → 复购 → 留存流失 → RFM 分类 → 注册前后行为**五步走。

## 顾客标识统一化 🅱️

跨渠道（会员卡 / 微信 / 支付宝 / 云闪付）的顾客 ID 必须**统一成一个 `顾客标识` 字段**，否则会员频次会被同一人的不同支付方式拆碎。

```sql
SELECT
  `会员卡号`,
  `微信支付openid`,
  `支付宝用户id`,
  `云闪付用户id`,

  /* 顾客标识：按优先级取第一个非空 */
  CASE
    WHEN `会员卡号` IS NOT NULL AND `会员卡号` != ''       THEN `会员卡号`
    WHEN `微信支付openid` IS NOT NULL AND `微信支付openid` != '' THEN `微信支付openid`
    WHEN `支付宝用户id` IS NOT NULL AND `支付宝用户id` != ''     THEN `支付宝用户id`
    WHEN `云闪付用户id` IS NOT NULL AND `云闪付用户id` != ''     THEN `云闪付用户id`
    ELSE ''
  END AS `顾客标识`,

  /* 标识分类：记录顾客标识来自哪个渠道，便于后续分析 */
  CASE
    WHEN `会员卡号` IS NOT NULL AND `会员卡号` != '' THEN '会员卡'
    WHEN `微信支付openid` IS NOT NULL AND `微信支付openid` != '' THEN '微信支付'
    WHEN `支付宝用户id` IS NOT NULL AND `支付宝用户id` != '' THEN '支付宝'
    WHEN `云闪付用户id` IS NOT NULL AND `云闪付用户id` != '' THEN '云闪付'
    ELSE '未知'
  END AS `标识分类`

FROM input1;
```

**坑**：
- 优先级要明确写好（会员卡 > 微信 > 支付宝 > 云闪付），否则跨表 join 时同一笔订单可能被分类到不同来源
- 字符串"null"（小写 4 字符）也要判，详见 [07 章三态判断](07-data-quality-traps.md#三态判断)

## 会员属性 ⚪

按"添加好友日期 vs 注册日期"判断"新会员 / 老会员"：

```sql
CASE
  WHEN [是否会员] = '是会员' AND [添加距离注册] >= 0 THEN '新会员'
  WHEN [是否会员] = '是会员' AND [添加距离注册] <  0 THEN '老会员'
  ELSE '非会员'
END
```

**口径**：`[添加距离注册] = DATEDIFF(添加好友日期, 注册日期)`
- 添加好友**在注册之后**（差值 ≥ 0）= 新会员（先注册再加好友 = 会员后行为）
- 添加好友**在注册之前**（差值 < 0）= 老会员（先加好友再注册 = 老粉转化）

## 新客 / 老客（多维度）⚪🅱️

### 日维度（卡片表达式版）🅰️

```sql
CASE
  WHEN [MemberType] = 'New'        THEN '日新客'
  WHEN [MemberType] = 'NonMember'  THEN '非会员'
  ELSE '日老客'
END
```

### 日维度（ETL 计算版，按"全历史第 1 单"）🅱️

```sql
/* 新老客-日：仅全历史第 1 单为"日新客"，其余均为"日老客" */
CASE
  WHEN ROW_NUMBER() OVER (
         PARTITION BY I.`顾客标识`
         ORDER BY to_timestamp(I.`下单时间`, 'yyyy-MM-dd HH:mm:ss'), I.`订单号`
       ) = 1
  THEN '日新客'
  ELSE '日老客'
END AS `新老客-日`
```

### 月维度 🅰️🅱️

```sql
-- 卡片表达式版
CASE
  WHEN [MemberType] = 'NonMember'       THEN '非会员'
  WHEN [首单日期] < [月开始日期]        THEN '月老客'
  ELSE '月新客'
END

-- ETL 版（按"首单所在月" = "当前订单所在月"判月新客）
CASE
  WHEN date_trunc('month', to_timestamp(I.`下单时间`, 'yyyy-MM-dd HH:mm:ss'))
       = MIN(date_trunc('month', to_timestamp(I.`下单时间`, 'yyyy-MM-dd HH:mm:ss')))
           OVER (PARTITION BY I.`顾客标识`)
  THEN '月新客'
  ELSE '月老客'
END AS `新老客-月`
```

### 周维度 🅰️

```sql
CASE
  WHEN [MemberType] = 'NonMember'           THEN '非会员'
  WHEN [首单日期] < [营运周开始日期]        THEN '周老客'
  ELSE '周新客'
END
```

**口径对比**：
- "日新客" 在不同业务里有两种定义：(a) 顾客的**生命周期首单当天** = 日新客（餐饮连锁 B 口径），(b) **首次会员注册当天有单** = 日新客（餐饮连锁 A 用 `MemberType='New'`，强调"会员状态" not "首单"）。**统计前必须先和业务方对清楚**。

## 月活跃类型 🅰️

把"非会员 / 月新 / 月老 / 召回"统一到一个字段，按优先级回填：

```sql
CASE
  WHEN [MemberType] = 'NonMember' THEN '非会员'
  ELSE ifnull([活跃类型], [月用户类型])
END
```

## 30 天消费会员拆解 🅰️

把"日新客 / 召回 / 活跃"按近 30 天频次类型再拆细，用于精细化运营分群。

```sql
CASE
  WHEN [日用户类型] = '日新客'   THEN '日新客'
  WHEN [月活跃类型] = '召回'     THEN '召回'
  ELSE CONCAT('活跃', [近30天频次类型])
END
```

输出形如：`日新客` / `召回` / `活跃高频` / `活跃中频` / `活跃低频`。

## 消费频次（3 个口径）🅱️

> ⚠️ **doc 2 原文有 4 个"消费频次"标题，本节去重并按粒度区分**。

### 消费频次 — 全表均值（卡片字段表达式）

```sql
COUNT(DISTINCT IF([顾客标识] IS NOT NULL AND TRIM([顾客标识]) <> '', [订单号], NULL))
/ COUNT(DISTINCT IF([顾客标识] IS NOT NULL AND TRIM([顾客标识]) <> '', [顾客标识], NULL))
```

**口径**：分子 = 有效顾客标识的去重订单数 / 分母 = 有效顾客标识的去重人数。结果是"每个顾客平均消费几次"。

**适用**：卡片 KPI 字段、看板默认聚合。

### 消费频次 — 顾客明细（ETL 输出）

```sql
SELECT
  `顾客标识`,
  ROUND(
    COUNT(DISTINCT IF(`顾客标识` IS NOT NULL AND `顾客标识` <> '', `订单号`, NULL)) * 1.0
    / NULLIF(
        COUNT(DISTINCT IF(`顾客标识` IS NOT NULL AND `顾客标识` <> '', `顾客标识`, NULL)),
        0
      ),
    4
  ) AS `消费频次`
FROM input1
GROUP BY `顾客标识`;
```

**口径**：每位顾客的"订单数 / 自身去重人数（恒为 1）" = 该顾客的订单总数。

**适用**：ETL 节点输出，作为下游 RFM 的 F 维度。

**坑**：`NULLIF(..., 0)` 兜底，避免 GROUP BY 出现极少数空记录导致除 0。

### 消费频次 — 门店×会员维度（聚合分析）

```sql
SELECT
  `门店编号`,
  `是否会员`,
  COUNT(DISTINCT IF(`顾客标识` != '', `订单号`, NULL)) * 1.0 /
  COUNT(DISTINCT IF(`顾客标识` != '', `顾客标识`, NULL)) AS `消费频次`
FROM input1
GROUP BY `门店编号`, `是否会员`;
```

**口径**：每家门店、每种会员状态下的"平均消费频次"。结果是个二维表，行 = 门店 × 是否会员。

**适用**：门店运营对比、会员 vs 非会员频次对比。

## 人均消费 🅰️🅱️

```sql
-- 卡片表达式版
SUM(IF([顾客标识] IS NOT NULL AND [顾客标识] != '', [income_应收], NULL))
/ COUNT(DISTINCT IF([顾客标识] IS NOT NULL AND [顾客标识] != '', [顾客标识], NULL))

-- ETL 门店×会员维度版 🅱️
SELECT
  `门店编号`,
  `是否会员`,
  SUM(IF(`顾客标识` != '', `income_应收`, NULL)) * 1.0
    / COUNT(DISTINCT IF(`顾客标识` != '', `顾客标识`, NULL)) AS `人均消费`
FROM input1
GROUP BY `门店编号`, `是否会员`;
```

## 复购口径（跨天 vs 非跨天）🅱️ {#复购口径}

### 跨天复购（同一天买多次只算 1 天，至少 2 个不同日期才算复购）

```sql
WITH user_order_count AS (
  SELECT
    `门店编号`,
    `是否会员`,
    `顾客标识`,
    COUNT(DISTINCT CAST(`订单日期` AS DATE)) AS TC   -- 注意：去重的是日期
  FROM input1
  WHERE `顾客标识` IS NOT NULL AND `顾客标识` != ''
  GROUP BY `门店编号`, `是否会员`, `顾客标识`
)
SELECT
  `门店编号`,
  `是否会员`,
  COUNT(DISTINCT `顾客标识`) AS `下单人数`,
  COUNT(DISTINCT IF(TC >= 2, `顾客标识`, NULL)) AS `复购人数`,
  COUNT(DISTINCT IF(TC >= 2, `顾客标识`, NULL)) * 1.0
    / COUNT(DISTINCT `顾客标识`) AS `复购率`
FROM user_order_count
GROUP BY `门店编号`, `是否会员`;
```

### 非跨天复购（订单数 TC ≥ 2 即复购）

```sql
WITH user_order_count AS (
  SELECT
    `门店编号`,
    `是否会员`,
    `顾客标识`,
    COUNT(DISTINCT `订单号`) AS TC   -- 注意：去重的是订单号
  FROM input1
  WHERE `顾客标识` IS NOT NULL AND `顾客标识` != ''
  GROUP BY `门店编号`, `是否会员`, `顾客标识`
)
SELECT
  `门店编号`,
  `是否会员`,
  COUNT(DISTINCT `顾客标识`) AS `下单人数`,
  COUNT(DISTINCT IF(TC >= 2, `顾客标识`, NULL)) AS `复购人数`,
  COUNT(DISTINCT IF(TC >= 2, `顾客标识`, NULL)) * 1.0
    / COUNT(DISTINCT `顾客标识`) AS `复购率`
FROM user_order_count
GROUP BY `门店编号`, `是否会员`;
```

**两种口径的差异**：

| 场景 | 跨天复购口径 | 非跨天复购口径 |
|---|---|---|
| 顾客 A 在同一天下了 5 单 | TC = 1，**不算复购** | TC = 5，**算复购** |
| 顾客 B 在 2 天下了 2 单 | TC = 2，**算复购** | TC = 2，**算复购** |

**业务选择**：
- 看"是否养成回访习惯" → 跨天复购更严格
- 看"是否产生持续交易" → 非跨天复购更宽松
- **混用一定会被业务方质疑数据对不上**

## 卡片表达式版的下单 / 复购 🅰️

简化的"是否下单 / 是否复购"标记，用于卡片层的统计：

```sql
-- 下单人数（按 TC 字段判，至少 1 单）
CASE WHEN [TC] >= 1 THEN 1 ELSE NULL END

-- 复购人数（TC >= 2）
CASE WHEN [TC] >= 2 THEN 1 ELSE NULL END

-- 下单转化率
SUM([下单人数]) / COUNT(DISTINCT [会员卡号])

-- 复购率
SUM([复购人数]) / SUM([下单人数])
```

## 最后一单距今天数 🅱️

```sql
SELECT
  `顾客标识`,
  GREATEST(
    0,
    DATEDIFF(
      date_sub(CURRENT_DATE, 1),    -- 锚定昨天
      MAX(TO_DATE(`订单日期`))
    )
  ) AS `最后一单距离今天的天数`
FROM input1
WHERE `顾客标识` IS NOT NULL AND `顾客标识` <> ''
GROUP BY `顾客标识`;
```

**坑**：`GREATEST(0, ...)` 是为了防止脏数据里出现"未来订单日期"导致负数（餐饮连锁 B 真遇到过门店时间设错的情况）。

## RFM 顾客分类（8 类）🅱️

经典的 RFM 三维拆分。**阈值（R=30 天 / F=2 次 / M=66 元）需要按你方业务调**。

```sql
SELECT
  `顾客标识`,

  /* R/F/M 的高低 */
  CASE WHEN `最后一单距今天数` <= 30 THEN '高' ELSE '低' END AS R,
  CASE WHEN `消费频次`         >= 2  THEN '高' ELSE '低' END AS F,
  CASE WHEN `消费金额`         >= 66 THEN '高' ELSE '低' END AS M,

  /* 组合 RFM */
  CONCAT(
    CASE WHEN `最后一单距今天数` <= 30 THEN '高' ELSE '低' END,
    CASE WHEN `消费频次`         >= 2  THEN '高' ELSE '低' END,
    CASE WHEN `消费金额`         >= 66 THEN '高' ELSE '低' END
  ) AS `RFM`,

  /* 顾客类型 — 8 类标准映射 */
  CASE
    WHEN `最后一单距今天数` <= 30 AND `消费频次` >= 2 AND `消费金额` >= 66 THEN '重要价值客户'
    WHEN `最后一单距今天数` <= 30 AND `消费频次` >= 2 AND `消费金额` <  66 THEN '一般价值客户'
    WHEN `最后一单距今天数` <= 30 AND `消费频次` <  2 AND `消费金额` >= 66 THEN '重要发展客户'
    WHEN `最后一单距今天数` <= 30 AND `消费频次` <  2 AND `消费金额` <  66 THEN '一般发展客户'
    WHEN `最后一单距今天数` >  30 AND `消费频次` >= 2 AND `消费金额` >= 66 THEN '重要保持客户'
    WHEN `最后一单距今天数` >  30 AND `消费频次` >= 2 AND `消费金额` <  66 THEN '一般保持客户'
    WHEN `最后一单距今天数` >  30 AND `消费频次` <  2 AND `消费金额` >= 66 THEN '重要挽留客户'
    ELSE '一般挽留客户'
  END AS `顾客类型`
FROM input1;
```

**口径解读**：
- R 高 = 近 30 天有消费（活跃）
- F 高 = 累计消费 ≥ 2 次（有粘性）
- M 高 = 累计金额 ≥ 66 元（贡献度）
- 三高 → 价值最高的"重要价值客户"；R 低 + F 高 + M 高 → 已流失的"重要挽留客户"

### RFM 8 类 × 营销策略对应（生产 ETL 加强版）

实战 V1 ETL 在 RFM 输出列后**多加了一列「营销策略」**，把"标签 → 该做什么动作"直接落到字段里，下游卡片/运营 SOP 直接照用。**这些策略词是行业通用参考（拼凑自 BI 教材 / 同行经验），非原创方法论，仅作为"运营动作示例"保留**。

```sql
SELECT
  `顾客标识`,

  /* R/F/M 标签（业务化文案）*/
  CASE WHEN `最后一单距今天数` <= 30 THEN '近期来过' ELSE '很久没来' END AS R,
  CASE WHEN `消费频次`         >= 2  THEN '常客'     ELSE '频次低' END AS F,
  CASE WHEN `消费金额`         >= 66 THEN '消费高'   ELSE '花钱少' END AS M,

  /* 顾客类型 8 类（同上 8 类映射，省略）*/
  CASE WHEN ... THEN '重要价值客户' ... END AS `顾客类型`,

  /* 营销策略（参考动作） */
  CASE
    WHEN `最后一单距今天数` <= 30 AND `消费频次` >= 2 AND `消费金额` >= 66
      THEN '提供 VIP 服务，新品尝鲜等'
    WHEN `最后一单距今天数` <= 30 AND `消费频次` >= 2 AND `消费金额` <  66
      THEN '推荐套餐或加价购提高客单价'
    WHEN `最后一单距今天数` <= 30 AND `消费频次` <  2 AND `消费金额` >= 66
      THEN '激励其提高消费频率，如赠送次卡'
    WHEN `最后一单距今天数` <= 30 AND `消费频次` <  2 AND `消费金额` <  66
      THEN '首单新顾客，发优惠券引导二次消费'
    WHEN `最后一单距今天数` >  30 AND `消费频次` >= 2 AND `消费金额` >= 66
      THEN '主动关怀，通过优惠券或活动召回'
    WHEN `最后一单距今天数` >  30 AND `消费频次` >= 2 AND `消费金额` <  66
      THEN '"强心针"式优惠召回并进行问卷调查'
    WHEN `最后一单距今天数` >  30 AND `消费频次` <  2 AND `消费金额` >= 66
      THEN '提供专属的人性化服务，给予情绪价值'
    ELSE
      '低优先级召回对象或进行问卷调查'
  END AS `营销策略`
FROM input1;
```

**对应表速查**：

| R | F | M | 顾客类型 | 参考运营动作 |
|---|---|---|---|---|
| 高 | 高 | 高 | 重要价值客户 | VIP 服务、新品尝鲜 |
| 高 | 高 | 低 | 一般价值客户 | 套餐 / 加价购抬客单 |
| 高 | 低 | 高 | 重要发展客户 | 次卡 / 频次激励 |
| 高 | 低 | 低 | 一般发展客户 | 二次消费券引导 |
| 低 | 高 | 高 | 重要保持客户 | 优惠券 / 活动召回 |
| 低 | 高 | 低 | 一般保持客户 | 强心针优惠 + 问卷调查 |
| 低 | 低 | 高 | 重要挽留客户 | 专属人性化服务 |
| 低 | 低 | 低 | 一般挽留客户 | 低优先级问卷 |

**用法**：把"营销策略"列同步给营销系统/CDP，自动化触达不同人群。

### R 阈值多档分级（按业务场景调）

doc 2 默认用 30 天单一阈值。**生产 ETL 中按业务场景至少有两种更精细的分级**：

#### 三档分级（用于活跃度运营，关注短期）

```sql
CASE
  WHEN `R天数` < 21  THEN '活跃（21 天内有消费）'
  WHEN `R天数` < 46  THEN '低活（21~45 天内有消费）'
  WHEN `R天数` <= 90 THEN '沉默（46~90 天内有消费）'
  ELSE                    '流失（90 天内无消费）'
END AS `顾客状态`
```

**适用**：私域运营周报、社群活跃度分析。每周末跑一次。

#### 四档分级（用于流失预警，关注衰减曲线）

```sql
CASE
  WHEN DATEDIFF(CURRENT_DATE(), `最后消费日期`) >= 60 THEN '60 天未消费'
  WHEN DATEDIFF(CURRENT_DATE(), `最后消费日期`) >= 30 THEN '30 天未消费'
  WHEN DATEDIFF(CURRENT_DATE(), `最后消费日期`) >= 21 THEN '21 天未消费'
  WHEN DATEDIFF(CURRENT_DATE(), `最后消费日期`) >= 14 THEN '14 天未消费'
  ELSE                                                     '14 天内有消费'
END AS `流失状态`
```

**适用**：营销分级触达。14/21/30/60 四档对应不同力度的优惠券推送策略。

**阈值选择决策表**：

| 业务场景 | 推荐分级 | 阈值要点 |
|---|---|---|
| 日活报表（每日刷新）| 单档 30 天 | 简单粗暴够用 |
| 周活/月活分析 | 三档 21/46/90 | 卡住"周/月活跃" 自然分界 |
| 流失预警 / 营销分级 | 四档 14/21/30/60 | 流失曲线分层细 |
| 重点客户挽回 | 单档 90 天 | 90 天 = "几乎已流失"的行业共识 |

**坑**：阈值定下来就不要乱改，否则历史报表口径变了，业务方会问"为什么上月活跃用户数对不上"。要调先和业务方对齐再发版。

## 90 天复购分桶 🅱️

把"首购日 ≤ 今天-90 天"的所有顾客分到 6 + 1 个桶里，按"下一次下单距首购的天数"切分，看保留曲线：

```sql
/* —— 锚定日：今天往前 90 天及之前的所有首购日（动态计算）—— */
SELECT
  R.`门店编号`,
  R.`门店名称`,
  R.`分公司`,
  R.`是否会员`,
  R.`复购状态`,
  COUNT(*) AS `顾客数`,
  SUM(COUNT(*)) OVER (
    PARTITION BY R.`门店编号`, R.`门店名称`, R.`分公司`, R.`是否会员`
  ) AS `顾客第一单数`    -- cohort 基数（分母）
FROM (
  SELECT
    C.`顾客标识`,
    F.`门店编号`,
    F.`门店名称`,
    F.`分公司`,
    F.`是否会员`,
    C.`first_date`,
    MIN(CAST(I2.`订单日期` AS DATE)) AS `next_date`,
    CASE
      WHEN MIN(CAST(I2.`订单日期` AS DATE)) IS NULL
           OR DATEDIFF(MIN(CAST(I2.`订单日期` AS DATE)), C.`first_date`) > 90
        THEN '>90天未消费/未复购'
      WHEN DATEDIFF(MIN(CAST(I2.`订单日期` AS DATE)), C.`first_date`) > 60 THEN '61-90天复购'
      WHEN DATEDIFF(MIN(CAST(I2.`订单日期` AS DATE)), C.`first_date`) > 30 THEN '31-60天复购'
      WHEN DATEDIFF(MIN(CAST(I2.`订单日期` AS DATE)), C.`first_date`) > 21 THEN '22-30天复购'
      WHEN DATEDIFF(MIN(CAST(I2.`订单日期` AS DATE)), C.`first_date`) > 14 THEN '15-21天复购'
      WHEN DATEDIFF(MIN(CAST(I2.`订单日期` AS DATE)), C.`first_date`) > 7  THEN '8-14天复购'
      ELSE '1-7天复购'
    END AS `复购状态`
  FROM (
    /* cohort：全历史首购日 <= 今天-90 天的顾客 */
    SELECT FB.`顾客标识`, FB.`first_date`
    FROM (
      SELECT
        I.`顾客标识`,
        MIN(CAST(I.`订单日期` AS DATE)) AS `first_date`
      FROM input1 I
      WHERE I.`顾客标识` IS NOT NULL AND I.`顾客标识` <> ''
        AND I.`订单日期` IS NOT NULL
      GROUP BY I.`顾客标识`
    ) FB
    WHERE FB.`first_date` <= date_sub(current_date(), 90)
  ) C
  LEFT JOIN (
    /* 首购当日的一条订单，拿门店/分公司/是否会员做归属 */
    SELECT *
    FROM (
      SELECT
        I0.`顾客标识`,
        CAST(I0.`订单日期` AS DATE) AS `ord_date`,
        I0.`门店编号`, I0.`门店名称`, I0.`分公司`, I0.`是否会员`,
        ROW_NUMBER() OVER (
          PARTITION BY I0.`顾客标识`, CAST(I0.`订单日期` AS DATE)
          ORDER BY to_timestamp(I0.`下单时间`, 'yyyy-MM-dd HH:mm:ss'), I0.`订单号`
        ) AS rn
      FROM input1 I0
      WHERE I0.`订单日期` IS NOT NULL
    ) T0
    WHERE T0.rn = 1
  ) F
    ON F.`顾客标识` = C.`顾客标识` AND F.`ord_date` = C.`first_date`
  /* 下一次下单（严格大于首购日，同日多单不算"再次"）*/
  LEFT JOIN input1 I2
    ON I2.`顾客标识` = C.`顾客标识`
   AND I2.`订单日期` IS NOT NULL
   AND CAST(I2.`订单日期` AS DATE) > C.`first_date`
  GROUP BY C.`顾客标识`, F.`门店编号`, F.`门店名称`, F.`分公司`, F.`是否会员`, C.`first_date`
) R
GROUP BY R.`门店编号`, R.`门店名称`, R.`分公司`, R.`是否会员`, R.`复购状态`
ORDER BY R.`分公司`, R.`门店编号`, R.`是否会员`, R.`复购状态`;
```

**输出形态**：每家门店 × 会员状态 × 7 个复购分桶（1-7 / 8-14 / 15-21 / 22-30 / 31-60 / 61-90 / >90），可直接做留存漏斗图。

**坑**：
- "下一次下单"用 `严格 > C.first_date`，同日多单不算复购（避免 90 天复购率虚高）
- `>90天未消费/未复购` 桶包含两种人：(a) 真的没复购 (b) `next_date IS NULL`（首购后再没下过单）

## 注册前后订单分群（CTE 4 层嵌套窗口）🅱️

判断"会员究竟是先消费再注册（老客转会员），还是先注册再消费（纯新会员）"。这是 doc 2 里最复杂的一段 SQL，体现了 BI 分析师对"会员归因"的细致处理。

```sql
WITH member_reg AS (
  /* 1. 每位会员的"注册日期" */
  SELECT
    I.`顾客标识`,
    MIN(CAST(I.`注册日期` AS DATE)) AS `注册日期`
  FROM input1 I
  WHERE I.`是否会员` = '会员'
    AND I.`顾客标识` IS NOT NULL AND I.`顾客标识` <> ''
    AND I.`注册日期` IS NOT NULL
  GROUP BY I.`顾客标识`
),

member_orders AS (
  /* 2. 这些会员的全部订单 + "下单距离注册" */
  SELECT
    I.`订单号`, I.`顾客标识`,
    CAST(I.`订单日期` AS DATE) AS `订单日期`,
    I.`门店编号`, I.`门店名称`, I.`分公司`,
    I.`income_应收`, I.`是否会员`,
    MR.`注册日期`,
    DATEDIFF(CAST(I.`订单日期` AS DATE), MR.`注册日期`) AS `下单距离注册`
    -- 注册前为负，注册当天 = 0，注册后为正
  FROM input1 I
  JOIN member_reg MR ON I.`顾客标识` = MR.`顾客标识`
  WHERE I.`订单日期` IS NOT NULL
),

member_orders_flag AS (
  /* 3. 在顾客维度打"有没有订单"的多窗口标记 */
  SELECT
    M.*,
    MAX(CASE WHEN M.`下单距离注册` < 0 THEN 1 ELSE 0 END)
      OVER (PARTITION BY M.`顾客标识`) AS has_pre_order,
    MAX(CASE WHEN M.`下单距离注册` > 0 THEN 1 ELSE 0 END)
      OVER (PARTITION BY M.`顾客标识`) AS has_post_order,
    -- 前后 30 / 60 / 90 天的等价标记（结构相同，省略，按需复用）
    MAX(CASE WHEN M.`下单距离注册` BETWEEN -30 AND -1 THEN 1 ELSE 0 END)
      OVER (PARTITION BY M.`顾客标识`) AS has_pre_30,
    MAX(CASE WHEN M.`下单距离注册` BETWEEN  1 AND 30 THEN 1 ELSE 0 END)
      OVER (PARTITION BY M.`顾客标识`) AS has_post_30
    -- 60、90 天同上
  FROM member_orders M
)

SELECT
  O.`订单号`, O.`顾客标识`, O.`订单日期`, O.`门店编号`, O.`门店名称`, O.`分公司`,
  O.`income_应收`, O.`是否会员`, O.`注册日期`, O.`下单距离注册`,

  /* 会员类型：看有没有注册前订单 */
  CASE WHEN O.has_pre_order = 1 THEN '老客转会员' ELSE '新客会员' END AS `会员类型`,

  /* 注册前后订单分群 */
  CASE
    WHEN O.has_pre_order = 1 AND O.has_post_order = 1 THEN '注册前后都有订单'
    WHEN O.has_pre_order = 1 AND O.has_post_order = 0 THEN '仅注册前有订单'
    WHEN O.has_pre_order = 0 AND O.has_post_order = 1 THEN '仅注册后有订单'
    ELSE '注册前后都无订单'   -- 只在注册当天有订单（罕见）
  END AS `注册前后订单分群`,

  CASE WHEN O.has_pre_30 = 1 AND O.has_post_30 = 1 THEN '是' ELSE '否' END
    AS `注册前后30天都有订单`

FROM member_orders_flag O;
```

**口径解读**：
- 注册前订单（下单距离注册 < 0）= 老客被运营拉来注册（"老客转会员"）
- 注册后订单（下单距离注册 > 0）= 注册后才下首单（"新客会员"）
- 注册当天订单（= 0）不计入前后判断，避免歧义

**业务用途**：
- 衡量"会员体系拉新效果" → 看"仅注册后有订单"占比
- 衡量"运营拉转化效果" → 看"老客转会员"占比
- 衡量"注册即流失" → 看"仅注册前有订单 + 注册当天无后续"

**方法论**：这套 CTE 4 层结构（基础聚合 → 衍生字段 → 窗口标记 → 最终归类）适合所有"用户行为前后比较"场景。**抄结构，换业务字段**。

## 累计会员总数 🅱️（累计窗口经典写法）

```sql
SELECT
  dsd.record_date AS `日期`,
  dsd.store_id    AS `注册门店编号`,
  dsd.store_name  AS `注册门店名称`,
  dsd.is_member   AS `是否会员`,
  SUM(COALESCE(da.daily_new_members, 0)) OVER (
    PARTITION BY dsd.store_id, dsd.is_member
    ORDER BY dsd.record_date
  ) AS `累计会员数`
FROM (
  /* 子查询1：完整日期×门店网格 */
  SELECT DISTINCT
    CAST(`注册日期` AS DATE) AS record_date,
    `注册门店编号` AS store_id,
    `注册门店名称` AS store_name,
    `是否会员`   AS is_member
  FROM input1
) AS dsd
LEFT JOIN (
  /* 子查询2：每日新增会员数 */
  SELECT
    CAST(`注册日期` AS DATE) AS record_date,
    `注册门店编号` AS store_id,
    `是否会员` AS is_member,
    COUNT(DISTINCT CASE WHEN `是否会员` = '会员' THEN `会员卡号` ELSE NULL END) AS daily_new_members
  FROM input1
  GROUP BY CAST(`注册日期` AS DATE), `注册门店编号`, `是否会员`
) AS da
  ON dsd.record_date = da.record_date
 AND dsd.store_id    = da.store_id
 AND dsd.is_member   = da.is_member
ORDER BY dsd.store_id, dsd.is_member, dsd.record_date;
```

**结构要点**：先构网格 (`DISTINCT` 拉出所有日期×门店组合) 再 LEFT JOIN 增量，最后 `SUM() OVER (PARTITION BY 门店 ORDER BY 日期)` 累计。**这个套路也适用于：累计 GMV / 累计活跃 / 累计核销**。

## 群成员留存 / 好友留存 🅱️

结构和"累计会员"一模一样，只是把"注册日期"换成"入群日期"或"添加日期"。

```sql
-- 群成员留存：每日新增的"在群人数"按 PARTITION BY 门店×会员状态 ORDER BY 日期 做累加
COUNT(DISTINCT CASE WHEN `状态` = '在群内' THEN `外部联系人id` ELSE NULL END) AS daily_new_group_members

-- 好友留存：每日新增的"正常状态"好友
COUNT(DISTINCT CASE WHEN `状态` = '正常' THEN `外部联系人id` ELSE NULL END) AS daily_new_friends_count
```

完整模板见上面"累计会员总数"，把字段名替换即可。

## 好友流失率 🅱️

```sql
SUM([流失好友数]) / (SUM([流失好友数]) + MAX([留存好友总数]))
```

**口径**：分母 = 流失 + 当前留存，避免按"全量"做分母（流失人数会变小很多）。**注意分母用 `MAX()` 而非 `SUM()`**，因为"留存好友总数"是个截面指标，跨日 SUM 会重复。

## 流失人数 / 留存人数（卡片字段表达式）🅰️

```sql
-- 流失人数（被动删除）
COUNT(IF([流失状态] = '已流失' AND [流失方式] = '被动删除', [外部联系人id], 0))

-- 同上，但去重
COUNT(DISTINCT IF([流失状态] = '已流失' AND [流失方式] = '被动删除', [外部联系人id], 0))

-- 总计留存
COUNT([外部联系人id]) OVER (PARTITION BY [添加时间])

-- "流失 = 总 - 未流失"
COUNT([外部联系人id]) - COUNT(IF([流失状态] = '未流失', [外部联系人id], 0))
```

**坑**：`COUNT(IF(cond, x, 0))` 把不满足条件的也按 0 计数；改写为 `COUNT(DISTINCT IF(cond, x, NULL))` 才是只数满足条件的。详见 [07 章](07-data-quality-traps.md#null-vs-0)。

## 90 天未消费（卡片字段）🅰️

简化版（不分桶，只判是否 ≥ 90 天）：

```sql
CASE WHEN [最后一单距今天数] >= 90 THEN 1 ELSE 0 END
```

详细分桶见上文"[90 天复购分桶](#90-天复购分桶-)"。
