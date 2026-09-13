# Task 15 release-candidate known limitations

Current repository automation can build, package, checksum, start, restart, reconnect, back up, verify, and restore the candidate in disposable environments. None of those results is a human release approval or proof of a public production deployment.

**NOT APPROVED — human acceptance remains.**

The current human/owner-environment gates remain:

1. Owner Windows gameplay pass for visible XP/level pacing and reconnect/restart persistence.
2. Normal-play progression and class feel.
3. Independent human adversarial/gameplay acceptance if independent approval is required.
4. Independent artistic approval at native/in-engine scale.
5. Full ordinary-account world and quest walkthrough.
6. Sustained economy and balance feel.
7. Audio listening approval.
8. Production-scale load validation if a specific concurrent-player capacity will be advertised.
9. Physical Windows DPI and hardware-input inspection.
10. Owner-machine clean Windows package extraction and launch if required for release sign-off.

Additional release-engineering boundaries:

- No GitHub release or tag is created by Task 15.
- No public realm, DNS name, certificate, cloud database, monitoring service, or backup destination is provisioned by repository automation.
- The operations utility proves logical PostgreSQL dump/restore recovery into a fresh database; it is not a substitute for an operator-owned retention schedule, encrypted off-site storage, disaster-recovery policy, or provider-level snapshots.
- The 2/10/25/50-client acceptance workload is a reference test, not a higher production-capacity promise.
- Automated visual/audio evidence remains structural/technical evidence rather than artistic/listening approval.
- Release screenshots suitable for public publication remain subject to the visual/art approval boundary.
