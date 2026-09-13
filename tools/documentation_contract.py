#!/usr/bin/env python3
"""Fail when current-facing release evidence drifts behind implementation."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "handoff" / "CURRENT_EVIDENCE.json"
TASK14_SENTINEL = ROOT / "src" / "release-candidate.trigger"
TASK15_SENTINEL = ROOT / "src" / "release-operations.trigger"
TASK16_SENTINEL = ROOT / "src" / "final-acceptance.trigger"
CURRENT_DOCS = [
    ROOT / "docs" / "handoff" / "VERIFICATION.md",
    ROOT / "docs" / "FINAL_AUDIT.md",
    ROOT / "docs" / "QA_MATRIX.md",
    ROOT / "docs" / "handoff" / "HANDOFF.md",
    ROOT / "docs" / "SESSION_STATUS.md",
    ROOT / "docs" / "handoff" / "LOCAL_AGENT_PROMPT.md",
    ROOT / "docs" / "qa" / "TASK16_EVIDENCE.md",
]
TASK16_PERMANENT_DOCS = [
    ROOT / "docs" / "qa" / "TASK16_OWNER_ACCEPTANCE.md",
    ROOT / "docs" / "release" / "CANDIDATE_AUDIT.md",
    ROOT / "docs" / "release" / "WINDOWS_SETUP.md",
    ROOT / "docs" / "release" / "KNOWN_LIMITATIONS.md",
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
EXPECTED_TASK15_WORKFLOWS = EXPECTED_WORKFLOWS | {"Task 13 adversarial acceptance", "Release operations acceptance"}
EXPECTED_TASK16_WORKFLOWS = EXPECTED_TASK15_WORKFLOWS
STALE_MARKERS = (
    "Current status as of 2026-09-11",
    "Current consolidated status as of 2026-09-11",
    "4/8/16-client",
    "Task 14 was not started",
    "Task 15 was not started",
    "Task 16 was not started",
    "will record exact Task 15 workflow evidence",
    "will record exact Task 16 workflow evidence",
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
        fail(f"{label} must point every workflow at evidence baseline {baseline}.")


def load_sentinel(path: Path, task: int, release_status: str) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != 1 or value.get("task") != task:
        fail(f"{path.relative_to(ROOT)} must remain the Task {task} schema-1 sentinel.")
    if value.get("releaseStatus") != release_status:
        fail(f"{path.relative_to(ROOT)} changed the human-acceptance boundary.")
    if task == 16 and value.get("publicationReady") is not False:
        fail("Task 16 sentinel must keep publicationReady false.")


def validate_owner_candidate(candidate: dict, baseline: str) -> None:
    run_id = candidate.get("workflowRunId")
    artifact_id = candidate.get("actionsArtifactId")
    expected_archive = f"Kairnfall-Release-Candidate-{baseline[:12]}.zip"
    expected_artifact = f"windows-package-{baseline}"
    if not isinstance(run_id, int) or run_id <= 0:
        fail("Task 16 owner candidate is missing its Windows package workflow run ID.")
    if candidate.get("workflowHeadSha") != baseline:
        fail("Task 16 owner candidate workflow head does not equal the implementation baseline.")
    if candidate.get("actionsArtifactName") != expected_artifact:
        fail("Task 16 owner candidate artifact name drifted.")
    if not isinstance(artifact_id, int) or artifact_id <= 0:
        fail("Task 16 owner candidate is missing its Actions artifact ID.")
    if candidate.get("candidateFile") != expected_archive:
        fail("Task 16 owner candidate archive name drifted.")
    if not re.fullmatch(r"[0-9a-f]{64}", candidate.get("candidateSha256", "")):
        fail("Task 16 owner candidate SHA-256 is missing or malformed.")
    if candidate.get("checksumFile") != "RELEASE-CANDIDATE.sha256":
        fail("Task 16 owner candidate checksum filename drifted.")
    if candidate.get("manifestFile") != "release-candidate.json":
        fail("Task 16 owner candidate manifest filename drifted.")
    if candidate.get("publicationReady") is not False:
        fail("Task 16 owner candidate must remain non-publishable.")


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("schema") != 1:
        fail("CURRENT_EVIDENCE.json schema must be 1.")

    baseline = evidence.get("implementationBaseline", "")
    actual = latest_implementation_commit()
    if baseline != actual:
        fail(f"Current evidence is stale: ledger baseline {baseline!r}, latest implementation {actual!r}.")

    task14_baseline = evidence.get("task14ReleaseCandidateBaseline", "")
    task15_baseline = evidence.get("task15ReleaseCandidateBaseline", "")
    if len(task14_baseline) != 40 or len(task15_baseline) != 40:
        fail("Historical Task 14/15 release-candidate baselines are missing.")
    if evidence.get("currentTask") != 16:
        fail("Current evidence must identify Task 16 as the active acceptance phase.")
    if evidence.get("releaseCandidateBaseline") != baseline:
        fail("Task 16 release-candidate baseline must equal the current implementation baseline.")
    if evidence.get("productClientBaseline") != baseline:
        fail("The current packaged-client baseline must equal the Task 16 implementation baseline.")
    if evidence.get("releaseCandidateTrigger") != "src/final-acceptance.trigger":
        fail("Task 16 final-acceptance trigger path drifted.")
    if evidence.get("releaseCandidateWorkflowCount") != len(EXPECTED_TASK16_WORKFLOWS):
        fail("Task 16 release-candidate workflow count drifted.")
    if evidence.get("task15ReleaseCandidateTrigger") != "src/release-operations.trigger":
        fail("Task 15 historical release-operations trigger path drifted.")
    if evidence.get("task15ReleaseCandidateWorkflowCount") != len(EXPECTED_TASK15_WORKFLOWS):
        fail("Task 15 historical workflow count drifted.")
    if evidence.get("task14ReleaseCandidateTrigger") != "src/release-candidate.trigger":
        fail("Task 14 historical release-candidate trigger path drifted.")
    if evidence.get("task14ReleaseCandidateWorkflowCount") != len(EXPECTED_TASK14_WORKFLOWS):
        fail("Task 14 historical workflow count drifted.")

    if evidence.get("referenceLoadClients") != [2, 10, 25, 50]:
        fail("Reference load evidence must match the retained 2/10/25/50-client acceptance gate.")
    if evidence.get("connectionAdmissionPerMinutePerSource") != 120:
        fail("Current evidence lost the verified 120/minute per-source play-admission boundary.")

    release_status = evidence.get("releaseStatus", "")
    if release_status != "NOT APPROVED — human acceptance remains.":
        fail("The machine-readable release status must preserve the human-acceptance boundary.")
    if evidence.get("publicationReady") is not False or evidence.get("releasePublished") is not False:
        fail("Task 16 evidence must remain explicitly non-published until human acceptance.")

    validate_run_set("Canonical Task 16 evidence", evidence.get("workflows", []), EXPECTED_WORKFLOWS, baseline)
    validate_run_set("Task 12 retained historical evidence", evidence.get("task12Workflows", []), EXPECTED_TASK12_WORKFLOWS, task14_baseline)
    validate_run_set("Task 13 current gate evidence", evidence.get("task13Workflows", []), EXPECTED_TASK13_WORKFLOWS, baseline)
    validate_run_set("Task 14 historical release-candidate evidence", evidence.get("task14Workflows", []), EXPECTED_TASK14_WORKFLOWS, task14_baseline)
    validate_run_set("Task 15 retained historical evidence", evidence.get("task15Workflows", []), EXPECTED_TASK15_WORKFLOWS, task15_baseline)
    task16 = evidence.get("task16Workflows", [])
    validate_run_set("Task 16 final-candidate evidence", task16, EXPECTED_TASK16_WORKFLOWS, baseline)
    validate_owner_candidate(evidence.get("task16OwnerCandidate", {}), baseline)

    load_sentinel(TASK14_SENTINEL, 14, release_status)
    load_sentinel(TASK15_SENTINEL, 15, release_status)
    load_sentinel(TASK16_SENTINEL, 16, release_status)

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

    for path in TASK16_PERMANENT_DOCS:
        text = path.read_text(encoding="utf-8")
        if "Task 16" not in text:
            fail(f"{path.relative_to(ROOT)} must identify the Task 16 acceptance phase.")
        if "CURRENT_EVIDENCE.json" not in text:
            fail(f"{path.relative_to(ROOT)} must point to the machine-readable evidence ledger.")
        if release_status not in text:
            fail(f"{path.relative_to(ROOT)} changed or omitted the release-status boundary.")

    runbook = (ROOT / "docs" / "qa" / "TASK16_OWNER_ACCEPTANCE.md").read_text(encoding="utf-8")
    for heading in (
        "Clean package validation",
        "Account and character flow",
        "Persistence",
        "First-hour progression",
        "Class and combat feel",
        "World, quests, resources, and bosses",
        "Economy",
        "Social and multiplayer",
        "UI/UX and accessibility",
        "Physical Windows DPI/input",
        "Art/visual review",
        "Audio listening review",
        "Finding severity",
    ):
        if heading not in runbook:
            fail(f"Task 16 owner runbook is missing required section: {heading}")

    verification = CURRENT_DOCS[0].read_text(encoding="utf-8")
    for item in task16:
        if str(item["runId"]) not in verification:
            fail(f"VERIFICATION.md is missing Task 16 run {item['runId']} ({item['name']}).")
    if task14_baseline not in verification or task15_baseline not in verification:
        fail("VERIFICATION.md must retain Task 14 and Task 15 historical provenance.")

    print(
        f"DOCUMENTATION_CONTRACT: baseline={baseline}; current_docs={len(CURRENT_DOCS)}; "
        f"task16_workflows={len(task16)}; retained_task15={len(evidence.get('task15Workflows', []))}; "
        f"retained_task14={len(evidence.get('task14Workflows', []))}; "
        "release=human-acceptance-pending"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"DOCUMENTATION_CONTRACT_FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
