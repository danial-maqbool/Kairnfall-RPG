#!/usr/bin/env python3
"""Graphical native UI regression against a fresh, retained test schema.

Uses only the launcher's isolated PostgreSQL user/volume on port 55433.
Each run retains its own schema so earlier loot/accounts cannot affect targeting.
No development saves, schemas, or volumes are deleted.
"""
from __future__ import annotations

import os
import subprocess
import uuid
import local_dev as dev


def main() -> None:
    port = 5078
    dev.ensure_free_port(port)
    godot = dev.godot_path()
    schema = 'visual_' + uuid.uuid4().hex
    evidence = dev.ROOT / 'artifacts/local/live-experience' / schema
    evidence.mkdir(parents=True)
    env, prefix = dev.start_database(testing=True)
    connection = env['KAIRNFALL_TEST_DB']
    if 'Port=55433;' not in connection or 'Database=kairnfall_test;' not in connection:
        raise RuntimeError('The graphical regression requires the isolated test database.')
    dev.run(prefix + ['exec', '-T', '-e', 'PGPASSWORD', 'test-postgres', 'psql',
                     '-h', '127.0.0.1', '-U', 'kairnfall_test', '-d', 'kairnfall_test',
                     '-v', 'ON_ERROR_STOP=1', '-c', 'CREATE SCHEMA ' + schema + ';'], env=env)
    env['KAIRNFALL_DB'] = connection + ';Search Path=' + schema
    env['ASPNETCORE_URLS'] = f'http://127.0.0.1:{port}'
    env['KAIRNFALL_SMOKE_URL'] = env['ASPNETCORE_URLS']
    env['KAIRNFALL_SCREENSHOTS'] = str(evidence / 'screenshots')
    dev.HEALTH = env['ASPNETCORE_URLS'] + '/health'
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    with (evidence / 'server.log').open('w', encoding='utf-8') as output:
        process = subprocess.Popen([dev.dotnet_path(), str(dev.ROOT / 'src/Kairnfall.Server/bin/Release/net10.0/Kairnfall.Server.dll')],
                                   cwd=dev.ROOT, env=env, stdout=output, stderr=output,
                                   creationflags=flags, start_new_session=os.name != 'nt')
        try:
            dev.wait_ready(process)
            dev.run([godot, '--path', dev.ROOT / 'client', 'res://Tests/LiveExperienceContract.tscn'],
                    env=env, timeout=240, log=evidence / 'client.log', check_godot_errors=True)
        finally:
            dev.stop_child(process)
            dev.run(prefix + ['stop', 'test-postgres'], env=env, timeout=60)
    print('Live native evidence: ' + str(evidence))


if __name__ == '__main__':
    main()
