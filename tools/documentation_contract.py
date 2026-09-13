#!/usr/bin/env python3
"""Fail when current-facing release evidence drifts behind implementation."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "handoff" / "CURRENT_EVIDENCE.json"
CURRENT_DOCS = [
    ROOT / "docs" / "handoff" / "VERIFICATION.md",
    ROOT / "docs" / "FINAL_AUDIT.md",
    ROOT / "docs" / "QA_MATRIX.md",
    ROOT / "docs" / "handoff" / "HANDOFF.md",
    ROOT / "docs" / "SESSION_STATUS.md",
    ROOT / "docs" / "handoff" / "LOCAL_AGENT_PROMPT.md",
]
EXPECTED_WORKFLOWS = {
    "Build and verify",
    "Load acceptance",
    "Transaction security regression",
    "Transaction integrity on Windows and Linux",
    "Compile Windows client source",
    "Live progression breadth",
    "Graphical multiplayer acceptance",
    "Windows package acceptance",
}
STALE_MARKERS = (
    "Current status as of 2026-09-11",
    "Current consolidated status as of 2026-09-11",
    "4/8/16-client",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def latest_implementation_commit() -> str:
    command = [
        "git", "log", "-1", "--format=%H", "HEAD", "--", ".",
        ":(exclude)docs/**",
        ":(exclude)tools/documentation_contract.py",
        ":(exclude).github/workflows/documentation-contract.yml",
    ]
    result = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    value = result.stdout.strip()
    if len(value) != 40:
        fail("Could not resolve the latest non-documentation implementation commit. Use a full-history checkout.")
    return value


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("schema") != 1:
        fail("CURRENT_EVIDENCE.json schema must be 1.")
    baseline = evidence.get("implementationBaseline", "")
    actual = latest_implementation_commit()
    if baseline != actual:
        fail(f"Current evidence is stale: ledger baseline {baseline!r}, latest implementation {actual!r}.")
    if evidence.get("referenceLoadClients") != [2, 10, 25, 50]:
        fail("Reference load evidence must match the retained 2/10/25/50-client acceptance gate.")
    if evidence.get("connectionAdmissionPerMinutePerSource") != 120:
        fail("Current evidence lost the verified 120/minute per-source play-admission boundary.")
    workflows = evidence.get("workflows", [])
    names = {item.get("name") for item in workflows}
    if names != EXPECTED_WORKFLOWS:
        fail(f"Current evidence workflow set drifted: {sorted(names)}")
    if len({item.get("runId") for item in workflows}) != len(workflows):
        fail("Current evidence contains duplicate workflow run IDs.")
    if any(item.get("conclusion") != "success" for item in workflows):
        fail("Only successful exact-baseline workflow evidence may be recorded as accepted.")
    release_status = evidence.get("releaseStatus", "")
    if release_status != "NOT APPROVED — human acceptance remains.":
        fail("The machine-readable release status must preserve the human-acceptance boundary.")

    for path in CURRENT_DOCS:
        text = path.read_text(encoding="utf-8")
        if evidence["statusDate"] not in text:
            fail(f"{path.relative_to(ROOT)} does not carry the current evidence date.")
        if baseline not in text:
            fail(f"{path.relative_to(ROOT)} does not carry the current implementation baseline.")
        if "CURRENT_EVIDENCE.json" not in text:
            fail(f"{path.relative_to(ROOT)} does not identify the machine-readable evidence ledger.")
        if release_status not in text:
            fail(f"{path.relative_to(ROOT)} changed or omitted the release-status boundary.")
        for marker in STALE_MARKERS:
            if marker in text:
                fail(f"{path.relative_to(ROOT)} contains stale current-status marker: {marker}")

    verification = CURRENT_DOCS[0].read_text(encoding="utf-8")
    for item in workflows:
        if str(item["runId"]) not in verification:
            fail(f"VERIFICATION.md is missing exact-baseline run {item['runId']} ({item['name']}).")

    print(f"DOCUMENTATION_CONTRACT: baseline={baseline}; current_docs={len(CURRENT_DOCS)}; workflows={len(workflows)}; release=human-acceptance-pending")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"DOCUMENTATION_CONTRACT_FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
