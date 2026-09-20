# Task 20 — Dynamic World Events

Task 20 deepens the existing eight-family public-event system instead of adding new overworld land or duplicating event templates.

## Director hardening

- The deterministic director refuses regions that already contain an active event or its temporary aftermath/reset window.
- If multiple eligible regions are available, an eligible region containing an active player is preferred before the normal deterministic rotation is used.
- The existing global cap of three active events remains unchanged, preserving bounded simulation and network cost.

## Participation and economy safety

- Event rewards still use server-authoritative contribution recorded from combat damage, kills, gathering, caches, support interactions, and escort presence.
- A small absolute meaningful-contribution floor prevents tag-and-leave farming.
- Eligibility does not depend on a percentage of the leading player, so late arrivals can qualify through a meaningful objective action.
- Existing tiered rewards, `Rewarded` duplicate protection, inventory/bank fallback, reputation, achievements, and progression remain authoritative.

## Persistence and reset

Automated regression coverage explicitly proves:

- deterministic scheduled start;
- occupied-region preference and no overlapping event placement;
- success and failure cleanup;
- multiplayer contribution scaling;
- low-effort reward rejection and meaningful late-help eligibility;
- active-event state surviving a server restart;
- disconnected contributors retaining earned credit;
- reconnect/restart not duplicating rewards;
- completed event aftermath expiring and resetting cleanly.

The current overworld footprint remains unchanged. No publication, public release, production realm, tag, or production infrastructure is authorized by this task.
