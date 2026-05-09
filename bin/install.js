#!/usr/bin/env node
/**
 * @supermajia/guanyuan-bi installer
 *
 * 把 skill 内容（SKILL.md / scripts/ / references/ 等）复制到目标 agent 工具的
 * skill 目录，并初始化 config.json（从 config.example.json 拷贝）。
 *
 * Usage:
 *   npx @supermajia/guanyuan-bi install                  # 自动检测可用工具，全装
 *   npx @supermajia/guanyuan-bi install --tool claude-code
 *   npx @supermajia/guanyuan-bi install --tool all       # 4 工具都装
 *   npx @supermajia/guanyuan-bi install --dry-run        # 只显示要做什么，不动文件
 *   npx @supermajia/guanyuan-bi uninstall --tool claude-code
 *   npx @supermajia/guanyuan-bi list                     # 列出已装的工具
 *
 * 安全约束：
 * - 默认不覆盖已存在的 config.json（含真凭据）
 * - 默认不覆盖已存在的 skill 目录，要 --force 才覆盖
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const SKILL_NAME = 'guanyuan-majia';
const PKG_DIR = path.resolve(__dirname, '..');

const TOOLS = {
  'claude-code': {
    label: 'Claude Code',
    installPath: path.join(os.homedir(), '.claude', 'skills', SKILL_NAME),
    parentDir: path.join(os.homedir(), '.claude', 'skills'),
    detectPath: path.join(os.homedir(), '.claude'),
  },
  'openclaw': {
    label: 'OpenClaw',
    installPath: path.join(os.homedir(), '.openclaw', 'skills', SKILL_NAME),
    parentDir: path.join(os.homedir(), '.openclaw', 'skills'),
    detectPath: path.join(os.homedir(), '.openclaw'),
  },
  'codex': {
    label: 'Codex',
    installPath: path.join(os.homedir(), '.codex', 'skills', SKILL_NAME),
    parentDir: path.join(os.homedir(), '.codex', 'skills'),
    detectPath: path.join(os.homedir(), '.codex'),
  },
  'hermes': {
    label: 'Hermes (gbrain)',
    installPath: path.join(os.homedir(), '.agents', 'skills', SKILL_NAME),
    parentDir: path.join(os.homedir(), '.agents', 'skills'),
    detectPath: path.join(os.homedir(), '.agents'),
  },
};

const FILES_TO_COPY = [
  'SKILL.md',
  'AGENTS.md',
  'manifest.json',
  'README.md',
  'README.en.md',
  'ATTRIBUTIONS.md',
  'LICENSE',
  'config.example.json',
  'scripts',
  'references',
];

// ---------- helpers ----------

function log(...args) {
  console.log(...args);
}

function warn(...args) {
  console.warn('⚠️ ', ...args);
}

function err(...args) {
  console.error('❌', ...args);
}

function ok(...args) {
  console.log('✅', ...args);
}

function copyRecursive(src, dest) {
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
    for (const entry of fs.readdirSync(src)) {
      // 排除运行时缓存与本地 config（防止把别人的 dev 状态发出去）
      if (entry === '.cache' || entry === 'columns_cache' || entry === 'config.json' || entry === '.DS_Store' || entry === 'node_modules') continue;
      copyRecursive(path.join(src, entry), path.join(dest, entry));
    }
  } else {
    fs.copyFileSync(src, dest);
  }
}

function detectAvailableTools() {
  const out = [];
  for (const [key, t] of Object.entries(TOOLS)) {
    if (fs.existsSync(t.detectPath)) out.push(key);
  }
  return out;
}

function parseArgs(argv) {
  const args = { command: argv[0], tool: null, force: false, dryRun: false };
  for (let i = 1; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--tool' || a === '-t') { args.tool = argv[++i]; }
    else if (a === '--force' || a === '-f') { args.force = true; }
    else if (a === '--dry-run' || a === '-n') { args.dryRun = true; }
    else if (a === '--help' || a === '-h') { args.command = 'help'; }
    else if (a === '--version' || a === '-v') { args.command = 'version'; }
  }
  return args;
}

// ---------- commands ----------

function cmdHelp() {
  log(`@supermajia/guanyuan-bi installer

Usage:
  npx @supermajia/guanyuan-bi <command> [options]

Commands:
  install              Install the skill (default: auto-detect available tools)
  uninstall            Remove the skill from a tool's skills directory
  list                 List which tools currently have this skill installed
  version              Print package version
  help                 Show this help

Options:
  --tool, -t <name>    Target: claude-code | openclaw | codex | hermes | all
                       (default: auto-detect, install to all tools whose home
                       directory exists)
  --force, -f          Overwrite an existing skill directory
                       (config.json is NEVER overwritten)
  --dry-run, -n        Show what would happen, do not touch files
  --help, -h           Show this help
  --version, -v        Print version

Examples:
  npx @supermajia/guanyuan-bi install
  npx @supermajia/guanyuan-bi install --tool claude-code
  npx @supermajia/guanyuan-bi install --tool all --force
  npx @supermajia/guanyuan-bi uninstall --tool claude-code
  npx @supermajia/guanyuan-bi list

Documentation: https://github.com/maojiebc/guanyuan-majia
`);
}

function cmdVersion() {
  const pkg = JSON.parse(fs.readFileSync(path.join(PKG_DIR, 'package.json'), 'utf8'));
  log(`@supermajia/guanyuan-bi v${pkg.version}`);
}

function cmdList() {
  log(`Skill installations of ${SKILL_NAME}:\n`);
  for (const [key, t] of Object.entries(TOOLS)) {
    if (fs.existsSync(t.installPath)) {
      const skillMd = path.join(t.installPath, 'SKILL.md');
      let version = '?';
      if (fs.existsSync(skillMd)) {
        // Frontmatter description can be long; read up to first 4KB to be safe.
        const head = fs.readFileSync(skillMd, 'utf8').slice(0, 4096);
        const m = head.match(/^version:\s*"?([\d.]+)"?\s*$/m);
        if (m) version = m[1];
      }
      ok(`${t.label.padEnd(20)} v${version}  →  ${t.installPath}`);
    } else {
      log(`  ${t.label.padEnd(20)} (not installed)`);
    }
  }
}

function resolveTargets(toolArg) {
  if (toolArg === 'all') return Object.keys(TOOLS);
  if (toolArg && TOOLS[toolArg]) return [toolArg];
  if (toolArg) {
    err(`Unknown --tool value: ${toolArg}. Valid: ${Object.keys(TOOLS).join(', ')}, all`);
    process.exit(2);
  }
  // auto-detect
  const detected = detectAvailableTools();
  if (detected.length === 0) {
    err(`No agent tool home directory detected (checked: ~/.claude, ~/.openclaw, ~/.codex, ~/.agents).`);
    err(`Install one of these tools first, or specify --tool <name>.`);
    process.exit(2);
  }
  return detected;
}

function cmdInstall(args) {
  const targets = resolveTargets(args.tool);
  log(`Installing ${SKILL_NAME} to: ${targets.join(', ')}\n`);
  if (args.dryRun) warn('DRY-RUN mode: no files will be modified.\n');

  let installed = 0;
  let skipped = 0;

  for (const key of targets) {
    const t = TOOLS[key];
    log(`▸ ${t.label}`);
    log(`  → ${t.installPath}`);

    const exists = fs.existsSync(t.installPath);
    if (exists && !args.force) {
      warn(`  Already installed. Use --force to overwrite. (config.json is preserved either way.)`);
      skipped++;
      continue;
    }

    if (args.dryRun) {
      log(`  Would copy ${FILES_TO_COPY.length} entries from package`);
      continue;
    }

    // Preserve user's existing config.json
    const existingConfig = path.join(t.installPath, 'config.json');
    let savedConfig = null;
    if (fs.existsSync(existingConfig)) {
      savedConfig = fs.readFileSync(existingConfig);
    }

    if (!fs.existsSync(t.parentDir)) {
      fs.mkdirSync(t.parentDir, { recursive: true });
    }
    if (!fs.existsSync(t.installPath)) {
      fs.mkdirSync(t.installPath, { recursive: true });
    }

    let copied = 0;
    for (const f of FILES_TO_COPY) {
      const src = path.join(PKG_DIR, f);
      const dest = path.join(t.installPath, f);
      if (!fs.existsSync(src)) continue;
      copyRecursive(src, dest);
      copied++;
    }

    // Restore preserved user config, otherwise seed from example
    if (savedConfig !== null) {
      fs.writeFileSync(existingConfig, savedConfig);
      log(`  ✓ Preserved your existing config.json`);
    } else {
      const example = path.join(t.installPath, 'config.example.json');
      if (fs.existsSync(example) && !fs.existsSync(existingConfig)) {
        fs.copyFileSync(example, existingConfig);
        log(`  ✓ Seeded config.json from config.example.json — edit to fill in BI credentials`);
      }
    }

    ok(`  Installed ${copied} entries to ${t.installPath}`);
    installed++;
  }

  log(`\nDone: ${installed} installed, ${skipped} skipped.`);

  if (installed > 0) {
    log(`\nNext steps:`);
    for (const key of targets) {
      const t = TOOLS[key];
      if (fs.existsSync(t.installPath)) {
        log(`  vim ${path.join(t.installPath, 'config.json')}   # fill in BI credentials`);
        break; // just show one example
      }
    }
    log(`  pip install httpx                                    # Part A dependency`);
    log(`  npm install -g @guandata/guancli && guancli auth login   # Part B/C dependency`);
    log(`\nDocs: https://github.com/maojiebc/guanyuan-majia`);
  }
}

function rmrf(p) {
  if (!fs.existsSync(p)) return;
  if (fs.rmSync) fs.rmSync(p, { recursive: true, force: true });
  else fs.rmdirSync(p, { recursive: true }); // node 12 fallback
}

function cmdUninstall(args) {
  if (!args.tool) {
    err(`uninstall requires --tool <name>. Refusing to uninstall everywhere implicitly.`);
    process.exit(2);
  }
  const targets = resolveTargets(args.tool);
  for (const key of targets) {
    const t = TOOLS[key];
    if (!fs.existsSync(t.installPath)) {
      warn(`${t.label}: not installed at ${t.installPath}`);
      continue;
    }
    if (args.dryRun) {
      log(`Would remove ${t.installPath}`);
      continue;
    }
    // Safety: warn if config.json has been customized
    const cfg = path.join(t.installPath, 'config.json');
    const example = path.join(t.installPath, 'config.example.json');
    if (fs.existsSync(cfg) && fs.existsSync(example)) {
      const a = fs.readFileSync(cfg, 'utf8');
      const b = fs.readFileSync(example, 'utf8');
      if (a !== b) {
        warn(`${t.label}: your config.json differs from the template (probably has real credentials).`);
        warn(`  Backing it up to ${cfg}.backup before removing.`);
        fs.copyFileSync(cfg, cfg + '.backup');
      }
    }
    rmrf(t.installPath);
    ok(`${t.label}: removed ${t.installPath}`);
  }
}

// ---------- main ----------

function main() {
  const args = parseArgs(process.argv.slice(2));
  switch (args.command) {
    case 'install': return cmdInstall(args);
    case 'uninstall': return cmdUninstall(args);
    case 'list': return cmdList();
    case 'version': return cmdVersion();
    case 'help':
    case undefined:
    default:
      return cmdHelp();
  }
}

try {
  main();
} catch (e) {
  err(e.message);
  process.exit(1);
}
