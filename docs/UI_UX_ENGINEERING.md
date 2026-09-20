# Task 12 — UI/UX engineering cleanup

Scope: Task 12 only. Task 13 was not started. These are objective engineering
checks, not subjective usability, visual-quality, art, combat-feel or playtest approval.

## Defects and repairs

The resumed baseline was `487c7d4007731e8f18d3a3b5cb268452321fcb23`, fetched from
GitHub before editing. Its failing workflows were documentation evidence,
Windows display/input, visual presentation and live progression breadth.

- Modal cleanup ran on a later physics tick, leaving an input blocker alive after
  closing. Opening and closing now synchronously update modal state, hide controls
  before deferred deletion, restore eligible focus, and cancel unfinished rebinding.
- The blocker was inserted after the page. Godot GUI picking follows tree order,
  independently of visual Z-index. The blocker now precedes the active page.
- Page minimum sizes and later container layout could move the window beyond the
  viewport. Layout uses actual window bounds and a shared overflow scroll container
  below the fixed title/Close row. Both outer and existing inner scroll containers
  follow keyboard focus. No page content or acceptance assertion was removed.
- Context actions rendered below the modal and lost the previous focus target.
  They now render above the page, restrict keyboard traversal while open, restore
  valid item focus, and dismiss immediately when their owner closes or item disappears.
- Purchase/reclaim confirmations now belong to their page, so a page transition
  also disposes its pending confirmation. Returning to a frontend screen closes
  the previous page and its blockers.
- Key capture now precedes GUI activation when rebinding, so reserved Enter is
  rejected rather than activating the focused button. Unhandled Enter cannot
  focus background chat through an open page. HUD shortcut labels follow bindings.
- Malformed or non-finite text-scale settings fall back to 100%. Valid bounded
  scales still restore. Fullscreen choice is saved and restored on startup.

The live regression previously pressed Space while the new default Close button
held focus. Closing was correct GUI behavior. The fixture now explicitly releases
GUI focus for its gameplay-isolation check and asserts Inventory stays open;
separate native tests still exercise focused activation and real mouse closing.
Movement, action-sequence and server equipment assertions remain intact.

The first implementation CI cycle also exposed an unchanged interaction fixture
that steered onto resource centers. A copper node at (28.5, 52.5) coincides with
the starter-building-2 doorway; leaving that position could enter the building,
depending on the sampled position. The fixture now matches the actual client's
2.15-tile, clear-line-of-sight interaction approach. Server-validated gathering,
crafting, quest, bank and auction assertions, the navigation timeout and the
unexpected-zone assertion remain intact. Gameplay, content and pathfinding were
not changed. A tighter waypoint tolerance alone was tested and did not solve the
failure; that attempted change was removed. Bounded movement diagnostics remain
in navigation failures.

An initial live reconnect XP equality assertion failed once and passed unchanged
on rerun. Its equality requirement remains intact, with per-skill before/after
diagnostics added for any recurrence. No persistence repair is inferred from a rerun.

## Permanent regression coverage

`client/Tests/WindowsScaleContract.cs` exercises actual native input with:

- Modal mouse ordering, immediate blocker release, Tab navigation, disabled focus
  restoration, reserved-key capture and Escape cancellation.
- Item keyboard activation, nested context-menu navigation, Escape restoration,
  removed-item cleanup and owner-page closure.
- Malformed/valid text settings, settings serialization round trip and updated
  shortcut discovery.
- 125%/150% window content-scale emulation at 1280×720 and 1920×1080.
- All 19 existing pages at the 1024×720 minimum with 90%, 100%, 115% and 125% text.
  Every page must fit, retain a reachable Close button, follow focus in overflow,
  and close through generated native mouse input.

Existing control, inventory/comparison, crafting, quest/journey, merchant,
social/party/guild/LFG, target/death, minimap, chat, HUD, tooltip, runtime and package
contracts remain enabled. The shared changes do not change server rewards,
transaction consent or save formats.

During local repair on Godot 4.7.2 .NET / Windows, the expanded Windows contract
passed 393 checks; control rules passed 1,160; player experience passed 52; XP HUD
passed 9; graphical presentation passed 307; live experience passed 117 against a
fresh isolated PostgreSQL test schema. The input contract also passed.
The corrected real-network integration driver passed all 20 checks on a fresh
isolated schema, including the gather/craft/quest chain and hard-restart persistence.
Native logs were checked for engine errors, and rendered Inventory/Crafting frames were inspected
for control bounds. Earlier local runs with stale asset imports were not accepted;
assets were rebuilt/imported before the successful runs. CI is the exact-revision
authority for the final integrated implementation.

## Evidence and remaining human evaluation

Implementation and exact-revision workflow evidence are recorded in
`handoff/CURRENT_EVIDENCE.json` and `handoff/VERIFICATION.md`.
The transaction-integrity workflow now permits manual dispatch so documentation-only
delivery commits can receive fresh exact-head evidence without touching source or
weakening its Windows/Linux matrix.

Physical monitor DPI, hardware-specific focus/input, subjective readability,
usability, art, audio and normal-play feel remain human evaluation. Content-scale
emulation and rendered fixtures do not establish those approvals.

**NOT APPROVED — human acceptance remains.**


## First-hour cohesive page-profile pass

The shared `PageLayoutProfiles` table now drives the real modal window geometry rather
than remaining dead configuration. Each page publishes a concise purpose summary through
the native tooltip/accessibility surface while retaining Task 12 modal blocking, focus
return, overflow scrolling, keyboard activation and error-prefix behavior.

Permanent Windows coverage now exercises every existing page at 1024×720, 1280×720,
1920×1080 and 2560×1440 across 90%, 100%, 115% and 125% UI text, plus 125%/150%
content-scale emulation for HUD, Inventory, Crafting and Map. Rendered visual review also
includes 2560×1440. Physical monitor DPI and subjective usability remain human-only gates.
