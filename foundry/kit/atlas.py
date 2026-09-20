"""Atlas packing.

Thousands of loose PNGs is a lot of file handles and a lot of draw calls. This
packs them onto a few pages and writes a map from asset key to rectangle, so a
client can bind one texture and blit regions out of it.

Packing is a shelf algorithm: sort by height, lay rows, start a new row when the
current one is full. It is not the tightest possible packing, but it is stable —
the same input always produces the same pages, so an atlas rebuild does not
churn the whole map.

Godot writes its own `.import` files the first time it sees a texture, so this
does not fake them. It emits the importer settings to paste into `project.godot`
instead, which is the part that actually needs saying: these are pixel sprites
and must not be filtered or mipmapped.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

PAGE = 2048
PADDING = 1

IMPORTER_DEFAULTS = """; Paste into project.godot so pixel art is not smoothed on import.
; Without this every sprite in the pack is filtered into mush at non-integer scale.

[importer_defaults]

texture={
"compress/mode": 0,
"compress/high_quality": false,
"compress/lossy_quality": 0.7,
"compress/hdr_compression": 0,
"compress/normal_map": 0,
"compress/channel_pack": 0,
"mipmaps/generate": false,
"mipmaps/limit": -1,
"roughness/mode": 0,
"process/fix_alpha_border": true,
"process/premult_alpha": false,
"process/normal_map_invert_y": false,
"process/hdr_as_srgb": false,
"process/hdr_clamp_exposure": false,
"process/size_limit": 0,
"detect_3d/compress_to": 0
}
"""


def collect(root: Path, extensions=('.png',), exclude=()):
    """Every image under root, keyed by its path relative to root.

    `exclude` skips whole subtrees by name, so a pack does not swallow its own
    atlas pages the next time it is packed.
    """
    entries = []
    for path in sorted(root.rglob('*')):
        if path.suffix.lower() not in extensions or not path.is_file():
            continue
        key = path.relative_to(root).with_suffix('').as_posix()
        if any(key == name or key.startswith(name + '/') for name in exclude):
            continue
        entries.append((key, path))
    return entries


def pack(entries, page=PAGE, padding=PADDING):
    """Shelf-pack (key, image) pairs onto pages.

    Returns (pages, placements, oversized) where placements maps key to a dict
    with page, x, y, width, height.
    """
    ordered = sorted(entries, key=lambda item: (-item[1].height, -item[1].width, item[0]))
    pages = []
    placements = {}
    oversized = []
    shelf_y = 0
    shelf_height = 0
    cursor_x = 0
    index = -1

    def new_page():
        nonlocal shelf_y, shelf_height, cursor_x, index
        pages.append(Image.new('RGBA', (page, page), (0, 0, 0, 0)))
        shelf_y = 0
        shelf_height = 0
        cursor_x = 0
        index += 1

    for key, image in ordered:
        width, height = image.width + padding, image.height + padding
        if width > page or height > page:
            oversized.append(key)
            continue
        if not pages:
            new_page()
        if cursor_x + width > page:
            shelf_y += shelf_height
            shelf_height = 0
            cursor_x = 0
        if shelf_y + height > page:
            new_page()
        pages[index].alpha_composite(image, (cursor_x, shelf_y))
        placements[key] = {'page': index, 'x': cursor_x, 'y': shelf_y,
                           'width': image.width, 'height': image.height}
        cursor_x += width
        shelf_height = max(shelf_height, height)
    return pages, placements, oversized


def occupancy(pages, placements):
    used = {}
    for entry in placements.values():
        used[entry['page']] = used.get(entry['page'], 0) + entry['width'] * entry['height']
    return [round(used.get(index, 0) / (image.width * image.height), 3)
            for index, image in enumerate(pages)]


def build(source: Path, out: Path, name='atlas', page=PAGE, exclude=()):
    """Pack `source` into `out`, writing pages, a JSON map and importer notes."""
    out.mkdir(parents=True, exist_ok=True)
    found = collect(source, exclude=exclude)
    entries = []
    skipped = []
    for key, path in found:
        with Image.open(path) as image:
            image = image.convert('RGBA')
            if image.width > page or image.height > page:
                skipped.append(key)
                continue
            entries.append((key, image.copy()))
    pages, placements, oversized = pack(entries, page)
    for index, image in enumerate(pages):
        image.save(out / ('%s_%d.png' % (name, index)), optimize=True, compress_level=9)
    report = {
        'schema': 1,
        'page_size': page,
        'padding': PADDING,
        'pages': ['%s_%d.png' % (name, index) for index in range(len(pages))],
        'occupancy': occupancy(pages, placements),
        'packed': len(placements),
        'too_large_for_a_page': sorted(set(skipped) | set(oversized)),
        'frames': placements,
    }
    (out / (name + '.json')).write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    (out / 'godot_importer_defaults.cfg').write_text(IMPORTER_DEFAULTS, encoding='utf-8')
    return report
