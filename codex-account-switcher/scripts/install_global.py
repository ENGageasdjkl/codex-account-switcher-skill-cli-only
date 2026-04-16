from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from common import installed_skill_dir, skill_root


EXCLUDE_NAMES = {"__pycache__", ".git", ".DS_Store"}


def copy_tree(src: Path, dst: Path) -> None:
    for item in src.iterdir():
        if item.name in EXCLUDE_NAMES:
            continue
        target = dst / item.name
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            copy_tree(item, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install the codex-account-switcher skill into CODEX_HOME/skills.")
    parser.add_argument("--force", action="store_true", help="Replace an existing installed skill directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    src = skill_root()
    dst = installed_skill_dir()
    if dst.exists():
        if not args.force:
            raise SystemExit(f"Target already exists: {dst}. Use --force to replace it.")
        shutil.rmtree(dst)

    dst.mkdir(parents=True, exist_ok=True)
    copy_tree(src, dst)
    print(dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
