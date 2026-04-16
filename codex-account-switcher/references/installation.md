# Installation

This skill is intended to be installed as a standard Codex skill.

Preferred user-facing install model:

- install the skill into `CODEX_HOME/skills/codex-account-switcher`
- or into `~/.codex/skills/codex-account-switcher` when `CODEX_HOME` is unset

Once it is installed there, it is already globally available after restarting Codex.

No extra post-install configuration is required for discovery.

## Standard User Paths

1. Install through the standard Codex skill installer from a repo/path
2. Or manually place the skill folder into the global skills directory

Both result in the same final state: the skill is globally installed.

## Development-Only Helper

`scripts/install_global.py` is not the primary user-facing install path.

It exists only for development scenarios where:

- the skill is being edited inside another repository
- the developer wants to copy the current local source tree into `CODEX_HOME/skills`

## Migration

Older project-local snapshots can be migrated into the global storage with:

```text
python .\scripts\migrate_snapshots.py
```
