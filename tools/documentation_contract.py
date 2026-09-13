#!/usr/bin/env python3
"""Fail when current-facing release evidence drifts behind implementation."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "handoff" / "CURRENT_EVIDENCE.json"
RELEASE_CANDIDATE = ROOT / "src" / "release-candidate.trigger"
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
EXPECTED_TASK12_WORKFLOWS = {
    "Windows display and input acceptance",
    "Visual acceptance matrix",
    "Audio acceptance",
}
EXPECTED_TASK13_WORKFLOWS = {"Task 13 adversarial acceptance", "Build and verify"}
EXPECTED_TASK14_WORKFLOWS = EXPECTED_WORKFLOWS | EXPECTED_TASK12_WORKFLOWS | {"Task 13 adversarial acceptance"}
STALE_MARKERS = (
    "Current status as of 2026-09-11",
    "Current consolidated status as of 2026-09-11",
    "4/8/16-client",
    "Task 14 was not started",
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


def validate_run_set(label: str, items: list[dict], expected: set[str], baseline: str) -> None:
    names = {item.get("name") for item in items}
    if names != expected:
        fail(f"{label} workflow set drifted: {sorted(names)}")
    run_ids = [item.get("runId") for item in items]
    if len(set(run_ids)) != len(run_ids):
        fail(f"{label} contains duplicate workflow run IDs.")
    if any(item.get("conclusion") != "success" for item in items):
        fail(f"{label} may contain only successful workflow evidence.")
    if any(item.get("headSha") != baseline for item in items):
        fail(f"{label} must point every workflow at implementation baseline {baseline}.")


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("schema") != 1:
        fail("CURRENT_EVIDENCE.json schema must be 1.")
    baseline = evidence.get("implementationBaseline", "")
    actual = latest_implementation_commit()
    if baseline != actual:
        fail(f"Current evidence is stale: ledger baseline {baseline!r}, latest implementation {actual!r}.")
    if evidence.get("releaseCandidateBaseline") != baseline:
        fail("Task 14 release-candidate baseline must equal the implementation baseline.")
    if evidence.get("releaseCandidateTrigger") != "src/release-candidate.trigger":
        fail("Task 14 release-candidate trigger path drifted.")
    if evidence.get("releaseCandidateWorkflowCount") != len(EXPECTED_TASK14_WORKFLOWS):
        fail("Task 14 release-candidate workflow count drifted.")
    if evidence.get("referenceLoadClients") != [2, 10, 25, 50]:
        fail("Reference load evidence must match the retained 2/10/25/50-client acceptance gate.")
    if evidence.get("connectionAdmissionPerMinutePerSource") != 120:
        fail("Current evidence lost the verified 120/minute per-source play-admission boundary.")

    release_status = evidence.get("releaseStatus", "")
    if release_status != "NOT APPROVED — human acceptance remains.":
        fail("The machine-readable release status must preserve the human-acceptance boundary.")

    validate_run_set("Canonical evidence", evidence.get("workflows", []), EXPECTED_WORKFLOWS, baseline)
    validate_run_set("Task 12 retained gate evidence", evidence.get("task12Workflows", []), EXPECTED_TASK12_WORKFLOWS, baseline)
    validate_run_set("Task 13 gate evidence", evidence.get("task13Workflows", []), EXPECTED_TASK13_WORKFLOWS, baseline)
    task14 = evidence.get("task14Workflows", [])
    validate_run_set("Task 14 release-candidate evidence", task14, EXPECTED_TASK14_WORKFLOWS, baseline)

    candidate = json.loads(RELEASE_CANDIDATE.read_text(encoding="utf-8"))
    if candidate.get("schema") != 1 or candidate.get("task") != 14:
        fail("src/release-candidate.trigger must remain the Task 14 schema-1 sentinel.")
    if candidate.get("releaseStatus") != release_status:
        fail("Release-candidate sentinel changed the human-acceptance boundary.")

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
    for item in task14:
        if str(item["runId"]) not in verification:
            fail(f"VERIFICATION.md is missing Task 14 run {item['runId']} ({item['name']}).")

    print(
        f"DOCUMENTATION_CONTRACT: baseline={baseline}; current_docs={len(CURRENT_DOCS)}; "
        f"task14_workflows={len(task14)}; release=human-acceptance-pending"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"DOCUMENTATION_CONTRACT_FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
