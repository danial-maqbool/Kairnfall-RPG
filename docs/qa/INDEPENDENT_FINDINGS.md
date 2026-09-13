# Task 13 adversarial acceptance findings

Status date: 2026-09-13  
Technical implementation baseline: `3dce816eade22c93a8dad65eee6964be3e12fd52`  
Unchanged product/client/art baseline: `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f`

## Integrity boundary

This record is a same-agent adversarial acceptance review performed while implementing Task 13. It is **not an independent approval**. The retained requirement that independent or subjective human review cannot be replaced by the implementation agent remains in force.

The review added a permanent `tests/IndependentQA` executable and the `Task 13 adversarial acceptance` workflow. It also reruns retained security, malformed-input/gameplay, world, concurrency, PostgreSQL/network and isolated save-conflict suites. Windows runs the same Task 13 executable through `Test-Kairnfall.ps1`.

## Initial findings

### T13-001 — audit assertions retained stale state objects after rollback

- Severity: **Medium — test/evidence defect; no production gameplay defect established**.
- Initial source SHA: `fe673d159168e673093e9f5a4a1a37f9167eaec9`.
- Reproduction: run `Build and verify` on Windows at that SHA. Three new assertions failed in bank identity, invalid-auction atomicity and respawn state.
- Expected: assertions inspect the authoritative post-command state.
- Actual: the audit retained pre-command `Character`/`Item` references. `RealmEngine.Execute` replaces `State` with a deep rollback snapshot after rejected commands, so those references become stale.
- Repair: `ed45f63235833e3e06b630b8c922c29695ad2d0d` reacquires authoritative actors through the engine before sequencing and post-rejection assertions.
- Retest: **PASS**. Windows run `34768386855` reports `TASK13_ADVERSARIAL_RESULTS passed=10 failed=0`; Linux Task 13 run `34768390034` also passes all scenarios.

### T13-002 — workflow title overstated independence

- Severity: **Low — evidence-label integrity**.
- Initial source SHA: `fe673d159168e673093e9f5a4a1a37f9167eaec9`.
- Reproduction: inspect the initial workflow display name `Independent adversarial acceptance`.
- Expected: same-agent work must not be presented as independent approval.
- Actual: the title could imply independence even though the implementation agent authored the tests and fixes.
- Repair: `3dce816eade22c93a8dad65eee6964be3e12fd52` renames the permanent gate to `Task 13 adversarial acceptance` and uses neutral Task 13 artifact/log labels.
- Retest: **PASS**. The corrected workflow is run `34768390034`.

### T13-003 — current evidence ledger became stale after Task 13 implementation

- Severity: **Expected documentation sequencing gate**.
- Reproduction: documentation contract at the first Task 13 implementation SHA rejected the prior implementation baseline.
- Expected: current-facing evidence must fail closed whenever a non-documentation implementation commit advances.
- Actual: the old ledger correctly became stale.
- Repair: this Task 13 evidence update records the verified technical baseline only after technical runs succeeded.
- Retest: final delivery-head documentation workflow must pass before Task 13 is complete.

## Permanent adversarial scenarios added

`tests/IndependentQA/Program.cs` now verifies against the real authoritative engine:

1. forged bank ownership is rejected and deposit/withdraw preserves unique item identity;
2. zero, negative and excessive auction quantities fail atomically;
3. forged auction ownership fails without charging the attacker;
4. auction escrow transfers exactly once and request replay cannot duplicate item/gold movement;
5. private trade snapshots are participant-only and detached from authoritative item state;
6. map transition cancels active private trade state;
7. death blocks mutations until authoritative respawn restores valid walkable state;
8. stale group commands fail while valid party leave cleans private trade state;
9. active trade and auction identities survive state serialization without duplication;
10. an ignored LFG requester cannot force party invitation state.

## Retest results

At `3dce816eade22c93a8dad65eee6964be3e12fd52`:

- `Task 13 adversarial acceptance` run `34768390034`: **success**. New Task 13 scenarios, transaction/privacy security, gameplay/malformed-input review, world/persistence/social, concurrency, PostgreSQL/network and isolated save-conflict checks all pass.
- `Build and verify` run `34768386855`: **success** on both Linux and Windows. The Windows log explicitly records `TASK13_ADVERSARIAL_RESULTS passed=10 failed=0`, `SECURITY_RESULTS passed=13 failed=0`, and the retained concurrency stress passes.

No production gameplay code was changed by Task 13 because the adversarial run did not establish a production defect.

## Retained unchanged-baseline client, package and rendered evidence

Task 13 changed test/evidence infrastructure, not client gameplay/art/package source. The latest verified product/client baseline remains `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f`:

- Windows display/input run `34766727800`: success.
- Visual acceptance matrix run `34766729859`: success.
- Compile Windows client source run `34766713586`: success.
- Windows package acceptance run `34766725549`: success.
- Graphical multiplayer acceptance run `34766723424`: success.
- Live progression breadth run `34766721059`: success.
- Load acceptance run `34766715225`: success.
- Transaction security run `34766717227`: success.
- Windows/Linux transaction integrity run `34766719055`: success.
- Audio acceptance run `34766731782`: success.

The retained visual artifact for run `34766729859` contains the required creature/player/equipment/environment/NPC rendered sheets and objective structural coverage, but its own manifest keeps `visual_approval`/artistic review unresolved. Counts and contact sheets are not artistic approval.

## Human-only remainder

The repository-side Task 13 adversarial engineering gate is complete when its delivery-head workflows are green, but these remain outside same-agent automated approval:

- independent human adversarial/gameplay approval if the project requires an independent reviewer;
- subjective gameplay/progression/economy feel;
- independent visual/artistic approval;
- audio listening approval;
- full ordinary-account exploratory traversal;
- physical Windows monitor/DPI/input inspection;
- owner-machine package acceptance where required;
- production-scale capacity claims beyond the retained reference CI workload.

**NOT APPROVED — human acceptance remains.**
