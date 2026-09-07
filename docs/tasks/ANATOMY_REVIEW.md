# Creature anatomy and animation repair

This is an implementation and rendered-review task. A passing sprite-count test
is not art approval. Read AGENTS.md, content_src/mobs.py, tools/art/creatures.py,
tools/build_assets.py, tools/art/common.py, and the renderer's frame contract.

## Ownership

Edit tools/art/creatures.py and creature-specific helper modules, creature art
tests, and docs/qa/ANATOMY_REVIEW.md. Do not change game IDs, creature counts,
server code, client code, workflow permissions, or the asset-builder public API.
Other integration work continues on the client and server branches.

## Required corrections

The current implementation needs actual distinct physical forms, not only
palette differences. An owlbear must show a hooked beak, feathered facial disc,
and bear anatomy. A moth must have antennae, six legs, and moth wings, not a bird
beak or bird feet. A snail must show its spiral shell, muscular foot, and eye
stalks. A crocodile needs a long jaw, armored dorsal ridges, splayed feet, and a
heavy tail. Quadrupeds need meaningful differences in muzzle, torso, gait, feet,
ears, horns, and tails. North-facing sprites must show the back, not a face with
extra lines. Bosses need unique native-resolution forms, not enlarged ordinary
sprites with identical ornaments. Remove repeated hit/death transformations.

Preserve the current native public frame function used by tools/build_assets.py.
Normal/elite frames are 64 pixels square and boss frames are 128 pixels square.
There are eight frames, six states, and four directions. Preserve alpha, nearest
sampling, consistent foot anchors, and deterministic generation. Keep all
required attack, cast, hit, and death animations. Do not reduce coverage or use
missing-asset fallbacks to make checks pass.

## Review and test

Generate the catalog and assets. Render contact sheets for every normal species,
all bosses, and representative complete animation strips. Open the actual PNG
images with a visual tool available in the worker runtime. Inspect native size
and integer zoom. Repair anatomical errors, clipping, frame drift, and muddy
materials. Check that each normal species has a distinct silhouette where its
anatomy demands one; adding a random pixel does not establish visual uniqueness.

Run tests for all frame dimensions, nonempty alpha, safe borders, determinism,
state/pose changes, and renderer API compatibility. Record exact commands,
result counts, image paths actually opened, inspected defects, and corrections
in docs/qa/ANATOMY_REVIEW.md. State plainly if an image viewer was unavailable.
Do not claim a visual review without opening images. Do not call the full game
complete. Commit the actual repair and evidence to this branch. Do not merge or
publish a release. Use only existing authorized tools and allowance.
