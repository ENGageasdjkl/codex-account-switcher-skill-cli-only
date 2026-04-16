from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from common import chinese_aliases


SCRIPT_DIR = Path(__file__).resolve().parent
EXECUTOR = SCRIPT_DIR / "codex_accounts.py"
NATIVE_SWITCH = SCRIPT_DIR / "native_switch.py"
PREFIX = "$codex-account-switcher"
CHINESE_ALIASES = chinese_aliases()


def _strip_prefix(raw: str) -> str:
    text = raw.strip()
    if text.lower().startswith(PREFIX):
        return text[len(PREFIX):].strip()
    return text


def _parse_command_text(raw: str) -> list[str]:
    text = _strip_prefix(raw)
    if not text:
        raise SystemExit("Missing command. Use list, current, add <name>, use <name>, or remove <name>.")

    normalized = CHINESE_ALIASES.get(text)
    if normalized:
        return normalized

    tokens = text.split()
    head = tokens[0].lower()

    if head in {"list", "ls"}:
        return ["list"]
    if head in {"current", "whoami"}:
        return ["current"]
    if head == "add":
        if len(tokens) < 2:
            raise SystemExit("Missing snapshot name for add.")
        return ["add", tokens[1]]
    if head == "use":
        if len(tokens) < 2:
            raise SystemExit("Missing snapshot name for use.")
        return ["use", tokens[1]]
    if head in {"remove", "rm", "delete"}:
        if len(tokens) < 2:
            raise SystemExit("Missing snapshot name for remove.")
        return ["remove", tokens[1]]

    if text.startswith("保存当前账号为"):
        name = text.removeprefix("保存当前账号为").strip()
        if not name:
            raise SystemExit("Missing snapshot name after 保存当前账号为.")
        return ["add", name]
    if text.startswith("保存账号为"):
        name = text.removeprefix("保存账号为").strip()
        if not name:
            raise SystemExit("Missing snapshot name after 保存账号为.")
        return ["add", name]
    if text.startswith("切换到"):
        name = text.removeprefix("切换到").strip()
        if not name:
            raise SystemExit("Missing snapshot name after 切换到.")
        return ["use", name]
    if text.startswith("删除账号"):
        name = text.removeprefix("删除账号").strip()
        if not name:
            raise SystemExit("Missing snapshot name after 删除账号.")
        return ["remove", name]

    raise SystemExit(f"Unsupported codex-account-switcher command: {raw}")


def _select_script(command_args: list[str]) -> tuple[Path, list[str]]:
    if command_args[0] == "use" and os.environ.get("CODEX_ACCOUNT_SWITCHER_SUPERVISED") == "1":
        return NATIVE_SWITCH, command_args[1:]
    return EXECUTOR, command_args


def run_command(command_args: list[str]) -> int:
    script_path, forwarded_args = _select_script(command_args)
    result = subprocess.run(
        [sys.executable, str(script_path), *forwarded_args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"codex-account-switcher failed with exit code {result.returncode}"
        sys.stderr.write(message + ("\n" if not message.endswith("\n") else ""))
    return int(result.returncode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Route codex-account-switcher commands.")
    parser.add_argument("--raw", help="Raw command text, with or without the $codex-account-switcher prefix.")
    parser.add_argument("command", nargs="*", help="Direct command tokens.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.raw:
        command_args = _parse_command_text(args.raw)
    elif args.command:
        command_args = _parse_command_text(" ".join(args.command))
    else:
        raise SystemExit("Missing command. Use --raw or pass command tokens.")
    return run_command(command_args)


if __name__ == "__main__":
    raise SystemExit(main())
