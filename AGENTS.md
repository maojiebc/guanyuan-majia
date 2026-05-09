# AGENTS.md — guanyuan-majia

This file is read by:
- **OpenAI Codex** as project-level instructions (when cwd is inside this repo)
- **Hermes / gbrain** as a resolver file (alternative to `RESOLVER.md`)
- Other AGENTS.md-aware tools (e.g., **Cursor**, **Aider**)

## What this repo is

A Claude Code Skill for **Guandata BI (观远 BI)** — a tool-agnostic agent skill packaged so it works with **Claude Code**, **OpenClaw**, **Hermes/gbrain**, **Codex**, and any other agent that recognizes `SKILL.md` frontmatter.

Three capabilities packaged into one skill:
- **Part A** — Data query & card creation
- **Part B** — ETL governance, write, delete (incl. full-chain rewrite methodology and ExecPlan workflow)
- **Part C** — Custom chart development & debugging

## Required reading order for any task

Before performing any work in this repo, always:

1. Read `SKILL.md` (the main doc, ~2000 lines). The `## 🧭 Part 选择` table at the top tells you which Part (A/B/C) covers the user's request.
2. Read only the relevant Part section in detail. Don't load the whole SKILL.md unnecessarily — Part B alone covers most ETL work.
3. Check `config.example.json` for the credential schema. The user's real `config.json` is `.gitignore`-d.

## Tool-specific entry points

| Tool | Install path | Entry |
|---|---|---|
| Claude Code | `~/.claude/skills/guanyuan-majia/` | `SKILL.md` |
| OpenClaw | `~/.openclaw/skills/guanyuan-majia/` or `<workspace>/skills/guanyuan-majia/` | `SKILL.md` |
| Codex | `~/.codex/skills/guanyuan-majia/` or `<repo>/.codex/skills/guanyuan-majia/` | `SKILL.md` (this `AGENTS.md` provides project-level instructions) |
| Hermes / gbrain | `<workspace>/skills/guanyuan-majia/` | `SKILL.md` (this `AGENTS.md` serves as the resolver pointer) |
| Other agents | Anywhere; see `manifest.json` and `SKILL.md` frontmatter | `SKILL.md` |

The `SKILL.md` frontmatter (`name: guanyuan-majia`, `description: ...`, `version: "1.3"`) is the universal handshake every agent should parse.

## Hard rules (do not violate)

- **Do not commit `config.json`** — it contains real BI credentials. Already in `.gitignore`. The committed template is `config.example.json`.
- **Do not modify `references/`** — they're verbatim original docs from contributors (CTO Zhang Jin SmartETL rewrite + custom chart playbook, OpenAI Codex ExecPlan spec, AGENTS.md spec). Cite, don't edit.
- **Do not strip version frontmatter** in `SKILL.md`. Bump `version` and update the version log section per the changelog convention when making changes.
- **Do not add tool-specific code paths** (e.g., `if claude_code: ...`) inside scripts or SKILL.md. The skill is tool-agnostic on purpose.

## Repo layout (one-liner per file)

    SKILL.md              ← Main agent doc (Part A + B + C). All Parts live here.
    AGENTS.md             ← This file (Codex/Hermes/Cursor entry).
    README.md             ← Human-facing 中文 README.
    README.en.md          ← Human-facing English README.
    ATTRIBUTIONS.md       ← Credits to contributors.
    LICENSE               ← MIT.
    manifest.json         ← Tool-agnostic metadata (name/version/triggers/entry).
    config.example.json   ← Credentials template.
    config.json           ← (gitignored) Real credentials.
    .gitignore
    scripts/
      guandata.py         ← Part A main script (cards / fetch / delete / publish).
      zonedata_builder/   ← zoneData builder module.
    references/
      execplan-spec.md          ← OpenAI Codex ExecPlan full spec.
      agents-rule.md            ← OpenAI Codex minimal scheduling rule.
      etl-rewrite-original.md   ← CTO Zhang Jin SmartETL rewrite (original).
      custom-chart-playbook.md  ← CTO Zhang Jin custom chart playbook (original).

## Verification

After modifying anything, run a sanity check that no real credentials leak:

    git ls-files | grep -E "config\.json$|\.cache/|columns_cache/"

The output must be empty (the only `config*` file tracked is `config.example.json`).
