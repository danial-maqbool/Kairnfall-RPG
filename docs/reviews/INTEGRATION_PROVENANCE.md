# Current source integration

This merge retains the verified server, core, transaction tests, test runner,
CI, and review records from main at c5d80d60f5803958da0a76a61f9aae436f49c310.
It combines the Godot client, native signal tests, asset generation, and Windows
launch scripts from f326b9aa87e1f1f5ee143d03d4756813e0165b0c.

The client-side Ui.Button implementation retains ActionButton. The merge does
not restore the older direct System.Action-to-native-signal connection.
The two parents retain the history of both workstreams. No source history is
rewritten and no unfinished PR is described as a completed game.

Both source roots must pass the same final integration run. That run records
its exact checkout commit, source blob identifiers, and executable file hashes.
Previous independent branch tests do not establish this merged build's status.
