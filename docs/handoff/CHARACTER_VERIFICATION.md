# Wayfarer character replacement verification

Status date: **2026-09-18**  
Verified implementation baseline: **`16f2798edc6b90791548b5bf551eab6433ac9277`**  
Evidence ledger: `docs/handoff/CURRENT_EVIDENCE.json`  
Release status: **NOT APPROVED — human acceptance remains.**

This document records repository-side technical acceptance for the **Wayfarer character replacement**. It does not grant artistic, UX, publication, deployment or release approval.

## Exact-head workflow evidence

All required workflows below completed successfully on exact `main` SHA `16f2798edc6b90791548b5bf551eab6433ac9277`:

| Workflow | Run ID |
| --- | ---: |
| Transaction security regression | 35305085938 |
| Compile Windows client source | 35305085953 |
| Live progression breadth | 35305085977 |
| Windows package acceptance | 35305085972 |
| Graphical multiplayer acceptance | 35305085908 |
| Load acceptance | 35305085906 |
| Build and verify | 35305085944 |
| Task 13 adversarial acceptance | 35305085917 |
| Release operations acceptance | 35305085927 |
| Transaction integrity on Windows and Linux | 35305085964 |
| New-player journey | 35305085947 |
| Character sprite acceptance | 35305085957 |
| Visual acceptance matrix | 35305085930 |
| Windows display and input acceptance | 35305085910 |
| Audio acceptance | 35305085955 |

The pre-synchronization Documentation evidence contract run `35305085922` failed because the checked-in evidence ledger still named the prior workstream. That stale-ledger rejection is expected; the documentation-only synchronization after the exact implementation baseline does not change the verified implementation SHA.

## Character-specific acceptance

The committed Wayfarer pack contains **1,245 base sheets**, **5,500 additional motion sheets**, **6,745 actor sheets**, and **415,040 validated frame cells**. The migration ledger records **1,245 replaced historical hashes**, **1,877 retired files**, and **zero historical actor fallbacks**.

Character sprite acceptance run `35305085957` passed both matrix jobs:

- `verify (ubuntu-latest, linux)` — success.
- `verify (windows-latest, windows)` — success.

Linux evidence artifact: `10531023507`, `character-sprites-ubuntu-latest-16f2798edc6b90791548b5bf551eab6433ac9277`, 29,126,538 bytes, SHA-256 `c7b990457b3568a754652741d8709bf8fd9216acb8a89046b8b7b43da82266c4`.

Windows evidence artifact: `10531604391`, `character-sprites-windows-latest-16f2798edc6b90791548b5bf551eab6433ac9277`, 29,127,492 bytes, SHA-256 `4ccb9749d8fe24462d45c67bf60f01a5ac41f3ebc329139fee1fe45652d47d97`.

The permanent checks cover deterministic asset reconstruction, animation-state coverage, source integrity, public action presentation, replay/privacy/save boundaries, native Godot rendering, Windows/Linux execution, visual-structure regressions, retained onboarding, multiplayer, persistence, security, packaging and load tests.

## Delivery boundary

Temporary migration, diagnostic and pack-refresh tooling has been removed from the working tree. Prior actor files are retired from the current tree without rewriting Git history or modifying save data. The persistent branch policy remains `main` only.

Automated evidence does not replace independent artistic review, owner gameplay testing, uncoached usability/retention measurement, normal-play balance/economy assessment, physical Windows input/DPI inspection, audio listening approval or production-scale validation.
