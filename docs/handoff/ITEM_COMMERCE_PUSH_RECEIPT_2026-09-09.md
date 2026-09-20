# Item panels and merchant selling: final verification receipt

Date: 2026-09-09.

## Source and integration

The requested runtime changes were already installed in main at `51b575323969da9c9b0fab5f3c23a7a5f0c4147e`. The earlier item-card integration is `dbd31fc4b0391045754966eb30c73fb1e4404f71`. Do not restore an older unintegrated candidate over these commits.

This final pass installs the two exact test files from passing candidate `fd1ea7c82636dc775dbdeef48f66be7f3d4967bb` on main parent `9173a909cab299e9464be2a8ec8db9ee4d5db62f`. The tested candidate is retained as an additional parent. All intervening source, Foundry and Atelier assets, request metadata and prior documentation remain intact. This receipt is the only additional file.

The final test-only repair reuses an isolated catalog's cached hunting layouts between two native merchant suites. Each suite still constructs fresh complete realm state. Added assertions verify that the catalog is separate from the game catalog and that the full creature population remains unchanged. Temporary fixture prices and stack limits are restored with their declared types. No production price, inventory capacity, gameplay rule, assertion or timeout was reduced.

## Requested behavior present

- Compact 328-logical-pixel item cards with centered names, icons, stat cells and notices. Long descriptions start collapsed.
- Separate stat comparisons with green improvements, red reductions, normal-color equality and signed numeric differences. Lower attack intervals are improvements. Affixes, runes, broken gear and removed incompatible offhands are included.
- Red actual equipment blockers. The current rules include skill requirements, death, broken items, backpack ownership and offhand compatibility. No nonexistent class or overall-level gate is invented.
- Merchant Sell quantity and Sell all for the selected stack. Typed whole quantities, plus/minus controls and both complete gold totals remain visible.
- Unsubmitted quantity text and caret survive snapshots. Invalid or excessive quantities are rejected, not silently converted.
- A successful sale waits for its authoritative inventory snapshot before allowing another request. Removing a sold stack requires explicit selection of another item. Repeated clicks cannot sell the next stack accidentally.
- Comparisons refresh when equipped affixes, runes or durability change without an item-ID change. Valuable-item confirmations remain in place.
- The server validates ownership, merchant eligibility, distance, line of sight, quantity and the gold limit. Replayed commands cannot duplicate proceeds.

Player instructions: [Item comparison and merchant selling](../ITEM_COMPARISON_AND_SELLING.md).
Prior runtime files and detailed acceptance record: [Merchant boundaries](MERCHANT_BOUNDARIES_2026-09-09.md).

## Final completed workflows

Full verification [34328343553](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34328343553) passed every stage. Verify job: `102390998192`. Diagnostic job: `102394828244`. The artifact revision file identifies `fd1ea7c82636dc775dbdeef48f66be7f3d4967bb`.

Graphical verification [34328343494](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34328343494) passed rendering and evidence upload. Render job: `102390772126`. Preview diagnostics: `102392979413`.

| Suite | Observed result |
| --- | --- |
| Client Debug compilation | Zero warnings and errors |
| Core / gameplay review / transaction security | 33 / 34 / 13 passed |
| Session and pending-status security | 5 passed |
| Real-network/PostgreSQL / save conflicts | 18 / 5 passed |
| Item comparison, merchant transactions and shutdown filtering | 7 groups passed |
| Python handoff and importer tests | 118 passed |
| Native signal lifetime and pointer/key routing | Passed |
| Native player-experience checks | 52 passed |
| Native control and layout checks | 1,142 passed |
| Live Godot/server/PostgreSQL checks | 116 passed |
| Native graphical presentation checks | 307 passed |
| Authenticated graphical smoke | Passed |

The full run retains the world, migration, gear, crafting, maintenance, density, progression and support-XP suites. The live suite uses an ordinary account and the production GameConnection. It verifies native partial-stack and full-stack sales, exact authoritative gold and removed quantities, and repeated reconnects with saved equipment and XP. Generated native input is not a human Windows playthrough.

## Evidence archives

Full-test artifact: `10095174908`, `player-experience-fd1ea7c82636dc775dbdeef48f66be7f3d4967bb`.
Archive SHA-256: `897c78094de19c676e881fd111ddaf0f3f8b37ac20ac79fd23c1d518a611548e`.

Graphical artifact: `10094946606`, `visual-review-fd1ea7c82636dc775dbdeef48f66be7f3d4967bb`.
Archive SHA-256: `458528dcf3dd2998f369c4d09cde676fd25b0f1a16d900c72783fdeb0ee281d1`.

Representative captures include `item-compare-1280.png`, `item-compare-1920.png`, `merchant-sell-1280.png`, `merchant-sell-1920.png`, `merchant-large-totals-1280.png`, `merchant-large-totals-1920.png`, `merchant-fresh-comparison-1280.png`, `merchant-fresh-comparison-1920.png`, `13-merchant-live.png` and `14-merchant-after-sale.png`. These archives are test evidence, not application packages.

## Retained failures and limits

Run `34324914335` was cancelled and is not counted as passed. Candidate `f358260120ceb98e5e09af7b35d9c2bdf489d9c2` failed compilation in run `34328033295` because a test restored a long into the catalog's int price field. That candidate was not integrated. The corrected candidate above preserves the original field type and passed every required stage.

Implemented: yes. Automatically tested: yes. Graphically rendered: yes.
Independent visual inspection in this chat: not completed because local execution tools timed out. Physical Windows input and 125%/150% DPI review: not completed. Whole-game, audio, sustained-load, measured hardware performance and Windows-package acceptance remain separate. Existing virtual-display and dependency warnings remain in logs; the zero-warning result applies to compilation.

Keep only main. Preserve local changes, credentials, saves, downloaded tools and Docker volumes. Rebuild and restart the client and server together from the current catalog before the next local test.
