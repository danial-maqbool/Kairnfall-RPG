# New-player experience — journey and early retention

Status date: **2026-09-16**. Verified implementation baseline: **`7b11027ba913781443871ece56c8ab13008408d5`**. Evidence authority: `docs/handoff/CURRENT_EVIDENCE.json`. Release status: **NOT APPROVED — human acceptance remains.**

The opening is designed to make the intended first roughly 15–30 minutes legible and rewarding, then hand the player into the existing persistent world. Automated fixtures prove reachability, authority, persistence and UI behavior; they do not measure an uncoached human's completion time or retention.

## Coherent opening sequence

1. **Meet Bren Gale.** A fresh, version-eligible character receives a clear first objective in the existing shared starting area. The dialogue and objective presentation name the action and preserve normal movement/interact controls.
2. **Fight two Field Rats.** Combat progress comes from server-owned kill credit rather than attack/cast attempts. Class-aware action guidance remains compatible with all eight classes, and death/respawn does not strand the sequence.
3. **Receive a deterministic useful upgrade.** Successful authoritative combat completion grants exactly one class-compatible Rare Roadwarden weapon with one socket, plus the potion ingredients needed for the craft lesson. The eight reward catalog identities are distinct: Roadwarden's Longsword (Vanguard), Greataxe (Berserker), Recurve (Ranger), Dirk (Rogue), Focus Staff (Arcanist), Thornstaff (Warden), Flanged Mace (Templar), and Arming Sword (Spellblade).
4. **Equip it deliberately.** The player uses the normal Inventory/equipment action; the reward is never silently auto-equipped. Until the equip milestone is safely recorded, the mandatory opening reward is protected from destructive or transferable paths that could make the sequence unrecoverable.
5. **Craft a useful consumable.** The opening supplies the ingredients and routes through the ordinary crafting system to brew Healing Potion recovery consumables. The craft milestone is authoritative and survives reconnect/restart.
6. **Return and hand off to the world.** The final Bren interaction closes the bounded opening and restores the broader existing journey: legitimate quests, travel, progression, social tools and optional shared-world activity rather than a separate tutorial instance.

This sequence is intentionally deterministic at the teaching moments that would otherwise create early confusion. It does not replace normal combat, inventory, equipment, crafting, quest, persistence or world systems with a parallel tutorial economy.

## Recovery, ordering and exactly-once behavior

Opening state is stored through server-owned, versioned character markers. A fresh eligible character can disconnect, reconnect, restart the realm process, die/respawn, or perform valid milestones out of the expected presentation order without losing authoritative progress. Historical characters are not reset or retroactively enrolled, and historical `first_hour` markers remain readable.

The reward transaction is atomic. When the inventory is full, the grant fails without partially consuming the milestone or duplicating items; the player can make space and retry. Replay/reconnect cannot duplicate the class reward. Pending mandatory equipment remains recoverable until the equip milestone is established. Client hint acknowledgements remain presentation-only and cannot manufacture reward, XP, quest, event or progression credit.

All eight classes execute the same conceptual sequence while receiving a compatible weapon identity and class-appropriate combat guidance. The permanent opening probe also covers full inventory, replay, reconnect/restart, out-of-order milestones, protected pending reward, death recovery and established-character exclusion.

## Early progression and multiplayer visibility

The first upgrade is visible because it is an actual class-usable Rare item and the player performs the equip action. Normal derived-stat comparison, equipment UI and progression feedback explain why an item is usable rather than introducing a fake tutorial power score. The potion craft produces an ordinary useful recovery item through the existing recipe path.

Kairnfall's persistent multiplayer nature is surfaced without requiring another human to be present. Existing nearby-traveler/social controls remain visible and truthfully report an empty area when appropriate. Existing chat, parties, friends, group finding and shared public activity remain discoverable, and the handoff points back into the normal shared-world route. No fake player, forced group member, separate tutorial shard or requestable reward event is created.

## UI and accessibility

The opening uses the existing HUD and modal architecture. Semantic quest action controls (`QuestAction_<quest-id>`) support native automation and keyboard/focus testing. Page-specific layout profiles drive the real modal dimensions while retaining Task #12 protections: modal input blocking, focus suspension/restoration, overflow scrolling, Escape behavior, keyboard activation, text scaling and non-color-only error feedback.

Permanent Windows acceptance covers 1024×720, 1280×720, 1920×1080 and 2560×1440, supported text scales, additional content-scale emulation, keyboard/mouse input, focus recovery, stale-state dismissal and malformed setting recovery. Physical-monitor DPI and subjective readability remain human gates.

## Verified automated evidence

Exact-head New-player journey run **`35103673241`** at `7b11027ba913781443871ece56c8ab13008408d5` passed:

- `NEW_PLAYER_JOURNEY: 12/12 groups passed`;
- `OPENING_JOURNEY_CHECKS: 5/5 groups; classes=8/8`;
- native `PLAYER_EXPERIENCE_CONTRACT`: **442** checks;
- native `CONTROL_RULES_CONTRACT`: **1,169** checks;
- real-server/PostgreSQL `LIVE_EXPERIENCE_CONTRACT`: **125** checks.

The exact-head artifact is `new-player-journey-7b11027ba913781443871ece56c8ab13008408d5` (artifact `10450286172`, 2,122,591 bytes, SHA-256 `ede37346a70897518559747eb008068676ed44bc885d996573116afa0571242d`). These are machine acceptance results, not evidence that a new player will personally finish in twenty minutes or that retention improved.

## Boundaries

This pass adds **zero new overworld regions** and does not deploy or publish anything. It adds eight deterministic class-specific opening reward identities and the single authored opening content module while preserving server authority and old-save compatibility. Existing later-world systems remain behind their normal prerequisites.

Human-only release gates still include uncoached first-hour usability/timing and retention measurement, normal-play balance/class feel, independent artistic review, audio listening approval, ordinary-account world walkthrough, physical Windows DPI/hardware input, owner-machine package launch where required, and production-scale validation before making any public capacity claim.
