from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
KNOWN_SUBCOMMANDS = {"exec", "resume", "login", "logout", "cloud-tasks", "proto"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def codex_home() -> Path:
    raw = os.environ.get("CODEX_HOME", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".codex"


def auth_path() -> Path:
    return codex_home() / "auth.json"


def account_switcher_root() -> Path:
    override = os.environ.get("CODEX_ACCOUNT_SWITCHER_ROOT", "").strip()
    if override:
        return Path(override).expanduser()
    return codex_home() / "account-switcher"


def snapshot_dir() -> Path:
    return account_switcher_root() / "snapshots"


def runtime_dir() -> Path:
    return account_switcher_root() / "runtime"


def state_path() -> Path:
    return runtime_dir() / "supervisor-state.json"


def request_path() -> Path:
    return runtime_dir() / "switch-request.json"


def installed_skill_dir() -> Path:
    return codex_home() / "skills" / "codex-account-switcher"


def legacy_repo_snapshot_dir() -> Path | None:
    current_root = skill_root()
    candidates = [
        current_root.parents[2],
        Path.cwd(),
    ]
    for candidate in candidates:
        marker = candidate / ".codex" / "account-switcher"
        if marker.exists():
            return marker
    return None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=str(path.parent)) as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        temp_name = handle.name
    Path(temp_name).replace(path)


def ensure_valid_name(name: str) -> None:
    if not NAME_RE.fullmatch(name):
        raise SystemExit("Invalid name. Use only letters, numbers, dot, underscore, and hyphen.")


def resolve_codex_command(raw: str | None) -> str:
    candidates = [raw, "codex.cmd", "codex"]
    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        path = Path(candidate)
        if path.exists():
            return str(path)
    raise SystemExit("Could not resolve codex executable. Pass --codex-command explicitly.")


def validate_forwarded_args(args: list[str]) -> None:
    for token in args:
        if not token:
            continue
        if token == "--":
            continue
        if token.startswith("-"):
            continue
        if token in KNOWN_SUBCOMMANDS:
            raise SystemExit("The supervised launcher only supports interactive Codex sessions, not subcommands.")
        raise SystemExit("The supervised launcher only supports Codex global flags. Prompts/subcommands are not supported.")


def strip_cd_args(args: list[str]) -> list[str]:
    cleaned: list[str] = []
    skip_next = False
    for token in args:
        if skip_next:
            skip_next = False
            continue
        if token in {"-C", "--cd"}:
            skip_next = True
            continue
        if token.startswith("--cd="):
            continue
        cleaned.append(token)
    return cleaned


def chinese_aliases() -> dict[str, list[str]]:
    return {
        "列出账号": ["list"],
        "列出已保存账号": ["list"],
        "显示当前账号": ["current"],
        "当前账号": ["current"],
    }
