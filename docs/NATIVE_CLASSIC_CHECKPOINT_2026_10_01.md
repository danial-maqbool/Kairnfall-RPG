# Local native Kairnfall checkpoint — October 1, 2026

This first-checkpoint record is superseded by [the continued native playable-loop checkpoint](NATIVE_CLASSIC_PLAYABLE_CHECKPOINT_2026_10_01.md), which adds grid movement, gathering, compact panels and real private PostgreSQL play/restart evidence. The older results and blockers below remain the historical record.

The current game is the native Kairnfall project at
`D:\1 - Personal\Docs\Danial\Masters\MS AI\3rd Sem\Side Projects\Kairnfall-RPG`.
This workspace's `04_game` Python/browser recreation is historical and was not rewritten.
The native client is Godot 4.7.2 .NET/C#, with an authoritative .NET 10 server and local PostgreSQL.
This checkpoint is an uncommitted working-tree change on `main`, based on HEAD
`192c8b50ce6ecac11e6327189af6208dd26c7944`, including the user's pre-existing dirty changes.
Historical CI evidence in `docs/handoff/CURRENT_EVIDENCE.json` is not evidence for this new tree.

## Implemented

- **Classic controls, enabled by default:** clicking a living, unowned creature arms that exact target.
  Moving within the existing weapon/class reach and line of sight repeats server attack intentions.
  Selection creates no chase path and never replaces the chosen target with another creature.
  Menus, chat, focus loss, death, disconnect, invalid targets, region changes, Escape and target changes cancel it.
  The existing cooldown/request gate remains authoritative. Disable classic controls in Settings to retain
  explicit attack/double-click behavior. Existing held-attack, short approach and ranged-class rules remain.
- **Contextual action:** Space/the Action button uses an available nearby object when a creature is not
  selected. E remains available. Existing gathering, loot, inspection and NPC command handlers own results.
  Space currently activates once per press; indefinite automatic gathering is not claimed.
- **Shift pickup:** an explicit Shift binding requests the existing loot command only for eligible
  piles on the player's current tile. Private foreign loot and other regions are excluded; the server
  still decides capacity, ownership, contents and rewards. E pickup remains available.
- **Compact world HUD, opt-in in Settings:** narrow overlay bars for health, mana, stamina, character XP
  and the active skill; Character/Bag/Menu remain reachable. The objective title and full tooltip remain.
  Chat, combat controls, all ten hotbar slots and other game panels are retained. The full HUD can be restored
  without reconnecting. The new layout uses existing native artwork.
- **Authoritative XP feedback:** changed snapshot XP produces an avatar popup and the active skill meter.
  A skill-up combines its level and XP in one popup, avoiding overlapping text. It neither invents rewards
  nor adopts unverified production XP curves or daily bonuses.
- **Local login boundary:** the native login accepts only localhost/loopback HTTP or HTTPS addresses.
  Nonlocal, embedded-credential, query and malformed addresses are rejected before connection creation.
  A saved nonlocal address is not used as the login field's default. Shared transport/protocol is unchanged.
- **Existing fixture repairs:** reflection calls now include the current optional animation argument.
  Ranged-combat tests reacquire authoritative state after rejected actions restore a copy. Cooldown,
  damage, invalid-target and duplicate-hit assertions were retained.

## Verification

The solution and native client compiled with `--no-restore`; no package download was needed.
The client retains one pre-existing CS8793 warning in `PlayerExperienceContract.cs`.

| Check | Result |
|---|---|
| Core gameplay | 41 passed, 0 failed |
| Gameplay review, without database | 34 passed, 0 failed |
| Security/transactions | 13 passed, 0 failed |
| New classic native fixture | 56 checks passed; engine error scan clean, including Shift tile/ownership checks |
| Retained native controls | 1,184 checks passed; engine error scan clean |
| Retained player experience | 447 checks passed; engine error scan clean |
| Native input routing | Passed; engine error scan clean |
| Windows layout/accessibility emulation | 1,639 checks passed; engine error scan clean |
| XP HUD acceptance | 9 checks passed; engine error scan clean |
| Character presentation | 177 checks passed with graphical rendering; engine error scan clean |

Native QA uses a copied client project named `Kairnfall-Classic-QA`; the fixture asserts its user settings
are separate from the normal application. It uses in-memory realm snapshots, not personal game accounts.
An initial original-project fixture run preceded that isolation correction and may have exercised ordinary
HUD preferences; preservation claims apply to gameplay saves, not a captured pre-test UI-preference snapshot.
The retained native batch passed before the late Shift addition. After that small binding/loot change,
the affected classic fixture and native input-routing contract were rebuilt and rerun successfully.
The character contract was initially invoked headless by the QA wrapper, rejected that mode as required,
and subsequently passed its graphical rerun; the failure was not ignored or treated as a pass.

Real rendered PNGs were inspected at 1024×720, 1280×720 and 1920×1080. The compact bars, navigation,
hotbar and restored expanded mode fit. Inspection found overlapping XP text in the first iteration;
the final frame shows a single readable skill-up popup. These are native fixtures, not live account play
or independent human approval of all artwork.

Evidence is in the MysteraLegacyLocal workspace:

- `scratch/native_classic_results/native-results.json` and per-fixture logs.
- `scratch/native_classic_results/frames/01-expanded-hud.png`.
- `scratch/native_classic_results/frames/02-compact-1024.png`, `02-compact-1280.png`, `02-compact-1920.png`.
- `scratch/native_classic_results/frames/03-authoritative-xp-feedback.png`.
- `scratch/native-classic-core-final.log`, `native-classic-gameplay.log`, `native-classic-security.log`.
- Prepared-file manifests and exact pre-edit source bytes in `scratch/native_classic_checkpoint/`,
  `native_classic_verification/`, `native_classic_final_fixes/`, and `native_offline_boundary/`.
  The late observed Shift control has its separate `scratch/native_shift_pickup/` byte-exact backup.

## Blockers and fidelity gaps

Docker's Linux engine is stopped: `docker info` fails because the `dockerDesktopLinuxEngine` pipe does not
exist. The server requires PostgreSQL. Consequently local account login, a real HTTP/WebSocket playthrough,
PostgreSQL reconnect/restart, and durable save reload could not be freshly verified. Docker was not started
to avoid implicitly starting unrelated services. This checkpoint is not a claimed complete playable release.

The tested in-memory suites cover movement/collision, gathering, inventory/equipment, crafting/building,
combat/rewards, progression and state serialization. Those checks do not replace the blocked database tests.

Observed Mystera reference and remaining differences:

| Observation | Current checkpoint / remaining gap |
|---|---|
| Centered player, camera follows | Already native; existing local motion changes preserved |
| Grid/tile arrow movement | Kairnfall remains continuous movement; grid timing was not invented |
| Click target, move adjacent, automatic attack | Added using existing class/weapon reach and authority |
| Facing + Space/action circle | Contextual Space added; current proximity/facing rules and rectangular action button remain |
| Stand on drops + Shift | Added through existing loot authority; live account verification remains blocked |
| Hold/release Space to continue mining | Not yet implemented; single-press gathering remains |
| Inventory right overlay, 15 slots/page, Drop/Use/Drop Amount | Existing native inventory/merchant panels retained; this exact layout remains a gap |
| Player green/enemy yellow HP, white damage/red hit pixels | Target selection and damage feedback already exist; this exact color treatment remains a gap |
| Thin overlay health/food/XP HUD | Compact overlay added; this server has mana/stamina, not a verified Mystera food model |
| Active skill XP, floating skill-up | Added from actual snapshot changes; timing/progression remains Kairnfall's |
| Dense stippled grass, layered tree crowns, small avatar and spawn pad | Existing original Kairnfall art/layout retained; close visual parity remains incomplete |
| Rat/tutorial sign quests, daily 20% bonus | Not copied as canonical mechanics; session-specific balance and tutorial semantics remain unverified |
| Build & Craft overlay, 3×5 icons, selected sprite/name and Craft/Info | Directly observed reference; native searchable recipe/inspector layout differs |
| Stone Pickaxe: 10 Stone + 5 Wood, Damage +4, mining use | Directly observed reference; no Stone Pickaxe template exists in the current native catalog |

Late crafting reference: the crossed-tools control opens an approximately 195×397 pixel translucent
Build & Craft panel with an upper-right X, a 3×5 icon grid and selected-item Craft/Info controls.
Missing materials dim Craft, and Info writes the recipe, damage and use into the top-left feed.
Unidentified bottle/rope-like icons remain unidentified. Holding Space at a pine temporarily labels
the XP bar Chopping; the final resource/building lifecycle is still not fully observed.

The current native starter `make_copper_pickaxe` recipe uses one copper bar, one cured leather and one
oak plank at a workbench; it is not the observed Stone Pickaxe recipe. The native crafting inspector
already displays owned/required ingredient quantities and disables Craft on missing requirements.
No existing recipe cost, template ID, item stat, save or server rule was rewritten from this observation.

No proprietary game code/assets were extracted. No original raw/reference corpus was changed.
No game save was deleted, reset, migrated or tested destructively. The historical character save/backup
sizes and timestamps remain unchanged. Native database volumes were never opened or modified by these checks.
No service outside the game was restarted, and there was no commit, push, deployment, release or history rewrite.

## Next bounded acceptance step

Once the local Docker engine is available, use the existing isolated test database and graphical
`tools/run_live_experience.py` runner. Verify a real single-click/approach/attack, gather→craft→equip,
build placement, death recovery and PostgreSQL restart/reconnect without touching development saves.
Keep classic and explicit controls separately covered. Further tile movement, hunger, tree/terrain art,
quests and action-circle changes need additional observed reference and a reviewed implementation scope.
