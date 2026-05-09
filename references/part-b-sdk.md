# Part B · v2 → v3 批量改造 SDK

> 由 SKILL.md V1.4.0 拆分而出。30+ 张表批量迁移时回到这里查 SDK 接口签名与实战陷阱。

---

## SDK 核心 API

```js
// v3_sdk.mjs
export function transformV2ToV3({
  v2PayloadFile,    // 旧 payload 路径
  v3Name,           // 新 ETL 名
  removeInputs = [],// 要移除的 INPUT_DATASET id（去循环依赖）
  newSql = null,    // 重写 SQL（null = 沿用原 SQL）
  inputMap = {},    // v1/v2 dsId → v3 dsId 替换
  description = "",
}) { ... }

export function pushAndExecute(v3Name, payloadPath) {
  // POST /api/etl/direct-save → POST /api/etl/execute
}

export function checkStatus(v3Name) {
  // guancli etl search → parse Status
}
```

## transformV2ToV3 内部 7 步

```text
1. 读 v2 payload JSON
2. 过滤掉 removeInputs 列表中的 INPUT_DATASET 节点
3. 替换 inputMap 中的 inputDsId（v1/v2 → v3）
4. 重新生成所有节点 ID（避免冲突），同步重映射 sources 数组
5. 改 OUTPUT_DATASET 的 outputDsName + parentDirId
6. 如有 newSql，覆盖 SQL_SCRIPT 节点的 `sql` 字段
7. 顶层换 name + parentDirId + dirPath + description
   + 更新 meta = JSON.stringify(actions)
```

## 关键陷阱（必读）

```text
- SQL 字段名是 `sql`，不是 `sqlScript`！（最大坑）
- 重排节点 ID 时 sources 数组要同步映射
- 删除 INPUT_DATASET 后剩余 input 索引重排（input1..N），SQL 可能要同步改
- meta 字段也要更新（meta = JSON.stringify(actions)）
- description 改了不影响行为，但便于追溯
```

## 时间窗口缩减实战

v2 是近 3 个月窗口（千万级），v3 改昨日窗口（验证沙盒）：

```js
let sql = v2_sql.replace(
  /add_months\(concat\(substr\(current_date\(\)\s*,1,7\),'-01'\),-3\)/g,
  "date_sub(current_date(), 1)",
);
sql = sql.replace(
  /WHERE\s+`order_date`\s*<\s*'today'/g,
  "WHERE `order_date` = date_sub(current_date(), 1)",
);
```

**结果**：v3 跑出 ~50 万行（与业务预期 60 万级别误差 8%）。
