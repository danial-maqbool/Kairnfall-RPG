#!/usr/bin/env python3
"""Validate current Task 17 evidence without rewriting historical Task 16 provenance."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "handoff" / "CURRENT_EVIDENCE.json"
CURRENT_DOCS = [
    ROOT / "HANDOFF.md",
    ROOT / "docs" / "SESSION_STATUS.md",
    ROOT / "docs" / "handoff" / "TASK17_CURRENT.md",
    ROOT / "docs" / "handoff" / "TASK17_VERIFICATION.md",
]
EXPECTED_TASK17 = {
    "Build and verify",
    "Load acceptance",
    "Compile Windows client source",
    "Task 13 adversarial acceptance",
    "Live progression breadth",
    "Windows package acceptance",
    "Graphical multiplayer acceptance",
    "Release operations acceptance",
    "Windows display and input acceptance",
    "Visual acceptance matrix",
    "Review exact visual candidate",
}
EXPECTED_TASK16 = {
    "Build and verify",
    "Load acceptance",
    "Transaction security regression",
    "Transaction integrity on Windows and Linux",
    "Compile Windows client source",
    "Live progression breadth",
    "Graphical multiplayer acceptance",
    "Windows package acceptance",
    "Task 13 adversarial acceptance",
    "Release operations acceptance",
}
RELEASE_STATUS = "NOT APPROVED — human acceptance remains."


def fail(message: str) -> None:
    raise RuntimeError(message)


def latest_implementation_commit() -> str:
    command = [
        "git", "log", "-1", "--format=%H", "HEAD", "--", ".",
        ":(exclude)docs/**",
        ":(exclude)HANDOFF.md",
        ":(exclude)tools/documentation_contract.py",
        ":(exclude).github/workflows/documentation-contract.yml",
    ]
    value = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()
    if len(value) != 40:
        fail("Could not resolve the latest implementation commit.")
    return value


def validate_runs(label: str, rows: list[dict], expected: set[str], baseline: str) -> None:
    if {row.get("name") for row in rows} != expected:
        fail(label + " workflow names drifted.")
    ids = [row.get("runId") for row in rows]
    if len(set(ids)) != len(ids) or any(not isinstance(value, int) or value <= 0 for value in ids):
        fail(label + " run IDs are invalid or duplicated.")
    if any(row.get("conclusion") != "success" or row.get("headSha") != baseline for row in rows):
        fail(label + " must contain successful exact-baseline evidence only.")


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("schema") != 1 or evidence.get("currentTask") != 17:
        fail("Current evidence must identify schema 1 / Task 17.")

    baseline = evidence.get("implementationBaseline", "")
    actual = latest_implementation_commit()
    if baseline != actual:
        fail(f"Current evidence is stale: {baseline!r} != {actual!r}.")
    if evidence.get("repositorySideTask16Closed") is not True or evidence.get("repositorySideTask17Implemented") is not True:
        fail("Task 16 closure and Task 17 implementation must both be explicit.")

    auth = evidence.get("task17Authorization", {})
    if auth.get("authorized") is not True or auth.get("publicationAuthorized") is not False or auth.get("deploymentAuthorized") is not False:
        fail("Task 17 development authorization boundary drifted.")
    if evidence.get("releaseStatus") != RELEASE_STATUS or evidence.get("publicationReady") is not False or evidence.get("releasePublished") is not False:
        fail("Release-status boundary drifted.")

    candidate = evidence.get("task17CandidateVerification", {})
    if candidate.get("workflowRunId") != 34781286752 or candidate.get("verifiedRevision") != evidence.get("task17CandidateBaseline") or candidate.get("conclusion") != "success":
        fail("Task 17 candidate provenance drifted.")
    validate_runs("Task 17", evidence.get("task17ImplementationWorkflows", []), EXPECTED_TASK17, baseline)

    sync = evidence.get("task17DocumentationSync", {})
    if sync.get("preSyncRunId") != 34782088704 or sync.get("preSyncConclusion") != "failure" or sync.get("preSyncHeadSha") != baseline:
        fail("The pre-synchronization documentation failure must remain explicit.")

    content = evidence.get("task17Content", {})
    expected_content = {
        "surfaceWildernessRegions": 20,
        "surfaceWildernessTiles": 2048000,
        "newOverworldRegions": 0,
        "settlementsEnriched": 10,
        "newPurposefulResidents": 30,
        "newNonRepeatableQuests": 30,
        "questChains": 10,
        "stagesPerChain": 3,
    }
    if content != expected_content:
        fail("Task 17 density evidence drifted.")

    task16 = evidence.get("releaseCandidateBaseline", "")
    if len(task16) != 40 or evidence.get("productClientBaseline") != task16:
        fail("Historical Task 16 release baseline drifted.")
    validate_runs("Task 16 historical", evidence.get("task16Workflows", []), EXPECTED_TASK16, task16)
    owner = evidence.get("task16OwnerCandidate", {})
    if owner.get("workflowHeadSha") != task16 or owner.get("publicationReady") is not False:
        fail("Historical Task 16 owner-candidate provenance drifted.")

    for path in CURRENT_DOCS:
        text = path.read_text(encoding="utf-8")
        for marker in (evidence["statusDate"], baseline, "CURRENT_EVIDENCE.json", RELEASE_STATUS, "Task 17"):
            if marker not in text:
                fail(f"{path.relative_to(ROOT)} is missing current marker: {marker}")

    verification = CURRENT_DOCS[-1].read_text(encoding="utf-8")
    for row in evidence["task17ImplementationWorkflows"]:
        if str(row["runId"]) not in verification:
            fail(f"TASK17_VERIFICATION.md is missing run {row['runId']}.")
    for historical in (task16, evidence.get("task15ReleaseCandidateBaseline", ""), evidence.get("task14ReleaseCandidateBaseline", "")):
        if historical not in verification:
            fail("TASK17_VERIFICATION.md lost historical baseline provenance.")

    print(f"DOCUMENTATION_CONTRACT: task=17; implementation={baseline}; workflows={len(evidence['task17ImplementationWorkflows'])}; task16_history={task16}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"DOCUMENTATION_CONTRACT_FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
