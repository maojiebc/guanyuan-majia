# Attributions / 致谢与来源

This skill is built on top of multiple predecessors and contributions from the Guandata BI community. Detailed attribution below.

本 skill 整合了观远 BI 社区多个前辈项目和经验贡献者的成果。详细致谢如下。

---

## 🌱 Original Skill Sources / 原始 Skill 来源

### 1. guandata-bi @ ClawHub

- **URL**: https://clawhub.ai/skills/guandata-bi
- **Description**: 观远 BI 通用版 skill，由 ClawHub 平台维护。本项目最早的灵感来源，提供了 list-datasets / get-columns / search-values / create-card / get-card-data 等基础能力的设计思路。
- **Contribution to this project / 对本项目的贡献**: Part A 基础架构（数据集查询、字段查询、卡片创建）。

### 2. zhengyuhe123/guandata

- **URL**: https://github.com/zhengyuhe123/guandata
- **Description**: guandata 原始 GitHub 开源项目，提供了 Python 脚本与观远 BI HTTP API 的初版对接实现。
- **Contribution / 贡献**: 脚本工程化结构（`guandata.py` 主文件 + `zonedata_builder/` 模块拆分）。

### 3. guandata70 (by 小小郑3号)

- **Original location / 原位置**: 用户本地 skill 目录 `~/.claude/skills/guandata70/`（V1.0 之前）
- **Author / 作者**: 小小郑3号
- **Date / 日期**: 2026-03-30
- **Description**: 观远 BI 7.0+ 适配版，针对 7.0+ 的 draft-release 机制做了自动处理。本项目 V0.x 直接前身。
- **Contribution / 贡献**: Part A 全部内容（26 种图表类型、自定义公式字段、缓存机制、`--task` 隔离、release-page 自动化），以及 V1.0 重命名前的所有历史。

---

## 🎓 Experience Contributors / 经验贡献者

### CTO Zhang Jin (张进) — Guandata BI

- **Source / 来源**: 用户从观远官方获得的两份内部经验文档：
  - `SmartETL改写经验/SKILL.md`（`guanbi-etl-rewrite`）
  - `自定义图表经验/SKILL.md` + `playbook.md`（`guandata-custom-chart`）
- **Contribution / 贡献**:
  - **Part B-17 全链路重写方法论** — 整套 SmartETL 完整改写工程化经验，包括 4 件交付要求、8 条硬规则、5 步标准工作流、三层验收（数据集/副本页/卡片级）、差异追踪 5 步法、空快照处理标准、ExecPlan/modeling/evidence/sql/raw 标准交付物清单
  - **Part C 自定义图表开发与排障** — 完整的 HTML/CSS/JS 注入开发与浏览器排障经验，包括 renderChart 4 参数 runtime 契约、payload_json 截断判断、固定卡片/overlay/z-index/stacking context、复制页 card id 重定位、懒加载 iframe 处理、路由切换销毁规则等
- **Original docs preserved / 原文留档**: [`references/etl-rewrite-original.md`](./references/etl-rewrite-original.md), [`references/custom-chart-playbook.md`](./references/custom-chart-playbook.md)

### OpenAI Codex

- **Source / 来源**: 用户提供的两份 OpenAI 官方文档 `PLANS.md`（ExecPlan 规范）和 `AGENTS.md`（极简调度规则），原文留档于 [`references/execplan-spec.md`](./references/execplan-spec.md) 和 [`references/agents-rule.md`](./references/agents-rule.md)。
- **Contribution / 贡献**:
  - **B-17.11 用 ExecPlan 管理重写工程**（V1.2 新增）— 借自 ExecPlan 规范的核心精神（自包含 + 活文档 + 可观察结果锚定）+ 四个活文档章节（Progress / Surprises & Discoveries / Decision Log / Outcomes & Retrospective），用于 30+ 张表跨多日 SmartETL 重写工程的项目化追踪。
  - **B-12 ExecPlan 指针** — 批量迁移工程经验入口处的判断阈值。

### maojiebc (马甲)

- **GitHub**: https://github.com/maojiebc
- **Contribution / 贡献**:
  - V1.0 重新整合：将 guandata70 + ETL 治理与写入实战经验合并为 `guanyuan-majia`
  - **Part B ETL 治理与写入实证** — 60+ 张 ETL 创建/重构/修复的真实战场记录，包括 11 个已实测 BI HTTP API endpoint、8 维 ETL + 4 维字段去留判断、ODS/DIM/DWD/DWS/APP 五层分层、字段使用度双源审计（page+etl）、v2→v3 批量改造 SDK、10 类高频报错修复手册
  - V1.1 整合 CTO 张进经验
  - V1.2 整合 OpenAI Codex ExecPlan 规范并定制化为 SmartETL 重写场景骨架
  - V1.3 工具无关化：新增 `AGENTS.md` + `manifest.json`，去硬编码路径，原生兼容 Claude Code / OpenClaw / Codex / Hermes (gbrain)
  - 所有文档双语化（中文 / 英文）
  - 公开发布到 GitHub

---

## 🛠️ Underlying Tools / 底层工具

### @guandata/guancli

- **Author / 作者**: Guandata 官方
- **Version / 版本**: 1.0.18
- **NPM**: `npm install -g @guandata/guancli`
- **Role / 角色**: Part B/C 的所有底层 BI HTTP API 调用都通过 `guancli fetch` 完成。本项目的工程化经验是基于 `guancli` 这套官方 CLI 反推 / 验证 / 总结而成。

---

## 📜 License

This skill is licensed under [MIT](./LICENSE).

The integrations and original content from this project (新增整合与原创部分) are under MIT.

For original sources whose licenses differ:
- ClawHub `guandata-bi`: refer to ClawHub's own terms
- `zhengyuhe123/guandata`: refer to upstream LICENSE
- guandata70 by 小小郑3号: 用户本地 skill，作者授权 / Internal skill, original author granted use
- CTO 张进经验文档: 用户内部分享 / Internal sharing, granted to integrate
- OpenAI Codex `PLANS.md` / `AGENTS.md`: 由用户提供原文，作者署名 OpenAI Codex / Provided by user, attribution to OpenAI Codex

If you are a rights-holder of any of the above and want adjustments to attribution or license, please open an issue.

如果您是上述任何资源的版权方且希望调整 attribution 或 license，欢迎提 issue 沟通。

---

## 🙏 Special Thanks

特别感谢观远 BI 团队（@guandata）提供：
- 稳定可反推的 HTTP API
- 详尽的错误信息（让用户能在 CLI 不直接支持的场景下完成大规模 ETL 工程）
- 开放的内部经验分享文化

希望这份 skill 对其他观远 BI 用户有帮助。
