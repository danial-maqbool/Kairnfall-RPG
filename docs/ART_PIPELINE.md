# Original art and audio pipeline

## Build

Use Python 3.12 or newer. Install `tools/requirements-art.txt` in a virtual environment. These are build dependencies, not client runtime dependencies.

```text
python -m pip install -r tools/requirements-art.txt
python tools/build_content.py
python -m unittest discover -s tests/art -p test_pipeline.py -v
python tools/build_assets.py --preview --output build/art-preview
python tools/build_assets.py --output client/Assets --workers 4 --review-dir build/art-review
```

Preview mode produces review images only. It does not produce a playable game pack. The complete build fails when the creature-art module is absent. It does not substitute a placeholder renderer.

## Native contract

Terrain tiles are 32 by 32 pixels. Human body, hair, and equipment frames are 64 by 64 pixels. Creature frames are 64 pixels; boss frames are 128 pixels. Sprite sheets have eight columns and 24 rows. Rows group six states, each with south, west, east, and north views. The state order is idle, walk, attack, cast, hit, and death. All layers use the same feet anchor: x = 0.5 times frame width; y = 0.86 times frame height.

`tools/art/creatures.py` must provide `frame_size(mob)` and `creature_frame(mob, state, frame_index, direction)`. The art worker owns this module. The orchestrator owns the pack generator and audio.

## Runtime paths

The generator writes item, skill, and ability icons; body, hair, equipment, NPC, and creature sheets; terrain variants; buildings; resource nodes; structures; chests; props; and WAV audio under `client/Assets`. It copies the exact generated catalog into that directory. The manifest lists per-file SHA-256 hashes, native sizes, frame layout, and source/catalog hashes.

Farming aliases include `resources/crop_wheat.png` and `resources/crop_wheat_stage0.png` through `stage3.png`. The server's catalog resource is `wheat_crop`; planted world instances use `crop_wheat`.

Audio includes ten original regional/encounter themes, four ambience loops, eight interaction effects, and four terrain footstep effects. The WAV format is stereo 16-bit PCM at 22,050 Hz. The source synthesizes original notes, instrumental timbres, and ambient/effect signals. It uses no sampled songs, voice recordings, or third-party music.

## Validation and limits of evidence

Technical tests check nonempty native images, palette diversity, frame dimensions, direction differences, deterministic source output, safe unique paths, audio format, finite bounded samples, and preservation of unmanaged files. These tests do not approve visual quality or gameplay. Actual frames and in-engine screenshots still require inspection. The manifest retains `visual_review: pending_independent_inspection` until a separate review record supports approval.

The installer builds in a temporary directory first. It installs the completed manifest last. It preserves unknown files in the target directory. It removes only obsolete files listed by the previous generated manifest.

## Licensing

Original drawing and synthesis code uses the repository's MIT license. The resulting original images and sound files use the same license. No third-party game sprites, songs, recordings, or developer font files are included by this pipeline. Build-only libraries retain their own licenses: Pillow is MIT-CMU; NumPy distributes its component notices with the package.
