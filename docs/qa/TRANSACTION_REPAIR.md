# Transaction repair

## Implemented behavior

Trade readiness records a SHA-256 fingerprint of both offers. The fingerprint
covers offered quantities, complete item instances, equipped state, and whether
each participant can still pay the offered gold. Rune, affix, rarity, durability,
quantity, ownership, or equipment changes invalidate both players' readiness and
confirmation. The server increments the trade revision. An unrelated inventory
change does not cancel consent.

The server checks fingerprints after commands, after simulation ticks, and
before accepting a readiness or confirmation request. An invalidation is a
persistent state change, not an exception that restores stale consent through
transaction rollback. Both players must review and confirm the new revision.

The `split` command creates a new unique item instance. It preserves total
quantity and requires a free inventory slot. It rejects equipped items,
nonstackable items, invalid quantities, and modified equipment. Replayed requests
return the original receipt without splitting again.

## Verification

The isolated repair run completed successfully on Ubuntu:
https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34113290443

It built the solution and ran the original core, gameplay-review, real-network,
PostgreSQL, database-conflict, and extended security suites. The tested source
was committed as `79fe245094364ba997bdfb0278a6275697e8a039`.

The PR additionally requires normal Windows and Linux CI on the final source.
The temporary source-migration workflow and its write permission were removed
from the final branch. The game runtime contains ordinary checked-in C# source.

These tests establish the repaired transaction behavior. They do not establish
full-game completion, approved sprites, or a tested graphical Windows release.
