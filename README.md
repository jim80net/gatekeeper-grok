# gatekeeper-grok

**Grok CLI PreToolUse adapter** for the [Gatekeeper](https://github.com/jim80net/gatekeeper-flotilla)
product family — shared `gatekeeper.toml` policy language, enforced on
[xAI grok](https://x.ai) agents via a global blocking hook.

This repo owns **Grok wire documentation, hook templates, and golden fixtures**.
Policy evaluation lives in [`gatekeeper-core`](https://github.com/jim80net/gatekeeper-core).
The installable multi-harness binary still ships from
[`gatekeeper-claude`](https://github.com/jim80net/gatekeeper-claude) as
`claude-gatekeeper` (binary name lag — see that repo's `COMPAT.md`).

## Status (Phase 3 docs)

| Surface | Location | Notes |
|---------|----------|--------|
| Wire adapter (Go) | `gatekeeper-claude/internal/adapter/grok` | Not yet extracted; evaluated via `--harness grok` |
| Core engine | `gatekeeper-core` | `canonical` / `config` / `engine` |
| Hook install | `claude-gatekeeper setup --harness grok` | Writes `~/.grok/hooks/gatekeeper.json` |
| Hook template | [`hooks/gatekeeper.json.template`](./hooks/gatekeeper.json.template) | Same shape as live fleet |
| Golden fixtures | [`fixtures/`](./fixtures/) | Live-verified 2026-07-03 (grok 0.2.82) + re-canaried 2026-07-10 |

Thin packaging (dedicated binary or pure-docs product) is **deferred** until the
extract plan's evidence gate (release blast radius / mental model / fleet ops).
Default recommendation: keep one multi-harness binary; this repo remains the
Grok-specific product surface (docs + templates + fixtures).

## Install (fleet / operator)

```bash
# 1. Install the multi-harness binary (from gatekeeper-claude releases or make build)
# Binary path on this fleet host: ~/go/bin/claude-gatekeeper

# 2. Register the global Grok PreToolUse hook
claude-gatekeeper setup --harness grok
# → writes ~/.grok/hooks/gatekeeper.json
# → Global user hooks need no per-folder /hooks-trust
```

Manual install: copy [`hooks/gatekeeper.json.template`](./hooks/gatekeeper.json.template),
replace `{{GATEKEEPER_BIN}}` with the absolute path to `claude-gatekeeper`, and
write it to `~/.grok/hooks/gatekeeper.json`.

Policy: same layered `gatekeeper.toml` as every other harness
(typically `~/.claude/gatekeeper.toml` plus project overlays).

## Wire summary (live-verified)

Full detail: [`docs/WIRE.md`](./docs/WIRE.md).

| Direction | Shape |
|-----------|--------|
| **stdin** | camelCase envelope: `toolName`, `toolInput`, `hookEventName`=`pre_tool_use`, `cwd`/`workspaceRoot`, `permissionMode` |
| **Shell tool name** | `"Shell"` (not `run_terminal_cmd`; that alias is kept defensively) |
| **deny** | stdout `{"decision":"deny","reason":"…"}` + **exit 2** |
| **allow** | stdout `{"decision":"allow"}` + **exit 0** |
| **abstain** | **no stdout** + **exit 1** (grok fail-open-on-error; no verdict asserted) |

Grok evaluates PreToolUse hooks **before** its permission system, including under
`--always-approve` / `bypassPermissions`. Settings-layer `--deny` is a *different*
mechanism and is **not** enforced under always-approve — the hook is.

## Quick canary

```bash
# Expect deny + exit 2 (default protected-branch rule)
printf '%s' '{"hookEventName":"pre_tool_use","toolName":"Shell","toolInput":{"command":"git push origin main"},"cwd":"/tmp","workspaceRoot":"/tmp","permissionMode":"bypassPermissions"}' \
  | claude-gatekeeper --harness grok
echo "exit=$?"
```

More fixtures: [`fixtures/`](./fixtures/).

## Product family

```
gatekeeper-core      shared engine + policy schema
gatekeeper-claude    Claude adapter + current all-in-one binary
gatekeeper-grok      this repo (Grok wire docs / hooks / fixtures)
gatekeeper-codex     Codex wire docs / hooks / fixtures
```

Coordination: private [`gatekeeper-flotilla`](https://github.com/jim80net/gatekeeper-flotilla).

## Namespace

Repos under **`jim80net` only** (operator standing rule).

## License

MIT — same as the rest of the Gatekeeper family.
