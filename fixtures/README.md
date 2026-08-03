# Golden fixtures — Grok wire

Pinned shapes for the Grok PreToolUse adapter. Prefer these over re-deriving
field names from memory.

## stdin/

| File | Provenance |
|------|------------|
| `pre_tool_use_shell_live.json` | Verbatim live grok 0.2.82 PreToolUse payload (probe 2026-07-03). Shell tool, camelCase envelope. |
| `pre_tool_use_shell_minimal.json` | Minimal valid envelope for local canaries. |

## Executable verdict contract

`cases.json` is the single machine-readable truth for each case's input,
deterministic policy, exact stdout bytes, exit code, and expected Grok behavior.
Run it against the unified binary:

```bash
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
