# Native CLI Relaunch

This skill supports a high-automation native CLI mode built around a launcher and a supervisor.

Why:

- a child skill command cannot safely replace the currently running Codex TUI process in place
- but a long-lived supervisor can own the current terminal window and restart Codex inside it

Flow:

1. Start Codex through `start_codex_supervised.*`
2. The launcher starts `supervisor.py`
3. The supervisor launches Codex as a child process
4. `use <name>` restores the selected snapshot and writes a switch request
5. The supervisor terminates the current Codex child
6. The supervisor relaunches:

```text
codex resume <exact-session-id> -C <same-cwd>
```

This preserves:

- exact session-id
- current working directory
- same terminal window / same pane
