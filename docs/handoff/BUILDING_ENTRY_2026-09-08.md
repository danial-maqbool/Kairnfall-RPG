# Building entry repair

Four visible Wayfarer's Rest buildings previously had no corresponding interior or door transition.
The starter now connects each door tile to a small interior with a reciprocal exit.
The Lantern Hearth has an innkeeper, Wayfarer Forge has a smith, Travelers' Store has a provisioner, and Mara's Workshop has a trainer.
The existing capital interiors also contain staff for their advertised building service.

The repair preserves existing outdoor NPC IDs, positions, shop data, and quest-giver references.
New interior staff are additional service endpoints, not replacements for active quest givers.
No saved character coordinates or database records are rewritten by the content builder.
Door actions continue through the server's ordinary transition command, range checks, and destination validation.

Authored-data regressions cover reciprocal door/arrival pairs, service roles, stock, existing NPC identity, all quest references, connected geography, and deterministic builds.
The existing world probe must also verify actual walkable tile paths to every new service and exit.
Graphical entry/exit, multiplayer presence, interior reconnect, and visual decoration remain separate acceptance checks.
These interiors are a functional entry repair, not completed art direction or a completed beginner tutorial.
