# ADR-0008 — Least-privilege host-action hook

**Status:** Accepted  **Date:** 2026-06-25  **Milestone:** M21

## Context

DESIGN 8.4 wants host operations from the portal: a log viewer, receiver
reconnect, reboot/shutdown, and (DESIGN 15) apply/rollback of updates. The web
process runs **unprivileged** (the `callisto` user) and must never execute
arbitrary commands — running `reboot` or `apt` from a web handler is a remote-code
hazard.

## Decision

A single **configured hook command** (`host_hook` setting, empty = disabled).
Host actions shell out to exactly `<host_hook> <action> [args]` with a **fixed,
closed set of action verbs**: `reconnect`, `reboot`, `shutdown`, `update`,
`rollback`. The web process never builds a shell string from user input — only
the verb + validated args reach the hook.

The hook script is installed by packaging and granted only the specific
privileges it needs (e.g. a `sudoers` line for `ecallisto-hook reboot`). The web
app stays unprivileged; privilege lives in the audited hook.

Read-only **log viewing** does *not* use the hook: it tails a configured
`log_file` directly (read-only), avoiding any privileged call for the common case.

Every host action is recorded to the **audit log** (ADR-0006) with the actor.

## Consequences

- No arbitrary command execution from the web process; the attack surface is the
  closed verb set + the hook's own privileges.
- Host actions are disabled by default (no `host_hook` configured) and return a
  clear "not configured" result — safe out of the box.
- Tests point `host_hook` at a fake script and assert the verb/args + the audit
  entry, with no real host effect.
