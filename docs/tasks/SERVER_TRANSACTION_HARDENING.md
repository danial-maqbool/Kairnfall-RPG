# Server transaction hardening

This file defines the task. It is not a test result or completion claim.

## Scope

Work on the existing .NET 10 authoritative server and shared core. Do not replace the architecture or create a second server. Preserve the protocol, Godot client, PostgreSQL persistence, and tested economic invariants. Do not modify client, art, content roster, or deployment files.

## Required work

1. Review and repair trade consent. A ready/confirmed offer must bind the exact offered instances, quantities, rarity, affixes, sockets, rune identities, durability, and gold. Changing an offered item through socketing, extraction, equipment, consumption, crafting, bank, sale, or combat must invalidate consent or reject the mutation. A revision must not silently refer to different item contents. Preserve the existing two-stage ready/confirm UX.
2. Test private `SnapshotPackets` trade previews. Only the two participants may receive offered-item details. Never reveal full inventories, bank contents, credentials, unrelated trades, or private chat.
3. Add an authoritative `split` command. `Item` identifies an owned unequipped stack. `Amount` is the quantity split off. Require `0 < Amount < original.Quantity`, a stackable template, and a free inventory slot. Preserve quantity and generate a new unique instance ID. Make retries idempotent. Do not merge the split immediately back into the original stack.
4. Inspect command validation, replay, negative and excessive quantities, nonfinite statistics, range/cooldown/resource enforcement, loot/rune uniqueness, bank and auction races, and persistence failure behavior. Keep fail-closed semantics and acknowledge mutations only after successful persistence.
5. Add regression tests for every confirmed defect. Use isolated test state and databases, not real accounts or production data.

## Tests and report

Use `python tools/build_content.py`, the existing core regression suite, and existing network/PostgreSQL tests. Add isolated tests under `tests/Kairnfall.SecurityTests` or a non-conflicting new test directory. Record exact commands, counts, failures, and fixed defects in `docs/qa/SERVER_SECURITY_REVIEW.md`. Do not claim the whole MMORPG is secure or complete because a finite test suite passes.

## Integration

Commit cohesive working changes on this PR branch. Respect other workstreams. Merge current main only when required and preserve all unrelated changes. Do not force-push main, publish a release, change billing, enable paid services, or bypass tool restrictions. Keep the PR in draft until evidence is reviewed.
