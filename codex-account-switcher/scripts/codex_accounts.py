from __future__ import annotations

import argparse
import base64
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import auth_path, ensure_valid_name, load_json, snapshot_dir, utc_now, write_json


AUTH_PATH = auth_path()
SNAPSHOT_DIR = snapshot_dir()


def decode_jwt_payload(token: str | None) -> dict[str, Any]:
    if not token or token.count(".") < 2:
        return {}
    try:
        payload_part = token.split(".")[1]
        padding = "=" * (-len(payload_part) % 4)
        decoded = base64.urlsafe_b64decode(payload_part + padding)
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}


def summarize_auth(auth: dict[str, Any]) -> dict[str, Any]:
    tokens = auth.get("tokens", {}) if isinstance(auth.get("tokens"), dict) else {}
    id_payload = decode_jwt_payload(tokens.get("id_token"))
    access_payload = decode_jwt_payload(tokens.get("access_token"))
    api_auth = id_payload.get("https://api.openai.com/auth", {})
    profile = access_payload.get("https://api.openai.com/profile", {})

    return {
        "auth_mode": auth.get("auth_mode", "(unknown)"),
        "email": id_payload.get("email") or profile.get("email") or "(unknown)",
        "name": id_payload.get("name") or "(unknown)",
        "account_id": tokens.get("account_id") or api_auth.get("chatgpt_account_id") or "(unknown)",
        "plan": api_auth.get("chatgpt_plan_type") or "(unknown)",
        "subscription_until": api_auth.get("chatgpt_subscription_active_until") or "(unknown)",
        "last_refresh": auth.get("last_refresh", "(unknown)"),
    }


def ensure_auth_exists() -> None:
    if not AUTH_PATH.exists():
        raise SystemExit(f"Missing live auth file: {AUTH_PATH}")


def snapshot_path(name: str) -> Path:
    return SNAPSHOT_DIR / f"{name}.json"


def backup_live_auth() -> Path:
    ensure_auth_exists()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = SNAPSHOT_DIR / f"_backup_{timestamp}.json"
    shutil.copy2(AUTH_PATH, backup_path)
    return backup_path


def snapshot_payload(name: str) -> dict[str, Any]:
    ensure_valid_name(name)
    path = snapshot_path(name)
    if not path.exists():
        raise SystemExit(f"Snapshot not found: {path}")
    payload = load_json(path)
    auth = payload.get("auth")
    if not isinstance(auth, dict):
        raise SystemExit(f"Invalid snapshot format: {path}")
    return payload


def list_snapshots() -> list[dict[str, Any]]:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for path in sorted(SNAPSHOT_DIR.glob("*.json")):
        if path.name.startswith("_backup_"):
            continue
        payload = load_json(path)
        summary = payload.get("summary", {})
        rows.append(
            {
                "name": payload.get("name", path.stem),
                "saved_at": payload.get("saved_at", "(unknown)"),
                "email": summary.get("email", "(unknown)"),
                "plan": summary.get("plan", "(unknown)"),
                "account_id": summary.get("account_id", "(unknown)"),
            }
        )
    return rows


def add_snapshot(name: str, force: bool = False) -> Path:
    ensure_auth_exists()
    ensure_valid_name(name)
    target = snapshot_path(name)
    if target.exists() and not force:
        raise SystemExit(f"Snapshot already exists: {target}. Use --force to overwrite.")

    auth = load_json(AUTH_PATH)
    payload = {
        "name": name,
        "saved_at": utc_now(),
        "summary": summarize_auth(auth),
        "auth": auth,
    }
    write_json(target, payload)
    return target


def restore_snapshot(name: str) -> dict[str, Any]:
    ensure_auth_exists()
    payload = snapshot_payload(name)
    auth = payload["auth"]
    backup = backup_live_auth()
    write_json(AUTH_PATH, auth)
    summary = payload.get("summary", {})
    return {
        "restored": name,
        "backup": str(backup),
        "email": summary.get("email", "(unknown)"),
        "plan": summary.get("plan", "(unknown)"),
        "account_id": summary.get("account_id", "(unknown)"),
    }


def command_current(_args: argparse.Namespace) -> int:
    ensure_auth_exists()
    auth = load_json(AUTH_PATH)
    print(json.dumps(summarize_auth(auth), ensure_ascii=False, indent=2))
    return 0


def command_list(_args: argparse.Namespace) -> int:
    print(json.dumps(list_snapshots(), ensure_ascii=False, indent=2))
    return 0


def command_add(args: argparse.Namespace) -> int:
    target = add_snapshot(args.name, force=args.force)
    print(f"Saved snapshot: {target}")
    return 0


def command_use(args: argparse.Namespace) -> int:
    print(json.dumps(restore_snapshot(args.name), ensure_ascii=False, indent=2))
    return 0


def command_remove(args: argparse.Namespace) -> int:
    ensure_valid_name(args.name)
    target = snapshot_path(args.name)
    if not target.exists():
        raise SystemExit(f"Snapshot not found: {target}")
    target.unlink()
    print(f"Removed snapshot: {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage local Codex account snapshots.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    current_parser = subparsers.add_parser("current", help="Show the current live Codex account summary.")
    current_parser.set_defaults(func=command_current)

    list_parser = subparsers.add_parser("list", help="List saved Codex account snapshots.")
    list_parser.set_defaults(func=command_list)

    add_parser = subparsers.add_parser("add", help="Save the current live auth.json as a named snapshot.")
    add_parser.add_argument("name")
    add_parser.add_argument("--force", action="store_true", help="Overwrite an existing snapshot.")
    add_parser.set_defaults(func=command_add)

    use_parser = subparsers.add_parser("use", help="Restore a named snapshot into the live auth.json.")
    use_parser.add_argument("name")
    use_parser.set_defaults(func=command_use)

    remove_parser = subparsers.add_parser("remove", help="Delete a saved snapshot.")
    remove_parser.add_argument("name")
    remove_parser.set_defaults(func=command_remove)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
