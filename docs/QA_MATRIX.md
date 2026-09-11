# QA acceptance matrix

Current consolidated status as of 2026-09-11.

This matrix defines required acceptance gates and their present state. Automated passes are not substitutes for human-only review. Consult `handoff/VERIFICATION.md` for the current evidence record and `FINAL_AUDIT.md` for release status.

| Area | Required check | Current status | Evidence / remaining work |
| --- | --- | --- | --- |
| Source / repository | Single authoritative mainline, required source present, generated assets reproducible. | **PASS** | Repository work is consolidated on `main`; current implementation baseline before docs-only cleanup is `defec56aadf5bc01289b4c7ec8c0e422b918624f`. |
| Backend | Core, gameplay, security, world, PostgreSQL/network and save-conflict suites. | **PASS** | Build and verify run `34555269188` passed Linux and Windows core on the Task 3 final baseline. |
| XP / HUD | Character XP from skill XP; Character XP and Skill XP visible in Vitals; real activity progression. | **IMPLEMENTED / HUMAN CHECK PENDING** | Automated live-progression coverage exists. Owner Windows gameplay pass remains intentionally deferred. |
| Progression | All 60 skills train through authoritative activities; XP, levels, unlocks, Character XP and persistence. | **PASS** | 60/60 real-activity audit passed; Task 2 final CI `34550409865`. |
| Classes | Eight classes retain distinct kits, affinities, equipment and abilities. | **PASS** | All 8 kits / 120 abilities are exercised through real effect handlers; subjective identity/feel remains human. |
| Native UI | Signals, lifecycle, input routing, controls and repeated page recreation. | **PASS** | Retained client/native contracts and current core CI are green. |
| Character art | Body variants and all visible equipment layers across actions/directions. | **PASS STRUCTURAL/GRAPHICAL; HUMAN ART APPROVAL PENDING** | 12 shipped body variants and 13 visible equipment slots are covered; isolated layer sheets, source parity and native Godot presentation pass. |
| Creature art | Normal species, elites and bosses across actions/directions. | **PASS STRUCTURAL/GRAPHICAL; HUMAN ART APPROVAL PENDING** | 100 normal creatures, 25 elites and 20 bosses are covered; boss-safe 128×128 evidence and native Godot presentation pass. |
| World | Cities, services, layers, objectives, resources and boss routes are represented and reachable by authored graph checks. | **PASS AUTOMATED; HUMAN WALKTHROUGH PENDING** | 109 zone-anchor checks pass. Full ordinary-account traversal remains human acceptance. |
| Quests | Objective anchors and quest routing/content references are valid. | **PASS AUTOMATED; HUMAN WALKTHROUGH PENDING** | 166 quest-anchor checks pass. Full objective/resource/boss-arena play remains human. |
| Economy | Crafting, price spreads, tiers, rarity, sinks and boss-drop design avoid clear pathologies. | **PASS AUTOMATED; HUMAN BALANCE PENDING** | Authored balance audit passes; sustained pacing/feel still requires play. |
| Audio | Runtime files are valid and technically clean. | **PASS TECHNICAL; LISTENING PENDING** | All 22 WAV assets pass format/duration/peak/RMS/DC/clipping/loop-boundary checks. |
| Multiplayer | Multiple graphical clients share state, chat and movement; protocol suites cover party/trade/loot/reconnect/restart. | **PASS** | Graphical multiplayer run `34534712045` passed; retained protocol suites remain green. |
| Load / performance | Increasing concurrency records server/database/resource metrics. | **PASS REFERENCE TARGET** | 4/8/16-client staged load probe records tick/snapshot latency, DB commits, RSS and CPU. This is not a production-capacity claim. |
| Windows display/input | Native Windows keyboard/mouse and 125%/150% scale coverage at supported resolutions. | **PASS AUTOMATED; PHYSICAL REVIEW PENDING** | HUD, XP bars, inventory/equipment, crafting, minimap and map are covered at 1280×720 and 1920×1080 with scale emulation. |
| Windows package | Export client/server, launch from clean path, restart/reconnect, checksums. | **PASS CI; OWNER-MACHINE CHECK OPTIONAL/PENDING** | Windows CI exports with pinned Godot .NET/tool templates, launches outside source, restarts/reconnects and produces SHA-256 manifests. |
| Documentation | Verification, audit, handoff and status docs match current mainline. | **PASS — Task 11** | Consolidated on 2026-09-11; historical dated files remain historical evidence. |
| Release | All applicable automated and human gates accepted against an exact package/revision. | **NOT APPROVED** | Human acceptance gates listed below remain. |

## Human acceptance still required for release approval

- Task 1 owner Windows gameplay pass for visible XP/level pacing and reconnect/restart persistence.
- Normal-play feel for skills/classes.
- Independent artistic approval at native/in-engine scale.
- Full ordinary-account world/quest walkthrough.
- Sustained economy/balance feel.
- Audio listening approval.
- Production-scale load/hardware target if a specific capacity will be advertised.
- Physical Windows DPI/input review.
- Owner-machine clean package extraction/launch if required for the release process.

## Current visual evidence

Final Task 3 baseline: `defec56aadf5bc01289b4c7ec8c0e422b918624f`.

- Build and verify: `34555269188` — passed.
- Visual acceptance matrix: `34555269207` — passed.
- Review exact visual candidate: `34555269185` — passed.
- Refined Atelier player source/asset parity is enforced read-only.
- Automated review includes readable per-creature sheets, isolated equipment-slot sheets and native Godot presentation captures.

## Review rules

- A catalog record is not proof that a mechanic works.
- A structural image check is not artistic approval.
- Emulated DPI is not a physical-monitor review.
- A fixed CI concurrency probe is not production-capacity proof.
- Technical WAV analysis is not listening approval.
- Do not delete failing tests, suppress engine errors, weaken production validation, or lower accepted scope to obtain green results.
- Historical September 7–9 files retain their original revision boundaries and must not override the current status above.
