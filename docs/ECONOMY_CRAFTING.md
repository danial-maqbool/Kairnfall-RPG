# Economy and crafting feel

Status: implemented and repository-verified as Area 6 economy/crafting work.

The economy pass keeps the existing item IDs, combat statistics, skill gates and crafting professions, but makes the value loop easier to read and harder to exploit.

- Progression gear now consumes materials from its own grade. High-level medium/heavy armor and fittings no longer fall back to starter cured leather, and progression equipment base value is derived from its real recipe inputs.
- Common vendor-bought ingredients cannot be turned into guaranteed merchant profit by crafting and immediately reselling the output. Exceptional crafted quality can still be worth more, so mastery has upside without a deterministic gold-print loop.
- Specialist merchants, Bartering, faction reputation and item quality all improve sale quotes. The client displays the exact server quote rather than a generic base resale number.
- Bartering can train from selling as well as buying, on the same bounded cooldown.
- Inn rest and waystone travel remain inexpensive early but scale gradually with progression, destination threat and route distance. Repair and rune-extraction fees use the same shared server/client price functions shown in the UI.
- Unwanted non-unique gear with a real crafting route can be reclaimed at that route's station. Reclaiming destroys the item and returns one deterministic material stack worth less than half of the original recipe inputs. Equipped gear, socketed gear, boss signatures and regional exploration keepsakes cannot be reclaimed.
- The Crafting guide now shows material value, output base value, baseline merchant resale, the next rarity gate and a reclaim preview so players can make informed production choices.

`EconomyCraftingFeelChecks` audits progression recipe value, common vendor-crafting arbitrage, exact specialist sale quotes, scalable service sinks, authoritative/replay-safe reclaiming and unchanged rarity gate ordering in the normal world-probe suite.

## Automated evidence

Feature commit `cf35708e306c65bb8c984fcec5ddcd01a66c7328` was published only after focused workflow run `34607419224` completed successfully. The focused gate built the solution and client with zero warnings/errors, passed all six economy/crafting groups, audited 1,071 progression equipment recipes and 264 fully vendor-supplied craft loops, and passed 55,639/55,639 deterministic asset checks. Observed service references were 5 gold for early rest, 43 for the late-progression fixture, and 58/63 gold for the sampled near/far waystone routes.

This evidence establishes repository-side mechanics and numeric guardrails. Sustained human market feel, perceived material scarcity and long-session gold pacing remain playtest judgments rather than CI claims.
