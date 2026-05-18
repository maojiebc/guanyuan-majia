# majia-guanyuan · Tool-Agnostic Agent Skill for Guandata BI

> **Tool-agnostic** Agent Skill for **Guandata BI (观远 BI)** — Data analysis / ETL governance & write / Custom chart development, **all-in-one**.
> Compatible with **Claude Code** · **OpenClaw** · **Codex** · **Hermes (gbrain)** and any agent that recognizes `SKILL.md` frontmatter.
> Battle-tested with 60+ ETL create/refactor/repair operations + governance scans + custom chart injection debugging.

[![Skill Version](https://img.shields.io/badge/skill-v2.1.5-blue)](./SKILL.md)
[![GitHub Release](https://img.shields.io/github/v/release/maojiebc/majia-guanyuan?label=release&color=success)](https://github.com/maojiebc/majia-guanyuan/releases)
[![skills.sh](https://skills.sh/b/maojiebc/majia-guanyuan)](https://skills.sh/maojiebc/majia-guanyuan)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-✓-orange)](https://docs.claude.com/en/docs/claude-code/skills)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-✓-blueviolet)](https://docs.openclaw.ai/tools/skills)
[![Codex](https://img.shields.io/badge/Codex-✓-black)](https://developers.openai.com/codex/skills)
[![Hermes](https://img.shields.io/badge/Hermes_(gbrain)-✓-darkgreen)](https://github.com/garrytan/gbrain)
[![WorkBuddy](https://img.shields.io/badge/WorkBuddy-compat-1abc9c)](https://www.codebuddy.cn)
[![Qoder](https://img.shields.io/badge/Qoder-compat-fa8231)](https://qoder.com)
[![BI](https://img.shields.io/badge/Guandata-BI_6.x_/_7.x-purple)](https://www.guandata.com/)

**[中文 README](README.md)** · English ↓

---

## Overview

This Skill consolidates three categories of Guandata BI operations into **a single Claude Code Skill**, so AI can handle daily reporting + serious ETL governance + frontend custom chart debugging — all in one place.

<p align="center">
  <img src="./docs/architecture.svg" alt="majia-guanyuan v2.1.3 capability map: three-skill ecosystem (guancli / guanvis-skill / majia-guanyuan) + Part A query + Part B ETL full-stack + Part C front-end injection / Part C-12 HTML application dashboard (NEW)" width="100%"/>
</p>

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
| **Claude Code** | ✅ Verified | `~/.claude/skills/majia-guanyuan/` | `SKILL.md` | Native support |
| **OpenClaw** | ✅ Verified | `~/.openclaw/skills/majia-guanyuan/` or `<workspace>/skills/majia-guanyuan/` | `SKILL.md` | Case-sensitive |
| **Codex (OpenAI)** | ✅ Verified | `~/.codex/skills/majia-guanyuan/` or `<repo>/.codex/skills/majia-guanyuan/` | `SKILL.md` + repo-root `AGENTS.md` (project instructions) | See [Codex skills docs](https://developers.openai.com/codex/skills) |
| **Hermes / gbrain** | ✅ Verified | `<workspace>/skills/majia-guanyuan/` | `SKILL.md` + repo-root `AGENTS.md` (resolver) | See [garrytan/gbrain](https://github.com/garrytan/gbrain) |
| **Cursor / Aider** etc. | 🟡 Theoretical | Anywhere | `AGENTS.md` as project instructions | Only the navigation pointer parts apply |
| Others | 🟡 Universal | Anywhere | `manifest.json` as tool-agnostic metadata | frontmatter + manifest dual fallback |

## 📦 Installation

> **This repo uses git as the single source of truth** — not published to the npm registry. The one-line install experience is preserved via `node bin/install.js` and `npx github:` directly.

### Option 0: GitHub CLI `gh skill` (GitHub CLI 2.90.0+)

```bash
# Install to user-level Codex / Claude Code / OpenClaw / Qoder, etc.
gh skill install maojiebc/majia-guanyuan majia-guanyuan --agent codex --scope user
gh skill install maojiebc/majia-guanyuan majia-guanyuan --agent claude-code --scope user
gh skill install maojiebc/majia-guanyuan majia-guanyuan --agent openclaw --scope user
gh skill install maojiebc/majia-guanyuan majia-guanyuan --agent qoder --scope user

# Preview before installing
gh skill preview maojiebc/majia-guanyuan majia-guanyuan
```

### ⭐ Option 1: Clone + built-in install CLI (recommended)

```bash
# Clone, then auto-install to every agent tool present on this machine
git clone https://github.com/maojiebc/majia-guanyuan.git ~/majia-guanyuan
cd ~/majia-guanyuan
node bin/install.js install                  # auto-detect all
node bin/install.js install --tool claude-code
node bin/install.js install --tool openclaw
node bin/install.js install --tool codex
node bin/install.js install --tool hermes
node bin/install.js install --tool all       # all four

# Other commands
node bin/install.js list                     # show current install state
node bin/install.js uninstall --tool codex   # remove (auto-backs-up your config.json)
```

### Option 2: `npx` from GitHub URL (no clone required)

```bash
# One-liner; npx fetches from GitHub and runs bin/install.js
npx github:maojiebc/majia-guanyuan install --tool claude-code
npx github:maojiebc/majia-guanyuan install --tool all
```

**`bin/install.js` behavior** (same for both options):
- Copies `SKILL.md` / `AGENTS.md` / `manifest.json` / `scripts/` / `references/` into the target tool's skills directory
- Seeds `config.json` from `config.example.json` and prompts you to edit it
- **Never overwrites your existing `config.json`** (real credentials are preserved across reinstalls)
- Skips already-installed targets by default; use `--force` to overwrite

### Option 3: Manual `git clone` directly into the tool's skill directory

```bash
# Claude Code
git clone https://github.com/maojiebc/majia-guanyuan.git ~/.claude/skills/majia-guanyuan

# OpenClaw (personal)
git clone https://github.com/maojiebc/majia-guanyuan.git ~/.openclaw/skills/majia-guanyuan

# Codex (personal)
git clone https://github.com/maojiebc/majia-guanyuan.git ~/.codex/skills/majia-guanyuan

# Codex (project-local)
git clone https://github.com/maojiebc/majia-guanyuan.git <your-repo>/.codex/skills/majia-guanyuan

# Hermes / gbrain (workspace-level)
git clone https://github.com/maojiebc/majia-guanyuan.git <your-workspace>/skills/majia-guanyuan
```

Then configure credentials (same for all tools):

```bash
cd <install_path>
cp config.example.json config.json
vim config.json  # fill in BI base_url / login_id / password / default_pg_id / default_folder_id
```

### Option 4: OpenClaw / ClawHub one-line install

```bash
openclaw skills install majia-guanyuan
clawhub install majia-guanyuan
```

> ClawHub may show a security scan warning: this skill includes a local Python client that encodes the BI login credential as required by the Guandata API and sends it only to the user-configured `base_url`. Before installing from registries, review [SECURITY.md](./SECURITY.md) and inspect [scripts/guandata.py](./scripts/guandata.py).

### Option 5: Hermes skillpack install (if published to gbrain registry)

```bash
gbrain skillpack install majia-guanyuan
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
  "password": "<BI_LOGIN_PASSWORD>",
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
cd <install_path>  # e.g. ~/.claude/skills/majia-guanyuan/

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
majia-guanyuan/
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
└── references/                       # Deep reference docs (V1.5.0 progressive disclosure: 12 files)
    ├── part-a-commands.md            # Full Part A command catalog + cache mechanism (V1.5.0)
    ├── part-a-cards.md               # Card parameters + 26 chart types + 6 examples (V1.5.0)
    ├── part-b-errors.md              # Part B 10-category error detailed fixes (V1.5.0)
    ├── part-b-payload.md             # ETL payload schema deep-dive (V1.5.0)
    ├── part-b-sdk.md                 # v2→v3 bulk refactoring SDK (V1.5.0)
    ├── part-b17-fullchain-rewrite.md # Full B-17 full-chain rewrite methodology (V1.5.0)
    ├── part-c-payload-json.md        # C-3 payload_json troubleshooting deep-dive (V1.5.0)
    ├── guancli-commands.md           # guancli 9-category command quick-ref (V1.5.0)
    ├── custom-chart-playbook.md      # CTO Zhang Jin's full custom chart playbook (V1.1)
    ├── etl-rewrite-original.md       # CTO Zhang Jin's SmartETL rewrite experience (V1.1)
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

## 👤 Author / Contact

**Majia (@maojiebc)** · 超级马甲 (Super Majia)

If this skill helps you, find me on any of these channels — happy to chat about field experience, take feature requests, hear bug reports, or trade notes on user operations / data platforms / BI engineering work:

| Channel | Link |
|---|---|
| 📧 Email | [m9224@163.com](mailto:m9224@163.com) |
| 🐙 GitHub | [github.com/maojiebc](https://github.com/maojiebc) |
| 🪝 ClawHub | [clawhub.ai/p/maojiebc](https://clawhub.ai/p/maojiebc) |
| 🐦 X | [@maojiebc](https://x.com/maojiebc) |
| 📕 Xiaohongshu | [Super Majia](https://xhslink.com/m/4fQMJeHHWKC) |
| 📰 WeChat Official Account | **超级马甲** |

> Built from 14 years of user-operations work, hands-on Guandata BI in production, and 60+ verified ETL write operations.

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

**Latest: V2.1.5** (2026-05-18) — **NEW `references/restaurant-bi-formulas/`: restaurant-chain BI formula playbook** (10 markdown files, 2881 lines, fully anonymized). Distilled from two consecutive production analyst tenures + 39 production ETLs, covering: ① **Formula handbook** (7 chapters, 60+ SQL snippets) — date/time, customer/membership (RFM 8-class × marketing-action mapping + R-threshold tiers), revenue KPIs (AC/ADS/ADT/Comp/CRM%), channel/store (multi-channel review pipeline), coupon/discount, SQL utilities, data-quality traps. ② **6 ETL engineering patterns** (Ch 08) — 10-CTE DWD wide-table base / light-node-heavy-SQL vs heavy-node-light-SQL philosophy / financial dual-source reconciliation / POS system identification / member lifecycle multi-output / Cohort date×store grid. ③ **39 production ETL catalog index** (Ch 09) — categorized across 11 business domains + per-ETL node/IO/SQL quick reference + reuse decision matrix. SKILL.md routing table now includes restaurant BI formula entry. Zero breaking change, pure docs increment. Full details in [CHANGELOG.md](./CHANGELOG.md).

**V2.1.4** (2026-05-15) — Command surface synced with `@guandata/guancli@1.0.21`: ① **`metric query` generalized query** (1.0.20) — `--compare`, `--xtd`, `--recent`, `--percentage`, `--rank-top`, `--last`, fallback `--adv-calc-json`; ② **`card preview -f excel`** (1.0.20) — Excel 2003 XML export; ③ **Cleaner error output** (1.0.21). Manifest dep bumped `^1.0.19 → ^1.0.21`.

**V2.1.3** (2026-05-14) — Documentation-only patch: refreshed `docs/architecture.svg` capability map to reflect the v2.1.x reality — new "three-skill ecosystem" strip (guancli 1.0.19 / guanvis-skill 0.1.13 / majia-guanyuan 2.1.3) + Part C-12 HTML application dashboard NEW highlight block (pink-purple gradient + glow). Also adds a 2880×1840 @2x DPI rendered PNG (`docs/architecture.png`) for npm/ClawHub page fallback. `package.json#files` now ships `docs/` inside the npm tarball.

**V2.1.2** (2026-05-14) — V2.1.1 npm-only packaging hotfix: `package.json#files` adds `templates/`, so `npm install` users finally get the `templates/html-dashboard/` starter pack. Other install paths (GitHub clone, `gh skill install`, ClawHub) already had it since V2.1.1.

**V2.1.1** (2026-05-14) — New **Part C-12: HTML application-style dashboard generation** (`references/part-c-html-dashboard.md` + `templates/html-dashboard/` starter pack with GDHTML runtime + 2 starter modules + `patch_selector_linkage.js`). When users ask for "more advanced / application-like / beyond standard dashboards", auto-routes to SDK subtype + DATA_GRID dataView layer architecture; the descriptor-level patch fills the gap where `guanvis-skill .linkToAll()` cannot reach custom chart internal dataViews. `guancli card preview` command surface corrected (no more `--pg-id`); adds `.data // .response` jq compatibility.

**V2.1.0** (2026-05-13) — `guanvis-skill@0.1.13` rolled out via Guandata internal Nexus; Part A standard card-creation now routes to it first; new `references/internal-nexus-install.md` tarball install playbook (incl. macOS `com.apple.quarantine` pitfall); coexistence section upgraded from 2-skill to 3-skill split.

Full changelog: [CHANGELOG.md](CHANGELOG.md) or [GitHub Releases](https://github.com/maojiebc/majia-guanyuan/releases).

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
