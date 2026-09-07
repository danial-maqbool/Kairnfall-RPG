# Single-main branch consolidation

The user requested one remaining branch, `main`. All 24 pre-existing remote
workstream/handoff branch tips below are retained as ancestors of the consolidation
commit. Branch deletion therefore does not discard those commits or their files
from Git history; an earlier file can be inspected with `git show <commit>:<path>`.

The current verified implementation from `15021e7d42c42004796c9c19ed284adf6db11731`
is retained. A deliberate history-only merge records divergent older branches
without restoring competing server code, obsolete launchers, or superseded asset
pipelines. This is preservation of historical work, not a claim that every old
feature is implemented in the current game. Existing acceptance gaps remain in
`docs/handoff/LOCAL_ACCEPTANCE_2026-09-07.md`.

The sole working-file change is the existing `Kairnfall.cmd` line-ending
normalization; its command text and behavior are unchanged. Private configuration,
saves, generated files, and tool downloads remain excluded from Git.

After review and merge, close superseded open PRs, remove all non-main local and
remote branches, and verify every recorded tip remains reachable from `main`.

| Retired branch | Preserved tip |
| --- | --- |
| `diagnostics/client-startup` | `9d0e2e854fb16510c669beaa855384d8ccc734db` |
| `handoff/local-qa` | `fe569b4f56641d8495e1ecb322feaf82240b265c` |
| `team/art/anatomy-and-animation-review` | `1b6acd93633e79de1d0b61576c33ead912a15a20` |
| `team/art/asset-pipeline` | `c25061f9eb5e3e4c5ddb9f2e0475a724a4a56215` |
| `team/art/detailed-assets` | `c5d58041a5b876af8477a1f3d657440e847499ee` |
| `team/art/environment-detail` | `0db5e69294afed6b515cb23d2c16b257f53bf448` |
| `team/client/native-signal-contract` | `b1c947480ef6d4cc17f2feb36b6c2f738ff9fc22` |
| `team/client/refinement-and-interaction` | `d5208fe8a6c2ea1a3c9a564c6188f22cd186c4ec` |
| `team/client/visual-world` | `5a4db913e182b0fb17fd8e8c594435124f48d086` |
| `team/client/windows-game` | `bb3d177c2c0ea4acdf0de04eff9c0da957733fe5` |
| `team/integration/completion-pass` | `f640d060be60716934995e05599ef10c5a48a1cf` |
| `team/integration/first-implementation` | `efd75607158500d62d4472e74d9886ce5212503b` |
| `team/integration/persistent-client-build` | `5570168bcb6c7b5e7885968edb34add780833555` |
| `team/integration/windows-launch` | `3483da3db1a62425634a6538d9d1f2cfbf85139a` |
| `team/local/acceptance-repair` | `d1c91df1afd4be0a64ff5b5f5f3408a4d1f3e307` |
| `team/qa/combat-equipment-repair` | `855e7cf676002d1e20b2244ef8a430031de6d1e1` |
| `team/qa/independent-adversarial-review` | `1038c30815a860d6e0557b6d2c00d9a9b8739215` |
| `team/qa/render-evidence` | `b7adb0068420392ec4a2fd44600c85098de32690` |
| `team/release/playable-verification` | `38cce77630dbd0a29b71722a4ee9d9e5af5d2e46` |
| `team/release/windows-packaging` | `5d758721e375b3146e7c26657e621ea5a4a420a8` |
| `team/server/consent-and-stack-repair` | `885655f9c6ae7fa3bb0c556129be2ecb52f595a9` |
| `team/server/transaction-hardening` | `4b6c4504f25c60a38de076fd95b82ea08dab9d14` |
| `team/server/verified-transaction-fixes` | `375cfd8d326c77801cda36e6dee92226fde9e5dc` |
| `team/world/connectivity-and-content` | `03f5674b327695d693d4cbf3d6a7ff477d3f47e9` |
