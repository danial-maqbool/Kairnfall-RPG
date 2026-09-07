# Windows packaging and launch verification

This task is not a release-completion claim.

## Target

Windows x86-64 Godot 4.7.2 .NET client, C#, .NET 10 authoritative server, PostgreSQL. Use the existing client and server. Preserve all game systems and protocol fields.

## Ownership

Own root Windows launch scripts, `tools/windows/`, Docker/Compose development setup, packaging scripts, and `docs/RUNNING.md`. A different workstream owns art and `tools/build_assets.py`. A security workstream owns server/core code. Do not overwrite those files.

## Deliverables

- `bootstrap.ps1`, `Run-Kairnfall-Dev.ps1`, `Run-Kairnfall-Server.ps1`, `Run-Kairnfall-Client.ps1` at repository root.
- Prerequisite checks, optional approved installation, deterministic content/asset generation, database startup, migrations, health checks, server startup, and client startup. Make failures actionable. Track child processes and never kill unrelated programs.
- Docker Compose with persistent PostgreSQL storage. Bind development ports to localhost. Generate local credentials or read operator-provided environment variables. Do not commit a real password or use a fixed production default.
- Verify the actual environment-variable names and health endpoints in server source. Do not invent a second configuration convention.
- Reproducible Windows export using the pinned Godot .NET editor and matching export templates. Read template `version.txt` to install the correct template directory. Use official TLS download sources and verify published digests where available. Publish the server self-contained for win-x64.
- Archive the complete client/server packages with launch instructions, original-code license, required third-party notices, and SHA-256 checksums. Do not package caches, account data, secrets, or developer font files.
- A real Godot smoke run must connect to an isolated local realm. The current client supports `-- --smoke`, `KAIRNFALL_SMOKE_URL`, and `KAIRNFALL_SCREENSHOTS`. Capture actual world/UI frames under a display server. A headless compilation does not prove rendering.
- Build and run on Windows where the available runner permits it. Record exactly which platforms executed and which only cross-compiled.

## Asset dependency

The orchestrator is implementing `python tools/build_assets.py --output client/Assets` after `python tools/build_content.py`. This must create `client/Assets/catalog.json` plus all PNG/WAV assets referenced by the Godot client. Do not fabricate placeholder assets or skip a failed/missing asset generation step. Keep runtime/export gates visibly blocked until the real asset work is integrated.

## Evidence

Write `docs/qa/WINDOWS_BUILD_REVIEW.md` with exact commands, artifact locations, checksums, tests, and blockers. Add packaging tests. If policy permits, add a workflow in `.github/workflows/windows-package.yml`; if workflow writes are disallowed, honor that restriction and implement the runnable packaging scripts without attempting to bypass it. Do not merge this PR, publish a final release, enable paid services, alter billing, or claim game completion.
