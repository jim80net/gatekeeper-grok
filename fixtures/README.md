# Golden fixtures — Grok wire

Pinned shapes for the Grok PreToolUse adapter. Prefer these over re-deriving
field names from memory.

## stdin/

| File | Provenance |
|------|------------|
| `pre_tool_use_shell_live.json` | Verbatim live grok 0.2.82 PreToolUse payload (probe 2026-07-03). Shell tool, camelCase envelope. |
| `pre_tool_use_shell_minimal.json` | Minimal valid envelope for local canaries. |

## stdout/

Adapter **encode** goldens (policy-independent):

| File | Decision | Exit code |
|------|----------|-----------|
| `deny.json` | deny | 2 |
| `allow.json` | allow | 0 |
| `abstain.empty` | abstain (fail-open) | 1 — **file is empty** |

## Re-canary

```bash
BIN="${BIN:-$HOME/go/bin/claude-gatekeeper}"

# Integration (policy-dependent)
"$BIN" --harness grok < stdin/pre_tool_use_shell_minimal.json
echo "exit=$?"

# Adapter unit tests live in gatekeeper-claude until extract:
#   go test ./internal/adapter/grok/ -count=1
```
