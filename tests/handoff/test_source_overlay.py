"""Source delivery invariants. Uses disposable Git repositories, never player data."""
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("source_overlay", ROOT / "tools/source_overlay.py")
overlay = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(overlay)


class SourceOverlayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo with spaces"
        self.repo.mkdir()
        self.run_git("init", "--initial-branch=main")
        self.run_git("config", "user.name", "Fixture")
        self.run_git("config", "user.email", "fixture@example.invalid")
        self.run_git("config", "core.autocrlf", "false")
        self.write("client/Scripts/Fixture.cs", "// original\n")
        self.base = self.save("base")

    def run_git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def write(self, name, value):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8", newline="\n")

    def save(self, message):
        self.run_git("add", "-A")
        self.run_git("commit", "-m", message)
        return self.run_git("rev-parse", "HEAD").decode().strip()

    def build(self, name="update.zip", target=None):
        output = Path(self.temp.name) / name
        target = target or self.save("update")
        manifest = overlay.build(self.repo, self.base, target, output)
        return output, manifest

    def test_structure_and_hashes(self):
        self.write("client/Scripts/Fixture.cs", "// updated\n")
        self.write("docs/handoff/UPDATE.md", "Source only.\n")
        output, result = self.build()
        self.assertEqual(overlay.verify(output), result)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read("updates/client/Scripts/Fixture.cs"), b"// updated\n")
            self.assertIn("updates/docs/handoff/UPDATE.md", archive.namelist())
            self.assertNotIn(".git/", archive.namelist())
        self.assertEqual(result["files"][0]["base_sha256"], overlay.digest(b"// original\n"))
        self.assertIsNone(result["files"][1]["base_sha256"])

    def test_ignores_uncommitted_and_untracked_contents(self):
        self.write("client/Scripts/Fixture.cs", "// committed\n")
        target = self.save("committed")
        self.write("client/Scripts/Fixture.cs", "// uncommitted private edit\n")
        self.write(".local/database.json", '{"private":"never copy"}')
        output, _ = self.build(target=target)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read("updates/client/Scripts/Fixture.cs"), b"// committed\n")
            self.assertFalse(any("database" in name for name in archive.namelist()))

    def test_deterministic_archives(self):
        self.write("client/Scripts/Fixture.cs", "// same\n")
        target = self.save("same")
        first, _ = self.build("one.zip", target)
        second, _ = self.build("two.zip", target)
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_does_not_overwrite_existing_archive(self):
        self.write("client/Scripts/Fixture.cs", "// changed\n")
        target = self.save("changed")
        self.build(target=target)
        with self.assertRaises(FileExistsError):
            self.build(target=target)

    def test_requires_immutable_commit(self):
        with self.assertRaises(ValueError):
            overlay.commit(self.repo, "main")
        with self.assertRaises(ValueError):
            overlay.commit(self.repo, "--help")

    def test_rejects_private_paths_even_when_tracked(self):
        self.write(".local/database.json", "must not enter archive")
        with self.assertRaises(ValueError):
            self.build()

    def test_rejects_deletions(self):
        (self.repo / "client/Scripts/Fixture.cs").unlink()
        self.write("docs/NEW.md", "replacement")
        with self.assertRaises(ValueError):
            self.build()

    def test_omits_ci_dispatch_files(self):
        self.write("client/Scripts/Fixture.cs", "// changed\n")
        self.write(".ci/request.json", "{}")
        self.write(".github/workflows/test.yml", "name: fixture\n")
        output, result = self.build()
        self.assertEqual(len(result["omitted_ci_paths"]), 2)
        with zipfile.ZipFile(output) as archive:
            self.assertFalse(any(name.startswith("updates/.ci/") or name.startswith("updates/.github/") for name in archive.namelist()))

    def test_rejects_empty_update(self):
        with self.assertRaises(ValueError):
            self.build(target=self.base)

    def test_rejects_unsafe_windows_paths(self):
        for name in ("../escape", "/root", "client/../other", "client//bad", "client/a\\b", "client/a:b", "client/NUL.cs", "client/COM1", "client/file. ", "client/a\nb"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                overlay.safe_path(name)

    def test_rejects_credential_or_generated_paths(self):
        for name in ("src/.env", "client/.env.local", "docs/server.pem", "client/.godot/cache", "src/bin/x.dll", "tools/database.json", "src/private.key"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                overlay.source_path(name)

    def test_rejects_symlink_blob_mode(self):
        raw = subprocess.run(["git", "-C", str(self.repo), "hash-object", "-w", "--stdin"],
                             input=b"../../private", stdout=subprocess.PIPE, check=True).stdout.decode().strip()
        self.run_git("update-index", "--add", "--cacheinfo", "120000," + raw + ",client/link")
        self.run_git("commit", "-m", "symlink fixture")
        target = self.run_git("rev-parse", "HEAD").decode().strip()
        with self.assertRaises(ValueError):
            self.build(target=target)

    def test_detects_payload_tampering(self):
        self.write("client/Scripts/Fixture.cs", "// changed\n")
        output, _ = self.build()
        corrupted = Path(self.temp.name) / "corrupted.zip"
        with zipfile.ZipFile(output) as source, zipfile.ZipFile(corrupted, "w") as destination:
            for entry in source.infolist():
                raw = source.read(entry.filename)
                if entry.filename.startswith("updates/"):
                    raw += b"tampered"
                destination.writestr(entry, raw)
        with self.assertRaises(ValueError):
            overlay.verify(corrupted)

    def test_detects_unlisted_extra_file(self):
        self.write("client/Scripts/Fixture.cs", "// changed\n")
        output, _ = self.build()
        with zipfile.ZipFile(output, "a") as archive:
            archive.writestr("extra.txt", "unexpected")
        with self.assertRaises(ValueError):
            overlay.verify(output)

    def test_rejects_nonancestor(self):
        self.write("client/Scripts/Fixture.cs", "// later\n")
        later = self.save("later")
        with self.assertRaises(RuntimeError):
            overlay.build(self.repo, later, self.base, Path(self.temp.name) / "backwards.zip")


if __name__ == "__main__":
    unittest.main()
