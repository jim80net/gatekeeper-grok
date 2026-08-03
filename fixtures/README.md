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

## Executable verdict contract

`cases.json` is the single machine-readable truth for each case's input,
deterministic policy, exact stdout bytes, exit code, and expected Grok behavior.
Run it against the unified binary:

```bash
./scripts/verify-fixtures.sh

GATEKEEPER_BIN="${GATEKEEPER_BIN:-$HOME/go/bin/claude-gatekeeper}"
./scripts/run-conformance.py --binary "$GATEKEEPER_BIN"
```

The command exits non-zero on a missing binary, timeout, malformed output, byte
mismatch, exit-code mismatch, or behavior mismatch. Merely printing an exit code
is not conformance evidence.

## Negative controls

The sensitivity suite plants the six failure modes required by the 2026-08-03
audit remediation. Five use a deliberately broken local stub; the
enforcement-removed case runs the real unified binary against
`config/no-push-deny.toml`.

```bash
./tests/negative_controls.py --binary "$GATEKEEPER_BIN"
```

This test succeeds only after it observes all six bad instruments fail for their
specified reason. The stubs test runner sensitivity; the positive contract above
is always judged against the real unified binary.
