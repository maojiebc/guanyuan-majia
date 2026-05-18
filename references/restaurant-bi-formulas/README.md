# 餐饮零售 BI 公式实战库

> 蒸馏自两段连续的餐饮 BI 分析师履职（**餐饮连锁 A + 餐饮连锁 B**，均为多门店连锁餐饮品牌），覆盖**观远 BI / Guandata** 平台上的常用 ETL SQL、卡片表达式、时间宏。所有品牌名、表名、密集业务字段已去敏，可自由复用。

## 路由表

| 我要算 / 处理 | 去 |
|---|---|
| 日期范围（T-1、本月、上月、近 N 天）、用餐时段、时间宏、跨月对齐 | [01-date-and-time.md](01-date-and-time.md) |
| 新老客 / 会员属性 / 消费频次 / 复购 / 留存 / 流失 / **RFM 8 类 × 营销策略** / R 阈值多档分级 | [02-customer-and-membership.md](02-customer-and-membership.md) |
| AC / ADS / ADT / AUD / Comp / TC_CRM% / NS_CRM% / 营收占比 | [03-revenue-kpi.md](03-revenue-kpi.md) |
| 堂食 vs 外卖渠道分流 / 订单子渠道大 case / 门店生命周期 / StoreDate / 成长类型 / **多渠道评价 Pipeline** | [04-channel-and-store.md](04-channel-and-store.md) |
| 核销率 / 折扣率 / 折扣分桶 / 首张券 / 30 天优惠订单比例 | [05-coupon-and-discount.md](05-coupon-and-discount.md) |
| `regexp_extract` / `explode-split` / `collect_set-concat_ws` / 开窗排名 / 字段拆解 | [06-sql-utils.md](06-sql-utils.md) |
| NULL / 空字符串 / 'null' 字面值三态 / 字段口径歧义 / 通用字段词典 | [07-data-quality-traps.md](07-data-quality-traps.md) |
| **ETL 工程范式**（10-CTE DWD 宽表 / 轻节点重 SQL vs 重节点轻 SQL / 财务双源对账 / POS 归一化 / Cohort 网格）| [08-etl-engineering-patterns.md](08-etl-engineering-patterns.md) |
| **39 个 V1 生产 ETL 索引清单**（按 11 个业务域分类 + 每 ETL 的节点/输入/输出/SQL 节点速查 + 复用决策表）| [09-etl-catalog.md](09-etl-catalog.md) |

## 通用字段词典

ETL 输入表统一称作 `input1`（观远 SmartETL 默认入参名），其余字段命名约定如下。**本库所有 SQL 都使用这套约定，复用时按你方实际字段名重命名即可。**

| 词典名 | 含义 | 等价别名（你可能遇到的） |
|---|---|---|
| `订单号` | 订单唯一 ID | `OrderKey` / `order_id` / `券包订单ID` |
| `订单日期` | 业务日期 | `businessDate` / `report_date` |
| `下单时间` | 含时分秒的下单时刻 | `OrderTime` / `create_time` |
| `去税营业额` | 营收口径（剔税） | `去税营业额 NS` / `income_应收` / `NS` |
| `含税营业额` | 营收口径（含税） | `含税营业额 GS` / `total` / `GS` |
| `原价金额` | 折扣前金额 | `原价金额 ALA_Sales` / `ALA` / `original_price` |
| `折扣金额` | 让利金额 | `Discount` |
| `销量` | 商品件数 | `QTY` |
| `订单产品` | 商品名字符串 | `Items` / `names` / `names_grill` |
| `顾客标识` | 跨渠道统一顾客 ID（优先级：会员卡号 > 微信 openid > 支付宝 user_id > 云闪付 user_id） | — |
| `会员卡号` | 会员 ID | `MemberShipID` / `dis_cardno` / `card_no` |
| `是否会员` | 二值或三值标记 | `MemberType` / `IsMember` |
| `门店编号` | 门店唯一 ID | `StoreID` / `store_code` |
| `门店名称` | 门店中文名 | `store_name` / `SHOP_NAME` |
| `分公司` | 区域分公司 | `注册所属分公司` / `归属分公司` |
| `渠道ID` | 数字化渠道码（外卖、堂食、自取等） | `CHANNEL_ID` |
| `来源类型` | 二级来源（微信/支付宝/拼单/POS 等） | `FromType` / `OrderSource` |
| `业务渠道` | 一级归类（堂食/外卖） | `Channel` / `业务渠道划分` |
| `StoreDate` | `CONCAT(门店编号, '_', 营业日期)`，作为门店×日的唯一键 | — |
| `Comp` 标记 | 是否同店可比 | `IsComp` |
| `TC` | 客流数 / 订单笔数 | — |

## 5 条最容易踩的坑（TL;DR）

1. **`COUNT(DISTINCT IF(cond, x, NULL))` 才正确，写 `IF(cond, x, 0)` 会把 0 也计数一个。** → 详见 [07](07-data-quality-traps.md#null-vs-0)
2. **顾客标识三态**：`NULL` / 空字符串 `''` / 字面量 `'null'` 必须**三个都判**，否则统计会漂。 → [07](07-data-quality-traps.md#三态判断)
3. **`COUNT(订单号)` 和 `COUNT(DISTINCT 订单号)` 不一样**：拼单订单一单多行，分母不去重会重复。 → [03](03-revenue-kpi.md#客单价-ac)
4. **跨天复购 vs 非跨天复购口径要明示**：`COUNT(DISTINCT 订单日期)>=2` 和 `COUNT(DISTINCT 订单号)>=2` 是两条曲线，不要混用。 → [02](02-customer-and-membership.md#复购口径)
5. **观远时间宏 `{{{...}}}` 必须三个花括号**，少一个就被当字符串：`{{{yesterday}}}` / `{{{monday last week - 28 days}}}` / `{{{%2025-12-12}}}`。 → [01](01-date-and-time.md#时间宏)

## 编排建议

- **写新 ETL 节点之前**：先看 [01](01-date-and-time.md)（确定时间范围）+ [07](07-data-quality-traps.md)（确定字段三态处理），再去对应业务文件抄公式。
- **建卡 / 写卡片字段表达式**：直接去 [03](03-revenue-kpi.md) / [05](05-coupon-and-discount.md) 拿对应 KPI。
- **接到"为什么这俩数对不上"的甩锅**：去 [07](07-data-quality-traps.md) 对一遍口径，80% 是 NULL / 重复字段名 / 三态判断不一致。

## 来源标记

- 🅰️ = 餐饮连锁 A 实战
- 🅱️ = 餐饮连锁 B 实战
- ⚪ = 两家通用 / 行业通用

格式参考 [02-customer-and-membership.md](02-customer-and-membership.md) 第一段。
