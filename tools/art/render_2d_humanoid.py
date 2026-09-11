#!/usr/bin/env python3
"""Generate the twelve Kairnfall humanoid body sheets as pure 2D pixel art.

The renderer uses the shared Atelier rig and Pillow drawing primitives only.
It also writes review sheets that composite the new body with existing 2D hair
and representative worn equipment. Those review sheets are not game assets;
they exist so anatomy, hair and clothing can be inspected together.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ATELIER = ROOT / "atelier"
sys.path.insert(0, str(ATELIER))

from forge import folk, illustrated_body, rig  # noqa: E402


def representative_equipment():
    catalog_path = ROOT / "content" / "catalog.json"
    if not catalog_path.exists():
        return []
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    wanted = ("legs", "boots", "chest", "gloves")
    chosen = []
    for slot in wanted:
        item = next((entry for entry in data.get("items", []) if entry.get("slot") == slot), None)
        if item is not None:
            chosen.append(item)
    return chosen


def compose_review_frame(build, skin, state, frame, direction, equipment):
    image = illustrated_body.body_frame(build, skin, state, frame, direction)
    style = (build * 2 + skin) % len(folk.HAIR_STYLES)
    colour = (skin + build + 1) % 8
    image.alpha_composite(folk.hair_frame(style, colour, state, frame, direction))
    for item in equipment:
        image.alpha_composite(folk.armour_frame(item, state, frame, direction))
    return image


def save_sheet(path, renderer):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = rig.sheet(renderer)
    if image.mode != "RGBA" or image.size != (512, 1536):
        raise ValueError(f"Invalid sheet contract for {path}: {image.mode} {image.size}")
    image.save(path, optimize=True, compress_level=9)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    args = parser.parse_args()

    equipment = representative_equipment()
    args.output.mkdir(parents=True, exist_ok=True)
    args.preview.mkdir(parents=True, exist_ok=True)

    for build in range(2):
        for skin in range(6):
            save_sheet(
                args.output / f"body_{build}_{skin}.png",
                lambda state, frame, direction, b=build, s=skin: illustrated_body.body_frame(
                    b, s, state, frame, direction
                ),
            )
            save_sheet(
                args.preview / f"character_{build}_{skin}.png",
                lambda state, frame, direction, b=build, s=skin: compose_review_frame(
                    b, s, state, frame, direction, equipment
                ),
            )

    print("Generated 12 pure-2D body sheets and 12 composite review sheets.")


if __name__ == "__main__":
    main()
