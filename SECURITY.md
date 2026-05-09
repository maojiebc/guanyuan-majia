# Security Policy

## Credential handling

`guanyuan-majia` is designed to run locally against a user's own Guandata BI instance.

- `config.json` is intentionally excluded by `.gitignore`.
- The sample `config.example.json` contains placeholders only.
- The Python client sends login credentials only to the `base_url` configured by the user.
- The project does not send BI credentials, tokens, datasets, card data, or ETL payloads to any third-party service.

Before installing any Agent Skill from a public registry, inspect its `SKILL.md`, scripts, and dependencies. For this repository, the main script is [scripts/guandata.py](./scripts/guandata.py), and all network calls are made to the configured Guandata BI host.

## Reporting a vulnerability

Please report security issues privately to the maintainer before opening a public issue.

- GitHub: [@maojiebc](https://github.com/maojiebc)
- X: [@maojiebc](https://x.com/maojiebc)

Include the affected version, reproduction steps, and the smallest safe snippet needed to understand the issue.
