# Golden fixtures — Grok wire

Pinned shapes for the Grok PreToolUse adapter. Prefer these over re-deriving
field names from memory.

## stdin/

| File | Provenance |
|------|------------|
| `pre_tool_use_shell_live.json` | Verbatim live grok 0.2.82 PreToolUse payload (probe 2026-07-03). Shell tool, camelCase envelope. |
| `pre_tool_use_shell_minimal.json` | Minimal valid envelope for local canaries. |
| `pre_tool_use_run_terminal_command.json` | Grok 0.2.101 shipped hook guide + captured `BashToolInput` schema (`command`). |
| `pre_tool_use_read_file.json` | Captured Grok 0.2.101 `ReadFileInput` schema (`target_file`). |
| `pre_tool_use_search_replace.json` | Captured Grok 0.2.101 `SearchReplaceInput` schema (`file_path`). |
| `pre_tool_use_write.json` | Captured Grok 0.2.101 `WriteInput` schema (`file_path`). |
| `pre_tool_use_list_dir.json` | Captured Grok 0.2.101 `ListDirInput` schema (`target_directory`). |
| `pre_tool_use_grep.json` | Captured Grok 0.2.101 `GrepSearchInput` schema (`pattern`). |
| `pre_tool_use_web_fetch.json` | Captured Grok 0.2.101 `WebFetchInput` schema (`url`). |

These are static-source fixtures, not new live probes. Grok's shipped hook guide
states that `toolName` is the real native tool name. WebSearch has no input
fixture: its native name is documented, but its primary input key remains
unverified without a live hook capture.

## stdout/

Adapter **encode** goldens (policy-independent):

| File | Decision | Exit code |
|------|----------|-----------|
| `deny.json` | deny | 2 |
| `allow.json` | allow | 0 |
| `abstain.empty` | abstain (fail-open) | 1 — **file is empty** |

## Re-canary

```bash
./scripts/verify-fixtures.sh

BIN="${BIN:-$HOME/go/bin/claude-gatekeeper}"

# Integration (policy-dependent)
"$BIN" --harness grok < stdin/pre_tool_use_shell_minimal.json
echo "exit=$?"

# Adapter unit tests live in gatekeeper-claude until extract:
#   go test ./internal/adapter/grok/ -count=1
```
