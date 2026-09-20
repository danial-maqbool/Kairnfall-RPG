# Source update ZIPs

The source overlay preserves the repository folder structure under `updates/`.
It contains changed committed source files only. It does not contain a Windows executable.
Package creation does not certify gameplay, visual quality, or release readiness.

## Create and verify

Use full commit SHAs. The base must be an ancestor of the target.

```powershell
py -3.12 tools/source_overlay.py build --base <base-commit> --target <target-commit> --output artifacts/delivery/Kairnfall-source-updates.zip
py -3.12 tools/source_overlay.py verify artifacts/delivery/Kairnfall-source-updates.zip
```

The tool reads Git objects, not the working directory. Uncommitted local changes are excluded.
It creates a manifest with target and base file checksums. It verifies every payload after creating the ZIP.
CI dispatch files are listed as omitted. They are not needed to apply local game source changes.
Deletions, symlinks, submodules, private configuration, build caches, and unsafe Windows paths fail packaging.
A copy-over ZIP cannot delete obsolete source safely. Use a reviewed Git update when files were removed.

## Apply

Close the game and its local server. Back up the local checkout.
Keep `.local/database.json`, `.tools`, `.venv`, and all Docker volumes unchanged.
Compare locally modified source with the manifest before replacing it.
Merge unrelated local changes rather than discarding them.
Copy the contents of `updates/` over the existing repository root.
Use the folder containing `bootstrap.ps1`, `client/`, and `src/`.
Do not create another nested checkout. Keep the original source filenames.

Regenerate content and assets when their source changed. Rebuild the client and server.
Run tests from the exact resulting source. Inspect fresh game captures.
The package does not change the local Git HEAD or commit the copied files.

Read the acceptance record for the tested target revision. An archived candidate with a failed gate is not an approved update.
