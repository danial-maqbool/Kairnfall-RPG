# Wayfarer character replacement

Status date: **2026-09-18**  
Verified implementation baseline: **`16f2798edc6b90791548b5bf551eab6433ac9277`**  
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`  
Release status: **NOT APPROVED — human acceptance remains.**

The Wayfarer character replacement is repository-side complete on `main`. Player bodies, hair, equipment overlays, NPCs and creatures are generated from the active Wayfarer source rather than the retired actor raster/master set. Prior actor files were removed from the working tree without rewriting Git history or save data.

The committed actor pack contains **1,245 base sheets**, **5,500 additional motion sheets**, **6,745 actor sheets**, and **415,040 validated frame cells**. Validation records **1,245 replaced historical hashes**, **1,877 retired files**, and **zero historical actor fallbacks**. Public action cues remain presentation-only and preserve server authority, replay safety, privacy boundaries and save compatibility.

Exact-head CI at `16f2798edc6b90791548b5bf551eab6433ac9277` passed the permanent Linux and Windows character matrix, visual acceptance matrix, exact visual review, Windows display/input, Windows package, multiplayer, load, security, build, progression, release-operations, audio and new-player regressions. The complete run list is in `docs/handoff/CHARACTER_VERIFICATION.md`.

Rebuild with `python tools/build_content.py`, `python tools/check_character_source.py`, `python tools/build_game_assets.py`, `python tools/complete_skill_icons.py`, `python tools/validate_character_assets.py`, and `python tools/build_wayfarer_pack.py`. The pack command is read-only verification by default; `--write` is an explicit authoring operation.

Automated verification does not grant independent artistic approval, human gameplay/UX approval, publication approval or release readiness. Those remain human-only gates.
