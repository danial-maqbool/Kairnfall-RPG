"""Atelier: an independent procedural art library for Kairnfall."""

# Install the refined base-body renderer without changing the shared humanoid
# rig. All callers that use forge.folk.body_frame therefore receive the same
# renderer, including the normal build, previews, tests, and asset integration.
from . import folk as _folk
from .refined_body import body_frame as _refined_body_frame

_folk.body_frame = _refined_body_frame
