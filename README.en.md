# guanyuan-majia · Tool-Agnostic Agent Skill for Guandata BI

> **Tool-agnostic** Agent Skill for **Guandata BI (观远 BI)** — Data analysis / ETL governance & write / Custom chart development, **all-in-one**.
> Compatible with **Claude Code** · **OpenClaw** · **Codex** · **Hermes (gbrain)** and any agent that recognizes `SKILL.md` frontmatter.
> Battle-tested with 60+ ETL create/refactor/repair operations + governance scans + custom chart injection debugging.

[![Skill Version](https://img.shields.io/badge/skill-v1.3-blue)](./SKILL.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-✓-orange)](https://docs.claude.com/en/docs/claude-code/skills)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-✓-blueviolet)](https://docs.openclaw.ai/tools/skills)
[![Codex](https://img.shields.io/badge/Codex-✓-black)](https://developers.openai.com/codex/skills)
[![Hermes](https://img.shields.io/badge/Hermes_(gbrain)-✓-darkgreen)](https://github.com/garrytan/gbrain)
[![BI](https://img.shields.io/badge/Guandata-BI_6.x_/_7.x-purple)](https://www.guandata.com/)

**[中文 README](README.md)** · English ↓

---

## Overview

This Skill consolidates three categories of Guandata BI operations into **a single Claude Code Skill**, so AI can handle daily reporting + serious ETL governance + frontend custom chart debugging — all in one place.

| Part | Capability | When to use |
|---|---|---|
| 🅰️ **A** | Data query & card creation | "Show February revenue by city" / "Make me a pivot table" / "Delete this card" |
| 🅱️ **B** | ETL governance & write | "Scan ETLs and tell me what can be deleted" / "Create a new ETL" / "Why does direct-save fail?" |
| 🅱️ **B-17** | Full-chain rewrite methodology | "Rewrite this SmartETL chain as pure SQL" / "Replica page verification / card-level comparison" |
| 🆎 **C** | Custom chart dev & debugging | "payload_json parsing fails" / "fixed card misaligned" / "overlay leaks across routes" |

---

## ✨ Features

### Part A — Data Analysis

- ✅ **26 chart types** one-shot card creation + data fetch (column / line / pivot / combo / bubble...)
- ✅ **Custom formula fields** — dynamic calculated columns like `SUM(x)/SUM(y)*100` without pre-defining in BI UI
- ✅ Multi-table / multi-page / per-task isolated cache (`--task` flag)
- ✅ 26 aggregations + 13 filter operators + 6 date granularities (year/quarter/month/week/day/weekday)
- ✅ Auto-handles Guandata 7.0+ draft-release mechanism

### Part B — ETL Governance & Write

- ✅ **11 battle-tested BI HTTP API endpoints** (POST/GET/DELETE/OPTIONS, full coverage)
- ✅ **Bulk governance scan**: dependency graph → cycle detection → complexity scoring → 8-dim ETL + 4-dim field retention judgment
- ✅ **ODS/DIM/DWD/DWS/APP** five-layer architecture refactoring guide
- ✅ **Field usage dual-source audit** (page + ETL grep — looking only at dashboards **overestimates removable fields by 8×**)
- ✅ **POST /api/etl/direct-save** — full payload schema for create + update (same endpoint)
- ✅ **Real error retrieval** — `status:FINISHED` is just the trigger result; the real error lives in `GET /api/task/<id>.response.result.error`
- ✅ **Delete topology**: `DELETE /api/data-source/` MUST come before `DELETE /api/etl/`
- ✅ **v2→v3 batch refactoring SDK**: `transformV2ToV3()` 7-step rewrite + node ID remapping
- ✅ **CTO Zhang Jin's full-chain rewrite methodology**: 4 deliverables + 8 hard rules + 5-step workflow + three-layer verification + diff tracking 5-step + empty snapshot handling

### Part C — Custom Chart Development

- ✅ **`renderChart` 4-arg runtime contract** explained (NOT what you think — first arg is NOT the DOM root)
- ✅ **5 `data` shape patterns** to recognize
- ✅ **payload_json truncation 3-step diagnosis** (`Unterminated string` → fix the data pipeline, don't pile on JS compatibility hacks)
- ✅ **Recommended: split into columns**, not one big JSON string
- ✅ **z-index baseline** (container 8 / mask 1 / fixed cards 20)
- ✅ **Lifecycle management** (URL mismatch / edit mode / phoneView / route exit → tear down injections)
- ✅ **MutationObserver infinite loop trap** — replace with low-frequency polling + precise rect comparison
- ✅ **Copied page card id relocation** (no error thrown, fails silently)
- ✅ **Real browser verification 8-checklist**

### Error Handling Manual

- 🔧 **10 categories of high-frequency ETL errors** documented with reproduction + root cause + fix:
  `请输入ETL名称` / `保存路径无效` / Upstream no-run permission / Hidden newlines in field names / `<> NULL` / relativeFieldAlias misalignment / CTE inner `;` / Self-join alias collision / UNION column count mismatch / String literal vs DATE comparison

---

## ✅ Suitable / ❌ Not Suitable

### ✅ Suitable

- Daily data analysis and reporting on Guandata BI (6.x / 7.x)
- ETL governance (cycle detection, field retention judgment, layer redesign)
- Bulk ETL rebuilding (30+ table v2→v3 migration)
- Replica page verification / card-level comparison / diff tracking
- Custom chart HTML/CSS/JS injection development & debugging
- Anyone who can't write code but wants AI to handle the above

### ❌ Not Suitable

- Other BI platforms (Tableau / Power BI / Superset) — this skill targets **Guandata BI ONLY**
- Compliance environments that prohibit raw HTTP API calls
- Users without BI account or write permissions (Part B requires ETL create + dataset run permissions)

---

## 🔌 Compatibility

This skill is **tool-agnostic**. Any agent that supports the `SKILL.md` frontmatter standard can load it. Verified on:

| Tool | Status | Install path | Entry | Notes |
|---|:---:|---|---|---|
| **Claude Code** | ✅ Verified | `~/.claude/skills/guanyuan-majia/` | `SKILL.md` | Native support |
| **OpenClaw** | ✅ Verified | `~/.openclaw/skills/guanyuan-majia/` or `<workspace>/skills/guanyuan-majia/` | `SKILL.md` | Case-sensitive |
| **Codex (OpenAI)** | ✅ Verified | `~/.codex/skills/guanyuan-majia/` or `<repo>/.codex/skills/guanyuan-majia/` | `SKILL.md` + repo-root `AGENTS.md` (project instructions) | See [Codex skills docs](https://developers.openai.com/codex/skills) |
| **Hermes / gbrain** | ✅ Verified | `<workspace>/skills/guanyuan-majia/` | `SKILL.md` + repo-root `AGENTS.md` (resolver) | See [garrytan/gbrain](https://github.com/garrytan/gbrain) |
| **Cursor / Aider** etc. | 🟡 Theoretical | Anywhere | `AGENTS.md` as project instructions | Only the navigation pointer parts apply |
| Others | 🟡 Universal | Anywhere | `manifest.json` as tool-agnostic metadata | frontmatter + manifest dual fallback |

## 📦 Installation

### Option 1: Clone into the target tool's skill directory

```bash
# Claude Code
git clone https://github.com/maojiebc/guanyuan-majia.git ~/.claude/skills/guanyuan-majia

# OpenClaw (personal)
git clone https://github.com/maojiebc/guanyuan-majia.git ~/.openclaw/skills/guanyuan-majia

# Codex (personal)
git clone https://github.com/maojiebc/guanyuan-majia.git ~/.codex/skills/guanyuan-majia

# Codex (project-local)
git clone https://github.com/maojiebc/guanyuan-majia.git <your-repo>/.codex/skills/guanyuan-majia

# Hermes / gbrain (workspace-level)
git clone https://github.com/maojiebc/guanyuan-majia.git <your-workspace>/skills/guanyuan-majia
```

Then configure credentials (same for all tools):

```bash
cd <install_path>
cp config.example.json config.json
vim config.json  # fill in BI base_url / login_id / password / default_pg_id / default_folder_id
```

### Option 2: OpenClaw one-line install (if available on ClawHub)

```bash
openclaw skills install guanyuan-majia
```

### Option 3: Hermes skillpack install (if available)

```bash
gbrain skillpack install guanyuan-majia
```

### Dependencies (same for all tools)

```bash
# Python deps (Part A)
pip install httpx

# guancli (required for Part B/C)
npm install -g @guandata/guancli
guancli auth login   # configure BI login
```

---

## ⚙️ Configuration

Copy `config.example.json` to `config.json` and fill in real credentials:

```json
{
  "version": "6",
  "base_url": "https://your-bi-instance.example.com/",
  "domain": "guanbi",
  "login_id": "your_username@example.com",
  "password": "your_password_here",
  "default_pg_id": "your_default_page_id",
  "default_folder_id": "your_default_folder_id"
}
```

| Field | Required | Description |
|---|:---:|---|
| `version` | ✅ | `"6"` (Guandata 6.x) or `"7"` (Guandata 7.0+, supports draft/release) |
| `base_url` | ✅ | BI instance URL, e.g., `https://bi.company.com:8080` |
| `domain` | ✅ | Login domain, usually `guanbi` (ask your BI admin) |
| `login_id` | ✅ | BI login account |
| `password` | ✅ | BI login password (**plaintext, local-only, excluded by .gitignore**) |
| `default_pg_id` | | Default page ID for cards when `pg_id` is not specified |
| `default_folder_id` | | Default folder ID for new pages |

> ⚠️ `config.json` is excluded by `.gitignore` and **will never be committed**. Still, handle credentials with care.

---

## 🚀 Quick Start

### Part A: Card creation & data fetch

```bash
# cwd = skill install dir, all paths are relative
cd <install_path>  # e.g. ~/.claude/skills/guanyuan-majia/

SCRIPT="python3 ./scripts/guandata.py"

# 1. List datasets
$SCRIPT list-datasets

# 2. Get columns
$SCRIPT get-columns <ds_id>

# 3. One-shot create card + fetch data
$SCRIPT create-and-get '{
  "name": "Feb Revenue by City",
  "ds_id": "<dataset_id>",
  "chart_type": "BASIC_COLUMN",
  "pg_id": "<page_id>",
  "row": ["city"],
  "metric": [{"name": "gross_revenue", "aggr": "SUM"}],
  "filters": [{"name": "biz_date", "op": "BT", "value": ["2026-02-01", "2026-02-28"]}],
  "sorting": [{"name": "gross_revenue", "order": "DESC"}]
}'
```

### Part B: Build an ETL

```bash
# 1. Governance scan
guancli etl tree
guancli --raw etl get <id> > raw/<id>.json
# Local script analyzes dependency graph, cycles, complexity → analysis.json + governance-report.md

# 2. Create v2 directories (one ETL + one DATA_SET)
guancli fetch POST /api/directory \
  '{"name":"warehouse_v2","parentDirId":"<parent>","dirType":"ETL"}'
guancli fetch POST /api/directory \
  '{"name":"warehouse_v2","parentDirId":"<parent>","dirType":"DATA_SET"}'

# 3. Save & execute
guancli fetch POST /api/etl/direct-save --stdin < payload.json
guancli fetch POST /api/etl/execute '{"dataFlowId":"<id>"}'

# 4. Real error diagnosis (KEY! don't trust status:FINISHED)
guancli fetch GET /api/task/<taskId> | jq '.response.result.error'
```

### Part C: Custom chart

```javascript
// Guandata runtime real signature (the first arg is NOT the DOM root!)
function renderChart(data, clickFunc, config, helpers) {
  // Common data shape:
  // [[ {name:"payload_json",data:["{...}"]}, {name:"report_date",data:["2026-03-18"]} ]]

  // Critical: if JSON.parse(payload_json) throws Unterminated string
  //  → diagnose as "data pipeline truncation", fix the data side (split into columns)
  //  → DO NOT pile on frontend compatibility hacks
}

new GDPlugin().init(renderChart);
```

---

## 📁 Directory Structure

```text
guanyuan-majia/
├── SKILL.md                          # Main doc for AI (Part A + B + C)
├── AGENTS.md                         # Codex project instructions / Hermes resolver (V1.3)
├── manifest.json                     # Tool-agnostic skill metadata (V1.3)
├── README.md                         # Chinese README
├── README.en.md                      # This file
├── ATTRIBUTIONS.md                   # Credits & sources
├── LICENSE                           # MIT
├── config.example.json               # Config template (public)
├── config.json                       # Your real credentials (gitignored)
├── .gitignore
├── scripts/
│   ├── guandata.py                   # Part A main script (cards / fetch / delete / publish)
│   └── zonedata_builder/             # zoneData builder module
└── references/                       # Deep reference docs
    ├── custom-chart-playbook.md      # CTO Zhang Jin's full custom chart playbook (original)
    ├── etl-rewrite-original.md       # CTO Zhang Jin's SmartETL rewrite experience (original)
    ├── execplan-spec.md              # OpenAI Codex ExecPlan specification (V1.2)
    └── agents-rule.md                # OpenAI Codex minimal scheduling rule (V1.2)
```

---

## 🎯 When to Use Part A / B / C

| User request | Goes to |
|---|---|
| "Show me February revenue by city" | A |
| "Make me a pivot table" | A |
| "Delete this card" | A |
| "Scan our BI ETLs and tell me what can be deleted" | B |
| "What about ETL circular dependencies?" | B |
| "Create a new ETL for me" | B |
| "How to fix direct-save errors" | B |
| "Field usage audit" | B |
| "Rewrite this SmartETL chain as pure SQL" | **B-17** |
| "Replica page verification / card-level comparison" | **B-17** |
| "How to write conclusions for empty upstream snapshots" | **B-17** |
| "Diff tracking — is it SQL bug or execution timing?" | **B-17** |
| "30+ table multi-day project — give me an ExecPlan skeleton" | **B-17.11** |
| "Custom chart script not running / payload_json error" | **C** |
| "Fixed card misaligned / overlay leaks across routes" | **C** |
| "What's the first arg of renderChart actually?" | **C** |

---

## ❤️ Credits & Attribution

This skill stands on the shoulders of multiple predecessors and experience contributors. Detailed credits in [ATTRIBUTIONS.md](./ATTRIBUTIONS.md):

- **[guandata-bi @ ClawHub](https://clawhub.ai/skills/guandata-bi)** — The original general-purpose Guandata BI skill that inspired this project
- **[zhengyuhe123/guandata](https://github.com/zhengyuhe123/guandata)** — Original guandata GitHub project
- **小小郑3号 · guandata70** — Guandata 7.0+ adapter (draft/release mechanism), the direct predecessor of Part A
- **CTO Zhang Jin (张进, Guandata BI)** — Core contributor of Part B-17 (SmartETL full-chain rewrite methodology) and Part C (custom chart dev & debugging)
- **OpenAI Codex** — V1.2 borrows the [ExecPlan specification](./references/execplan-spec.md) (self-contained living docs + four-section project management structure), used to track multi-day, 30+ table SmartETL rewrite engineering work
- **maojiebc (马甲)** — Part A/B integration and 60+ ETL write empirical records

> Without the open-source spirit of ClawHub / Zhang Jin / Xiao Xiao Zheng 3hao / OpenAI Codex, this skill wouldn't exist.

---

## 📋 Version History

Full changelog in [SKILL.md version record](./SKILL.md#-版本记录).

- **V1.3** (2026-05-09) — Tool-agnostic. Native support for Claude Code / OpenClaw / Codex / Hermes (gbrain). Added repo-root `AGENTS.md` (Codex project instructions + Hermes resolver) and `manifest.json` (tool-agnostic metadata); removed all `~/.claude/skills/` hardcoded paths; README adds Compatibility section listing per-tool install commands.
- **V1.2** (2026-05-09) — Adopted OpenAI Codex's ExecPlan spec; added B-17.11 (SmartETL-tailored ExecPlan skeleton + four-section workflow), B-12 engineering pointer; references/ adds execplan-spec.md + agents-rule.md
- **V1.1** (2026-05-09) — Integrated CTO Zhang Jin's two experience docs: B-17 full-chain rewrite methodology + Part C custom chart
- **V1.0** (2026-05-09) — Renamed `guandata70` → `guanyuan-majia`, added Part B: full ETL governance & write guide
- **V0.x** (2026-03-30) — guandata70 initial version (by 小小郑3号), Guandata BI 7.0+ adapter

---

## 🤝 Contributing

Issues and PRs welcome:

- 🐛 Found an error not in the manual? Submit an issue with error message + payload + real error (`/api/task/<id>.response.result.error`)
- 📝 Tested a new BI HTTP API endpoint? Add it to Part B's API map
- 🎨 New custom chart scenario? Add it to Part C
- 📚 Doc improvements, translations, typo fixes — PR directly

---

## 📄 License

[MIT](./LICENSE) © 2026 [maojiebc](https://github.com/maojiebc) and contributors.

This skill is built upon other open-source works. See [ATTRIBUTIONS.md](./ATTRIBUTIONS.md) for detailed attribution.
