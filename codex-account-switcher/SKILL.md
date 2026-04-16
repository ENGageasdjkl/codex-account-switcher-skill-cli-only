---
name: codex-account-switcher
description: Save, inspect, and switch multiple local Codex accounts by snapshotting and restoring CODEX_HOME/auth.json. Use when the user wants to list saved Codex accounts, show the current account, save the current login under a name, restore another saved account, or trigger exact-session account switching in the native supervised Codex CLI. Trigger on requests like "save current Codex account as work", "switch Codex to personal", "list saved Codex accounts", "show current Codex account", or explicit calls such as "$codex-account-switcher ...".
---

# Codex Account Switcher

Manage multiple local Codex logins without third-party tooling.

This skill is designed to work as a **standard installable Codex skill**. When it is installed into:

- `CODEX_HOME/skills/codex-account-switcher`
- or `~/.codex/skills/codex-account-switcher` when `CODEX_HOME` is unset

it is already globally available. No extra post-install configuration is required.

## Storage Model

The live Codex auth file is always:

- `CODEX_HOME/auth.json`
- or `~/.codex/auth.json` when `CODEX_HOME` is unset

Skill-managed data lives under:

- `CODEX_HOME/account-switcher/snapshots/`
- `CODEX_HOME/account-switcher/runtime/`

This makes the skill portable across repositories and users.

Read these references as needed:

- `references/installation.md`
- `references/native-cli-relaunch.md`
- `references/session-recovery.md`

## Structure

- `SKILL.md` - behavior contract
- `agents/openai.yaml` - UI metadata
- `references/` - installation, relaunch, and session semantics
- `scripts/codex_accounts.py` - low-level snapshot manager
- `scripts/router.py` - explicit command router
- `scripts/native_switch.py` - native CLI account switch request
- `scripts/supervisor.py` - same-window Codex supervisor
- `scripts/migrate_snapshots.py` - migrate legacy project-local snapshots
- `scripts/install_global.py` - development helper for copying this local source tree into `CODEX_HOME/skills`
- `assets/start_codex_supervised.*` - launcher templates

## When To Use

Use this skill when the user wants to:

- save the current Codex login under a name
- list saved account snapshots
- inspect the current live Codex account
- switch back to a previously saved account
- remove an old saved snapshot

Examples:

- `保存当前 Codex 账号为 work`
- `列出已保存的 Codex 账号`
- `显示当前 Codex 登录账号`
- `切换到 personal`
- `$codex-account-switcher list`
- `$codex-account-switcher use work`

## Standard Installation

Preferred installation path:

- install this skill through the standard Codex skill installer
- or place the skill folder directly into `CODEX_HOME/skills`

Once installed there, the skill is globally available after restarting Codex.

`scripts/install_global.py` exists only as a development convenience when this skill is being edited inside another repository and needs to be copied into the global skills directory.

## Core Commands

Supported commands:

- `current`
- `list`
- `add <name>`
- `use <name>`
- `remove <name>`

These commands can be invoked through the router:

```powershell
python .\scripts\router.py --raw "$codex-account-switcher list"
```

## Built-In Direct Command Behavior

When the host entrypoint supports explicit skill passthrough, these commands should execute directly through `router.py` instead of going through Codex reasoning:

- `$codex-account-switcher list`
- `$codex-account-switcher current`
- `$codex-account-switcher add <name>`
- `$codex-account-switcher remove <name>`

The router also normalizes these Chinese forms:

- `列出账号`
- `列出已保存账号`
- `显示当前账号`
- `当前账号`
- `保存当前账号为 <name>`
- `保存账号为 <name>`
- `切换到 <name>`
- `删除账号 <name>`

## Execution Modes

### 1. Standard mode

Default behavior:

- `list/current/add/remove` run locally and return structured results
- `use <name>` restores the target snapshot into the live auth file
- no process restart is attempted

This mode is safe for host integrations such as Web adapters.

### 2. Native supervised CLI mode

This mode is for the native Codex CLI only.

Start Codex through a launcher from `assets/start_codex_supervised.*`. The launcher starts `supervisor.py`, which owns the current terminal window and runs Codex as a child process.

In this mode, `use <name>` does all of the following:

- captures the exact current `CODEX_THREAD_ID`
- captures the current `cwd`
- backs up the live auth file
- restores the selected snapshot
- asks the supervisor to terminate the current Codex child process
- relaunches Codex in the same terminal window with:

```text
codex resume <exact-session-id> -C <same-cwd>
```

This is the high-automation path.

## Migration

If older project-local snapshots exist, they can be migrated into the global storage with:

```powershell
python .\scripts\migrate_snapshots.py
```

## Reporting Rules

When reporting command results, summarize:

- snapshot name
- email
- plan
- backup path if a restore happened

Never print token fields.

For native supervised switching, also report:

- `session_id`
- `cwd`
- `relaunch: same-window`

## Safety Rules

- Require `--force` before overwriting an existing snapshot
- Always back up the live auth file before a restore
- If `CODEX_THREAD_ID` is missing in native supervised mode, fail and do not modify live auth
- Treat snapshot files as secrets
- Do not expose tokens in normal output
