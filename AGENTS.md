# Kairnfall implementation contract

Use the accepted MMORPG specification and the real-object pixel-art requirement.
The required workstreams are orchestration, server, client, world, combat, items,
creatures, narrative, art, UI, audio, QA, adversarial review, visual review, and release.
Keep ownership boundaries under src, client, content, tools, tests, and docs.
Use team/<workstream>/<task> branches. Integrate through reviewed pull requests.

## Evidence

Do not claim independent agents ran unless their runtime produced task results.
The initial authoring session has no connected worker runtime. Role-based review
in that session is sequential review, not an independent multi-agent audit.

Do not call the game complete until its executable acceptance tests, content
coverage, multiplayer checks, art review, and Windows release test all pass.
Do not count catalog records as finished gameplay or recolours as new species.
Record actual command outputs. Keep failed and unrun tests visible.

## Security

The server owns gameplay state. Clients send intentions, not rewards or results.
Never expose a production server during development without TLS and deployment review.
Never commit credentials, account data, private chat logs, or database backups.
Do not force-push main. Do not publish a release that failed acceptance gates.

## Art

Objects must show real construction and materials at native resolution.
Use real anatomy as the basis for animals and articulated humanoids.
A sword has a blade, guard, grip, and pommel. A chest has boards, hinges, a lid,
and a lock. Cloth, leather, metal, stone, and wood need distinct pixel clusters.
Inspect actual frames and in-engine screenshots. Numeric palette tests alone
cannot approve art. Do not mark any generated asset as approved without review.
