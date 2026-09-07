"""Creature sprite construction and animation at native resolution."""
from __future__ import annotations

import math
from PIL import Image

from .common import INK, Pixel, animation_pose, canvas, finish_frame, palette, seed, shade, sheet

STATES = ("idle", "walk", "attack", "cast", "hit", "death")
DIRECTIONS = {"south": 0, "west": 1, "east": 2, "north": 3}


FUR_BASES = ("9c7f5c", "7f6a53", "b59b79", "8a6d59", "6f635a")
SKIN_BASES = ("b89b7d", "8f775f", "6f8a7f", "7d6963", "8d7c68")
SCALE_BASES = ("6f8063", "66817f", "807259", "6a6e7f", "8a6e63")
FEATHER_BASES = ("9a9e93", "7e8e9d", "8f7e73", "b4ad91", "6b7488")
CHITIN_BASES = ("786a57", "65758a", "6e835d", "8f7459", "74747a")
BONE_BASES = ("c8bb96", "b1a57f", "9f9787")
STONE_BASES = ("8b8e8a", "73767b", "8f8374")
CLOTH_BASES = ("7f6c5a", "657a86", "7b6c86", "6b866f", "936b64")
GLOW_BASES = ("9ecfd1", "b9a6d9", "d6bf8d", "a6d2a0", "d39a90")


QUADRUPED = {
    "rat", "mouse", "hare", "fox", "boar", "deer", "wolf", "stag", "wolverine", "bear", "badger", "goat", "ibex",
    "leopard", "arctic_fox", "ox", "hound", "polar_bear", "weasel", "jackal", "horse", "monkey", "armadillo", "mudskipper",
    "lizard", "crocodile", "toad", "frog", "turtle", "tortoise", "salamander"
}
BIRD = {"owl", "harpy", "griffon", "heron", "skimmer", "gull", "vulture", "crow", "bat", "moth", "spore_moth"}
ARACHNID = {"spider", "quartz_spider", "tick", "scorpion", "automaton"}
INSECT = {"beetle", "bark_beetle", "fire_beetle", "crystal_beetle", "scarab", "wasp", "mantis"}
SERPENT = {"worm", "grave_worm", "ice_worm", "leech", "serpent", "viper", "centipede"}
CRAB = {"crab", "sand_crab", "glacier_crab", "hermit_crab"}
DRACONIC = {"drake", "wyvern", "wyrm"}
HUMANOID = {"goblin", "bandit", "pirate", "kobold", "ogre", "hermit", "myconid", "knight", "skeleton", "revenant", "ghoul"}
CONSTRUCT = {"construct", "golem", "tree", "guardian", "prism", "coral", "gargoyle", "sentinel", "mimic", "elemental"}
SPIRIT = {"wisp", "sprite", "djinn", "wraith", "phantom", "geode", "spell_wisp", "fungus", "horror", "manta", "cuttle", "owlbear"}


def frame_size(mob: dict) -> int:
    return 128 if mob.get("boss") else 64


def _choice(values: tuple[str, ...], key: str) -> str:
    return values[seed(key) % len(values)]


def _colors(mob: dict) -> dict[str, str]:
    ident = mob["id"]
    anatomy = mob.get("anatomy", "")
    family = mob.get("family", "")
    biome = mob.get("biome", "")
    primary = _choice(SKIN_BASES, ident)
    hair = _choice(FUR_BASES, ident + "-fur")
    scale = _choice(SCALE_BASES, ident + "-scale")
    cloth = _choice(CLOTH_BASES, ident + "-cloth")
    if "animal:" in anatomy:
        if any(x in family for x in ("bird", "owl", "gull", "vulture", "crow", "griffon", "harpy", "bat", "moth")):
            primary = _choice(FEATHER_BASES, ident + "-feather")
        elif any(x in family for x in ("spider", "scorpion", "beetle", "wasp", "tick", "centipede")):
            primary = _choice(CHITIN_BASES, ident + "-chitin")
        elif any(x in family for x in ("drake", "wyvern", "wyrm", "lizard", "crocodile", "salamander", "serpent", "viper", "turtle", "tortoise")):
            primary = scale
        else:
            primary = hair
    elif "construct:" in anatomy or family in CONSTRUCT:
        primary = _choice(STONE_BASES, ident + "-stone")
        scale = shade(primary, 0.8)
    elif "undead:" in anatomy or family in {"skeleton", "revenant", "ghoul", "jackal", "wraith", "phantom"}:
        primary = _choice(BONE_BASES, ident + "-bone")
        cloth = "6c707f"
    elif "spirit:" in anatomy or family in SPIRIT:
        primary = _choice(GLOW_BASES, ident + "-glow")
        cloth = shade(primary, 0.85)
    if biome in {"glacier", "tundra"}:
        primary = shade(primary, 1.07, 10)
    if biome in {"volcanic", "ash"}:
        primary = shade(primary, 0.92, 8)
    return {"body": primary, "fur": hair, "scale": scale, "cloth": cloth}


def _anchors(size: int) -> tuple[int, int]:
    return round(size * 0.5), round(size * 0.86)


def _pose(mob: dict, state: str, frame_index: int, direction: int) -> dict:
    p = animation_pose(state, frame_index, direction)
    if mob.get("boss"):
        p["bob"] += 1
        p["stride"] *= 1.2
    if mob.get("elite"):
        p["stride"] *= 1.1
    return p


def _material_strokes(p: Pixel, points: list[tuple[float, float]], base: str, kind: str) -> None:
    colors = palette(base)
    if kind == "fur":
        for x, y in points:
            p.line([(x - 1, y), (x + 1, y - 1)], colors[4])
    elif kind == "feather":
        for x, y in points:
            p.line([(x - 1, y - 1), (x + 1, y + 1)], colors[4])
    elif kind == "scale":
        for x, y in points:
            p.dot(x, y, colors[3])
            p.dot(x + 1, y + 1, colors[1])
    elif kind == "stone":
        for x, y in points:
            p.poly([(x - 1, y), (x + 1, y - 1), (x + 2, y + 1), (x - 1, y + 2)], colors[2], colors[0])
    elif kind == "bone":
        for x, y in points:
            p.dot(x, y, colors[4])


def _draw_quadruped(image: Image.Image, mob: dict, state: str, frame: int, direction: int, scale: float) -> None:
    p = Pixel(image)
    size = image.width
    cx, fy = _anchors(size)
    pose = _pose(mob, state, frame, direction)
    colors = _colors(mob)
    base = colors["body"]
    c = palette(base)
    side = direction in (1, 2)
    back = direction == 3

    body_w = round(size * (0.36 if mob.get("boss") else 0.28) * scale)
    body_h = round(size * (0.22 if mob.get("boss") else 0.18) * scale)
    body_y = fy - round(size * 0.22) - pose["bob"]
    body_x = cx + (4 if side else 0)

    p.ellipse((body_x - body_w, body_y - body_h, body_x + body_w, body_y + body_h), c[2], INK)
    p.ellipse((body_x - body_w + 3, body_y - body_h + 3, body_x + body_w - 4, body_y + body_h - 2), c[3], None)

    neck_x = body_x + (body_w - 4 if direction == 2 else -body_w + 4 if direction == 1 else 0)
    if not side:
        neck_x = body_x + (3 if not back else -3)
    head_w = round(body_w * 0.52)
    head_h = round(body_h * 0.55)
    head_y = body_y - round(body_h * 0.25)
    p.ellipse((neck_x - head_w, head_y - head_h, neck_x + head_w, head_y + head_h), c[3], INK)

    # Distinct front/back by snout and facial placement.
    if not back:
        snout = 1 if direction == 2 else -1 if direction == 1 else 0
        p.poly([(neck_x + snout * head_w, head_y), (neck_x + snout * (head_w + 6), head_y + 1), (neck_x + snout * head_w, head_y + 4)], c[1], INK)
        p.dot(neck_x + snout * (head_w + 2), head_y + 1, INK)
    else:
        p.line([(neck_x - 3, head_y + 2), (neck_x + 3, head_y + 2)], c[1])

    anatomy = mob.get("anatomy", "").lower()
    family = mob.get("family", "")
    if "antler" in anatomy or family in {"deer", "stag", "ibex", "goat", "ox"}:
        for dx in (-1, 1):
            x = neck_x + dx * 3
            p.line([(x, head_y - head_h + 1), (x + dx * 3, head_y - head_h - 7)], shade(c[4], 0.9), 2)
            p.line([(x + dx * 2, head_y - head_h - 4), (x + dx * 5, head_y - head_h - 6)], shade(c[4], 1.1))
    if "ear" in anatomy or family in {"hare", "rabbit"}:
        ear_h = 12 if "hare" in family or "long ears" in anatomy else 6
        for dx in (-1, 1):
            p.poly([(neck_x + dx * 2, head_y - head_h + 1), (neck_x + dx * 4, head_y - head_h - ear_h), (neck_x + dx, head_y - head_h + 2)], c[3], INK)
    if "tusk" in anatomy:
        for dx in (-1, 1):
            p.poly([(neck_x + dx * (head_w - 1), head_y + 2), (neck_x + dx * (head_w + 4), head_y + 4), (neck_x + dx * (head_w + 1), head_y + 6)], "d7c8a1", INK)

    # Folded hind legs and gait.
    step = round(pose["stride"] * 3)
    leg_pairs = [(-body_w + 7, 0), (body_w - 7, -step)]
    for i, (dx, add) in enumerate(leg_pairs):
        lift = step if i == 0 else -step
        hip_x = body_x + dx
        knee_y = fy - 8 + add
        paw_y = fy + (1 if i else 0)
        p.limb((hip_x, body_y + body_h - 3), (hip_x + (2 if i else -2), knee_y), 4, colors["scale"] if "scale" in anatomy else base)
        p.limb((hip_x + (2 if i else -2), knee_y), (hip_x + lift, paw_y), 3, base)
        if "hoof" in anatomy:
            p.rect((hip_x + lift - 2, paw_y - 1, hip_x + lift + 2, paw_y + 2), shade(base, 0.65), INK)
        else:
            p.ellipse((hip_x + lift - 3, paw_y - 1, hip_x + lift + 3, paw_y + 2), c[2], INK)

    # Tail shape by anatomy.
    tail_base = (body_x - body_w + 2, body_y + 1) if direction != 2 else (body_x + body_w - 2, body_y + 1)
    tail_sign = -1 if direction != 2 else 1
    if "hairless" in anatomy or family in {"rat", "mouse"}:
        p.line([tail_base, (tail_base[0] + tail_sign * 10, tail_base[1] + 2), (tail_base[0] + tail_sign * 14, tail_base[1] + 8)], "b69388", 2)
    elif "brush" in anatomy or family in {"fox", "arctic_fox", "wolf", "hound", "jackal"}:
        p.poly([tail_base, (tail_base[0] + tail_sign * 12, tail_base[1] - 2), (tail_base[0] + tail_sign * 18, tail_base[1] + 4), (tail_base[0] + tail_sign * 8, tail_base[1] + 8)], colors["fur"], INK)
    else:
        p.line([tail_base, (tail_base[0] + tail_sign * 9, tail_base[1] + 3)], c[1], 3)

    _material_strokes(p, [(body_x - 8, body_y - 2), (body_x + 4, body_y + 1), (body_x + 10, body_y - 3)], colors["fur"], "scale" if "scale" in anatomy else "fur")


def _draw_bird(image: Image.Image, mob: dict, state: str, frame: int, direction: int, scale: float) -> None:
    p = Pixel(image)
    size = image.width
    cx, fy = _anchors(size)
    pose = _pose(mob, state, frame, direction)
    colors = _colors(mob)
    c = palette(colors["body"])
    side = direction in (1, 2)
    back = direction == 3

    torso_y = fy - round(size * 0.24) - pose["bob"]
    torso_w = round(size * 0.18 * scale)
    torso_h = round(size * 0.16 * scale)
    p.ellipse((cx - torso_w, torso_y - torso_h, cx + torso_w, torso_y + torso_h), c[2], INK)

    wing_span = round(size * (0.22 if mob.get("boss") else 0.16))
    flap = round(math.sin(frame / 7 * math.tau) * 5) if state in {"walk", "attack", "cast"} else 0
    for sign in (-1, 1):
        wing_tip = (cx + sign * wing_span, torso_y - 2 - flap if state != "hit" else torso_y + 1)
        p.poly([(cx + sign * 3, torso_y - 4), (cx + sign * 11, torso_y + 2), wing_tip, (cx + sign * 5, torso_y + 8)], c[1], INK)
        p.line([(cx + sign * 4, torso_y - 1), (wing_tip[0] - sign * 2, wing_tip[1] + 1)], c[4])

    head_x = cx + (6 if direction == 2 else -6 if direction == 1 else 0)
    head_y = torso_y - torso_h + 2
    p.ellipse((head_x - 7, head_y - 7, head_x + 7, head_y + 7), c[3], INK)
    if not back:
        beak_sign = 1 if direction != 1 else -1
        p.poly([(head_x + beak_sign * 6, head_y), (head_x + beak_sign * 12, head_y + 1), (head_x + beak_sign * 7, head_y + 3)], "d4b47a", INK)
        p.dot(head_x + beak_sign * 3, head_y - 2, INK)

    # Bird feet.
    for sign in (-1, 1):
        x = cx + sign * 4 + round(pose["stride"] * 2 * sign)
        p.limb((x, torso_y + torso_h - 2), (x, fy - 2), 2, "8a7b61")
        p.line([(x, fy - 1), (x - 3, fy + 2)], "a89167")
        p.line([(x, fy - 1), (x + 3, fy + 2)], "a89167")

    tail = [(cx - 2, torso_y + torso_h - 1), (cx + 2, torso_y + torso_h - 1), (cx + 7, torso_y + torso_h + 8), (cx - 7, torso_y + torso_h + 8)]
    p.poly(tail, c[1], INK)
    _material_strokes(p, [(cx - 5, torso_y + 1), (cx + 3, torso_y - 1), (cx + 1, torso_y + 5)], colors["body"], "feather")


def _draw_arachnid(image: Image.Image, mob: dict, state: str, frame: int, direction: int, scale: float) -> None:
    p = Pixel(image)
    size = image.width
    cx, fy = _anchors(size)
    pose = _pose(mob, state, frame, direction)
    colors = _colors(mob)
    c = palette(colors["body"])

    abdomen_y = fy - round(size * 0.20) - pose["bob"]
    ceph_y = abdomen_y - 5
    p.ellipse((cx - 12 * scale, abdomen_y - 8 * scale, cx + 12 * scale, abdomen_y + 8 * scale), c[2], INK)
    p.ellipse((cx - 8 * scale, ceph_y - 7 * scale, cx + 8 * scale, ceph_y + 6 * scale), c[1], INK)
    if "fang" in mob.get("anatomy", ""):
        p.poly([(cx - 2, ceph_y + 6), (cx - 5, ceph_y + 11), (cx - 1, ceph_y + 9)], "c7b389", INK)
        p.poly([(cx + 2, ceph_y + 6), (cx + 5, ceph_y + 11), (cx + 1, ceph_y + 9)], "c7b389", INK)
    # Eight jointed legs.
    stride = round(pose["stride"] * 3)
    for i in range(4):
        y = ceph_y + i * 2
        spread = 10 + i * 4
        bend = 5 + (i % 2) * 3
        p.line([(cx - 3, y), (cx - spread, y + bend - stride), (cx - spread - 8, y + bend + 3)], INK, 3)
        p.line([(cx - 3, y), (cx - spread, y + bend - stride), (cx - spread - 8, y + bend + 3)], c[3], 2)
        p.line([(cx + 3, y), (cx + spread, y + bend + stride), (cx + spread + 8, y + bend + 3)], INK, 3)
        p.line([(cx + 3, y), (cx + spread, y + bend + stride), (cx + spread + 8, y + bend + 3)], c[3], 2)


def _draw_insect(image: Image.Image, mob: dict, state: str, frame: int, direction: int, scale: float) -> None:
    p = Pixel(image)
    size = image.width
    cx, fy = _anchors(size)
    pose = _pose(mob, state, frame, direction)
    colors = _colors(mob)
    c = palette(colors["body"])

    y = fy - round(size * 0.22) - pose["bob"]
    p.ellipse((cx - 9, y - 6, cx + 9, y + 6), c[2], INK)
    p.ellipse((cx - 12, y, cx + 12, y + 12), c[1], INK)
    p.ellipse((cx - 7, y - 12, cx + 7, y - 3), c[3], INK)

    # Six legs and segmentation.
    for i in range(3):
        yy = y - 3 + i * 6
        reach = 8 + i * 3
        step = round(pose["stride"] * (i + 1))
        p.line([(cx - 3, yy), (cx - reach, yy + 3 - step), (cx - reach - 5, yy + 6)], c[3], 2)
        p.line([(cx + 3, yy), (cx + reach, yy + 3 + step), (cx + reach + 5, yy + 6)], c[3], 2)

    if "wing" in mob.get("anatomy", "") or mob.get("family") in {"wasp", "moth", "spore_moth"}:
        flap = round(math.sin(frame / 7 * math.tau) * 4) if state in {"walk", "attack", "cast"} else 0
        p.poly([(cx - 2, y - 8), (cx - 12, y - 16 - flap), (cx - 8, y - 2)], shade(colors["body"], 1.1, 20), INK)
        p.poly([(cx + 2, y - 8), (cx + 12, y - 16 + flap), (cx + 8, y - 2)], shade(colors["body"], 1.1, 20), INK)
    p.line([(cx - 2, y - 12), (cx - 8, y - 18)], c[4])
    p.line([(cx + 2, y - 12), (cx + 8, y - 18)], c[4])


def _draw_serpent(image: Image.Image, mob: dict, state: str, frame: int, direction: int, scale: float) -> None:
    p = Pixel(image)
    size = image.width
    cx, fy = _anchors(size)
    pose = _pose(mob, state, frame, direction)
    colors = _colors(mob)
    c = palette(colors["body"])

    y = fy - round(size * 0.18) - pose["bob"]
    sway = round(pose["stride"] * 6)
    path = [(cx - 16, y + 5), (cx - 6, y - 4 + sway), (cx + 6, y + 4 - sway), (cx + 16, y - 3)]
    if mob.get("family") in {"worm", "grave_worm", "ice_worm", "leech"}:
        p.line(path, INK, 11)
        p.line(path, c[2], 8)
        for x in range(cx - 12, cx + 13, 4):
            p.line([(x, y - 2), (x + 1, y + 6)], c[1])
    else:
        p.line(path, INK, 9)
        p.line(path, c[2], 6)
        for x in range(cx - 10, cx + 11, 4):
            p.dot(x, y, c[3])
    head = (cx + 18 if direction != 1 else cx - 18, y - 2)
    p.ellipse((head[0] - 6, head[1] - 5, head[0] + 6, head[1] + 5), c[3], INK)
    if "tongue" in mob.get("anatomy", "") or mob.get("family") in {"serpent", "viper"}:
        sign = -1 if direction == 1 else 1
        p.line([(head[0] + sign * 5, head[1] + 1), (head[0] + sign * 11, head[1]), (head[0] + sign * 13, head[1] - 2)], "cb7b78")


def _draw_crab(image: Image.Image, mob: dict, state: str, frame: int, direction: int, scale: float) -> None:
    p = Pixel(image)
    size = image.width
    cx, fy = _anchors(size)
    pose = _pose(mob, state, frame, direction)
    colors = _colors(mob)
    c = palette(colors["body"])

    y = fy - round(size * 0.19) - pose["bob"]
    p.ellipse((cx - 14, y - 8, cx + 14, y + 8), c[2], INK)
    for i in range(4):
        yy = y - 1 + i * 2
        dx = 10 + i * 3
        s = round(pose["stride"] * (2 if i % 2 else -2))
        p.line([(cx - 4, yy), (cx - dx, yy + 5 + s), (cx - dx - 4, yy + 9)], c[3], 2)
        p.line([(cx + 4, yy), (cx + dx, yy + 5 - s), (cx + dx + 4, yy + 9)], c[3], 2)
    # Claws
    lift = round(pose["attack"] * 8) if state == "attack" else 0
    p.poly([(cx - 14, y - 2), (cx - 23, y - 8 - lift), (cx - 26, y - 2 - lift), (cx - 18, y + 2)], c[1], INK)
    p.poly([(cx + 14, y - 2), (cx + 23, y - 8 - lift), (cx + 26, y - 2 - lift), (cx + 18, y + 2)], c[1], INK)
    if mob.get("family") == "hermit_crab":
        p.poly([(cx - 3, y - 12), (cx + 8, y - 14), (cx + 15, y - 8), (cx + 9, y - 2), (cx - 1, y - 4)], shade(colors["body"], 0.8), INK)


def _draw_draconic(image: Image.Image, mob: dict, state: str, frame: int, direction: int, scale: float) -> None:
    _draw_quadruped(image, mob, state, frame, direction, scale)
    p = Pixel(image)
    size = image.width
    cx, fy = _anchors(size)
    pose = _pose(mob, state, frame, direction)
    colors = _colors(mob)
    c = palette(colors["scale"])
    by = fy - round(size * 0.26) - pose["bob"]
    flap = round(math.sin(frame / 7 * math.tau) * 6) if state in {"walk", "attack", "cast"} else 0
    p.poly([(cx - 6, by - 1), (cx - 18, by - 16 - flap), (cx - 8, by + 4)], c[2], INK)
    p.poly([(cx + 6, by - 1), (cx + 18, by - 16 + flap), (cx + 8, by + 4)], c[2], INK)
    p.line([(cx - 8, by - 4), (cx - 15, by - 12 - flap)], c[4])
    p.line([(cx + 8, by - 4), (cx + 15, by - 12 + flap)], c[4])


def _draw_humanoid(image: Image.Image, mob: dict, state: str, frame: int, direction: int, scale: float) -> None:
    p = Pixel(image)
    size = image.width
    cx, fy = _anchors(size)
    pose = _pose(mob, state, frame, direction)
    colors = _colors(mob)
    body = palette(colors["body"])
    cloth = palette(colors["cloth"])
    side = direction in (1, 2)
    back = direction == 3

    bob = pose["bob"]
    stride = round(pose["stride"] * 3)
    shoulder_y = fy - round(size * 0.46) - bob
    hip_y = fy - round(size * 0.29) - bob
    head_y = shoulder_y - round(size * 0.13)

    # articulated legs
    for sign in (-1, 1):
        knee_x = cx + sign * 4 + stride * sign
        foot_x = cx + sign * 5 - stride * sign
        p.limb((cx + sign * 3, hip_y), (knee_x, fy - 10), 4, colors["cloth"])
        p.limb((knee_x, fy - 10), (foot_x, fy), 3, colors["body"])
        p.ellipse((foot_x - 3, fy - 1, foot_x + 3, fy + 2), cloth[2], INK)

    # torso + clothing
    p.poly([(cx - 7, shoulder_y), (cx + 7, shoulder_y), (cx + 9, hip_y + 2), (cx + 5, fy - 12), (cx - 5, fy - 12), (cx - 9, hip_y + 2)], cloth[2], INK)
    p.poly([(cx - 4, shoulder_y + 2), (cx + 4, shoulder_y + 2), (cx + 5, fy - 15), (cx - 4, fy - 14)], cloth[3], None)

    # arms + weapon/offhand gestures
    reach = round(pose["attack"] * 10)
    cast = round(pose["cast"] * 9)
    left_hand = (cx - (9 if not side else 4), shoulder_y + 11 - cast)
    right_hand = (cx + (9 if not side else 6) + reach, shoulder_y + 11 - cast)
    p.limb((cx - 6, shoulder_y + 2), left_hand, 3, colors["body"])
    p.limb((cx + 6, shoulder_y + 2), right_hand, 3, colors["body"])

    p.ellipse((cx - 7, head_y - 7, cx + 7, head_y + 7), body[3], INK)
    if not back:
        eye_x = cx + (2 if direction == 2 else -2 if direction == 1 else 0)
        p.dot(eye_x, head_y - 1, INK)
        p.line([(cx - 2, head_y + 3), (cx + 2, head_y + 3)], body[1])
    if "ear" in mob.get("anatomy", "") or mob.get("family") in {"goblin", "kobold"}:
        p.poly([(cx - 7, head_y - 1), (cx - 10, head_y - 4), (cx - 7, head_y + 1)], body[2], INK)
        p.poly([(cx + 7, head_y - 1), (cx + 10, head_y - 4), (cx + 7, head_y + 1)], body[2], INK)

    if "shield" in mob.get("anatomy", "") or "knight" in mob.get("family", ""):
        p.poly([(left_hand[0] - 6, left_hand[1] - 8), (left_hand[0], left_hand[1] - 10), (left_hand[0] + 6, left_hand[1] - 8), (left_hand[0] + 5, left_hand[1] + 2), (left_hand[0], left_hand[1] + 7), (left_hand[0] - 5, left_hand[1] + 2)], "768793", INK)
    if any(tag in mob.get("attacks", []) for tag in ("line", "charge", "cone")) or "sword" in mob.get("lore", "").lower():
        p.line([(right_hand[0], right_hand[1]), (right_hand[0] + 8, right_hand[1] - 12)], INK, 3)
        p.line([(right_hand[0], right_hand[1]), (right_hand[0] + 8, right_hand[1] - 12)], "b2b9bf", 2)


def _draw_construct(image: Image.Image, mob: dict, state: str, frame: int, direction: int, scale: float) -> None:
    p = Pixel(image)
    size = image.width
    cx, fy = _anchors(size)
    pose = _pose(mob, state, frame, direction)
    colors = _colors(mob)
    stone = palette(colors["body"])

    bob = pose["bob"]
    body_y = fy - round(size * 0.30) - bob
    p.poly([(cx - 10, body_y - 12), (cx + 10, body_y - 12), (cx + 14, body_y + 8), (cx + 7, body_y + 18), (cx - 7, body_y + 18), (cx - 14, body_y + 8)], stone[2], INK)
    p.poly([(cx - 6, body_y - 7), (cx + 6, body_y - 7), (cx + 8, body_y + 10), (cx - 6, body_y + 11)], stone[3], None)

    stride = round(pose["stride"] * 2)
    for sign in (-1, 1):
        p.limb((cx + sign * 6, body_y + 16), (cx + sign * (6 + stride), fy - 8), 5, colors["body"])
        p.rect((cx + sign * (4 + stride), fy - 8, cx + sign * (10 + stride), fy + 1), stone[1], INK)
        p.limb((cx + sign * 11, body_y - 1), (cx + sign * 17, body_y + 10 + stride), 5, colors["body"])

    if mob.get("family") == "tree":
        bark = palette("786544")
        for x in (-7, -2, 3, 8):
            p.line([(cx + x, body_y - 8), (cx + x + 1, body_y + 14)], bark[1])
        p.poly([(cx - 5, body_y - 18), (cx + 5, body_y - 18), (cx + 9, body_y - 9), (cx - 9, body_y - 9)], "5e7a56", INK)
    if mob.get("family") == "mimic":
        p.rect((cx - 12, body_y - 3, cx + 12, body_y + 6), "3a2e2e", INK)
        for x in range(cx - 10, cx + 11, 5):
            p.poly([(x, body_y - 2), (x + 3, body_y - 2), (x + 1, body_y + 2)], "d8c79a")
    if mob.get("family") in {"sentinel", "prism", "elemental", "geode"}:
        glow = palette(_choice(GLOW_BASES, mob["id"]))
        p.poly([(cx, body_y - 14), (cx + 4, body_y - 8), (cx, body_y - 2), (cx - 4, body_y - 8)], glow[3], INK)


def _draw_spirit(image: Image.Image, mob: dict, state: str, frame: int, direction: int, scale: float) -> None:
    p = Pixel(image)
    size = image.width
    cx, fy = _anchors(size)
    pose = _pose(mob, state, frame, direction)
    glow = palette(_colors(mob)["body"])

    bob = pose["bob"] + round(math.sin(frame / 7 * math.tau) * 2)
    center_y = fy - round(size * 0.28) - bob

    p.ellipse((cx - 11, center_y - 14, cx + 11, center_y + 9), glow[2], INK)
    p.poly([(cx - 11, center_y + 4), (cx - 7, fy - 8), (cx - 1, fy - 13), (cx + 5, fy - 8), (cx + 11, fy - 14), (cx + 8, fy - 3), (cx + 2, fy), (cx - 6, fy - 2)], glow[1], INK)

    if mob.get("family") in {"wisp", "spell_wisp", "geode"}:
        for r in (12, 17):
            points = []
            for i in range(8):
                a = i * (math.tau / 8) + frame * 0.07 * (1 if r == 12 else -1)
                points.append((cx + math.cos(a) * r * 0.5, center_y + math.sin(a) * r * 0.35))
            p.line(points + [points[0]], glow[4])

    if mob.get("family") in {"manta", "cuttle", "horror"}:
        p.poly([(cx - 18, center_y - 4), (cx - 5, center_y - 12), (cx + 14, center_y - 6), (cx + 18, center_y + 1), (cx + 4, center_y + 7), (cx - 10, center_y + 5)], glow[3], INK)
        for i in range(4):
            tx = cx - 8 + i * 5
            p.line([(tx, center_y + 6), (tx + round(math.sin((frame + i) / 2) * 2), fy - 1)], glow[1], 2)

    if "face" in mob.get("anatomy", "") or mob.get("family") in {"phantom", "wraith"}:
        p.dot(cx - 3, center_y - 4, INK)
        p.dot(cx + 3, center_y - 4, INK)
        p.line([(cx - 2, center_y + 1), (cx + 2, center_y + 1)], glow[0])


def _draw_creature(image: Image.Image, mob: dict, state: str, frame: int, direction: int) -> None:
    family = mob.get("family", "")
    size = image.width
    scale = 1.6 if mob.get("boss") else 1.0

    if family in DRACONIC:
        _draw_draconic(image, mob, state, frame, direction, scale)
    elif family in HUMANOID:
        _draw_humanoid(image, mob, state, frame, direction, scale)
    elif family in ARACHNID:
        _draw_arachnid(image, mob, state, frame, direction, scale)
    elif family in INSECT:
        _draw_insect(image, mob, state, frame, direction, scale)
    elif family in SERPENT:
        _draw_serpent(image, mob, state, frame, direction, scale)
    elif family in CRAB:
        _draw_crab(image, mob, state, frame, direction, scale)
    elif family in BIRD:
        _draw_bird(image, mob, state, frame, direction, scale)
    elif family in CONSTRUCT or "construct:" in mob.get("anatomy", ""):
        _draw_construct(image, mob, state, frame, direction, scale)
    elif family in SPIRIT or "spirit:" in mob.get("anatomy", ""):
        _draw_spirit(image, mob, state, frame, direction, scale)
    elif family in QUADRUPED:
        _draw_quadruped(image, mob, state, frame, direction, scale)
    else:
        _draw_quadruped(image, mob, state, frame, direction, scale)

    # Elite marks and boss-specific mechanics cues.
    p = Pixel(image)
    cx, fy = _anchors(size)
    if state == "attack":
        thrust = round(math.sin(frame / 7 * math.pi) * 10)
        sign = -1 if direction == 1 else 1 if direction == 2 else 0
        x = cx + sign * (8 + thrust)
        y = fy - 26
        p.line([(x - 4, y + 2), (x + sign * 7, y - 6), (x + sign * 12, y - 2)], "d4b89a", 2)
    if state == "cast":
        pulse = 3 + round(abs(math.sin(frame / 7 * math.tau)) * 4)
        for r in (pulse, pulse + 4):
            p.ellipse((cx - r, fy - 40 - r, cx + r, fy - 40 + r), (0, 0, 0, 0), "9fc5cf")
    if direction == 3:
        p.line([(cx - 7, fy - 34), (cx - 3, fy - 26), (cx + 2, fy - 21), (cx + 7, fy - 12)], shade(_colors(mob)["body"], 0.65), 2)
    elif direction == 0:
        p.dot(cx - 3, fy - 27, INK)
        p.dot(cx + 3, fy - 27, INK)
        p.line([(cx - 2, fy - 22), (cx + 2, fy - 22)], shade(_colors(mob)["body"], 1.2, 10))
    if mob.get("elite"):
        glow = palette(_choice(GLOW_BASES, mob["id"] + "-elite"))
        p.line([(cx - 9, fy - 33), (cx - 3, fy - 28), (cx + 3, fy - 32), (cx + 9, fy - 26)], glow[3], 2)
    if mob.get("boss"):
        attacks = mob.get("attacks", [])
        if "ring" in attacks:
            p.ellipse((cx - 19, fy - 9, cx + 19, fy + 2), (0, 0, 0, 0), "c4b07a")
        if "summon" in attacks:
            p.poly([(cx - 5, fy - 48), (cx, fy - 58), (cx + 5, fy - 48), (cx, fy - 43)], "c9b987", INK)
        if "interruptible" in attacks and state == "cast":
            pulse = round(5 * math.sin(frame / 7 * math.tau))
            p.rect((cx - 4, fy - 49 + pulse, cx + 4, fy - 43 + pulse), "d1a678", INK)


def creature_frame(mob: dict, state: str, frame_index: int, direction: int) -> Image.Image:
    if state not in STATES:
        raise ValueError(f"Unsupported state '{state}'.")
    if direction not in (0, 1, 2, 3):
        raise ValueError("Direction must be 0=south,1=west,2=east,3=north.")
    if not isinstance(frame_index, int):
        raise TypeError("frame_index must be an integer.")
    index = frame_index % 8
    size = frame_size(mob)
    image = canvas((size, size))
    _draw_creature(image, mob, state, index, direction)

    # Support mirrored west/east only where suitable.
    family = mob.get("family", "")
    if direction == 1 and family not in {"hermit_crab", "mimic", "phantom", "sentinel"}:
        east_image = canvas((size, size))
        _draw_creature(east_image, mob, state, index, 2)
        image = east_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    return finish_frame(image, state, index, direction)


def creature_sheet(mob: dict) -> Image.Image:
    size = frame_size(mob)
    return sheet(lambda state, frame, direction: creature_frame(mob, state, frame, direction), size=size)
