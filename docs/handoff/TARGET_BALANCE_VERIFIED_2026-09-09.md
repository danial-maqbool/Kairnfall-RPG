# Targeting, hunting and challenge balance: verified integration — 2026-09-09

## Published implementation

Task 1 (native target-key routing) is retained at `1628b73770393980bb2d1e8017345f2f830786d7`.

The remaining density, challenge-XP, pursuit, HUD and support-reward implementation is integrated on main at:

```text
8e02613101194894186abc4a936dd99852ec7c30
```

The remote ref was fetched after the non-forced update and matched that SHA. Its first parent is the then-current main, `34716db414177f98455761c55235cb0e1edaa588`. Its second parent retains the exact tested source, `ef8073f8b0e0e210521bf980c19ca7b276c6d356`.

The comparison from the tested source to the integration contains only current `.ci` requests, the reviewed README/player-guide updates, and retained historical handoffs. No implementation or test file differs. Old failed attempts remain in history. No new branch, PR, force push, save reset, credential change, release or deployment is part of this integration.

This record supersedes the pending-status interpretation of `TARGET_DENSITY_XP_SESSION_END_2026-09-09.md`. Keep that file as scoped recovery history; do not restore its old candidate over main.

## Completed implementation tasks

### Native target routing

During active gameplay, the configured target key is intercepted before Godot GUI focus traversal. Tab selects the next eligible creature; Shift+Tab selects the previous creature. The radius is 12 tiles with clear line of sight. Corpses, companions and other regions are excluded. With no eligible creature, the stale target clears rather than transferring focus to chat. Key repeat cannot rapidly cycle the list.

Typing, open menus and binding capture retain their ordinary keyboard navigation. Selecting a creature does not send an attack or movement command. Both offline native input and authenticated live-client tests cover the actual key path.

### Denser, wider hunting distribution

Ordinary populations double relative to the preceding hunting update. The level bands now use 60 / 40 / 30 / 20 / 10 instances per original ordinary species for region levels 0–20 / 21–40 / 41–60 / 61–80 / 81+. Bosses and elites retain separate single instances.

The seeded census is 9,302 creatures across 109 regions. These are world instances, not a claim that every creature is simultaneously active or visible. One introductory patch per species stays near a safe arrival route. Later patches use deterministic sectors of reachable terrain. Coverage checks require at least 60% of each reachable map axis on eligible large wilderness maps. The earlier density record counted 20 such maps; all retained distribution assertions pass in the final source.

Doors, services, safe interiors, arrivals, reachable positions, separated actors, owned pets and existing killed-creature timers remain protected. Existing saves migrate through HuntingRevision 3. No database deletion is required. Monster health, damage, armor, aggression and loot definitions are not inflated with player level.

### Nonlinear advancement and weak-enemy practice

The complete equations and research references are in [Challenge balance](../CHALLENGE_BALANCE.md).

For current player level P, the ten-level band is floor((P−1)/10). The future overall-credit factor is 0.25 / (1 + 0.14*b + 0.035*b*b). It decreases at levels 11, 21, 31 and later boundaries. Noncombat raw skill training retains its existing formula, but its overall contribution also uses the pacing factor.

Enemy-gap penalties begin beyond a three-level allowance. A creature 20 levels below the player gives approximately 9.4% practice before the skill-mastery and class-affinity factors. It gives approximately 1.69% encounter credit before the overall pacing factor. These factors apply in sequence, not as interchangeable percentages. Fractional practice and overall credit accumulate and persist; many tiny hits cannot each receive a free whole XP point.

The implementation preserves previously earned skill XP and levels. `PracticeOnlyXp` excludes the appropriate part of future gains from overall advancement. Legacy fields default to zero. A gradual late-game mastery floor avoids stranding a character below the overall cap after all individual skills reach their caps. Tests cover that floor without a last-point jump.

Physical and spell mastery use bounded diminishing-return curves. Existing armor, elemental resistance, critical caps, vulnerability, weather and actual-health damage limits remain in force. These are original tuning choices, not a claim that all classes or progression times are optimally balanced.

### Actual-encounter support XP

A source review found that support rewards could use a high region level while the player fought a weak creature. The new `SupportTraining` helper records actual hostile contact in serializable character state.

Healing uses the recipient's most recent valid hostile contact within 15 seconds. Other support uses the caster's contact within 10 seconds. Later weak contact replaces older strong contact. Expired, missing, dead-recipient and foreign-region context grant no support XP. Valid healing still restores health without qualifying XP context. Death clears the context. Serialization, request replay and transaction rollback preserve the reward rules.

Four new server-side groups verify attribution, expiry, invalid metadata, actual casts in a high-level map against a field rat, unchanged healing without credit, and replay safety. Tests use disposable engine state, not production saves.

### HUD and bounded combat pursuit

Vitals show overall-credit pacing and the next ten-level boundary. The target frame explains skill practice and overall advancement separately. A shared vertical container now places the objective panel below the actual measured vitals height. The retained overlap test passes, including an extra wrapped-text case at both 1280×720 and 1920×1080.

The original dense-world live encounter had exposed an exhausted approach window after two accepted hits. Only a newer authoritative attack cooldown can refresh the short 2.5-tile/1.5-second approach window. A six-tile bound from the engagement origin remains. Replanning and rejected requests cannot refresh the budget. The original live encounter timeout was not extended.

## Exact-source verification read from completed workflows

Full retained run: [34307522559](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34307522559), verify job `102327315634`, diagnostics `102329480742`: SUCCESS.

Graphical run: [34307522576](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34307522576), render job `102327345430`, preview/diagnostics `102328453901`: SUCCESS.

Both workflows identify `ef8073f8b0e0e210521bf980c19ca7b276c6d356` as the tested source.

| Suite | Observed result |
| --- | --- |
| Solution and client builds | Passed; client zero compiler warnings/errors |
| Core / gameplay review / transaction security | 33 / 34 / 13 passed |
| Session and status-damage probes | 5 passed |
| Real HTTP/WebSocket/PostgreSQL integration | 18 passed |
| Save-conflict checks | 5 passed |
| Retained world, migration, furnishing, gear, maintenance and hunting checks | Passed |
| Added population/distribution assertions | Passed |
| Challenge-XP and attack curves | 9 groups; 50 exported scenarios |
| Actual-encounter support training | 4 groups passed |
| Python handoff/importer tests | 118 passed |
| Native signal lifetime and pointer/keyboard routing | Passed |
| Native player-experience fixtures | 52 passed |
| Native control/layout fixtures | 1,040 passed |
| Authenticated live Godot/server/PostgreSQL | 101 passed |
| Native graphical presentation | 197 passed |
| Authenticated graphical smoke | Passed |

The live suite checks native Tab/Shift+Tab, chat focus, non-text HUD focus, radius, line of sight, echo, no-target behavior, pursuit limits, Q dash, mana, held attacks, equipment actions, owned loot and reconnect. It is generated native input with a real server and disposable database, not physical Windows input or human playtesting.

## Warnings and acceptance limits

The smoke log included a caught shutdown warning, `Connection cleanup: ObjectDisposedException`, at `GameRoot.Lifetime.cs:32`. The process and required tests passed. This integration does not claim that the shutdown race is repaired. Keep the warning in the evidence and investigate it in a separate lifecycle task; do not suppress it merely to make a log clean. Linux virtual-display V-Sync and cursor warnings also remain distinct from compiler results.

Independent image inspection was not completed. The execution runtime failed, and the public preview PNG could not be retrieved through the available image path. Successful rendering and geometry tests are not artwork approval.

No independent coding-agent team ran. Discovery exposed customer-support agents, not an appropriate installed coding-team runtime. Separate CI jobs and specialist test suites must not be described as independent coding agents.

Long-term human progression/class balance, Windows physical input and 125%/150% scaling, audio listening, sustained multiplayer load, hardware frame-time targets and Windows package/release acceptance remain open. No whole-game completion is asserted.

## Evidence and next use

The full run retained artifact `10087434634`, named `player-experience-ef8073f8b0e0e210521bf980c19ca7b276c6d356`. The graphical run retained artifact `10087314426`, named `visual-review-ef8073f8b0e0e210521bf980c19ca7b276c6d356`. These are test artifacts, not game packages.

The source writes the 50 scenario results to `artifacts/experience/balance/xp-curves.json` and spatial coverage to `artifacts/experience/hunting/distribution.json`. Native rendered fixtures are under the graphical artifact's `engine/` directory. Source-generator sheets remain separate from the actual Atelier-backed renderer.

Fetch live main before any further edit. Pull with fast-forward only, rebuild content/art and restart client and server together. Preserve local changes, credentials, `.local`, `.tools`, `.venv`, verified partial downloads and Docker volumes. Existing inflated levels are not reset; only future rewards use the new advancement rules.
