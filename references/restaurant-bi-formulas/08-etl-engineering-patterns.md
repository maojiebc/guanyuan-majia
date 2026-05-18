# 08 · ETL 工程范式

> 本节蒸馏自 39 个 V1 生产 ETL 的工程实践，**不讲 SQL 公式**（公式去 01~07），讲**节点拓扑取舍、CTE 串联模式、双源对账、轻节点重 SQL vs 重节点轻 SQL 哲学**。

## 范式 1：DWD 宽表底座的 10-CTE 范式 🅱️ {#dwd-cte-范式}

> 整张订单宽表用 **1 个 SQL_SCRIPT 节点** 包揽，节点拓扑只有 `6 INPUT_DATASET + 1 SQL_SCRIPT + 1 OUTPUT_DATASET = 8 节点`。代价是 SQL 长，回报是**所有清洗逻辑集中在一个文件里，改字段口径只动一处**。

### 节点拓扑

```
[INPUT] 订单原始明细        ──┐
[INPUT] 加盟门店信息          ─┤
[INPUT] 门店支付通道          ─┤── [SQL_SCRIPT] DWD_订单明细宽表 ── [OUTPUT] DWD 宽表
[INPUT] user 卡号对应         ─┤   (10 个 CTE 串联)
[INPUT] tb_card_info 会员卡   ─┤
[INPUT] tb_user_info 会员表   ─┘
```

### 10-CTE 串联结构

| # | CTE 名 | 职责 | 关键 know-how |
|---|---|---|---|
| 1 | `raw_order` | 取业务主键 + 状态/日期筛选 | **用 `third_order_id` 而非 `order_id` 防退款重复**；`SELECT DISTINCT` 去重 |
| 2 | `store_dim` | 门店 → 分公司映射 | **边远省份兜底回填**：`CASE WHEN province LIKE '%边远省份A%' THEN '边远省份A分公司' ... ELSE 分公司 END`（业务背景：总部分公司体系不覆盖个别新拓展省份，需按省份关键词单独建分公司）|
| 3 | `pay_channel` | 门店 → 支付通道维表 | `MAX(...)` GROUP BY 取定值（每店一条） |
| 4 | `openid_card_map` | 微信 openid ↔ 会员卡号 | 用于支付层补会员卡号 |
| 5 | `card_user` | 会员卡 ↔ 用户 ID | **过滤作废卡**：`卡状态 IS NULL OR 卡状态 <> 0` |
| 6 | `user_card_profile` | 同上但来自另一张表（双口径校验）| 双口径互补，避免某张表脏数据导致丢卡 |
| 7 | `user_profile` | 用户 ID → 昵称/手机号 | `MAX(...)` 取每用户最新 profile |
| 8 | `order_calc` | 订单衍生字段（取餐方式 / 支付大类 / POS 系统 / 星期 / 口味）| 业务字段的"集中加工层"——避免下游各业务方各写一遍 |
| 9 | `order_enriched` | 主表 LEFT JOIN 4 张维表 | 双 openid 通道找卡：`LEFT JOIN openid_card_map w ON wechat_openid = w.openid` + `LEFT JOIN openid_card_map a ON alipay_openid = a.openid` |
| 10 | `member_profile` | `UNION` 两套卡源 + JOIN 用户档案 | `member_cards = card_user.卡号 UNION user_card_profile.卡号`，确保任一来源的卡都能解析到用户 |

### 最终 SELECT（输出宽表）

主表 35+ 列，包含：
- **业务主键**：订单号、订单日期、StoreDate
- **订单状态**：状态、渠道、订单类型、取餐方式、POS 系统
- **门店元数据**：门店编号、门店名称、分公司、支付通道
- **支付信息**：支付方式（原值）、支付大类（聚类）、微信 openid、支付宝 user_id
- **用户信息**：用户 ID、会员昵称、手机号、会员卡号
- **衍生标识**：顾客标识（4 级回填）、标识分类、是否会员、会员订单
- **业务字段**：周几、口味（15 类）、优惠信息
- **金额**：total_实付、income_应收、original_price_原价

### 工程取舍：为什么用 1 个大 SQL 而不是 30 个节点？

| 维度 | 1 个大 SQL（10-CTE）| 30 个拖拽节点 |
|---|---|---|
| **可读性** | SQL 工程师友好（CTE 是标准 SQL）| 业务方友好（点开节点看每步）|
| **可维护性** | ✅ 单点修改，全 SQL 一次 review | 改字段要找 5+ 节点同步改 |
| **可调试性** | 把 CTE 单独跑 = 单节点调试 | 节点级断点，但要点开 30 次 |
| **可复用性** | ❌ 整段 SQL 难拆 | ✅ 单节点可复制到其他 ETL |
| **执行性能** | 引擎统一优化（CBO 通常比节点拓扑更好）| 节点之间存中间结果，I/O 开销大 |
| **业务方理解** | 看不懂 SQL 的人完全黑盒 | 即使看不懂 SQL 也能"看图说话" |

**选择规则**：
- DWD 底座（清洗逻辑稳定、业务方不需要点开看）→ **1 个大 SQL**
- 业务建模层（频繁变动、业务方要看每步）→ **多节点**

### 复用方法

把上面 10 个 CTE 当模板：
1. `raw_order` 改成你方的"主表过滤条件"
2. 中间 7 个 CTE 按你方维表数量增减（少则 2-3 个，多则 15+）
3. 最后 SELECT 输出所有需要的列名（注意中文别名）
4. 一次性塞进观远 SmartETL 的 **SQL_SCRIPT** 节点，配上 N 个 INPUT_DATASET 即可

完整 SQL 见**本地 V1 ETL JSON 目录**下的 `DWD_订单明细宽表.json` 的 `meta[].sql` 字段（详细位置查 [09 章索引清单](09-etl-catalog.md) 末尾的"引用方式"段）。

## 范式 2：轻节点重 SQL vs 重节点轻 SQL 工程哲学

观远 SmartETL 上构建同一张表有两种风格，**选哪种取决于业务方画像和后续维护人**。

### 风格 A：轻节点重 SQL（DWD 流派）

**典型 ETL**：DWD_订单明细宽表 (8 节点) / 90 天未消费 (3 节点) / 近 30 天复购 (5 节点)

特征：
- 节点数 < 10
- 含 1~2 个大型 SQL_SCRIPT 节点（每个 100+ 行 SQL）
- INPUT / OUTPUT 节点为主，中间只一个核心 SQL

**适合**：
- 数据 ETL 工程师维护（看 SQL 顺手）
- 清洗逻辑稳定（一旦写好少改）
- 性能敏感（引擎统一优化）

### 风格 B：重节点轻 SQL（业务建模流派）

**典型 ETL**：券明细 (48 节点) / 顾客标识 (43 节点) / 门店信息 (40 节点) / 订单明细 (32 节点)

特征：
- 节点数 30~50
- 大量 GROUP_BY / FILTER_ROWS / CALCULATOR / JOIN_DATA 节点
- SQL_SCRIPT 节点少且短

**适合**：
- 业务分析师维护（看不懂 SQL 但会"点节点"）
- 业务逻辑频繁变动（运营策略调一调，节点连线改一改）
- 多人协作（不同人维护不同节点链）

### 39 个 V1 ETL 的复杂度分布

| 节点数范围 | ETL 数量 | 代表 | 风格 |
|---|---|---|---|
| ≤ 5 | 4 | 90 天未消费、近 30 天复购、CRM 订单表、日期维度 | 轻节点重 SQL |
| 6~10 | 8 | DWD 宽表、订单产品、商品风味分类 | 混合 |
| 11~20 | 14 | RFM 顾客分层（19 节点，9 SQL_SCRIPT！）、堂食评价、财务异常门店 | 倾向重节点 |
| 21~30 | 8 | 会员表、好友数据、群标签、会员注册首单 | 重节点轻 SQL |
| 31~50 | 5 | 顾客标识、门店信息、订单明细、券明细 | 重节点轻 SQL |

**经验法则**：
1. 表越基础（ODS/DWD），越倾向"轻节点重 SQL"——稳定性 + 性能优先
2. 表越业务（DM 层），越倾向"重节点轻 SQL"——可维护性 + 业务方理解优先
3. RFM 这种"中等复杂业务建模"用 **混合风格**：9 个 SQL_SCRIPT 算单维度（R/F/M），再用 JOIN_DATA 节点把它们 JOIN 起来——单维度逻辑用 SQL 表达更准确，组装用节点更直观

## 范式 3：财务双源对账 🅱️

> 财务数据最易出错的场景：**两条数据链路（业务系统 A / 业务系统 B）对同一笔订单的金额不一致**，必须建一个 ETL 监控并输出"异常门店"列表。

### 节点拓扑

```
[INPUT] DWD-订单总计财务     →  [GROUP_BY] 按门店日聚合 → [FILTER_ROWS] 状态过滤 ──┐
                                                                                   │
[INPUT] DWD-订单总计         →  [GROUP_BY] 按门店日聚合 → [FILTER_ROWS] 状态过滤 ──┴── [JOIN_DATA] 关联 → [FILTER_ROWS] 差异 ≠ 0 → [OUTPUT] 财务表异常门店
                                                                                                                                  ↓
[INPUT] DWS财务订单表        →  [GROUP_BY] 检测重复 ───→ [OUTPUT] 一个编号多个名字（次输出）
```

### 关键 Know-how

1. **两源同维度聚合**：双源都按"门店 + 日期"GROUP_BY 后再 JOIN，保证 JOIN 维度对齐
2. **过滤稳定状态**：JOIN 前先 FILTER `订单状态 = '完成'`，避免拿"取消订单"对账
3. **差异不为 0 才输出**：JOIN 后的 FILTER `abs(差异) <> 0`（公式见 [07 章 · 不等于 0 标记](07-data-quality-traps.md)），只输出有问题的门店
4. **附加质量检查**：同一个 ETL 多挂一个 OUTPUT，检测"一个门店编号对应多个名字"（数据治理 bug）

### 通用对账模板

```sql
WITH src_a AS (
  SELECT 门店编号, 业务日期, SUM(金额) AS amt_a
  FROM input1
  WHERE 状态 = '完成'
  GROUP BY 门店编号, 业务日期
),
src_b AS (
  SELECT 门店编号, 业务日期, SUM(金额) AS amt_b
  FROM input2
  WHERE 状态 = '完成'
  GROUP BY 门店编号, 业务日期
)
SELECT
  COALESCE(a.门店编号, b.门店编号) AS 门店编号,
  COALESCE(a.业务日期, b.业务日期) AS 业务日期,
  COALESCE(a.amt_a, 0)             AS amt_a,
  COALESCE(b.amt_b, 0)             AS amt_b,
  COALESCE(a.amt_a, 0) - COALESCE(b.amt_b, 0) AS 差异
FROM src_a a
FULL OUTER JOIN src_b b
  ON a.门店编号 = b.门店编号
 AND a.业务日期 = b.业务日期
WHERE ABS(COALESCE(a.amt_a, 0) - COALESCE(b.amt_b, 0)) > 0.01;
-- 差异 > 0.01 元（剔除浮点精度噪声）
```

**坑**：用 `FULL OUTER JOIN` 而非 `LEFT JOIN`，确保**任一源出现/缺失**的门店日都进异常名单。LEFT 会漏掉"B 有 A 没有"的差异。

## 范式 4：POS 系统识别 + 渠道归一化 🅱️

DWD 宽表里的"POS 系统识别"段是渠道归一化的好范例（**POS 厂商名已脱敏为 POS_A ~ POS_E**，实际命名可按你方采购的 POS 厂商替换）：

```sql
CASE
  WHEN order_no LIKE '%AB%'        THEN 'POS_A'   -- 订单号有 AB 前缀的是 POS_A 厂商
  WHEN pos_type_raw = 'linux'      THEN 'POS_Linux'
  WHEN pos_type_raw = '1'          THEN 'POS_B'
  WHEN pos_type_raw = '2'          THEN 'POS_C'
  WHEN pos_type_raw = '5'          THEN 'POS_D'
  WHEN order_type_name = '堂食'    THEN 'POS_D'   -- 堂食单兜底也归 POS_D
  WHEN order_type_name = '外卖'    THEN '外卖'
  WHEN order_type_name = '自取'    THEN '外卖'
  ELSE pos_type_raw
END AS pos_system
```

**口径**：
- **优先级最高：订单号特征**（`%AB%` 字符串特征是 POS_A 厂商的订单号指纹，业务系统会把厂商代号嵌进订单号）
- **次优先：pos_type_raw 数字码**（业务系统给的字段，每个厂商对应一个数字）
- **再次优先：order_type_name 业务语义**（兜底）
- **最后兜底：保留原值**（人工排查后补码）

**实战背景**：连锁餐饮门店 POS 选型经常有 5 ~ 8 个厂商并存（不同省份/不同加盟商/不同时代采购的）。归一化 case 必须把这些厂商映射到统一的 `pos_system` 字段，下游才能按 POS 维度做对比分析（销售/会员/优惠各 POS 的表现）。

**为什么这样设计**：
- 业务系统 `pos_type_raw` 经常缺值或不规范，所以**先用订单号的不可篡改特征**做最准识别
- `order_type_name`（堂食/外卖/自取）是业务录入的，准确率中等，**作为次级兜底**
- ELSE 不写死值，**保留原始字段 + 后续清洗**——避免新 POS 系统接入时无法识别

### 通用 know-how：归一化 case 的优先级排序

```
不可篡改特征 > 数字编码 > 业务语义文字 > 原值兜底
```

把这个原则抄过去，任何"多源同义字段统一"场景都能用。

## 范式 5：会员注册前后行为追踪（生产强化版）🅱️

doc 2 的"注册前后订单"SQL 是单一 ETL 节点输出。生产环境下经常拆成 27+ 节点 ETL，引入：

1. **多张维表 JOIN**：会员主表 + 会员卡表 + 注册门店表 + 首单门店表 + 最后交易门店表 = 5 个 INPUT_DATASET
2. **归属门店优先级回填**：见 [04 章 · 注册门店清洗](04-channel-and-store.md#注册门店清洗优先级回填-)
3. **多个 OUTPUT**：同一份 ETL 同时输出"会员注册档案"、"会员首单档案"、"会员最后交易档案"三张派生表

**节点拓扑示例**（会员注册_首单_最后门店 27 节点）：

```
[INPUT] 会员主表         ─┐
[INPUT] 会员卡表         ─┤── [JOIN_DATA] × 8 + [FILTER_ROWS] × 3
[INPUT] 注册门店表       ─┤
[INPUT] 首单门店表       ─┤── [SQL_SCRIPT] 优先级回填（见 04 章）
[INPUT] 最后交易门店表   ─┘
                         │
                         ├── [GROUP_BY] × 9 ── [OUTPUT] 派生表 1
                         ├── [SQL_SCRIPT] 注册前后判断 ── [OUTPUT] 派生表 2
                         └── ...
```

**业务用途**：CDP 中"客户归属门店"的判断（运营推送时按归属门店给店长奖励）。

## 范式 6：维表辅助 — 日期 × 门店 cohort 网格 🅱️

> Cohort 分析（留存/复购）必须先构建"日期 × 门店"的完整笛卡尔积，再 LEFT JOIN 业务事实，否则"没有订单的日子"会缺行。

### 节点拓扑（日期&门店组合表）

```
[INPUT] 日期维度表        ─┐
                           ├── [JOIN_DATA] 笛卡尔积 → [GROUP_BY] 去重 → [CALCULATOR] 衍生 → [OUTPUT] 日期&门店组合
[INPUT] 门店信息维表       ─┘
```

### 通用模板

```sql
SELECT
  d.日期,
  s.门店编号,
  s.门店名称,
  s.分公司
FROM (
  SELECT DISTINCT 日期
  FROM input1   -- 日期维度
  WHERE 日期 >= '2024-01-01'
) d
CROSS JOIN (
  SELECT DISTINCT 门店编号, 门店名称, 分公司
  FROM input2   -- 门店主数据
  WHERE 门店状态 = 'Open'  -- 只保留在营门店
) s;
```

**适用场景**：
- 累计会员数（见 [02 章](02-customer-and-membership.md#累计会员总数-累计窗口经典写法)）
- 累计 GMV、累计核销
- 留存曲线分析
- 任何"按日期×门店"的填零网格

**坑**：
- 笛卡尔积可能爆炸（500 门店 × 365 天 = 18.25 万行），ETL 节点要预估行数
- 在营门店要按日期过滤（开业前/闭店后不该有数据）

## 范式总结：选哪种？

| 场景 | 推荐范式 |
|---|---|
| ODS → DWD 一步到位 | **范式 1：10-CTE 大 SQL** |
| 业务逻辑频繁调整 | **范式 2 风格 B：重节点轻 SQL** |
| 财务/库存对账 | **范式 3：双源对账** |
| 多渠道 / 多 POS 系统数据归一 | **范式 4：归一化 case 优先级** |
| 会员生命周期分析 | **范式 5：多维表 + 多输出** |
| Cohort / 累计指标 | **范式 6：日期×门店网格 + LEFT JOIN** |
| 多渠道评价/差评整合 | **[04 章 · 多渠道评价 Pipeline](04-channel-and-store.md#多渠道评价pipeline)** |

## 来源说明

本节蒸馏自**本地 V1 ETL JSON 目录**下 39 个生产 ETL（餐饮连锁 A + 餐饮连锁 B 实战）。**节点拓扑和工程取舍源自实战，不是教科书**——遇到不同业务系统/POS 系统/支付通道时，相同范式可以照抄不变。具体 ETL 索引见 [09 章](09-etl-catalog.md)。
