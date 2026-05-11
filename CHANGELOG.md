# Changelog

All notable changes to **guanyuan-majia** are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project follows [Semantic Versioning](https://semver.org/) — see SKILL.md for
the project's specific patch / minor / major rules.

## [1.7.3] — 2026-05-11

### Added
- **Author/contact block appended to `SKILL.md` end** — ClawHub renders
  `SKILL.md` (not `README.md`) on the skill listing page; without this
  the 6-row channel table that v1.7.2 added to `README.md` wasn't
  visible to ClawHub visitors. Block sits after all agent instructions
  so it doesn't pollute the active context during invocation.

Follows `majia-ota-skill` v0.6.1 two-placements rule.

## [1.7.2] — 2026-05-11

### Changed
- **Author/contact section consolidated** — removed the duplicate `## 作者` /
  `## Author` block at the bottom of `README.md` and `README.en.md` (it duplicated
  channels already covered by the canonical `## 👤 作者 / 联系` template above).
- **Skill version badge** synced from stale `v1.6.0` to `v1.7.2`.

### Fixed
- **ClawHub link** in author/contact template — `https://clawhub.ai/maojiebc`
  → `https://clawhub.ai/p/maojiebc` (followed `majia-ota-skill` v0.5.2 template fix).

## [1.7.1] — 2026-05-11

### Security / Sanitization
- **Removed all business-identifying data** from public docs and code examples.
  Previously, docstring examples in `scripts/guandata.py`, multiple references
  pages, `docs/architecture.svg`, and the B-15 ID quick-reference contained
  real customer brand name, real store name, real internal directory IDs, and
  customer-specific field naming (`销售额`, `实收金额`, `客户数` etc.).
  All replaced with generic equivalents (`销售额`, `实收金额`, `客户数`, `示例门店A`,
  `城市A/B`, `<v2_etl_dir_id>` placeholders). No code behavior change.

## [1.7.0] — 2026-05-11

### Added
- **Token disk persistence** — JWT saved to `.cache/token.json`, survives across
  process restarts. Three-tier auth cascade: disk cache → in-memory → API login.
  Eliminates redundant `/public-api/sign-in` calls on every invocation.
- **401/403 auto-retry** — `get_card_data` now catches server-side token rejection,
  force re-authenticates, and retries the request once before failing.
- **CSV metadata sidecar** — `get-card-data` and `create-and-get` now emit a
  `_meta.json` companion alongside each cached CSV, containing field-level metadata
  (name, type, metaType, fieldId, granularity, alias, annotation, role).
- **`status` command** — one-shot diagnostics: config, token validity, cache stats.
- **`set-token` command** — paste a JWT from the browser to bypass credential login.
- `extract_field_metadata()` static method on `GuandataClient`.
- `ensure_auth()` public method replacing explicit `login()` in all 13 cmd functions.

### Changed
- All cmd functions now call `ensure_auth()` instead of unconditional `login()`.
- Command skeleton in SKILL.md updated from 8 to 10 commands.

## [1.6.0] — 2026-05-10

### Added
- `.claude-plugin/marketplace.json` — enables Claude Code plugin marketplace
  install (`/plugin marketplace add maojiebc/guanyuan-majia`). Adds a fourth
  install path alongside `gh skill`, `npx skills`, and clone+copy.
- `CHANGELOG.md` — this file. Consolidates v1.1 → v1.6.0 history that was
  previously scattered across commit messages and only two GitHub Releases.
- `docs/architecture.svg` — a one-page Part A / B / C capability map embedded
  near the top of the README, so the project's three-pillar story is visible
  before a reader scrolls 22 KB of text.
- README "作者 / 联系" section with email, GitHub, ClawHub, X, 小红书,
  公众号 channels.
- `manifest.json` `contact` block (email + GitHub + ClawHub) so non-README
  consumers (registries, agents, indexers) can reach the author.
- LICENSE copyright line: 中文署名 "超级马甲" alongside `maojiebc`.

### Changed
- README signal density: visual diagram pulled the 60+ ETL stories /
  10 报错手册 / 30 条法则白皮书 numbers out of the body into a glance.

## [1.5.3] — 2026-05-09

### Added
- ClawHub scanner-warning documentation (one of the publish-time warnings is
  expected and explained in SECURITY.md / README).

### Changed
- Distribution metadata polish (manifest, badges, attributions).

## [1.5.2] — 2026-05-09

### Added
- ClawHub initial publication. Skill is now installable via ClawHub /
  OpenClaw registry in addition to GitHub.

## [1.5.1] — 2026-05-09

### Changed
- npm path simplified — git is the single source of truth. Skill is no longer
  published as an npm package; `bin/install.js` and `npx github:` flows still
  work for one-line install.

## [1.5.0] — 2026-05-09

### Changed
- **Progressive disclosure refactor.** `SKILL.md` reduced from 2087 → 913
  lines (-56%) by moving deep references into the `references/` directory,
  loaded on demand. The frontmatter description and the top-level pillars
  stay in context; the war-story detail is fetched only when the user's
  task hits that case.

### Fixed
- README / AGENTS.md / ATTRIBUTIONS.md re-synced to v1.5.0 reality after the
  refactor.

## [1.4.0] — 2026-05-09

### Added
- npm package path: `npx @supermajia/guanyuan-bi install` one-liner for users
  who prefer node-based install over `gh skill` or clone.

## [1.3.1] — 2026-05-09

### Fixed
- External-review patch:
  - Code-fence consistency across SKILL.md
  - DELETE-gate language (delete data-source before etl)
  - Task-traversal fix in audit walker

## [1.3.0] — 2026-05-09

### Added
- **Tool-agnostic compatibility.** Verified install paths for
  Claude Code / OpenClaw / Codex / Hermes(gbrain). `AGENTS.md` added at repo
  root for Codex + Hermes projects that read AGENTS.md as resolver.

## [1.2.0] — 2026-05-09

### Added
- **OpenAI Codex `ExecPlan` spec adopted** for SmartETL rewrite engineering.
  All v2→v3 batch refactor flows now produce ExecPlan-style 4-deliverable
  outputs (plan / sql / verify / dispatch).

## [1.1.0] — 2026-05-09

### Added
- Initial public release. Bundled three pillars:
  - **Part A** — Data query + card creation (26 chart types, 26 aggregations,
    13 filter operators, 6 date granularities)
  - **Part B** — ETL governance + write (11 实测 endpoints, 5-layer
    ODS/DIM/DWD/DWS/APP architecture, dual-source field-usage audit,
    direct-save schema, task-error真错误定位, delete topology)
  - **Part C** — Custom chart development & debugging (renderChart 4-arg
    runtime contract, 5 data shapes, payload_json truncation handling,
    z-index baselines, MutationObserver loop traps)
  - 10 类 ETL 高频报错修复手册
  - CTO 张进的全链路重写方法论（4 件交付 + 8 条硬规则 + 5 步标准工作流）

[1.6.0]: https://github.com/maojiebc/guanyuan-majia/releases/tag/v1.6.0
[1.5.3]: https://github.com/maojiebc/guanyuan-majia/releases/tag/v1.5.3
[1.5.2]: https://github.com/maojiebc/guanyuan-majia/releases/tag/v1.5.2
[1.5.1]: https://github.com/maojiebc/guanyuan-majia/releases/tag/v1.5.1
[1.5.0]: https://github.com/maojiebc/guanyuan-majia/releases/tag/v1.5.0
[1.4.0]: https://github.com/maojiebc/guanyuan-majia/releases/tag/v1.4.0
[1.3.1]: https://github.com/maojiebc/guanyuan-majia/releases/tag/v1.3.1
[1.3.0]: https://github.com/maojiebc/guanyuan-majia/releases/tag/v1.3.0
[1.2.0]: https://github.com/maojiebc/guanyuan-majia/releases/tag/v1.2.0
[1.1.0]: https://github.com/maojiebc/guanyuan-majia/releases/tag/v1.1.0
