# Local client update verification — 2026-09-08

This commit publishes the existing local client edits on top of
`5a6c63357f7e7adcd18a1c7177833fadee6e7552`: inventory context-menu actions,
item-slot click callbacks, headless audio handling and stream detachment,
and one smoke stage per frame. It also records the generated InputContract UID.
The audio cleanup block received whitespace-only formatting before commit.

Local Windows checks on these edits:

- `dotnet build client/Kairnfall.Client.csproj -c Debug`: exit 0, zero warnings/errors.
- `tools/local_dev.py signals`: exit 0; native signal and input contracts passed.
- Python handoff unittest discovery: exit 0, 35 tests passed.
- `Run-Kairnfall-Client.ps1 -Smoke`: exit 0 using the existing local server and
  real NVIDIA/OpenGL display. Four fresh world/inventory/skills/map captures in
  `artifacts/local/smoke/1788836266303958500/` were inspected; no engine errors
  were reported. This does not test every context-menu action or approve art.

Logs remain local under `artifacts/local/push-client-build.log`, `push-native.log`,
`push-handoff.log`, and `push-smoke.log`. No private accounts/configuration or saves
are published. The existing user client/server was not stopped for this work.

The separate candidate `820d2d39cf097aad2d111dd206af7f9890973be1` has NOT been
integrated. Its GitHub run `34163386054` failed because the native equipment
context-menu test timed out waiting for unequip. That candidate contains a broader
redesign and different source than these local edits. Its failed gate remains
visible and must pass before candidate integration. The local checks above do not
override that failure or establish live equipment-context acceptance.

Only `main` is used. This update is not full-game, audio, artwork, multiplayer-load,
or Windows-package acceptance.
