"""Compile Blender-rendered 64 px frames into Kairnfall 8x24 humanoid sheets."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
RIG_PATH = ROOT / "atelier" / "forge" / "rig.py"
SPEC = importlib.util.spec_from_file_location("kairnfall_rig_for_assembler", RIG_PATH)
rig = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = rig
SPEC.loader.exec_module(rig)

FRAME = 64
COLS = 8
ROWS = 24


def finish_frame(image: Image.Image, pose) -> Image.Image:
    image = image.convert("RGBA")
    alpha = image.getchannel("A").point(lambda value: 255 if value >= 72 else 0)
    rgb = image.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.08)
    # Keep enough tonal steps for 3D form while stopping soft-rendered edges from
    # becoming blurry at native 1x scale.
    quantized = rgb.quantize(colors=56, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).convert("RGB")
    image = Image.merge("RGBA", (*quantized.split(), alpha))
    if pose.flash:
        weight = 0.24 * pose.flash
        overlay = Image.new("RGBA", image.size, (255, 236, 206, 255))
        mixed = Image.blend(image, overlay, weight)
        mixed.putalpha(alpha)
        image = mixed
    if pose.fade < 1.0:
        image.putalpha(alpha.point(lambda value: round(value * pose.fade)))
    return image


def compile_sheet(source: Path, output: Path, build: int, skin: int):
    sheet = Image.new("RGBA", (FRAME * COLS, FRAME * ROWS), (0, 0, 0, 0))
    unique = set()
    for state_index, state in enumerate(rig.STATES):
        for direction in range(4):
            row = state_index * 4 + direction
            for frame in range(rig.FRAMES):
                path = source / f"body_{build}_{skin}" / f"{state_index:02d}_{direction}_{frame}.png"
                if not path.exists():
                    raise SystemExit(f"Missing Blender frame: {path}")
                with Image.open(path) as raw:
                    pose = rig.pose(build, state, frame, direction)
                    image = finish_frame(raw, pose)
                if image.size != (FRAME, FRAME) or image.getchannel("A").getbbox() is None:
                    raise SystemExit(f"Invalid rendered frame: {path}")
                unique.add(image.tobytes())
                sheet.alpha_composite(image, (frame * FRAME, row * FRAME))
    if len(unique) <= 100:
        raise SystemExit(f"Insufficient animation variation for body_{build}_{skin}: {len(unique)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)
    print(f"Compiled {output} ({len(unique)} distinct frames)", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    for build in range(2):
        for skin in range(6):
            compile_sheet(args.source, args.output / f"body_{build}_{skin}.png", build, skin)


if __name__ == "__main__":
    main()
