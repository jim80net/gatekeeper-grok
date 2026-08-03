#!/usr/bin/env python3
"""Prove the conformance runner rejects six known-bad instruments."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run-conformance.py"
MANIFEST = ROOT / "fixtures" / "cases.json"
NO_DENY_CONFIG = ROOT / "fixtures" / "config" / "no-push-deny.toml"


STUB = r'''#!/usr/bin/env python3
import json
import os
import sys
import time

payload = json.load(sys.stdin)
command = payload["toolInput"]["command"]
mode = os.environ["STUB_MODE"]

if command == "git push origin main":
    if mode == "wrong_exit":
        print('{"decision":"deny","reason":"Push to protected branch (main/master)"}')
        raise SystemExit(0)
    if mode == "malformed":
        sys.stdout.write('{"decision":')
        raise SystemExit(2)
    if mode == "timeout":
        time.sleep(6)
    print('{"decision":"deny","reason":"Push to protected branch (main/master)"}')
    raise SystemExit(2)

if command == "git status":
    print('{"decision":"allow"}')
    raise SystemExit(0)

if mode == "nonempty_abstain":
    print('{"decision":"abstain"}')
raise SystemExit(1)
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--binary",
        default=os.environ.get("GATEKEEPER_BIN", "claude-gatekeeper"),
        help="real unified binary used for the enforcement-removed control",
    )
    return parser.parse_args()


def run_expected_failure(
    name: str,
    command: list[str],
    expected_fragment: str,
    *,
    env: dict[str, str] | None = None,
) -> bool:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    combined = result.stdout + result.stderr
    if result.returncode == 0:
        print(f"NEGATIVE-CONTROL ERROR {name}: unexpectedly passed", file=sys.stderr)
        return False
    if expected_fragment not in combined:
        print(
            f"NEGATIVE-CONTROL ERROR {name}: failed for wrong reason; "
            f"wanted {expected_fragment!r}\n{combined}",
            file=sys.stderr,
        )
        return False
    matching_line = next(line for line in combined.splitlines() if expected_fragment in line)
    print(f"OBSERVED FAIL {name}: {matching_line}")
    return True


def main() -> int:
    args = parse_args()
    failures = 0
    base = [sys.executable, str(RUNNER), "--manifest", str(MANIFEST)]

    if not run_expected_failure(
        "missing_binary",
        [*base, "--binary", "/definitely/missing/claude-gatekeeper"],
        "binary not found or not executable",
    ):
        failures += 1

    if not run_expected_failure(
        "enforcement_removed",
        [*base, "--binary", args.binary, "--config-override", str(NO_DENY_CONFIG)],
        "expected deny, got abstain",
    ):
        failures += 1

    with tempfile.TemporaryDirectory(prefix="gatekeeper-grok-negative-") as temp:
        stub = Path(temp) / "gatekeeper-stub"
        stub.write_text(textwrap.dedent(STUB), encoding="utf-8")
        stub.chmod(0o755)
        for name, fragment in (
            ("wrong_exit", "right body, wrong exit code"),
            ("malformed", "malformed stdout"),
            ("timeout", "timeout is not clean abstain"),
            ("nonempty_abstain", "abstain emitted non-empty body"),
        ):
            env = os.environ.copy()
            env["STUB_MODE"] = name
            if not run_expected_failure(
                name,
                [*base, "--binary", str(stub)],
                fragment,
                env=env,
            ):
                failures += 1

    if failures:
        print(f"FAIL: {failures} negative control(s) did not fail correctly", file=sys.stderr)
        return 1
    print("PASS: all 6 negative controls failed for the required reason")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
