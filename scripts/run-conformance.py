#!/usr/bin/env python3
"""Run the Grok wire contract against the unified gatekeeper binary."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


BEHAVIOR_CONTRACT = {
    "blocked": (2, "deny"),
    "proceeds_allowed": (0, "allow"),
    "defers_fail_open": (1, None),
}


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--binary",
        default=os.environ.get("GATEKEEPER_BIN", "claude-gatekeeper"),
        help="unified gatekeeper binary (default: GATEKEEPER_BIN or PATH)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "fixtures" / "cases.json",
    )
    parser.add_argument(
        "--config-override",
        type=Path,
        help="test-only: use one config for every case",
    )
    return parser.parse_args()


def resolve_binary(value: str) -> str | None:
    if os.sep in value:
        path = Path(value)
        return str(path.resolve()) if path.is_file() and os.access(path, os.X_OK) else None
    return shutil.which(value)


def decision_from_stdout(stdout: bytes) -> str | None:
    if not stdout:
        return None
    try:
        value = json.loads(stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"malformed stdout: {exc}") from exc
    decision = value.get("decision") if isinstance(value, dict) else None
    return decision if isinstance(decision, str) else None


def main() -> int:
    args = parse_args()
    binary = resolve_binary(args.binary)
    if binary is None:
        return fail(f"binary not found or not executable: {args.binary}")

    manifest_path = args.manifest.resolve()
    fixture_root = manifest_path.parent
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"cannot read manifest: {exc}")
    if manifest.get("schema_version") != 1:
        return fail("manifest schema_version must be 1")
    timeout = manifest.get("hook_timeout_seconds")
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        return fail("hook_timeout_seconds must be positive")

    failures = 0
    for case in manifest.get("cases", []):
        case_id = case.get("id", "<missing-id>")
        try:
            expected_stdout = case["expected_stdout_utf8"].encode("utf-8")
            expected_exit = case["expected_exit_code"]
            behavior = case["expected_harness_behavior"]
            contract_exit, contract_decision = BEHAVIOR_CONTRACT[behavior]
            if expected_exit != contract_exit:
                raise ValueError(
                    f"manifest behavior {behavior} requires exit {contract_exit}, got {expected_exit}"
                )
            expected_decision = decision_from_stdout(expected_stdout)
            if expected_decision != contract_decision:
                raise ValueError(
                    f"manifest behavior {behavior} requires decision {contract_decision!r}, "
                    f"got {expected_decision!r}"
                )
            input_bytes = (fixture_root / case["input"]).read_bytes()
            config_path = (args.config_override or fixture_root / case["config"]).resolve()
            config_bytes = config_path.read_bytes()
        except (KeyError, OSError, TypeError, ValueError) as exc:
            print(f"FAIL {case_id}: invalid case: {exc}", file=sys.stderr)
            failures += 1
            continue

        with tempfile.TemporaryDirectory(prefix="gatekeeper-grok-") as temp:
            temp_path = Path(temp)
            config_dir = temp_path / "xdg" / "gatekeeper"
            config_dir.mkdir(parents=True)
            (config_dir / "gatekeeper.toml").write_bytes(config_bytes)
            env = os.environ.copy()
            env.update({"XDG_CONFIG_HOME": str(temp_path / "xdg"), "HOME": str(temp_path / "home")})
            try:
                result = subprocess.run(
                    [binary, "--harness", "grok"],
                    input=input_bytes,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    timeout=timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                print(
                    f"FAIL {case_id}: timed out after {timeout}s; timeout is not clean abstain",
                    file=sys.stderr,
                )
                failures += 1
                continue

        if result.stdout != expected_stdout:
            if expected_stdout == b"" and result.stdout:
                detail = "abstain emitted non-empty body"
            else:
                try:
                    actual_decision = decision_from_stdout(result.stdout)
                except ValueError as exc:
                    detail = str(exc)
                else:
                    detail = (
                        f"expected {expected_decision or 'abstain'}, "
                        f"got {actual_decision or 'abstain'}"
                    )
            print(
                f"FAIL {case_id}: stdout mismatch ({detail}); "
                f"expected={expected_stdout!r} actual={result.stdout!r}",
                file=sys.stderr,
            )
            failures += 1
            continue
        if result.returncode != expected_exit:
            print(
                f"FAIL {case_id}: right body, wrong exit code: "
                f"expected {expected_exit}, got {result.returncode}",
                file=sys.stderr,
            )
            failures += 1
            continue
        print(f"PASS {case_id}: {behavior} stdout={result.stdout!r} exit={result.returncode}")

    if failures:
        return fail(f"{failures} case(s) failed")
    print(f"PASS: {len(manifest.get('cases', []))} conformance cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
