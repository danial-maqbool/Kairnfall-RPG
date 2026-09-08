# Action presentation and native UI checkpoint - 2026-09-08

Status: tested source repair. Full visual acceptance and whole-game acceptance remain open.

## Source and integration

Reviewed base: `9c6dd629ad96c5c898ae5676b4291401b008d82a`.
Tested candidate: `dd3900bd1dcdb3baa3a7860bcdd7a306e47fa159`.
Source is integrated by the commit that adds this record. The integration copies the twelve tested source/test blobs onto main, preserving intervening CI request commits. It does not reset main to the candidate tree. No branch, pull request, release, force-push, or history rewrite is part of this pass.

The requested historical failure in run `34253608437` was the practice-ring palette assertion. By this continuation, main already contained the meaningful chalk boot/stance markings and furnished rooms. The side-facing bow and stable ability browser were also integrated in `9c6dd629ad96c5c898ae5676b4291401b008d82a`. Those repairs were retained rather than replaced with the older candidate `670948e23b94a105475645da160083359c829f8d`.

## Repairs

- Spider and quartz-spider actions now set their front legs, withdraw, strike with their fangs, and recover. Hit reactions use a separate recoil. The four leg pairs and directional projection remain intact.
- Turtle and tortoise attacks withdraw and extend the neck while the shell stays planted. The front limbs brace during the strike. Hit reactions tuck the head and limbs. Existing idle, walk, cast, and death pose offsets are unchanged.
- WorldView maps all eight action frames to the actual action duration. The old fixed 12-frame-per-second expression cut short hit reactions before their recovery frames. A corpse completes its collapse over 0.65 seconds and holds frame 7 independently of the existing retention timer.
- AbilityGuidePanel reconnects its search/filter signals after scene-tree reattachment. It uses two retained selection styles instead of allocating a new style for each ability on every snapshot refresh.
- Hotbar artwork now keeps a square aspect ratio inside each button. Button dimensions and native input behavior are unchanged.
- The objective toggle updates its plus/minus symbol when its content expands or collapses.
- Native review captures include frames 1 and 3 in addition to 0, 2, 4, and 7. Anticipation and strike frames are no longer absent from the sampled galleries.

No server damage, cooldown, movement, ownership, rewards, persistence, catalog identities, or credentials were changed in this pass. Original art source remains MIT project source. No external assets or dependencies were added.

## Verification

Exact-source full verification: run `34258153781`, verify job `102169138851`, SUCCESS.
Graphical fixture workflow: run `34258153880`, render job `102169085544`, SUCCESS.
Diagnostics were read from jobs `102170878491` and `102170396039`.

| Suite | Observed result |
| --- | --- |
| Client Debug build | PASS; zero warnings and errors |
| Core | 33 passed |
| Gameplay review | 34 passed |
| Transaction security | 13 passed |
| Session/status security probes | 5 passed |
| Network/PostgreSQL integration | 18 passed |
| Save-conflict checks | 5 passed |
| Save-migration groups | 5 passed |
| Furnishing collision/recovery checks | 7 passed |
| Python handoff tests | 94 passed |
| Native signals and input | PASS |
| Native player experience | 51 passed |
| Native control/layout/presentation rules | 601 passed |
| Native live client/server/PostgreSQL | 83 passed |
| Native graphical presentation | 126 passed |
| Asset structural checks | 45,610 passed; zero failed |
| Graphical authenticated smoke | PASS |

The new native tests exercise actual WorldView action playback, short and long durations, corpse retention, objective-button mouse input, ability search after repeated detachment/reattachment, style resource identity, and icon bounds. The Python tests verify action phases, fixed canvases, meaningful geometry changes outside the hit-flash frame, and input immutability. Tests were added; none were removed or weakened.

The Linux graphical logs retain the Xvfb VSync and cursor warnings. These runs do not establish Windows hardware input or Windows graphics performance.

## Graphical evidence

Full graphical artifact: `10068863114` in run `34258153880`.
Artifact name: `visual-review-dd3900bd1dcdb3baa3a7860bcdd7a306e47fa159`.
Artifact SHA-256: `fe77eb80b8c4493925e7e45a212a263cb5c3d35de5d6db0e899b8304b6fc7312`.

Live/verification artifact: `10068922462` in run `34258153781`.
Artifact name: `player-experience-dd3900bd1dcdb3baa3a7860bcdd7a306e47fa159`.

Sanitized preview object: `e32add0f5243c54406f8db9292f8f0856c818bed`, with `review/manifest.json` and `review/before`, `review/after`, `review/engine` PNGs. This object is evidence, not a branch or an alternative game tree. Never reset main to it.

The graphical artifact contains source contact sheets and native fixtures at 1280x720 and 1920x1080. The native contract produced 92 fixture PNGs, including equipment and creature actions, main UI pages, village and starter interiors. The separate smoke and live test artifacts contain authenticated-client captures.

Important limit: the integration owner read the source and executable test logs but could not independently open the PNG images in this chat runtime. Terminal and Python image extraction returned ClientError. Rendering and structural checks are not visual approval. Do not mark these assets visually approved without inspecting the saved images and in-game animation.

## Remaining gates

- Independently inspect the new spider/turtle actions, shortened hit reactions, and retained bow/ability changes in the saved native captures and in the running Windows game.
- Review populated HUD states, shop/dialogue/crafting layouts, and the remaining creature roster. These are not fully accepted by this bounded pass.
- Windows 125% and 150% DPI checks were not performed. Icon-bound unit checks do not replace those checks.
- A full manual beginner playthrough, two simultaneous graphical clients, audio listening, sustained load, measured client/server performance, and extracted Windows packages remain unapproved.

No Windows package, release tag, signing result, or package checksum is produced by this checkpoint.
