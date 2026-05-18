# 07 · 数据质量陷阱

> 餐饮 BI 80% 的"数对不上"问题都源自这几个陷阱。**先读这章，再去对应业务文件抄公式**。

## NULL vs 0 vs 空字符串 {#null-vs-0}

### 陷阱：`IF(cond, x, 0)` 在 COUNT DISTINCT 里会多算一个 0

```sql
-- ❌ 错误写法（0 也被当独立值计数一个）
COUNT(DISTINCT IF([门店状态] = 'Open', [门店], 0))

-- ✅ 正确写法（NULL 不会被计数）
COUNT(DISTINCT IF([门店状态] = 'Open', [门店], NULL))
```

**演示**：

| [门店] | [门店状态] | IF(..., [门店], 0) | IF(..., [门店], NULL) |
|---|---|---|---|
| A001 | Open | A001 | A001 |
| A002 | Open | A002 | A002 |
| A003 | Closed | 0 | NULL |
| A004 | Closed | 0 | NULL |

- 错误版 COUNT DISTINCT = 3（A001, A002, **0**）
- 正确版 COUNT DISTINCT = 2（A001, A002）

**口径**：`null` 不为 0，**不会被去重计数统计**。这是 `COUNT(DISTINCT)` 的标准行为。

**例外**：当你用 SUM 而非 COUNT 时，`IF(cond, x, 0)` 反而是安全的（0 求和不影响结果）：

```sql
-- 这种 OK
SUM(IF([业务渠道划分] = 'HD外卖', [去税营业额 NS], 0))

-- 这种也 OK（NULL 在 SUM 中自动跳过）
SUM(IF([业务渠道划分] = 'HD外卖', [去税营业额 NS], NULL))
```

### 总结表

| 函数 \ 兜底值 | `0` | `NULL` |
|---|---|---|
| `COUNT(DISTINCT ...)` | ❌ 多算一个 0 | ✅ 正确 |
| `COUNT(...)` | ❌ 0 也被计数 | ✅ 跳过 NULL |
| `SUM(...)` | ✅ 0 不影响 | ✅ 跳过 NULL |
| `AVG(...)` | ❌ 0 拉低均值 | ✅ 跳过 NULL |
| `MAX/MIN(...)` | ⚠️ MIN 会变 0 | ✅ 跳过 NULL |

**规则**：除非你明确要 0 参与计算（SUM 场景），其他一律用 NULL 兜底。

## 三态判断：NULL / `''` / `'null'` {#三态判断}

### 陷阱

业务系统在不同 PHP/Node/Java 版本下，把"无值"序列化为三种东西：

| 实际值 | SQL 中的样子 |
|---|---|
| 真 NULL | `NULL`（数据库 NULL） |
| 空字符串 | `''` |
| 字面值 "null" | `'null'`（4 个字符的字符串） |

**只判一种都会漏**。

### 正确的"三态判断"模板 🅱️

```sql
-- ❌ 只判 NULL，漏掉 '' 和 'null'
WHERE [顾客标识] IS NOT NULL

-- ❌ 只判 NULL + ''，漏掉 'null'
WHERE [顾客标识] IS NOT NULL AND [顾客标识] <> ''

-- ✅ 三态全判
WHERE [顾客标识] IS NOT NULL
  AND TRIM([顾客标识]) <> ''
  AND TRIM([顾客标识]) <> 'null'
```

### 实战例子（来自餐饮连锁 A）🅰️

```sql
-- 统计"微信支付但 openid 为空"的订单数
COUNT(
  IF(
    [支付大类] = '微信支付'
    AND (
      [微信支付openid] IS NULL
      OR [微信支付openid] = ''
      OR [微信支付openid] = 'null'
    ),
    [订单号],
    NULL
  )
)
```

**业务背景**：微信支付理应有 openid，发现 `null/空/'null'` 都说明对接异常。餐饮连锁 A 和 B 的会员体系都被这个问题坑过。

### 顾客标识有效性判定 🅱️

```sql
-- 卡片表达式中"有效顾客"的标准判定
[顾客标识] IS NOT NULL AND TRIM([顾客标识]) <> ''

-- ETL 中更严格的版本
WHERE `顾客标识` IS NOT NULL
  AND TRIM(`顾客标识`) <> ''
  AND TRIM(LOWER(`顾客标识`)) <> 'null'
```

## 字段口径歧义

### 同名字段不同含义

| 字段名 | 在 A 系统 | 在 B 系统 |
|---|---|---|
| `订单数` | 去重订单号 | 订单明细行数（一单多行不去重） |
| `消费金额` | 实收（含/去税待确认） | 原价（折前） |
| `会员` | 当前会员状态 | 历史曾会员 |

**规则**：写新 ETL 前，必须从字段定义文档或上游表 schema 里**确认口径**。"看名字猜含义"是最容易翻车的方式。

### TC（客流数）的三个口径

```sql
-- 口径 1：去重订单数（最常见）
COUNT(DISTINCT [订单号])

-- 口径 2：去重订单日期（"跨天"复购口径）
COUNT(DISTINCT CAST([订单日期] AS DATE))

-- 口径 3：去重顾客数（其实是 UV，业务里有人也叫 TC，警惕）
COUNT(DISTINCT [顾客标识])
```

**最常翻车场景**：业务方说"上个月 TC 涨了 30%"，分析师查"订单数"也涨了 30% → 但其实业务方说的是"顾客数"。**报数据前先和业务方对一遍 TC 是啥**。

### 复购口径分歧

详见 [02 章 · 复购口径](02-customer-and-membership.md#复购口径)。

| 业务问法 | 跨天口径 | 非跨天口径 |
|---|---|---|
| 同一天买 5 单 | 不算复购 | 算复购 |
| 跨 2 天各买 1 单 | 算复购 | 算复购 |

## 重复字段名（doc 来源）

### doc 2 原文有 4 个"消费频次"标题

实际是 3 个不同语义 + 1 个重复稿（已在 [02 章 · 消费频次](02-customer-and-membership.md#消费频次3-个口径-) 中重命名）：

| 原标题位置 | 实际语义 | 蒸馏后名字 |
|---|---|---|
| 第 1 处（903 行）| 卡片字段表达式 | 消费频次-全表均值 |
| 第 2 处（911 行）| SELECT 按顾客聚合 | 消费频次-顾客明细 |
| 第 3 处（989 行）| **和第 2 处完全相同** | 已删除（重复稿） |
| 第 4 处（1237 行）| SELECT 按门店×会员聚合 | 消费频次-门店会员维度 |

**教训**：飞书 wiki 里"边做边记"的文档容易堆出同名重复段。整理时**一定要逐段看上下文、按 GROUP BY 的维度命名**。

## 字段对照表（餐饮连锁 A vs 餐饮连锁 B vs 通用）

> 蒸馏库里所有公式用"通用字段名"。复用时按下表替换为你方实际名。**A、B 都是真实生产环境的字段命名，反映两类不同业态的命名风格**——A 是英文驼峰为主（外资品牌典型）、B 是中文反引号为主（本土品牌典型）。

| 通用名 | 餐饮连锁 A 字段（英文驼峰风格）| 餐饮连锁 B 字段（中文反引号风格）|
|---|---|---|
| 订单号 | `OrderKey` / `订单号` | `订单号` / `union_order_id` |
| 订单日期 | `businessDate` / `订单日期` | `订单日期` |
| 下单时间 | `OrderTime` / `下单时间` | `下单时间` |
| 营业额（去税）| `去税营业额 NS` / `NS` | `income` / `income_应收` |
| 营业额（含税）| `含税营业额 GS` / `GS` | `total` |
| 原价金额 | `原价金额 ALA_Sales` / `ALA` | `original_price` |
| 折扣金额 | `Discount` | （由 ALA - total 推导）|
| 销量 | `QTY` / `销量QTY` | `quantity` |
| 顾客标识 | `MemberShipID` / `会员号` | `顾客标识`（自定义复合字段，见 02 章）|
| 会员卡号 | `dis_cardno` / `会员号` | `会员卡号` / `card_no` |
| 是否会员 | `MemberType`（'New'/'NonMember'/...）| `是否会员`（'会员'/'非会员'）|
| 门店编号 | `StoreID` | `门店编号` / `store_code` |
| 门店名称 | `SHOP_NAME` | `门店名称` / `store_name` |
| 分公司 | `Region` | `注册所属分公司` / `分公司` |
| 渠道（一级）| `Channel`（'03.HomeDelivery'/'01.DineIn'）| `渠道` |
| 渠道码 | `CHANNEL_ID` | `channel_name` |
| 来源类型 | `FromType` / `OrderSource` | `POS_TYPE` |
| 业务日期 | `businessDate` | `business_time`（CAST to DATE）|
| 商品名 | `Items` / `订单产品` | `names` / 烧烤明细字段 / `订单产品` |
| Comp 标记 | `IsComp` | （不用，餐饮连锁 B 无 Comp 概念）|

## ETL 中的"input1" 约定

观远 SmartETL 节点把上游输入统一暴露为 `input1`、`input2`...，这是固定关键字。

```sql
-- ETL SQL 节点的标准入参
SELECT * FROM input1;

-- 双输入 JOIN
SELECT a.*, b.字段X
FROM input1 a
LEFT JOIN input2 b ON a.订单号 = b.订单号;
```

**坑**：写 ETL 时不要写实际表名（如 `tb_order_log`），那会导致 SmartETL 找不到上游。**注释里可以写"input1 = 订单明细表"作为提醒**。

## 日期边界陷阱

### 用 `>= + <` 而非 `BETWEEN`

```sql
-- ❌ BETWEEN 可能漏算或重算边界
WHERE [订单日期] BETWEEN '2024-01-01' AND '2024-01-31'

-- ✅ 推荐写法
WHERE [订单日期] >= '2024-01-01'
  AND [订单日期] <  '2024-02-01'
```

**为什么**：`BETWEEN` 包含右端点，跨小时/跨秒精度时容易混乱。`>=` + `<` 模式语义无歧义。

### CURDATE() vs current_date() vs now()

| 函数 | 返回 |
|---|---|
| `CURDATE()` | DATE（仅日期）—— MySQL 风格 |
| `current_date()` | DATE —— Hive / Spark 标准 |
| `now()` | TIMESTAMP（带时分秒） |
| `TO_DATE(now())` | 把 now() 截到 DATE |

**坑**：用 `now()` 做日期比较时容易把"今天 00:00:01"和"今天 23:59:59"算成不同日。**做日期比较前先 `TO_DATE` 或 `CAST AS DATE`**。

## 取数前先 SELECT TOP

写复杂 ETL 之前，**先 `SELECT * FROM input1 LIMIT 100` 看一眼数据形态**。

特别留意：
- 字段类型（字符串型日期、数值型字符串）
- NULL / 空字符串 / `'null'` 三态
- 重复主键（订单号是否有重复？）
- 字符编码（中文是否乱码？）
- 时区（UTC vs 北京时间）

**这一步省 30 分钟，后面追数据问题至少省 3 小时**。
