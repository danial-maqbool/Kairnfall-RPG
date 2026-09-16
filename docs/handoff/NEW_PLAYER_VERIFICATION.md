# New-player experience — verification evidence

Status date: **2026-09-16**.  
Repository: `danial-maqbool/Kairnfall-RPG`; persistent branch: **main only**.  
Implementation baseline: **`7b11027ba913781443871ece56c8ab13008408d5`**.  
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.  
Release status: **NOT APPROVED — human acceptance remains.**

## Exact implementation-head workflows

Every evidence-required technical workflow below completed successfully on `main` at the exact implementation SHA above. Earlier-head or candidate-only successes are not substituted.

| Workflow | Run ID | Conclusion |
| --- | ---: | --- |
| Transaction security regression | `35103673287` | success |
| Compile Windows client source | `35103673135` | success |
| Live progression breadth | `35103673160` | success |
| Windows package acceptance | `35103673233` | success |
| Graphical multiplayer acceptance | `35103673163` | success |
| Load acceptance | `35103673246` | success |
| Build and verify | `35103673180` | success |
| Task 13 adversarial acceptance | `35103673247` | success |
| Release operations acceptance | `35103673242` | success |
| Transaction integrity on Windows and Linux | `35103673240` | success |
| New-player journey | `35103673241` | success |
| Grounded actor acceptance | `35103673162` | success |
| Visual acceptance matrix | `35103673155` | success |
| Windows display and input acceptance | `35103673222` | success |

Supplemental **Audio acceptance** run `35103673192` also succeeded at the same SHA. Pre-synchronization Documentation evidence contract run `35103673245` failed for the intended reason: the checked-in ledger still named the older implementation. Its guard regressions remained active. This failure is not treated as acceptance evidence; the documentation-only delivery head must pass a fresh live evidence check.

## Opening journey evidence

New-player journey run `35103673241` produced artifact **`10450286172`**, named `new-player-journey-7b11027ba913781443871ece56c8ab13008408d5`, size **2,122,591 bytes**, SHA-256 `ede37346a70897518559747eb008068676ed44bc885d996573116afa0571242d`.

| Check | Exact result |
| --- | --- |
| Retained new-player journey | `12/12` groups passed |
| Authoritative opening journey | `5/5` groups passed |
| Classes through opening | `8/8` |
| Native player-experience contract | `442` checks passed |
| Native control/layout contract | `1,169` checks passed |
| Real-server/PostgreSQL live experience | `125` checks passed |

The opening probe covers Bren Gale → two Field Rats → exactly-once class-compatible Rare reward + potion ingredients → normal Inventory equip → ordinary Healing Potion craft → return/world handoff. It also covers full-inventory atomic rollback, pending-reward protection/recovery, reward replay, reconnect/restart, death/respawn, valid out-of-order milestone retention, old-character exclusion and all eight class reward mappings. Combat completion comes from server-owned kill credit, not an attack/cast attempt.

Automated proximity and deterministic fixtures prove a reachable coherent path; they do not establish an uncoached human twenty-minute completion time or retention lift.

## Actor migration and visual evidence

Grounded actor acceptance run `35103673162` succeeded on the exact implementation SHA. Its artifact is **`10450285632`**, `grounded-actors-7b11027ba913781443871ece56c8ab13008408d5`, size **24,799,957 bytes**, SHA-256 `dd15ff16cc16dae7c32faecb25aac1bd2b586309310126635f413633ade86964`.

The verified Grounded-2026 set contains **1,245 active actor sheets**, **239,040 nonblank state/direction/frame cells**, **5,322 anatomy-appropriate motion checks**, **1,237 replaced historical actor hashes**, and **zero actor fallbacks**. The measured active actor PNG footprint is **21,305,167 bytes**: people 1,649,840; equipment 12,726,680; NPC roles 2,180,429; mobs 4,748,218. Representative player/equipment/mob action/death states render through Godot; structural/native rendering evidence does not constitute independent artistic approval.

The Visual acceptance matrix `35103673155` also passed its exact-head deterministic asset and native presentation checks. `docs/ASSET_MIGRATION_FIRST_HOUR_UI.md` is the migration manifest.

## UI/Windows acceptance

`PageLayoutProfiles` drives real page geometry and purpose summaries while the existing Task #12 modal/input/focus architecture remains in force. Exact-head Windows display and input acceptance `35103673222` passed. Permanent native coverage includes 1024×720, 1280×720, 1920×1080 and 2560×1440, supported text scaling, additional content-scale emulation, keyboard/mouse activation, modal input blocking, background-focus suspension/restoration, Escape behavior, overflow scrolling, settings persistence, malformed setting recovery, stale context-menu dismissal, and `Error ·` text that does not rely on color alone.

Physical monitor DPI, hardware-specific input feel and subjective usability remain human-only gates.

## Windows package evidence

Windows package acceptance `35103673233` succeeded on the exact implementation SHA, including clean Windows x86_64 export, packaged executable launch, restart/reconnect and native smoke coverage. Its non-published CI artifact is **`10450049656`**, `windows-package-7b11027ba913781443871ece56c8ab13008408d5`, archive size **56,319,111 bytes**, SHA-256 `9054e6367082e4c4768ebceece4b59076b62f13c5173a599bcdc805b954977ba`.

No like-for-like historical package measurement was captured for this pass, so no package-size delta is claimed. The artifact is acceptance evidence, not a release or deployment.

## Load/performance evidence

Load acceptance `35103673246` exercised **2, 10, 25 and 50 real clients for 20 seconds per stage**. Aggregate snapshot p95 was **204.8 ms**; final rolling tick p95 was **42.8 ms**; maximum sampled server RSS was **647,120 KiB**; and the 50-client stage included **10 reconnects**. This is a bounded CI reference target, not a public production-capacity claim.

## Persistence, security and compatibility

Build, adversarial, transaction-security, Windows/Linux transaction-integrity and release-operations acceptance all passed at the exact implementation head. The opening uses ordinary authoritative persistence/transaction rules, old characters are not reset, historical `first_hour` markers remain compatible, and presentation acknowledgements cannot manufacture XP, items, gold, reputation, quest completion or event contribution. The implementation adds zero new overworld regions and no deployment/production-infrastructure change.

Relative to starting main `dff9f170f25f44c8ae024e8d94133f72d63f6446`, the only authored `content_src` addition/change is `content_src/opening_journey.py`. The previous Task 22 evidence remains archived verbatim, and temporary candidate/repair/diagnostic workflows are absent.

## Delivery-head contract and human-only gates

The synchronized delivery commit contains documentation only, so it does not change the verified gameplay/tests/workflows. `tools/documentation_contract.py` independently checks the exact implementation SHA, each required run's ID/name/branch/repository/conclusion, the single-main policy, authored-content footprint, archived Task 22 blob, zero temporary tooling, Grounded source/fallback boundary, UI resolution matrix and release-authorization limits.

Repository-side technical completion does **not** approve artistic quality, uncoached first-hour pacing/retention, class/economy feel, audio by listening, a full ordinary-account walkthrough, physical Windows DPI/hardware input, owner-machine package behavior, or production-scale capacity. Publication, deployment and release approval remain separate and unauthorized.
