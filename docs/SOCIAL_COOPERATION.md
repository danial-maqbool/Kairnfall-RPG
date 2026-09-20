# Stronger MMO and social cooperation

Kairnfall's social layer now makes other players materially useful rather than merely visible.

## Party cooperation
- Party kill and boss credit includes nearby active supporters, not only characters that personally generated creature threat.
- Healing a party member in an active encounter records support participation, including public-event contribution.
- New loot uses round-robin party ownership. The owner receives a short exclusive window, party members gain access afterward, and the pile later becomes public.
- Party leadership can start a 45-second ready check; members explicitly mark themselves ready.
- A living party member can revive a nearby downed member. Revives restore 35% health with partial resources and temporary revive sickness, and have a server-side stamina/cooldown cost.

## Finding and keeping people
- Players can advertise an activity and role through LFG. Listings cover questing, dungeons, public events, boss hunts, exploration, and gathering.
- Requesting an LFG group creates an invitation; it never silently forces membership.
- Friend requests require recipient acceptance and friendships are mutual and persistent.
- Nearby players are remembered as recent travelers for a limited realm-time window.
- The social page exposes online status, last-seen recency, class, level, guild, nearby inspection, and visible equipment without exposing private inventories.

## Guild progression
- Guilds accumulate persistent renown through completed cooperative projects.
- Leadership can start Hunt, Adventure, Artisan, or Fellowship projects.
- Relevant member gameplay advances the shared goal. Completion grants renown, project achievements, and gold to every guild member, including offline members represented in the persistent realm state.
- Guild level is derived from renown and provides a small cooperative combat-training bonus when two or more guildmates participate together.

## Safety and authority
All membership, friendship, LFG, ready-check, revive, loot reservation, project progress, contribution, and reward decisions are server-authoritative. Historical saves remain compatible because all new fields have safe defaults.
