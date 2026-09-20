# Task 16 release-candidate known limitations

Machine-readable candidate/evidence authority: `docs/handoff/CURRENT_EVIDENCE.json`.
Owner acceptance procedure: `docs/qa/TASK16_OWNER_ACCEPTANCE.md`.

**NOT APPROVED — human acceptance remains.**

Repository automation can build, package, checksum, start, restart, reconnect, back up, verify, restore, and exercise the candidate in disposable environments. Those results are technical evidence, not human release approval or proof of a public production deployment.

The remaining human/owner-environment gates include:

1. Clean owner-machine Windows candidate checksum/extraction/launch.
2. Account, character, disconnect/reconnect, relaunch and restart persistence.
3. Normal-play first-hour progression and pacing.
4. Class/combat feel and boss readability.
5. Ordinary-account world, quest, resource, travel and boss walkthrough.
6. Sustained economy correctness observation and subjective balance feel.
7. Two-client social/multiplayer usability where practical.
8. UI/UX/accessibility inspection with physical mouse/keyboard.
9. Physical Windows DPI/resolution/fullscreen inspection at representative scaling.
10. Artistic review at gameplay/native scale.
11. Actual audio listening review.
12. Production-scale load validation only if a specific public capacity will be advertised.
13. Independent human adversarial/gameplay review only if independent approval is required.

Additional release-engineering boundaries:

- No GitHub release or tag is created by Task 16 preparation.
- No public realm, DNS name, certificate, cloud database, monitoring service, or backup destination is provisioned by repository automation.
- The operations utility proves logical PostgreSQL dump/restore recovery into a fresh database; it is not a substitute for an operator-owned retention schedule, encrypted off-site storage, disaster-recovery policy, or provider-level snapshots.
- The 2/10/25/50-client acceptance workload is a reference test, not a public capacity promise.
- Automated visual/audio evidence is structural/technical evidence rather than artistic/listening approval.
- Hosted display/input checks are not physical-monitor approval.
- Release screenshots suitable for publication remain subject to human visual/art approval.
- The Actions artifact is a release candidate, not a public release. Artifact retention is not a permanent distribution mechanism.
