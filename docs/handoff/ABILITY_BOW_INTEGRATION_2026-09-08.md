# Ability browser and side-facing bow integration — 2026-09-08

This commit integrates the actual seven source/test files from candidate `f565e839fc4d88f0b9d1076611ad93b0d641cd22` into the current main tree. It retains the preceding furnishing integration and all request/history records.

Full verification: run `34255660217`, verify job `102160741771`, SUCCESS.
Native graphical fixtures: run `34255660264`, render job `102160689100`, SUCCESS.

## Changes

The ability page now uses a stable two-column browser. It filters by class/shared abilities, equipped weapon, magic, learning status and element. The inspector shows the implemented effect, resources, range, effective cooldown, learning requirements and assigned hotbar keys. Cross-class requirements use the same extra twenty skill levels as server validation. Assignment controls stay outside the scrolling text. Selection, resource changes and cooldown refreshes do not replace the pressed list button.

New native input tests run from ControlRulesContract. They use real Godot pointer/key events at 1280x720 and 1920x1080. They check selection, node identity, search, empty results, hotbar assignment, foreign-class learning restrictions, weapon filtering and native panel disposal.

The side-facing bow uses the existing hand anchors. The grip lies on the bow rather than its string. Attack frames distinguish drawing, release, an empty string and reloading. The release geometry points outwards in both side directions. Five Python regression groups cover every side frame, grip contact, direction, clipping and input-data immutability. The existing player/equipment tests remain enabled. Front/back bow poses are unchanged by this repair.

Dragging a game window no longer permits its bottom actions to be pushed below the viewport.

## Boundaries

Implemented and automatically tested: YES. Graphical fixture generation: YES.
Independent image inspection in this chat runtime: not completed because the image-processing runtime was unavailable. Actual Windows DPI and hardware-input acceptance remain open. This is not full art approval, a normal first-twenty-minute playthrough, or a Windows package release.
