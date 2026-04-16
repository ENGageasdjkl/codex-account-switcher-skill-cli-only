from __future__ import annotations

import argparse
import os
import subprocess
import time
from typing import Any

from common import (
    request_path,
    resolve_codex_command,
    runtime_dir,
    state_path,
    strip_cd_args,
    utc_now,
    validate_forwarded_args,
    write_json_atomic,
    load_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Keep Codex running in one console window and relaunch on account switch.")
    parser.add_argument("--cwd", help="Initial working directory for the supervised Codex session.")
    parser.add_argument("--codex-command", help="Explicit path to codex/codex.cmd.")
    return parser


class CodexSupervisor:
    def __init__(self, codex_command: str, initial_cwd: str, launch_args: list[str]) -> None:
        self.codex_command = codex_command
        self.initial_cwd = initial_cwd
        self.launch_args = strip_cd_args([arg for arg in launch_args if arg != "--"])
        self.child: subprocess.Popen[str] | None = None
        self.pending_request: dict[str, Any] | None = None

    def child_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["CODEX_ACCOUNT_SWITCHER_SUPERVISED"] = "1"
        env["CODEX_ACCOUNT_SWITCHER_RUNTIME_DIR"] = str(runtime_dir())
        env["CODEX_ACCOUNT_SWITCHER_REQUEST_PATH"] = str(request_path())
        env["CODEX_ACCOUNT_SWITCHER_SUPERVISOR_PID"] = str(os.getpid())
        return env

    def launch_initial(self) -> subprocess.Popen[str]:
        return self._launch([self.codex_command, *self.launch_args], self.initial_cwd, mode="initial")

    def launch_resume(self, request: dict[str, Any]) -> subprocess.Popen[str]:
        cwd = str(request["cwd"])
        session_id = str(request["session_id"])
        command = [self.codex_command, *self.launch_args, "resume", session_id, "-C", cwd]
        return self._launch(command, cwd, mode="resume", request=request)

    def _launch(
        self,
        command: list[str],
        cwd: str,
        *,
        mode: str,
        request: dict[str, Any] | None = None,
    ) -> subprocess.Popen[str]:
        process = subprocess.Popen(command, cwd=cwd, env=self.child_env())
        self._write_state(process, cwd, mode=mode, request=request)
        return process

    def _write_state(
        self,
        process: subprocess.Popen[str],
        cwd: str,
        *,
        mode: str,
        request: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "updated_at": utc_now(),
            "supervisor_pid": os.getpid(),
            "child_pid": process.pid,
            "cwd": cwd,
            "mode": mode,
            "codex_command": self.codex_command,
            "launch_args": self.launch_args,
            "request_path": str(request_path()),
        }
        if request:
            payload["active_request"] = {
                "target_name": request.get("target_name"),
                "session_id": request.get("session_id"),
                "cwd": request.get("cwd"),
                "requested_at": request.get("requested_at"),
            }
        write_json_atomic(state_path(), payload)

    def _read_request(self) -> dict[str, Any] | None:
        current_request_path = request_path()
        if not current_request_path.exists():
            return None
        payload = load_json(current_request_path)
        current_request_path.unlink(missing_ok=True)
        if payload.get("action") != "switch-account":
            return None
        return payload

    def _terminate_child(self) -> None:
        if self.child is None:
            return
        if self.child.poll() is not None:
            return
        self.child.terminate()
        try:
            self.child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.child.kill()
            self.child.wait(timeout=5)

    def run(self) -> int:
        runtime_dir().mkdir(parents=True, exist_ok=True)
        self.child = self.launch_initial()
        try:
            while True:
                request = self._read_request()
                if request:
                    self.pending_request = request
                    self._terminate_child()

                if self.child is None:
                    return 0

                exit_code = self.child.poll()
                if exit_code is None:
                    time.sleep(0.2)
                    continue

                if self.pending_request:
                    request = self.pending_request
                    self.pending_request = None
                    self.child = self.launch_resume(request)
                    continue

                return int(exit_code)
        except KeyboardInterrupt:
            self._terminate_child()
            return 130


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, launch_args = parser.parse_known_args(argv)
    validate_forwarded_args(launch_args)

    codex_command = resolve_codex_command(args.codex_command)
    initial_cwd = args.cwd or os.getcwd()
    supervisor = CodexSupervisor(codex_command, initial_cwd, launch_args)
    return supervisor.run()


if __name__ == "__main__":
    raise SystemExit(main())
