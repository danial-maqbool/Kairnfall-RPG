# Skill guide redesign

## Problem

The old Skills window repeated training text and bars for all 60 skills in a single long list.
Its periodic snapshot refresh rebuilt that list. Browsing and comparing skills required repeated scrolling.

## Design

The new browser separates category navigation, skill selection, and one detailed skill explanation.
Categories are Combat, Magic, Defense, Gathering, Crafting, and Utility.
These are presentation groups. They do not rename persistent skill IDs or change XP formulas.
The original skill definitions still provide training and benefit text.

The detail view shows the actual current level, exact XP progress, class affinity, and upcoming catalog unlocks.
Equipment, recipe, and ability requirements determine the unlock list.
Cross-class abilities retain the server's additional 20-level requirement.
No synthetic rank or unimplemented item is invented for an unlock message.
A missing catalog unlock is reported explicitly.

Snapshot refresh updates existing navigation buttons. It does not recreate the scrolling list.
Search and category changes rebuild the list deliberately. Existing selection is retained when it still matches.
The detail area scrolls independently. Category controls wrap when available width decreases.

## Reference research

The Mystera Legacy player guide separates controls, equipment, skills, and active abilities:
https://www.mysteralegacy.com/mystera-legacy-players-guide/

The Mirage Realms spell guide exposes unlock level, mana, cooldown, effects, and casting conditions:
https://miragerealms.com/wiki/index.php/Spells

These references informed information grouping only. No external artwork, icons, or interface layout was copied.

## Evidence limits

Catalog descriptions are not proof that all 60 skill benefits work.
The full gameplay skill audit remains required.
Native tests and graphical inspection must validate the new browser before visual approval.
