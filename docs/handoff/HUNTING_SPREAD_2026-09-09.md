# Task 2: map-wide hunting distribution

The previous planner used increasingly large arrival-centered rings. More distant map sections could remain empty even when the total census was high. The revision retains one local patch per species, then places remaining patches using a deterministic 4 by 4 stratification of the reachable, nonprotected floor bounds. A coprime sector stride visits the whole set before repeating. The existing collision, reachability, actor separation and narrow-tunnel fallback remain mandatory.

Ordinary population per original species is now 60/40/30/20/10 for region levels 0-20/21-40/41-60/61-80/81+. This is twice the previous total. Boss and elite counts remain one. Interiors, services and arrivals stay protected. Hunting revision 3 updates wild home positions while preserving pets, injuries, killed-creature timers and saves. Existing migration tests remain in place.

Added tests independently check the exact bands and 60% or greater X/Y extent across eligible broad wilderness maps. Existing seed-count, reachable-position, non-overlap, migration, respawn, motion, snapshot-size and measured tick-cost checks still execute. The final session handoff must report the measured census and tests rather than assuming a performance target from this design.
