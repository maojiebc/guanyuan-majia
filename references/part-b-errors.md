# Part B · 报错修复手册（10 类真坑）

> 由 SKILL.md V1.4.0 拆分而出。SKILL.md 主文档保留 B-13 红线条目（提到这些坑各一句话）；遇到 task error 走 B-5 三步定位后回这里查完整修复方案。

---

## 坑 1：`请输入ETL名称` / `保存路径无效`

```bash
$ printf '{}' | guancli fetch POST /api/etl/direct-save --stdin
=> 请输入ETL名称
$ printf '{"name":"x","actions":[]}' | guancli fetch POST /api/etl/direct-save --stdin
=> 保存路径无效
```

**根因**：顶层 `parentDirId` 缺失或填错（必须是 `dirType=ETL` 那棵树的 id）。

**修复**：先建好 ETL 目录拿到 id，写到 payload 顶层。

---

## 坑 2：保存成功但 execute 数据为空（上游运行权限不足）

**现象**：写入返回 `{success:true}`，execute 也返回 ok，但输出表始终为空。

**根因**：`INPUT_DATASET.inputDsId` 当前账号只有"读权限"没有"运行权限"。

**修复**：
1. 换一个账号确实能运行的输入表
2. 写自包含 ETL：`SELECT explode(sequence(...))` 或 `VALUES(...)` 直接生成数据

---

## 坑 3：上游字段名带隐藏 `\n`（含升级版）

**现象**：列名显示成两行，但 SQL 引用永远查不到。

**修复（基础版）**：编译 SQL 时 `` `带换行的原字段名` AS `干净别名` ``，下游用别名。

**升级版坑**：v2 SQL 里字段名实际是 `` `field\n  ` ``（换行 + 2 空格），但 fieldAlias 是 `` `field\n` ``（仅换行）——**两边不一致**。BI 老引擎容错跑得通，重生节点 ID 后挂了。

**修复**：把 SQL 里 `` `field\n  ` `` 改成 `` `field\n` `` 对齐 fieldAlias。

---

## 坑 4：`<> NULL` 把所有行过滤光

**现象**：旧"非空筛选"节点编译成 `WHERE field <> NULL`，输出 0 行。

**根因**：SQL 标准里 `<> NULL` 永远是 `unknown`。

**修复**：编译器 `FILTER_ROWS` → SQL 强制规则：
- "非空" → `IS NOT NULL`
- "为空" → `IS NULL`

---

## 坑 5：字段引用与 relativeFieldAlias 错位

**现象**：SQL 引用 `t.id`，但 INPUT_DATASET 在 `relativeFieldAlias` 里映射成了 `coupon_id`。`cannot resolve column`。

**修复**：编译 payload 时**必须读 INPUT_DATASET 的 `relativeFieldAlias`**，把 SQL 里所有原字段名替换成节点级别名。

---

## 坑 6：CTE 内 `;` + 中文注释

**现象**：

```text
[PARSE_SYNTAX_ERROR] Syntax error at or near ';'.(line 196, pos 24)
== SQL ==
... FROM n_id_xxx;  -- 请将这里替换为您的源数据表名 ...
```

**修复**：

```js
fixed = sql.replace(/(\s+FROM\s+n_id_\w+);(\s*--[^\n]*)?/g, "$1");
fixed = fixed.replace(/;\s*--[^\n]*/g, "");
```

---

## 坑 7：FROM/JOIN 同表别名同名

**现象**：

```sql
FROM n_id_aaa s1
  LEFT JOIN n_id_aaa s1 ON s2.`field_a` = s1.`field_a`
-- 错误: AMBIGUOUS_REFERENCE Reference s1.`field_a` is ambiguous
```

**修复**：把 FROM 别名改成 s2，对齐 ON 子句：

```sql
FROM n_id_bbb s2
LEFT JOIN n_id_aaa s1 ON s2.`field_a` = s1.`field_a`
```

---

## 坑 8：FROM 表错位（自连而非 JOIN 不同表）

**现象**：

```sql
FROM n_id_aaa s1
  LEFT JOIN n_id_aaa s1 ON s2.`key` = s1.`key`
-- 错误: s2.`some_field` 找不到
```

但 SELECT 用 `s2.specific_field` —— 说明 v2 SQL 写错表。

**修复**：

```sql
FROM n_id_aaa s1
LEFT JOIN n_id_ccc s2 ON s2.`key` = s1.`key`
```

---

## 坑 9：UNION 列数不匹配

**现象**：

```text
[NUM_COLUMNS_MISMATCH] UNION can only be performed on inputs with the same number of columns,
but the first input has 35 columns and the second input has 36 columns.
```

**根因**：BI 老引擎对 UNION 列差异自动补 NULL，重生节点 ID 后严格化。

**修复（彻底）**：手工把两侧 SELECT 列表对齐，缺的字段用 `NULL AS xxx` 补。

---

## 坑 10：日期字段 vs 字符串字面量混淆

**现象**：

```sql
SELECT *, current_date() AS `today_field` FROM ...
WHERE `order_date` < 'today_field'   -- ❌ 字符串字面量，恒为 false
```

**修复**：

```sql
WHERE `order_date` = date_sub(current_date(), 1)
```
