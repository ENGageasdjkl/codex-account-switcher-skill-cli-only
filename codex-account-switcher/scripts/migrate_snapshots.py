from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from common import legacy_repo_snapshot_dir, snapshot_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Migrate legacy project-local account snapshots into the global account-switcher storage.")
    parser.add_argument("--force", action="store_true", help="Overwrite destination files when names already exist.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    source = legacy_repo_snapshot_dir()
    if source is None or not source.exists():
        raise SystemExit("No legacy project-local snapshot directory was found.")

    destination = snapshot_dir()
    destination.mkdir(parents=True, exist_ok=True)

    migrated = 0
    for path in sorted(source.glob("*.json")):
        target = destination / path.name
        if target.exists() and not args.force:
            continue
        shutil.copy2(path, target)
        migrated += 1

    print(f"Migrated {migrated} snapshot(s) from {source} to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
