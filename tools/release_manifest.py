#!/usr/bin/env python3
"""Build a fail-closed manifest for a non-publishable Windows release candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

STATUS = "NOT APPROVED — human acceptance remains."


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def entry(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"Required release-candidate file is missing or empty: {path}")
    return {"file": path.name, "bytes": path.stat().st_size, "sha256": digest(path)}


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

    documents = {
        "setup": entry(args.setup),
        "knownLimitations": entry(args.limitations),
        "audit": entry(args.audit),
    }
    manifest = {
        "schema": 1,
        "kind": "kairnfall-windows-release-candidate",
        "sourceSha": args.source_sha.lower(),
        "releaseStatus": STATUS,
        "publicationReady": False,
        "packages": packages,
        "checksumsFile": args.checksums.name,
        "documents": documents,
        "humanOnlyGates": human_gates,
        "publicationRule": "Do not create a release or tag until the applicable human acceptance gates are recorded as complete.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"RELEASE_MANIFEST_OK: source={manifest['sourceSha']}; packages={len(packages)}; publicationReady=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
