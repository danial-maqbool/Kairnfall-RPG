# Wayfarer character replacement

The new character and creature source, complete runtime atlases, additional action sheets, authority cues and native rendering tests are integrated. Prior actor PNGs and authored masters are deleted from the working tree; Git history and saves are retained.

The accepted candidate is recorded in `docs/art/character-rebuild/integration-report.json`. Native viewport samples are retained in `docs/art/character-rebuild/native/`. Permanent workflow installation and Linux/Windows delivery-head verification remain pending. Compilation and structural checks do not establish independent artistic approval, ordinary-account play quality or release readiness.

Rebuild with `python tools/build_content.py`, `python tools/check_character_source.py`, `python tools/build_game_assets.py`, `python tools/complete_skill_icons.py`, `python tools/validate_character_assets.py`, and `python tools/build_wayfarer_pack.py`. The pack command compares committed pixels; its `--write` option is an explicit source-authoring operation, not validation.
