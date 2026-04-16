# Session Recovery

In native supervised mode, this skill treats `CODEX_THREAD_ID` as the exact resumable interactive session identifier.

Recovery semantics:

- `same session` means the exact current session UUID
- `same cwd` means the current process working directory at the moment of switching
- `same console window` means the same terminal window or pane, with a new Codex child process launched by the supervisor

Failure rule:

- if `CODEX_THREAD_ID` is missing, native `use <name>` must fail before writing the live auth file

Resume command:

```text
codex resume <exact-session-id> -C <same-cwd>
```

The resumed process is a new Codex child process, not the same OS process.
