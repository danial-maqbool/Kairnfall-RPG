"""Atelier: an independent procedural art library for Kairnfall."""

# The twelve base humanoids use authored 2D pixel sheets when those sheets are
# present. The loader falls back to the pure 2D illustrated renderer in
# source-only development checkouts.
from . import folk as _folk
from .authored_body import body_frame as _authored_body_frame

_folk.body_frame = _authored_body_frame
