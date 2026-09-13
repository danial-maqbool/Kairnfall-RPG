# Verification record

Current consolidated status as of 2026-09-13.

Current implementation baseline: `3dce816eade22c93a8dad65eee6964be3e12fd52` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 13 adds a permanent same-agent adversarial acceptance executable/workflow and cross-platform regression coverage. It is not an independent approval. Detailed findings and retests are in `docs/qa/INDEPENDENT_FINDINGS.md`. Task 14 was not started.

**NOT APPROVED — human acceptance remains.**

## Exact Task 13 technical evidence

Both runs below execute the Task 13 technical baseline `3dce816eade22c93a8dad65eee6964be3e12fd52`:

- Task 13 adversarial acceptance — run `34768390034`, success. The new ten-scenario audit plus retained security, gameplay/malformed-input, world, concurrency, PostgreSQL/network and isolated save-conflict checks pass.
- Build and verify — run `34768386855`, success. Both Linux and Windows jobs pass; Windows runs `Test-Kairnfall.ps1` and reports `TASK13_ADVERSARIAL_RESULTS passed=10 failed=0`.

## Canonical retained workflow evidence

The current ledger keeps the newest applicable verified run for each canonical gate. Build is exact Task 13 baseline; product/client/path-filtered gates below are retained from the unchanged product/client baseline `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f` and are not misrepresented as `3dce816` executions:

- Build and verify — run `34768386855` — `3dce816eade22c93a8dad65eee6964be3e12fd52`.
- Load acceptance — run `34766715225` — `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f`.
- Transaction security regression — run `34766717227` — `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f`.
- Transaction integrity on Windows and Linux — run `34766719055` — `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f`.
- Compile Windows client source — run `34766713586` — `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f`.
- Live progression breadth — run `34766721059` — `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f`.
- Graphical multiplayer acceptance — run `34766723424` — `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f`.
- Windows package acceptance — run `34766725549` — `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f`.

Task 12 retained evidence at `d4d1b4e` also includes Windows display/input `34766727800`, visual matrix `34766729859`, and audio `34766731782`, all successful.

## Evidence boundary

Task 13 changed tests, solution/Windows test wiring and its permanent workflow; it did not change production gameplay/client/art/package source. Retaining successful client/package/art runs at `d4d1b4e` is therefore unchanged-baseline evidence, not a claim that path-filtered workflows ran at the later test-only SHA.

The visual artifact proves structural/render presence for required cohorts but explicitly does not establish artistic quality. Automated/emulated Windows results do not establish physical-monitor/DPI approval.

## Human acceptance still required before release approval

1. Owner Windows gameplay pass for visible XP/level pacing and reconnect/restart persistence.
2. Normal-play progression and class feel.
3. Independent human adversarial/gameplay acceptance if independence is required.
4. Independent artistic approval at native/in-engine scale.
5. Full ordinary-account world and quest walkthrough.
6. Sustained economy and balance feel.
7. Audio listening approval.
8. Production-scale load validation if a specific concurrent-player capacity will be advertised.
9. Physical Windows DPI and hardware-input inspection.
10. Owner-machine clean Windows package extraction and launch if required for release sign-off.

`tools/documentation_contract.py` validates the ledger baseline against the latest non-documentation implementation commit and checks this current-facing status set for synchronized evidence and release boundary.
