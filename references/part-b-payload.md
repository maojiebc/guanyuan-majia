# Part B · ETL payload 完整模板与复用工作流

> 由 SKILL.md V1.4.0 拆分而出。SKILL.md 主文档只保留"三节点骨架 + 字段最小集"的速查；写新 ETL 时回到这里查完整 payload 和复用脚本。
>
> 上游章节：B-3 新建目录（在 SKILL.md 主文）。下游章节：B-5 执行 + B-9 报错手册（[references/part-b-errors.md](part-b-errors.md)）。

## 目录
1. [反推 schema](#反推-schema)
2. [最小骨架：3 节点](#最小骨架3-节点)
3. [完整 payload 模板](#完整-payload-模板)
4. [节点字段速查（含踩坑标注）](#节点字段速查含踩坑标注)
5. [SQL 节点的位置式 input 索引](#sql-节点的位置式-input-索引必须警惕)
6. [已知支持的节点类型](#已知支持的节点类型)
7. [dataFlowId 控制 create vs update](#dataflowid-控制-create-vs-update)
8. [B-8 复用模板：从扫描到落表](#b-8-复用模板从扫描到落表)

---

## 反推 schema

```bash
guancli --raw etl get <旧ETL_id> > old.json
jq '.data.actions[] | {id,name,type,sources,inputDsId,outputDsName,parentDirId,sql,dataSource,relativeFieldAlias}' old.json
```

## 最小骨架：3 节点

```text
INPUT_DATASET → SQL_SCRIPT → OUTPUT_DATASET
```

## 完整 payload 模板

```json
{
  "name": "dim_store_master_v2",
  "parentDirId": "<etl_dir_id>",
  "actions": [
    {
      "id": "id_1778227328970_1",
      "name": "input_source",
      "type": "INPUT_DATASET",
      "sources": [],
      "inputDsId": "<source_ds_id>"
    },
    {
      "id": "id_1778227328970_2",
      "name": "transform",
      "type": "SQL_SCRIPT",
      "sources": ["id_1778227328970_1"],
      "sql": "SELECT DISTINCT\n  `store_code` AS `store_id`,\n  `store_name` AS `store_name`\nFROM input1\nWHERE `store_code` IS NOT NULL;"
    },
    {
      "id": "id_1778227328970_3",
      "name": "dim_store_master_v2",
      "type": "OUTPUT_DATASET",
      "sources": ["id_1778227328970_2"],
      "outputDsName": "dim_store_master_v2",
      "parentDirId": "<ds_dir_id>",
      "dataSource": {
        "created": false,
        "name": "dim_store_master_v2",
        "parentDirName": "warehouse_v2",
        "parentDirId": "<ds_dir_id>",
        "dirPath": [
          { "dirId": "<root_dir_id>", "dirName": "Root" },
          { "dirId": "<parent_ds_dir_id>", "dirName": "ParentDB" },
          { "dirId": "<ds_dir_id>", "dirName": "warehouse_v2" }
        ]
      }
    }
  ]
}
```

## 节点字段速查（含踩坑标注）

| 字段 | INPUT_DATASET | SQL_SCRIPT | OUTPUT_DATASET |
|---|---|---|---|
| `id` | 必填 | 必填 | 必填 |
| `type` | `"INPUT_DATASET"` | `"SQL_SCRIPT"` | `"OUTPUT_DATASET"` |
| `sources` | `[]` | 上游节点 id 数组 | 上游节点 id 数组 |
| `inputDsId` | **必填** | null | null |
| `sql` | null | **必填**，字段名是 `sql` ⚠️ **不是 `sqlScript`** | null |
| `outputDsName` | null | null | **必填** |
| `parentDirId` | null | null | **数据集目录 id** |
| `dataSource` | null | null | 必填，含 dirPath、parentDirId |
| `relativeFieldAlias` | **关键**：fieldHash → 字段名映射 | null | null |
| `displayType` | DATAFLOW / CLICKHOUSE / MYSQL / FEISHU_SPREADSHEET | null | DATAFLOW |
| `cascadeUpdateEnabled` | true/false | null | null |

⚠️ **`sql` vs `sqlScript` 字段名最大坑**：写错时 direct-save 不报错（接受任意字段），但 SQL 不生效——BI 落库后看到的还是老 SQL。这个 bug 极隐蔽，必须用正确字段名 `sql`。

## SQL 节点的位置式 input 索引（必须警惕）

```text
SQL 里 input1 = sources[0] 对应的 INPUT_DATASET
SQL 里 input2 = sources[1] 对应的 INPUT_DATASET
... (位置式索引，不是按 ID)
```

**关键陷阱**：删除某个 INPUT_DATASET 节点（去循环依赖时常见），其余 input 索引会**自动往前补**：原 input3 变成 input2，原 input5 变成 input3。**改 input 节点必须同时改 SQL！**

## 已知支持的节点类型

```text
INPUT_DATASET     上游输入
SQL_SCRIPT        Spark SQL（推荐）
OUTPUT_DATASET    输出数据集
FILTER_ROWS       行筛选（看 .filterConditions）
JOIN_DATA         多表 join（看 .dataFusion）
GROUP_BY          分组聚合（看 .zoneData.metric）
CALCULATOR        计算字段（看 .formulas[].expr）
SELECT_COLUMNS    选列
APPEND_ROWS       纵向合并 / UNION
```

**实战推荐**：把所有非 SQL 节点全部编译成单条 SQL_SCRIPT，三节点结构最简单可控。

## dataFlowId 控制 create vs update

```bash
# 新建：payload 顶层不带 dataFlowId
guancli fetch POST /api/etl/direct-save --stdin < payload.json
# => {"result":"ok","response":{"success":true,"dataFlowId":"<new_id>"}}

# 更新：payload 顶层加 "dataFlowId":"<existing_id>"
guancli fetch POST /api/etl/direct-save --stdin < payload-updated.json
```

create 和 update 是**同一个接口**。SQL 改错直接改 payload 加 `dataFlowId` 再 POST，**不要**删了重建。

---

## B-8 复用模板：从扫描到落表

```bash
# === 阶段一：治理扫描 ===
PARENT_DIR="<父ETL目录id>"
guancli etl search '' -d $PARENT_DIR --raw > etl-list.json

mkdir -p raw
jq -r '.response.contents[].dataFlowId' etl-list.json | while read id; do
  guancli --raw etl get $id > raw/$id.json
done

node analyze.mjs raw/ > analysis.json
# 人工 review → migration-plan.json

# === 阶段二：建目录 ===
NEW_DIR_NAME="warehouse_v2"
PARENT_ETL_DIR="<父ETL目录id>"
PARENT_DS_DIR="<父数据集目录id>"

ETL_DIR=$(guancli fetch POST /api/directory \
  "{\"name\":\"$NEW_DIR_NAME\",\"parentDirId\":\"$PARENT_ETL_DIR\",\"dirType\":\"ETL\"}" \
  | jq -r '.response.dirId')

DS_DIR=$(guancli fetch POST /api/directory \
  "{\"name\":\"$NEW_DIR_NAME\",\"parentDirId\":\"$PARENT_DS_DIR\",\"dirType\":\"DATA_SET\"}" \
  | jq -r '.response.dirId')

# === 阶段三：写入 + 执行（每张 v2 表循环） ===
TARGET_NAME="<输出表名>"
DFID=$(guancli fetch POST /api/etl/direct-save --stdin < payload.json \
  | jq -r '.response.dataFlowId')

# 节点预览（成功再 execute）
NODE_OUT=$(guancli etl get $DFID --raw \
  | jq -r '.data.actions[] | select(.type=="OUTPUT_DATASET") | .id')
guancli etl preview $DFID $NODE_OUT --limit 5 --timeout 120

TASK=$(guancli fetch POST /api/etl/execute "{\"dataFlowId\":\"$DFID\"}" \
  | jq -r '.response.taskId')

until [ "$(guancli task get $TASK --raw | jq -r '.response.status')" != "RUNNING" ]; do
  sleep 10
done

# 失败定位
guancli fetch GET "/api/task/$TASK" | jq '.response.result.error'

# 成功验证
guancli ds search $TARGET_NAME --raw \
  | jq '.response.contents[0] | {dsId,name,rowCount,colCount}'

# === 阶段四：删除旧链路（确认 v2 对账无误后） ===
# ⚠️ 见 SKILL.md B-7.0 删除前的硬性安全闸 — 必须用户逐项确认 + 下游切流 + 对账通过
guancli fetch DELETE /api/data-source/<v1_dsId>
guancli fetch DELETE /api/etl/<v1_etlId>
```
