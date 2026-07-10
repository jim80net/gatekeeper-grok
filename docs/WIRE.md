# Grok PreToolUse wire (gatekeeper-grok)

**Authority:** live probe 2026-07-03 against grok **0.2.82**, re-checked against
the shipping adapter in `gatekeeper-claude/internal/adapter/grok` and a
host canary of `claude-gatekeeper --harness grok` on 2026-07-10.

This document is the product surface for Grok. Implementation today still lives
in the multi-harness binary; do not invent a second wire.

## Registration

Global user hook (preferred — hard enforcer, no per-folder trust):

```
~/.grok/hooks/gatekeeper.json
```

On-disk format is the **Claude-shaped** hooks envelope (verified against grok's
own embedded `~/.grok/hooks/` examples):

```json
{
  "description": "agent-gatekeeper PreToolUse hard enforcer",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/claude-gatekeeper --harness grok",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Project-local `./.grok/hooks/` files require the project to be `/hooks-trust`ed.
Global `~/.grok/hooks/` does not.

Install via:

```bash
claude-gatekeeper setup --harness grok
```

## stdin (harness → gatekeeper)

Fields are **camelCase** (design docs that claimed snake_case were wrong).

| Field | Role |
|-------|------|
| `toolName` | Grok tool id (`Shell` for shell; others pass through or map) |
| `toolInput` | Object; shell command is `toolInput.command` |
| `hookEventName` | Value `"pre_tool_use"` (adapter normalises to canonical `PreToolUse`) |
| `cwd` | Working directory when present |
| `workspaceRoot` | Fallback when `cwd` empty |
| `permissionMode` | e.g. `bypassPermissions` under always-approve |
| `sessionId`, `timestamp`, `transcriptPath`, `toolUseId`, `toolInputTruncated` | Present on live payloads; ignored for matching |

### Live golden (verbatim probe 2026-07-03)

See [`../fixtures/stdin/pre_tool_use_shell_live.json`](../fixtures/stdin/pre_tool_use_shell_live.json).

### Tool name aliases (adapter)

| Grok `toolName` | Canonical tool | Status |
|-----------------|----------------|--------|
| `Shell` | `Bash` | **Live-verified** |
| `run_terminal_cmd` | `Bash` | Defensive alias (design-era) |
| `search_replace` | `Edit` | Design-inferred |
| `read_file` | `Read` | Design-inferred |
| `grep_search` | `Grep` | Design-inferred |
| unmapped | pass-through | — |

### Primary match string keys (per canonical tool)

Tried in order; first present string wins. Empty string is a real value (not a miss).

| Canonical tool | Candidate keys |
|----------------|----------------|
| Bash | `command`, `cmd` |
| Read / Write / Edit | `file_path`, `path`, `target_file` |
| Glob | `pattern`, `glob_pattern`, `path` |
| Grep | `pattern`, `query`, `regex` |
| WebFetch | `url` |
| WebSearch | `query`, `search_term` |

## stdout + exit (gatekeeper → harness)

Grok's blocking-hook contract is **native**, not Claude's `hookSpecificOutput`:

| Verdict | stdout | exit code | Grok behaviour |
|---------|--------|-----------|----------------|
| **Deny** | `{"decision":"deny","reason":"…"}` | **2** | Tool **blocked** (even under full auto) |
| **Allow** | `{"decision":"allow"}` | **0** | Tool proceeds as allowed by hook |
| **Abstain** | *(empty)* | **1** | Fail-open-on-error: **no verdict asserted**; native permission layer decides |

### Why abstain is exit 1 (not silent exit 0)

Grok has no first-class "defer / no opinion" code. A silent exit 0 may be read as
authoritative allow. Routing abstain through the documented **hook-error
fail-open** path (non-zero, non-deny) asserts neither allow nor deny.

**Live probe (2026-07-03):** under `--permission-mode bypassPermissions`,
deny+exit2 blocked a canary file create; abstain exit1 let a control command run.

### Encode goldens

| File | Meaning |
|------|---------|
| [`fixtures/stdout/deny.json`](../fixtures/stdout/deny.json) | Deny body (exit 2) |
| [`fixtures/stdout/allow.json`](../fixtures/stdout/allow.json) | Allow body (exit 0) |
| [`fixtures/stdout/abstain.empty`](../fixtures/stdout/abstain.empty) | Empty body (exit 1) |

### Integration canaries (policy-dependent; 2026-07-10 host)

Against default fleet `gatekeeper.toml` + `claude-gatekeeper --harness grok`:

| Command in `toolInput.command` | Observed |
|--------------------------------|----------|
| `git push origin main` | deny + exit 2 — `Push to protected branch (main/master)` |
| `rm -rf /tmp/foo` | deny + exit 2 — `Destructive: recursive delete (rm -r)` |
| `git status` | allow + exit 0 (default allow rules) |
| `ls` | allow + exit 0 (default allow rules) |

Abstain is rare under a fully populated default rule set; pin it at the adapter
encode layer (fixtures above), not only via integration.

## Interaction with Grok native permissions

1. PreToolUse hooks run **first**, including under `--always-approve` /
   `bypassPermissions` (live-verified).
2. Grok settings-layer `--deny` / allow lists are **not** the same mechanism and
   are **not** enforced under always-approve — do not rely on them for fleet
   desks that run auto-approve.
3. On hook crash / non-deny error exit, grok **fail-opens** to the native layer.

## Source of truth in code

Until Phase-3 packaging extracts the package:

```
gatekeeper-claude/internal/adapter/grok/grok.go
gatekeeper-claude/internal/adapter/grok/grok_test.go
gatekeeper-claude/internal/setup/setup.go  # InstallGrok
```

Any change to those files that alters stdin field names, exit codes, or JSON keys
**must** update this document and the fixtures in the same PR (or a linked
gatekeeper-grok PR).
