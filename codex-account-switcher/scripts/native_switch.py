from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from common import request_path, utc_now, write_json_atomic
from codex_accounts import restore_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Native Codex account switch with supervisor relaunch.")
    parser.add_argument("name", help="Saved snapshot name to restore and relaunch into.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if os.environ.get("CODEX_ACCOUNT_SWITCHER_SUPERVISED") != "1":
        raise SystemExit("Native auto-switch is only available inside the supervised Codex CLI launcher.")

    session_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not session_id:
        raise SystemExit("Missing CODEX_THREAD_ID. Cannot capture the exact current session-id.")

    request_path_raw = os.environ.get("CODEX_ACCOUNT_SWITCHER_REQUEST_PATH", "").strip()
    if not request_path_raw:
        raise SystemExit("Missing CODEX_ACCOUNT_SWITCHER_REQUEST_PATH. Supervisor runtime is not available.")
    request_file = Path(request_path_raw) if request_path_raw else request_path()

    restored = restore_snapshot(args.name)
    cwd = str(Path.cwd())
    request_payload = {
        "action": "switch-account",
        "requested_at": utc_now(),
        "target_name": args.name,
        "session_id": session_id,
        "cwd": cwd,
        "restored": restored,
    }
    write_json_atomic(request_file, request_payload)

    print(
        json.dumps(
            {
                **restored,
                "session_id": session_id,
                "cwd": cwd,
                "relaunch": "same-window",
                "mode": "native-supervised",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
