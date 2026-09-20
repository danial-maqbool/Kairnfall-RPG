#!/usr/bin/env python3
"""Build a deterministic source-only update ZIP from two immutable Git commits.

No worktree contents, credentials, generated caches, or database volumes are read.
This package is source code. It is not an exported or accepted Windows game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

SHA = re.compile(r"[0-9a-f]{40}\Z")
ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = frozenset({"client", "src", "content_src", "tests", "tools", "docs"})
ROOT_FILES = frozenset({
    "AGENTS.md", "README.md", "HANDOFF.md", "LICENSE", "LICENSE.md",
    "THIRD_PARTY.md", "CITATION.cff", "global.json", "Kairnfall.slnx",
    "Directory.Build.props", "Directory.Build.targets", "NuGet.Config",
    "nuget.config", "compose.local.yml", "Kairnfall.cmd", "bootstrap.ps1",
    "Run-Kairnfall-Dev.ps1", "Run-Kairnfall-Server.ps1", "Run-Kairnfall-Client.ps1",
    "Test-Kairnfall-Local.ps1", "Stop-Kairnfall-Database.ps1", ".gitignore", ".gitattributes",
})
PRIVATE_PARTS = frozenset({".git", ".local", ".tools", ".venv", ".godot", "bin", "obj", "node_modules", "__pycache__", "artifacts"})
RESERVED = re.compile(r"(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?\Z", re.IGNORECASE)
MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
META = frozenset({"UPDATE_MANIFEST.json", "INSTALL_UPDATES.md", "CHECKSUMS.sha256"})


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(value: str) -> str:
    if not value or "\\" in value or ":" in value or value.startswith("/"):
        raise ValueError("Unsafe package path")
    parts = value.split("/")
    for part in parts:
        if not part or part in {".", ".."} or part.endswith((".", " ")):
            raise ValueError("Unsafe path component")
        if RESERVED.fullmatch(part) or any(ord(c) < 32 or c in '<>\"|?*' for c in part):
            raise ValueError("Path is not portable to Windows")
    return value


def source_path(value: str) -> bool:
    safe_path(value)
    parts = PurePosixPath(value).parts
    lower = tuple(part.casefold() for part in parts)
    if any(part in PRIVATE_PARTS for part in lower):
        raise ValueError("Private or generated path cannot enter a source package: " + value)
    name = lower[-1]
    if name.startswith(".env") or name in {"database.json", "godot.json"} or name.endswith((".pem", ".key", ".pfx", ".p12")):
        raise ValueError("Credential-like path cannot enter a source package: " + value)
    if parts[0] in {".ci", ".github"}:
        return False  # CI request/automation files are not local game updates.
    if parts[0] in SOURCE_DIRS or value in ROOT_FILES:
        return True
    raise ValueError("Unreviewed source path: " + value)


def git(repo: Path, *args: str) -> bytes:
    process = subprocess.run(["git", "-C", str(repo), *args], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, check=False)
    if process.returncode:
        raise RuntimeError("Git operation failed: " + args[0])
    return process.stdout


def commit(repo: Path, value: str) -> str:
    if not SHA.fullmatch(value):
        raise ValueError("Use a full immutable 40-character commit SHA")
    resolved = git(repo, "rev-parse", "--verify", value + "^{commit}").decode().strip()
    if resolved != value:
        raise ValueError("The requested object is not a commit")
    return resolved


def tree(repo: Path, revision: str) -> dict[str, tuple[str, str, str]]:
    result: dict[str, tuple[str, str, str]] = {}
    for record in git(repo, "ls-tree", "-rz", "--full-tree", revision).split(b"\0"):
        if not record:
            continue
        info, raw_name = record.split(b"\t", 1)
        mode, kind, object_id = info.decode("ascii").split()
        result[raw_name.decode("utf-8")] = (mode, kind, object_id)
    return result


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")


def add(archive: zipfile.ZipFile, name: str, value: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    archive.writestr(info, value, compresslevel=9)


def build(repo: Path, base: str, target: str, output: Path) -> dict:
    base = commit(repo, base)
    target = commit(repo, target)
    git(repo, "merge-base", "--is-ancestor", base, target)
    previous, current = tree(repo, base), tree(repo, target)
    files, omitted = [], []
    payload: dict[str, bytes] = {}
    names: set[str] = set()
    total = 0
    for path in sorted(set(previous) | set(current)):
        if previous.get(path) == current.get(path):
            continue
        if not source_path(path):
            omitted.append(path)
            continue
        if path not in current:
            raise ValueError("Copy-over updates cannot safely delete a file: " + path)
        mode, kind, blob = current[path]
        if mode not in {"100644", "100755"} or kind != "blob":
            raise ValueError("Links and submodules are not supported: " + path)
        key = unicodedata.normalize("NFC", path).casefold()
        if key in names:
            raise ValueError("Case-insensitive package path collision: " + path)
        names.add(key)
        raw = git(repo, "cat-file", "blob", blob)
        total += len(raw)
        if len(raw) > MAX_FILE or total > MAX_TOTAL:
            raise ValueError("Source update exceeds its size limit")
        old = previous.get(path)
        if old is not None and (old[0] not in {"100644", "100755"} or old[1] != "blob"):
            raise ValueError("The base path is not a normal file: " + path)
        before = git(repo, "cat-file", "blob", old[2]) if old else None
        payload["updates/" + path] = raw
        files.append({"path": path, "sha256": digest(raw), "size": len(raw),
                      "base_sha256": digest(before) if before is not None else None,
                      "mode": mode, "git_blob": blob})
    if not files:
        raise ValueError("No changed source files to package")
    manifest = {
        "schema": 1, "kind": "source_overlay_not_windows_release",
        "base_commit": base, "target_commit": target,
        "tests": "Consult the acceptance report for this exact revision. Packaging does not run gameplay tests.",
        "files": files, "omitted_ci_paths": omitted,
    }
    instructions = (
        "# Apply the Kairnfall source update\n\n"
        "This is source code, not an exported or accepted Windows game.\n\n"
        f"Base commit: `{base}`\n\nTarget commit: `{target}`\n\n"
        "Close the game and its local server. Keep Docker volumes and private configuration.\n"
        "Back up your checkout before copying. Preserve any uncommitted source changes.\n"
        "Compare each existing file with base_sha256 in UPDATE_MANIFEST.json.\n"
        "A different local file needs a manual merge; do not blindly overwrite it.\n"
        "Copy the CONTENTS of updates/ into the existing repository root.\n"
        "The destination is the folder containing bootstrap.ps1, client/, and src/.\n"
        "Do not create a nested Kairnfall-RPG checkout. Keep the original source filenames.\n\n"
        "The archive never contains .local/, .tools/, .venv/, .git/, generated caches, or saves.\n"
        "CI request/workflow changes are omitted because this is a local source overlay.\n"
        "It does not move your Git branch. Compare git status/diff before committing.\n\n"
        "Regenerate content/assets when their source changed, then rebuild the client and server.\n"
        "Use docs/LOCAL_REQUIREMENTS.md and the latest docs/handoff/ record.\n"
        "Run the native input tests and graphical tests. A successful copy is not test evidence.\n"
    ).encode("utf-8")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError("Refuse to overwrite an existing delivery archive")
    with output.open("xb") as handle:
        with zipfile.ZipFile(handle, "w") as archive:
            for path, raw in payload.items():
                add(archive, path, raw)
            add(archive, "UPDATE_MANIFEST.json", json_bytes(manifest))
            add(archive, "INSTALL_UPDATES.md", instructions)
            checks = "".join(digest(raw) + "  " + path + "\n" for path, raw in payload.items())
            add(archive, "CHECKSUMS.sha256", checks.encode("utf-8"))
    verify(output)
    return manifest


def verify(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        paths = [entry.filename for entry in entries]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate ZIP entries")
        if sum(entry.file_size for entry in entries) > MAX_TOTAL + 1024 * 1024:
            raise ValueError("Archive exceeds the source size limit")
        for entry in entries:
            safe_path(entry.filename)
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("ZIP symlinks are not supported")
        manifest = json.loads(archive.read("UPDATE_MANIFEST.json"))
        if manifest.get("schema") != 1 or manifest.get("kind") != "source_overlay_not_windows_release":
            raise ValueError("Unknown source package format")
        for key in ("base_commit", "target_commit"):
            if not SHA.fullmatch(manifest.get(key, "")):
                raise ValueError("Invalid revision in manifest")
        expected = set(META)
        portable: set[str] = set()
        checks = []
        for row in manifest["files"]:
            name = row["path"]
            if not source_path(name):
                raise ValueError("CI metadata cannot be an overlay payload")
            key = unicodedata.normalize("NFC", name).casefold()
            if key in portable:
                raise ValueError("Duplicate portable payload name")
            portable.add(key)
            member = "updates/" + name
            expected.add(member)
            raw = archive.read(member)
            if len(raw) > MAX_FILE or len(raw) != row["size"] or digest(raw) != row["sha256"]:
                raise ValueError("Payload checksum or size mismatch: " + name)
            checks.append(digest(raw) + "  " + member + "\n")
        if not portable or set(paths) != expected:
            raise ValueError("Unexpected or missing archive entries")
        if archive.read("CHECKSUMS.sha256") != "".join(checks).encode("utf-8"):
            raise ValueError("Checksum list differs from the payload")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC verification failed")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("build")
    create.add_argument("--base", required=True)
    create.add_argument("--target", required=True)
    create.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("verify")
    check.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        result = build(ROOT, args.base, args.target, args.output)
        archive = args.output
    else:
        result = verify(args.archive)
        archive = args.archive
    print(json.dumps({"archive": archive.name, "sha256": digest(archive.read_bytes()),
                      "files": len(result["files"]), "base_commit": result["base_commit"],
                      "target_commit": result["target_commit"], "kind": result["kind"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
