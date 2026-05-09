# Part A · 完整命令清单与数据缓存机制

> 由 SKILL.md V1.4.0 拆分而出。SKILL.md 主文档只保留命令骨架；写卡片/排查取数/管缓存时回到这里查全表。

---

## 核心命令

```bash
SCRIPT="python3 scripts/guandata.py"

# 查数据集（默认读本地缓存）
$SCRIPT list-datasets
$SCRIPT list-datasets --columns   # 同时显示每个数据集的字段
$SCRIPT list-datasets --refresh   # 强制刷新缓存（数据源有变更时用）

# 查字段（默认读本地缓存，自动包含计算字段）
$SCRIPT get-columns <ds_id>             # 输出原始字段 + 计算字段
$SCRIPT get-columns <ds_id> --refresh   # 强制刷新缓存
$SCRIPT get-columns <ds_id> --with-calc # 同时显示计算字段（公式字段）

# 查枚举值（筛选前必查，避免值不存在）
# fd_id 从 get-columns 输出第二列拿
$SCRIPT search-values <ds_id> <fd_id> --search "关键词"
$SCRIPT search-values <ds_id> --name "门店名称" --search "某门店"  # 用字段名代替 fd_id

# 建卡+取数（一步到位）
$SCRIPT create-and-get '{"name":"卡片名","ds_id":"数据集ID","chart_type":"SINGLE_VALUE","pg_id":"页面ID","metric":[{"name":"会员id","aggr":"CNT_DISTINCT"}],"filters":[{"name":"营业日期","op":"BT","value":["2026-02-01","2026-02-28"]}]}'
$SCRIPT create-and-get '{...}' --limit 200   # 限制返回200行数据（默认500行上限）

# 建卡+取数（组合图，metric_additional 传折线叠加数据）
$SCRIPT create-and-get '{"name":"达成率趋势","ds_id":"数据集ID","chart_type":"STACKED_COLUMN_WITH_LINE","pg_id":"页面ID","metric":[{"name":"营业额","aggr":"SUM"}],"metric_additional":[{"name":"人数","aggr":"SUM"}],"row":["营业日期(月)"],"column":["销售类型"],"filters":[...]}'

# 仅建卡（不取数）
$SCRIPT create-card '{...}'

# 取卡片数据（含筛选条件）
$SCRIPT get-card-data <card_id>

# 列页面
$SCRIPT list-pages
$SCRIPT list-pages --manageable  # 只显示有编辑权限的页面（日常用这个）

# 注意：list-datasets 默认显示父文件夹ID
# 输出格式示例：
#   数据集名称
#     ID: 数据集ID  |  行数  列数  |  状态
#     父文件夹ID: 父文件夹ID
#     描述: 描述信息
#     路径: 目录路径

# 创建页面
$SCRIPT create-page "页面名称"
$SCRIPT create-page "页面名称" --parent-dir "目录ID" --desc "描述"

# 获取页面卡片列表
$SCRIPT get-page-cards <pg_id>

# 批量删除卡片（需要 pg_id）
$SCRIPT delete-cards <pg_id> <card_id1> <card_id2> ...
```

---

## 💾 数据缓存机制

**`create-and-get`、`get-card-data` 命令都会自动将数据保存到本地 CSV 缓存文件。**

输出末尾会显示缓存路径：`📁 缓存: .cache/data/xxx.csv`

### 缓存目录结构

```
.cache/
├── data/                   # 数据查询缓存（CSV），默认共享目录
├── datasets/               # 数据集列表缓存（JSON）
├── columns/                # 字段列表缓存（JSON）
└── tasks/                  # 按任务隔离的缓存（使用 --task 参数时）
    └── {task_name}/
        ├── data/
        ├── datasets/
        └── columns/
```

### 按任务隔离缓存（--task）

不同任务的缓存混在一起时，用 `--task` 参数按任务名分组。**`--task` 放在子命令前面：**

```bash
# 堂食分析任务 → .cache/tasks/堂食分析/data/
$SCRIPT --task "品类分析" create-and-get '{"name":"品类","ds_id":"<dataset_id>",...}'

# 查字段也隔离
$SCRIPT --task "会员分析" get-columns <dataset_id>
```

不加 `--task` 时，缓存仍在默认的 `.cache/data/` 共享目录。

### 缓存清理

当缓存占用过多空间或数据过期时，需要清理缓存：

```bash
# 清理所有数据查询缓存（保留最近7天）
find .cache/data -name "*.csv" -mtime +7 -delete

# 清理所有缓存（彻底清空）
rm -rf .cache/*
```

### 缓存文件格式

CSV，首行为表头，后续行为数据。用 Excel / pandas / csv 模块直接读即可。

### 大模型使用规范

**当拿到取数结果后，必须用缓存文件处理数据，不要把大量数据塞进上下文。**

正确做法：
```python
import csv
# 1. 从输出中提取缓存路径
# 2. 用代码读取缓存
with open('.cache/data/xxx.csv', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    headers = next(reader)
    rows = list(reader)
# headers[j] 是第 j 列的字段名
# rows[i][j] 是第 i 行第 j 列的值（字符串）
```

---

## 错误处理

| 状态码 | 处理 |
|--------|------|
| 500 | 终止，服务器问题 |
| 401 | 终止，登录失效 |
| 403 | 终止，无权限 |
| 404 | 终止，资源不存在 |
