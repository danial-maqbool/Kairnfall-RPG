# Task 1: native target-key routing

The reported Tab defect is caused by GUI focus traversal consuming the key before GameRoot._UnhandledInput. Handle only the configured target key in _Input when GameplayInputAllowed is true. Text, menus, rebind capture, disconnect and death keep their normal priority. Key-repeat is consumed without repeatedly changing target. Deliberate selection uses a 12-tile radius with line of sight; neutral animals can be selected, but pets and corpses cannot. No selection issues an attack request. Empty selection clears the stale target and uses the existing debounced notification.

Primary reference: https://docs.godotengine.org/en/stable/tutorials/inputs/inputevent.html — _Input precedes GUI event handling; _UnhandledInput runs after GUI handling. This is the reason for the narrowly scoped interception, not a reason to move all gameplay input before the GUI.

TargetKeyChecks uses native events with an authenticated client and an explicitly substituted offline scene snapshot. The remaining live test still uses the real network realm. Check the final session handoff for exact pass/fail results. Do not mark physical Windows input or human playtesting accepted from this fixture.
