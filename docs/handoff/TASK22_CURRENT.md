# Task 22 current state

Status date: 2026-09-15. Implementation baseline: `d83aa0f9d09a081cd5ebe7f43fe2e2ed9c34baec`. Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

**NOT APPROVED — human acceptance remains.**

Task 22 is repository-side complete. Five existing city factions now expose deterministic daily endgame contract boards through their existing guild registrars, with three contracts per faction per world day and no map expansion. The rotation reuses established elite hunts, gathering, crafting, dungeon, boss, and public-event content instead of adding arbitrary factions or new overworld regions.

Contract acceptance, objective progression, claims, reputation, milestone rewards, persistence, replay protection, and abandonment are server-authoritative. Rewards are idempotent per rotation, reputation is capped at 1,000 with exactly-once rank milestone bonuses, and world-probe coverage exercises persistence, rotation, anti-duplication, and the unchanged map footprint.

All ten functional workflows triggered at the exact implementation baseline passed. Windows client source run `34885269419` passed after repairing the Task 22 claim callback; Windows package acceptance run `34885269513`, Build and verify run `34885269413`, and both transaction-security workflows also passed. The pre-sync Documentation evidence contract run `34885269511` failed as expected because current evidence still identified Task 21 before this synchronization.

Historical Task 21 evidence is preserved at `docs/handoff/TASK21_EVIDENCE.json`. Publication and deployment remain unauthorized.
