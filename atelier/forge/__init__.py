"""Atelier: an independent procedural art library for Kairnfall."""

# The twelve base humanoids use Blender-authored 3D volume renders when the
# authored sheets are present. The loader falls back to the previous refined
# procedural renderer in source-only development checkouts.
from . import folk as _folk
from .blender_body import body_frame as _blender_body_frame

_folk.body_frame = _blender_body_frame
