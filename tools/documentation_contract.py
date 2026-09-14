#!/usr/bin/env python3
"""Validate current Task 18 evidence without rewriting historical release provenance."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "handoff" / "CURRENT_EVIDENCE.json"
CURRENT_DOCS = [
    ROOT / "HANDOFF.md",
    ROOT / "docs" / "SESSION_STATUS.md",
    ROOT / "docs" / "handoff" / "TASK18_CURRENT.md",
    ROOT / "docs" / "handoff" / "TASK18_VERIFICATION.md",
]
EXPECTED_TASK18 = {
    "Build and verify",
    "Load acceptance",
    "Transaction security regression",
    "Transaction integrity on Windows and Linux",
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
TASK18_CANDIDATE = "d8ad0d28d0ca60aac161064cbd739e20ba00983d"
TASK18_CANDIDATE_RUN = 34794421856
TASK18_ARTIFACT = 10329611278
TASK18_ARTIFACT_DIGEST = "sha256:4237c998e88e612ba12bcccb3e55c7cc15c18b2c41171e5fab2b5e0bb13e5c16"


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
    if evidence.get("schema") != 1 or evidence.get("currentTask") != 18:
        fail("Current evidence must identify schema 1 / Task 18.")

    baseline = evidence.get("implementationBaseline", "")
    actual = latest_implementation_commit()
    if baseline != actual:
        fail(f"Current evidence is stale: {baseline!r} != {actual!r}.")
    if evidence.get("repositorySideTask16Closed") is not True or evidence.get("repositorySideTask17Implemented") is not True or evidence.get("repositorySideTask18Implemented") is not True:
        fail("Task 16 closure and Task 17/18 implementation states must be explicit.")

    auth = evidence.get("task18Authorization", {})
    if auth.get("authorized") is not True or auth.get("publicationAuthorized") is not False or auth.get("deploymentAuthorized") is not False:
        fail("Task 18 development authorization boundary drifted.")
    if evidence.get("releaseStatus") != RELEASE_STATUS or evidence.get("publicationReady") is not False or evidence.get("releasePublished") is not False:
        fail("Release-status boundary drifted.")

    candidate = evidence.get("task18CandidateVerification", {})
    if evidence.get("task18CandidateBaseline") != TASK18_CANDIDATE or candidate.get("workflowRunId") != TASK18_CANDIDATE_RUN or candidate.get("verifiedRevision") != TASK18_CANDIDATE or candidate.get("conclusion") != "success":
        fail("Task 18 candidate provenance drifted.")
    if candidate.get("actionsArtifactId") != TASK18_ARTIFACT or candidate.get("actionsArtifactDigest") != TASK18_ARTIFACT_DIGEST:
        fail("Task 18 candidate artifact provenance drifted.")
    validate_runs("Task 18", evidence.get("task18ImplementationWorkflows", []), EXPECTED_TASK18, baseline)

    sync = evidence.get("task18DocumentationSync", {})
    if sync.get("preSyncRunId") != 34795232735 or sync.get("preSyncConclusion") != "failure" or sync.get("preSyncHeadSha") != baseline:
        fail("The pre-synchronization Task 18 documentation failure must remain explicit.")

    content = evidence.get("task18Content", {})
    expected_content = {
        "surfaceWildernessRegions": 20,
        "surfaceWildernessTiles": 2048000,
        "newOverworldRegions": 0,
        "normalSpecies": 100,
        "eliteVariants": 25,
        "championElites": 6,
        "rareElites": 19,
        "bosses": 20,
    }
    if content != expected_content:
        fail("Task 18 encounter evidence drifted.")

    task17 = evidence.get("task17ImplementationBaseline", "")
    if len(task17) != 40 or evidence.get("task17DeliveryBaseline") != "1544ab7df4b892b4524909dbfda20bf5ba5637a2":
        fail("Historical Task 17 provenance drifted.")
    validate_runs("Task 17 historical", evidence.get("task17ImplementationWorkflows", []), EXPECTED_TASK17, task17)

    task16 = evidence.get("releaseCandidateBaseline", "")
    if len(task16) != 40 or evidence.get("productClientBaseline") != task16:
        fail("Historical Task 16 release baseline drifted.")
    validate_runs("Task 16 historical", evidence.get("task16Workflows", []), EXPECTED_TASK16, task16)
    owner = evidence.get("task16OwnerCandidate", {})
    if owner.get("workflowHeadSha") != task16 or owner.get("publicationReady") is not False:
        fail("Historical Task 16 owner-candidate provenance drifted.")

    for path in CURRENT_DOCS:
        text = path.read_text(encoding="utf-8")
        for marker in (evidence["statusDate"], baseline, "CURRENT_EVIDENCE.json", RELEASE_STATUS, "Task 18"):
            if marker not in text:
                fail(f"{path.relative_to(ROOT)} is missing current marker: {marker}")

    verification = CURRENT_DOCS[-1].read_text(encoding="utf-8")
    for row in evidence["task18ImplementationWorkflows"]:
        if str(row["runId"]) not in verification:
            fail(f"TASK18_VERIFICATION.md is missing run {row['runId']}.")
    for historical in (evidence.get("task17DeliveryBaseline", ""), task16, evidence.get("task15ReleaseCandidateBaseline", ""), evidence.get("task14ReleaseCandidateBaseline", "")):
        if historical not in verification:
            fail("TASK18_VERIFICATION.md lost historical baseline provenance.")

    print(f"DOCUMENTATION_CONTRACT: task=18; implementation={baseline}; workflows={len(evidence['task18ImplementationWorkflows'])}; task17_history={evidence['task17DeliveryBaseline']}; task16_history={task16}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"DOCUMENTATION_CONTRACT_FAIL: {error}", file=__import__('sys').stderr)
        raise SystemExit(1)
