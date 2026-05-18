# 06 · SQL 工具箱

> 跨业务通用的 SQL 工具：**字符串处理 → 数组聚合拆分 → 开窗函数 → 字段拆解**。所有公式都与具体业务解耦。

## 字符串拆解

### LEFT + INSTR：截取分隔符前段 ⚪

```sql
-- 拆"门店编号_门店名称"取门店编号
LEFT([关联活动], INSTR([关联活动], '_') - 1)

-- 句号拆分（取第一段）
LEFT([渠道活码名称], INSTR([渠道活码名称], '.') - 1)
```

**口径**：`INSTR(s, c)` 返回字符 `c` 在 `s` 中首次出现的位置（1-based），用 `LEFT(s, pos - 1)` 截到前面那一段。

### SUBSTR：取分隔符后段 ⚪

```sql
SUBSTR([关联活动], INSTR([关联活动], '_') + 1)
```

### 取前 N 字符 ⚪

```sql
-- 注册门店取前两字（如"北京三里屯店" → "北京"）
SUBSTR([SHOP_NAME], 1, 2)
```

### 正则提取数字 🅰️

```sql
-- 从"123.活码A" 抽出 "123"
regexp_extract([渠道活码名称], '^(\\d+)', 1)
```

**口径**：`regexp_extract(s, pattern, group_index)` 返回正则匹配的第 N 个分组（0 = 整个匹配，1 = 第一个括号组）。

### REPLACE：替换 ⚪

```sql
-- 去掉货币符号
REPLACE([券售卖金额], '¥', '')

-- 把"上海分公司" 压缩成"上海"
REPLACE([注册所属分公司], "分公司", "")
```

### 用 CONCAT 拼字段 ⚪

```sql
CONCAT(HOUR([下单时间]), '点')              -- 整点字符串
CONCAT([StoreID], '_', [businessDate])       -- StoreDate 门店日键
```

### 文本日期转日期 🅱️

```sql
to_date([日期], 'yyyyMMdd')          -- "20241101" → DATE
to_timestamp([交易日期], 'yyyyMMdd') -- "20241101" → TIMESTAMP
```

## 数组聚合 / 拆分

### explode + split：一列拆多行 🅰️

```sql
-- 把"tag1,tag2,tag3" 一列拆成 3 行
explode(split([tags], ','))
```

**适用**：一对多明细展开。常见于"商品 tag 表"、"订单备注列表"、"多标签会员"。

**坑**：`explode` 在 SmartETL 节点里通常需要单独节点使用，不能和其他聚合混在一个 SELECT。

### collect_set + concat_ws：多行聚一列 🅰️🅱️

```sql
-- 一个群下的所有标签聚成"标签1,标签2,标签3"
SELECT
  input1.`群id`,
  input1.`群名称`,
  input1.`标签组名称`,
  concat_ws(',', collect_set(`标签名称`)) AS `群标签`
FROM input1
GROUP BY 1, 2, 3;

-- 一家门店下的所有群名聚成"群1,群2,群3"
SELECT
  input1.`门店名称`,
  concat_ws(',', collect_set(input1.`群名`)) AS `门店群`
FROM input1
GROUP BY 1;

-- 一个会员去过的所有商圈聚成"商圈A,商圈B"
SELECT
  input1.`会员号MemberShipID`,
  concat_ws(',', collect_set(input1.`商圈`)) AS `商圈偏好`
FROM input1
GROUP BY 1;
```

### collect_set 窗口版（不收敛行数）⚪

```sql
-- 每个明细行带上"同地区的所有门店列表"
concat_ws(',', collect_set([门店]) OVER (PARTITION BY [地区]))
```

**特点**：不写 GROUP BY，每行明细都带衍生汇总字段。和 SUM/COUNT OVER 一样的玩法。

## 开窗函数 ⚪ {#开窗排名}

### 三种排名函数对比

| 函数 | 同分时的处理 | 例：分数 90, 90, 85, 80, 70 |
|---|---|---|
| `ROW_NUMBER()` | 强制唯一序号 | 1, 2, 3, 4, 5 |
| `RANK()` | 同分相同名次，下一名跳过 | 1, 1, 3, 4, 5 |
| `DENSE_RANK()` | 同分相同名次，下一名不跳 | 1, 1, 2, 3, 4 |

**业务选择**：
- 取"每会员第一笔订单" → `ROW_NUMBER()` + `WHERE rn = 1`
- "我是分公司第几名" + 允许并列 → `RANK()` 或 `DENSE_RANK()`
- 用于分页/TopN → `ROW_NUMBER()`

### 标准模板

```sql
-- 每会员的下单顺序
ROW_NUMBER() OVER (
  PARTITION BY [会员号]
  ORDER BY [用餐时间] ASC
) AS `第几笔订单`

-- 取每会员第一张券
ROW_NUMBER() OVER (
  PARTITION BY [dis_cardno]
  ORDER BY [dis_disDate]
)
-- 配合 WHERE rn = 1 在外层用

-- 每门店日期降序（取最新日）
ROW_NUMBER() OVER (
  PARTITION BY [门店]
  ORDER BY [门店], [日期] DESC
)
```

### 累计窗口 ⚪

```sql
-- 每门店按日期累计的"营业天数"
SUM([营业]) OVER (
  PARTITION BY [门店]
  ORDER BY [门店], [日期] ASC
  ROWS BETWEEN UNBOUNDED PRECEDING AND 0 FOLLOWING
)

-- 整张表按时间累计的"注册人数"
SUM(1) OVER (
  PARTITION BY 1
  ORDER BY [注册时间]
)
```

**关键字**：
- `PARTITION BY 1`：不分区（整表作一个窗口）
- `UNBOUNDED PRECEDING`：从分区起始
- `CURRENT ROW` 或 `0 FOLLOWING`：到当前行
- 不写 `ROWS BETWEEN` 默认范围 = `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`（按值域累计，处理同分值时与 ROWS 行为不同）

### 不分区聚合 ⚪

```sql
-- 顾客累计消费几笔订单
COUNT([订单日期]) OVER (PARTITION BY [会员号MemberShipID])

-- 顾客累计消费金额
SUM([含税营业额 GS]) OVER (PARTITION BY [会员号MemberShipID])

-- 每订单内"是否最高单价产品"
IF(
  [原价金额 ALA] / [销量QTY]
    = MAX([原价金额 ALA] / [销量QTY]) OVER (PARTITION BY [订单号]),
  'Y',
  'N'
)
```

## 条件去重计数 ⚪

```sql
-- 去重 + 且的关系
COUNT(DISTINCT CASE WHEN [门店类型] = '金枫店' AND [门店状态] = 'Open' THEN [门店] END)

-- 特定条件下的订单去重数（IF 写法）
COUNT(DISTINCT IF([门店状态] = 'Open', [门店], 0))
COUNT(DISTINCT IF([大区] = '华东', [券包订单ID], NULL))
```

**两种等价写法**：
- `CASE WHEN cond THEN x END`（默认 ELSE = NULL）
- `IF(cond, x, NULL)`

**坑**：写 `IF(cond, x, 0)` 在 `COUNT(DISTINCT)` 里**会把 0 也算成一个独立值**。详见 [07 章 · NULL vs 0](07-data-quality-traps.md#null-vs-0)。

## JOIN 速查 ⚪

| JOIN 类型 | 行为 |
|---|---|
| `INNER JOIN` | 两表都匹配上的行 |
| `LEFT JOIN` | 左表全保留，右表匹配不上 = NULL 填充 |
| `RIGHT JOIN` | 右表全保留（极少用，可用 LEFT 反向写） |
| `FULL OUTER JOIN` | 两表都保留，匹配不上互为 NULL |

**餐饮 BI 常用模式**：

```sql
-- 1. 日期×门店网格作为左表，业务事实作为右表 LEFT JOIN
--    保证"没产生订单的店天数据"也出现在结果里（默认 0 而非缺行）
-- 详见 02 章 · 累计会员总数

-- 2. 主表 + 多张明细 LEFT JOIN（订单 + 支付 + 商品 + 会员 + 活动）
--    详见 02 章 · 数据库抓取
```

## 数据库抓取（ClickHouse 多表 JOIN）🅱️

doc 2 里有一段完整的 ClickHouse 业务库取数 SQL，作为"主表 + 多明细 LEFT JOIN"的模板：

```sql
WITH
    toDateTime('2025-04-01 00:00:00') AS start_time,
    toDateTime('2025-05-01 00:00:00') AS end_time,

-- 订单主表
order_info_all AS (
    SELECT
        order_id, third_order_id, channel_name, POS_TYPE, order_type_name,
        store_code, store_name,
        CAST(total          AS Decimal(10,2)) AS total,
        CAST(income         AS Decimal(10,2)) AS income,
        CAST(original_price AS Decimal(10,2)) AS original_price,
        take_code, order_status_msg,
        order_time, complete_time, create_time,
        toDate(business_time) AS business_time,
        refund_order_id
    FROM orderdb.order_info
    WHERE create_time >= start_time AND create_time < end_time
),

-- 支付信息汇总
order_payments_union AS (
    SELECT
        order_id,
        arrayStringConcat(arraySort(groupUniqArray(type_name)), ',') AS type_names,
        maxIf(pay_user_id, type_name ILIKE '%微信%')   AS wechat_pay_user_id,
        maxIf(pay_user_id, type_name ILIKE '%支付宝%') AS alipay_user_id,
        maxIf(pay_user_id, type_name ILIKE '%云闪付%') AS yun_pay_user_id
    FROM orderdb.order_info_payments
    WHERE create_time >= start_time AND create_time < end_time
    GROUP BY order_id
),

-- 商品明细 / 会员卡号 / 活动备注 等，结构同上
order_products_union AS (...),
order_products_grill_union AS (...),
order_members_union AS (...),
order_activity_union AS (...)

-- 最终聚合输出（主表 LEFT JOIN 多张明细）
SELECT
    o.*,
    p.type_names, p.wechat_pay_user_id, p.alipay_user_id, p.yun_pay_user_id,
    d.names, g.names_grill, m.card_no, a.merged_remark
FROM order_info_all       AS o
LEFT JOIN order_payments_union       AS p ON o.order_id = p.order_id
LEFT JOIN order_products_union       AS d ON o.order_id = d.order_id
LEFT JOIN order_products_grill_union AS g ON o.order_id = g.order_id
LEFT JOIN order_members_union        AS m ON o.order_id = m.order_id
LEFT JOIN order_activity_union       AS a ON o.order_id = a.order_id
ORDER BY o.create_time ASC;
```

**方法论**：
- 每张明细表先 GROUP BY 主键聚合（避免 JOIN 时膨胀）
- 用 ClickHouse 的 `arrayStringConcat + groupArray` / `maxIf + ILIKE` 在聚合阶段把多行明细压成单行
- 主表用 `WITH ... AS start_time` 把日期参数化在最顶，方便调整

**坑**：ClickHouse 的 `ILIKE` 是不区分大小写的 LIKE；`maxIf(x, cond)` 等价于 `MAX(IF(cond, x, NULL))`，写起来简洁。

## 聚合空值为 0 🅱️

```sql
SELECT
  `归属门店编号`,
  `归属门店名称`,
  `归属门店分公司`,
  COALESCE(`积分中奖人数`, 0)    AS `积分中奖人数`,
  COALESCE(`活动A中奖人数`, 0)   AS `活动A中奖人数`,
  COALESCE(`活动B中奖人数`, 0)   AS `活动B中奖人数`,
  COALESCE(`活动C中奖人数`, 0)   AS `活动C中奖人数`
FROM input1;
```

**适用**：把 NULL 列统一显示为 0，方便下游求和 / 平均 / 比例计算。

**等价写法**：

```sql
IFNULL(`字段`, 0)         -- MySQL / Hive 通用
COALESCE(`字段`, 0)       -- 标准 SQL，更推荐
IF([字段] IS NULL, 0, [字段])  -- 老式写法，繁琐
```

## 不等于 0 标记 🅱️

```sql
CASE
  WHEN [字段A&字段B有差异] <> 0 THEN '异常'
  ELSE                               '正常'
END
```

**适用**：双数据源对比、数据质量监控、差异审计。

## 评价分类的归一化技巧 🅱️

虽然完整 SQL 太长（见 [04 章末尾](04-channel-and-store.md#评价分类情绪--标签-)），但核心**文本归一化**技巧值得单列：

```sql
LOWER(
  REGEXP_REPLACE(
    REGEXP_REPLACE(
      REGEXP_REPLACE(
        COALESCE(t.`评价内容`, ''),
        '[\\r\\n\\t ]+', ''         -- 去空白
      ),
      '　', ''                       -- 去全角空格
    ),
    '[，,。\\.！!？\\?；;：:、#\\[\\]\\(\\)（）""'‘''·…_\\-—]+', '|'   -- 标点统一为分隔符
  )
)
```

**用途**：把任意文本归一化后再做正则匹配，避免"标点不同 / 全角半角 / 大小写"导致漏匹配。**所有"文本分类 / 关键词打标"任务都先做这一步**。
