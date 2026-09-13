#!/usr/bin/env python3
"""Build a fail-closed manifest for a non-publishable Windows release candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

STATUS = "NOT APPROVED — human acceptance remains."


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def entry(path: Path, bundled_name: str | None = None) -> dict:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"Required release-candidate file is missing or empty: {path}")
    return {
        "file": bundled_name or path.name,
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }


def actions_provenance(source_sha: str) -> dict:
    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true":
        return {
            "producer": "local",
            "workflowRunId": None,
            "workflowRunAttempt": None,
            "actionsArtifactName": None,
            "workflowRunUrl": None,
        }

    run_id = os.environ.get("GITHUB_RUN_ID", "")
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    env_sha = os.environ.get("GITHUB_SHA", "")
    if not run_id.isdigit() or not attempt.isdigit():
        raise RuntimeError("GitHub Actions candidate is missing numeric run provenance.")
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", repository):
        raise RuntimeError("GitHub Actions candidate is missing repository provenance.")
    if env_sha.lower() != source_sha.lower():
        raise RuntimeError("GitHub Actions source SHA does not match --source-sha.")

    artifact_name = f"windows-package-{source_sha.lower()}"
    return {
        "producer": "github-actions",
        "workflowRunId": int(run_id),
        "workflowRunAttempt": int(attempt),
        "actionsArtifactName": artifact_name,
        "workflowRunUrl": f"https://github.com/{repository}/actions/runs/{run_id}",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--client", type=Path, required=True)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--operations", type=Path, required=True)
    parser.add_argument("--checksums", type=Path, required=True)
    parser.add_argument("--setup", type=Path, required=True)
    parser.add_argument("--limitations", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", args.source_sha):
        raise RuntimeError("source SHA must be a full 40-character Git commit.")

    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    if evidence.get("releaseStatus") != STATUS:
        raise RuntimeError("Current evidence changed the human-acceptance boundary.")
    if evidence.get("publicationReady") is not False:
        raise RuntimeError("Current evidence must keep publicationReady false.")
    human_gates = evidence.get("humanOnlyGates")
    if not isinstance(human_gates, list) or not human_gates:
        raise RuntimeError("Current evidence must keep explicit human-only release gates.")

    packages = {
        "client": entry(args.client),
        "server": entry(args.server),
        "operations": entry(args.operations),
    }
    checksum_lines = {
        line.split(None, 1)[1].strip(): line.split(None, 1)[0].lower()
        for line in args.checksums.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    }
    for package in packages.values():
        if checksum_lines.get(package["file"]) != package["sha256"]:
            raise RuntimeError(f"SHA256SUMS.txt does not match {package['file']}.")

    # These names intentionally match the filenames copied into the outer bundle by
    # windows-package.yml. Keeping the manifest aligned with the actual bundle avoids
    # a stale/renamed-document provenance gap.
    documents = {
        "setup": entry(args.setup, "SETUP.md"),
        "knownLimitations": entry(args.limitations, "KNOWN_LIMITATIONS.md"),
        "audit": entry(args.audit, "AUDIT.md"),
    }
    manifest = {
        "schema": 1,
        "kind": "kairnfall-windows-release-candidate",
        "task": 16,
        "sourceSha": args.source_sha.lower(),
        "candidateLabel": f"task16-{args.source_sha.lower()[:12]}",
        "releaseStatus": STATUS,
        "publicationReady": False,
        "packages": packages,
        "checksums": entry(args.checksums),
        "checksumsFile": args.checksums.name,
        "documents": documents,
        "ownerAcceptance": {
            "repositoryPath": "docs/qa/TASK16_OWNER_ACCEPTANCE.md",
            "required": True,
            "resultsMayBeRecordedOnlyAfterHumanObservation": True,
        },
        "provenance": actions_provenance(args.source_sha),
        "humanOnlyGates": human_gates,
        "publicationRule": (
            "Do not create a release or tag until the applicable human acceptance gates "
            "are recorded as complete and the owner explicitly authorizes publication."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        "RELEASE_MANIFEST_OK: "
        f"source={manifest['sourceSha']}; task=16; packages={len(packages)}; "
        f"producer={manifest['provenance']['producer']}; publicationReady=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
