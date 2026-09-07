#!/usr/bin/env python3
"""Local source development commands. No public deployment or release publication."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local'
VENV = ROOT / '.venv'
GODOT_VERSION = '4.7.2'
GAME_PORT = 5077
DEV_DB_PORT = 55432
TEST_DB_PORT = 55433
HEALTH = f'http://127.0.0.1:{GAME_PORT}/health'
PROJECT = 'kairnfall-' + hashlib.sha256(str(ROOT).encode()).hexdigest()[:10]


def scrub(text: str, environment: dict[str, str] | None = None) -> str:
    for key, value in (environment or {}).items():
        if value and ('PASSWORD' in key or key.endswith('_TOKEN')):
            text = text.replace(value, '[REDACTED]')
    return re.sub(r'(?i)(Password\s*=\s*)[^;\r\n]+', r'\1[REDACTED]', text)


def run(args: list[str | Path], *, env: dict[str, str] | None = None,
        timeout: int = 900, log: Path | None = None) -> str:
    """Check native exit codes. Do not print environment values or credentials."""
    result = subprocess.run([str(x) for x in args], cwd=ROOT, env=env,
                            text=True, encoding='utf-8', errors='replace',
                            capture_output=True, timeout=timeout)
    output = scrub(result.stdout + result.stderr, env)
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(output, encoding='utf-8')
    if output:
        print(output, end='' if output.endswith('\n') else '\n', flush=True)
    if result.returncode:
        raise RuntimeError(f'{Path(str(args[0])).name} failed with exit code {result.returncode}.')
    return result.stdout.strip()


def command(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f'{name} is not on PATH. Read docs/LOCAL_REQUIREMENTS.md.')
    return path


def python_path() -> Path:
    path = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not path.is_file():
        raise RuntimeError('The project Python environment is missing. Run bootstrap.ps1 first.')
    return path


def dotnet_path() -> str:
    path = command('dotnet')
    version = run([path, '--version'], timeout=30)
    if not version.startswith('10.'):
        raise RuntimeError('Install a stable .NET 10 SDK. A runtime-only install is not sufficient.')
    return path


def godot_path() -> Path:
    configured = os.environ.get('GODOT_BIN')
    if configured:
        path = Path(configured).expanduser().resolve()
    else:
        manifest = ROOT / '.tools/godot.json'
        if not manifest.is_file():
            raise RuntimeError('The Godot toolchain is missing. Run bootstrap.ps1 or set GODOT_BIN.')
        record = json.loads(manifest.read_text(encoding='utf-8'))
        if record.get('version') != GODOT_VERSION:
            raise RuntimeError('The stored Godot version does not match the project.')
        path = Path(record['binary'])
    if not path.is_file():
        raise RuntimeError('The Godot executable path is invalid. Re-run bootstrap.ps1.')
    version = run([path, '--version'], timeout=30)
    if not version.startswith(GODOT_VERSION + '.') or 'mono' not in version.lower():
        raise RuntimeError('Use Godot 4.7.2 .NET, not the standard editor or mismatched templates.')
    return path


def prepare(skip_godot: bool = False) -> None:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('Use Python 3.12.x to create the pinned build environment.')
    dotnet = dotnet_path()
    if not VENV.exists():
        run([sys.executable, '-m', 'venv', VENV])
    py = python_path()
    run([py, '-m', 'pip', 'install', '-r', 'tools/requirements-art.txt'])
    assets()
    run([dotnet, 'restore', 'Kairnfall.slnx'])
    run([dotnet, 'build', 'Kairnfall.slnx', '-c', 'Release', '--no-restore'])
    run([dotnet, 'build', 'client/Kairnfall.Client.csproj', '-c', 'Debug'])
    if not skip_godot:
        if not os.environ.get('GODOT_BIN'):
            run([py, 'tools/get_godot.py', '--os', 'windows' if os.name == 'nt' else 'linux',
                 '--with-templates'], timeout=1200)
        run([godot_path(), '--headless', '--path', ROOT / 'client', '--editor', '--import'],
            timeout=300, log=ROOT / 'artifacts/local/import.log')
    print('Source preparation finished. This does not certify gameplay, artwork, or a Windows release.')


def assets() -> None:
    py = python_path()
    run([py, 'tools/build_content.py'], log=ROOT / 'artifacts/local/content.log')
    run([py, 'tools/build_game_assets.py'], timeout=1200,
        log=ROOT / 'artifacts/local/assets.log')
    run([py, 'tools/complete_skill_icons.py'], log=ROOT / 'artifacts/local/skill-icons.log')
    run([py, 'tools/validate_game_assets.py'], log=ROOT / 'artifacts/local/asset-checks.log')


def compose_prefix() -> list[str | Path]:
    docker = command('docker')
    run([docker, 'compose', 'version'], timeout=30)
    kind = run([docker, 'info', '--format', '{{.OSType}}'], timeout=30)
    if kind != 'linux':
        raise RuntimeError('Open Docker Desktop and select Linux containers.')
    return [docker, 'compose', '--project-name', PROJECT, '--file', ROOT / 'compose.local.yml']


def load_credentials() -> dict[str, str]:
    """Store random local-only passwords. Never reset an existing volume on failure."""
    PRIVATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = PRIVATE / 'database.json'
    if not path.exists():
        docker = command('docker')
        for suffix in ('realm', 'tests'):
            found = subprocess.run([docker, 'volume', 'inspect', PROJECT + '_' + suffix],
                                   capture_output=True, timeout=30)
            if found.returncode == 0:
                raise RuntimeError('A database volume exists but its local credential file is missing. '
                                   'Recover .local/database.json. Do not delete the volume.')
        data = {'schema': 1, 'project': PROJECT, 'development': secrets.token_hex(32),
                'testing': secrets.token_hex(32)}
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                json.dump(data, handle, indent=2)
                handle.write('\n')
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema') != 1 or data.get('project') != PROJECT:
        raise RuntimeError('Local database configuration belongs to a different checkout. Do not overwrite it.')
    for key in ('development', 'testing'):
        if not isinstance(data.get(key), str) or not re.fullmatch(r'[a-f0-9]{64}', data[key]):
            raise RuntimeError('Local database credentials are invalid. Recover the existing file; do not reset saves.')
    return data


def database_environment(data: dict[str, str]) -> dict[str, str]:
    env = os.environ.copy()
    env['KAIRNFALL_COMPOSE_PROJECT'] = PROJECT
    env['KAIRNFALL_DEV_PASSWORD'] = data['development']
    env['KAIRNFALL_TEST_PASSWORD'] = data['testing']
    return env


def start_database(testing: bool = False) -> tuple[dict[str, str], list[str | Path]]:
    prefix = compose_prefix()
    data = load_credentials()
    env = database_environment(data)
    service = 'test-postgres' if testing else 'postgres'
    run(prefix + ['--profile', 'test', 'up', '-d', '--wait', '--wait-timeout', '90', service],
        env=env, timeout=180)
    # pg_isready alone does not verify that the stored password is correct.
    user = 'kairnfall_test' if testing else 'kairnfall'
    password_key = 'testing' if testing else 'development'
    env['PGPASSWORD'] = data[password_key]
    run(prefix + ['exec', '-T', '-e', 'PGPASSWORD', service, 'psql', '-h', '127.0.0.1',
                  '-U', user, '-d', user, '-v', 'ON_ERROR_STOP=1', '-c', 'SELECT 1;'], env=env, timeout=30)
    db = (f'Host=127.0.0.1;Port={TEST_DB_PORT if testing else DEV_DB_PORT};'
          f'Database={user};Username={user};Password={data[password_key]}')
    # Do not inherit a production/test database connection from the caller.
    env.pop('KAIRNFALL_DB', None)
    env.pop('KAIRNFALL_TEST_DB', None)
    env['KAIRNFALL_TEST_DB' if testing else 'KAIRNFALL_DB'] = db
    env['KAIRNFALL_CATALOG'] = str(ROOT / 'content/catalog.json')
    env['KAIRNFALL_ALLOW_LOCAL_HTTP'] = '1'
    env['ASPNETCORE_ENVIRONMENT'] = 'Testing' if testing else 'Development'
    env['DOTNET_ENVIRONMENT'] = env['ASPNETCORE_ENVIRONMENT']
    env['ASPNETCORE_URLS'] = f'http://127.0.0.1:{GAME_PORT}'
    return env, prefix


def ensure_free_port(port: int) -> None:
    with socket.socket() as listener:
        if os.name == 'nt':
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            listener.bind(('127.0.0.1', port))
        except OSError as error:
            raise RuntimeError(f'Port {port} is already in use. No existing process was stopped.') from error


def wait_ready(process: subprocess.Popen, timeout: float = 60) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('The local server stopped during startup. Read artifacts/local/server-errors.log.')
        try:
            with urllib.request.urlopen(HEALTH, timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(0.5)
    raise RuntimeError('The local server did not become ready. Existing database volumes were preserved.')


def stop_child(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == 'nt':
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.send_signal(signal.SIGINT)
        process.wait(timeout=15)
        return
    except (OSError, subprocess.TimeoutExpired):
        print('Graceful server shutdown did not finish. Stopping only the child started by this command.')
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def client(smoke: bool = False) -> None:
    godot = godot_path()
    env = os.environ.copy()
    args: list[str | Path] = [godot, '--path', ROOT / 'client']
    if smoke:
        directory = ROOT / 'artifacts/local/smoke' / str(time.time_ns())
        directory.mkdir(parents=True, exist_ok=False)
        env['KAIRNFALL_SMOKE_URL'] = f'http://127.0.0.1:{GAME_PORT}'
        env['KAIRNFALL_SCREENSHOTS'] = str(directory)
        args += ['--', '--smoke']
        run(args, env=env, timeout=120, log=directory / 'client.log')
        expected = ['01-world.png', '02-inventory.png', '03-skills.png', '04-map.png']
        missing = [name for name in expected if not (directory / name).is_file()]
        if missing:
            raise RuntimeError('Graphical smoke evidence is missing: ' + ', '.join(missing))
        print(f'Smoke screenshots saved in {directory}. Visual approval is still required.')
    else:
        result = subprocess.run([str(x) for x in args], cwd=ROOT, env=env)
        if result.returncode:
            raise RuntimeError(f'Godot exited with code {result.returncode}.')


def serve(with_client: bool = False, smoke: bool = False) -> None:
    if with_client:
        godot_path()
    dotnet = dotnet_path()
    assembly = ROOT / 'src/Kairnfall.Server/bin/Release/net10.0/Kairnfall.Server.dll'
    if not assembly.is_file():
        raise RuntimeError('The server build is missing. Run bootstrap.ps1 first.')
    ensure_free_port(GAME_PORT)
    env, _ = start_database()
    logs = ROOT / 'artifacts/local'
    logs.mkdir(parents=True, exist_ok=True)
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    with (logs / 'server.log').open('w', encoding='utf-8') as stdout, \
            (logs / 'server-errors.log').open('w', encoding='utf-8') as stderr:
        process = subprocess.Popen([dotnet, str(assembly)], cwd=ROOT, env=env,
                                   stdout=stdout, stderr=stderr, creationflags=flags,
                                   start_new_session=os.name != 'nt')
        try:
            wait_ready(process)
            print(f'Local realm ready at http://127.0.0.1:{GAME_PORT}. Press Ctrl+C to stop.', flush=True)
            if with_client:
                client(smoke)
            else:
                code = process.wait()
                if code:
                    raise RuntimeError(f'The server exited with code {code}.')
        except KeyboardInterrupt:
            print('Stopping the local child server. Database saves are retained.')
        finally:
            stop_child(process)
    print('The server stopped. The PostgreSQL volume and credentials are retained.')


def tests(with_database: bool = False) -> None:
    dotnet = dotnet_path()
    run([python_path(), 'tools/build_content.py'])
    run([dotnet, 'build', 'Kairnfall.slnx', '-c', 'Release'])
    env = os.environ.copy()
    env.pop('KAIRNFALL_DB', None)
    env.pop('KAIRNFALL_TEST_DB', None)
    suites = [('core', 'Kairnfall.Tests', ['content/catalog.json']),
              ('gameplay', 'Kairnfall.ReviewTests', []),
              ('security', 'Kairnfall.SecurityTests', ['content/catalog.json'])]
    prefix = None
    try:
        if with_database:
            env, prefix = start_database(testing=True)
            suites += [('network-postgres', 'Kairnfall.Integration', []),
                       ('save-conflicts', 'Kairnfall.ReviewTests', ['--database'])]
        for name, project, extra in suites:
            args = [dotnet, 'run', '--no-build', '--project', 'tests/' + project, '-c', 'Release']
            if extra:
                args += ['--'] + extra
            run(args, env=env, timeout=600, log=ROOT / 'artifacts/local-tests' / (name + '.log'))
    finally:
        if prefix is not None:
            run(prefix + ['stop', 'test-postgres'], env=env, timeout=60)
    print('Requested suites passed. These suites do not replace graphical playtesting or a release audit.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'assets', 'server', 'client', 'dev', 'test', 'stop-db', 'signals'])
    parser.add_argument('--skip-godot', action='store_true')
    parser.add_argument('--with-database', action='store_true')
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    try:
        if args.action == 'prepare': prepare(args.skip_godot)
        elif args.action == 'assets': assets()
        elif args.action == 'server': serve()
        elif args.action == 'client': client(args.smoke)
        elif args.action == 'dev': serve(with_client=True, smoke=args.smoke)
        elif args.action == 'test': tests(args.with_database)
        elif args.action == 'signals':
            run([godot_path(), '--headless', '--path', ROOT / 'client', 'res://Tests/SignalContract.tscn'],
                timeout=60, log=ROOT / 'artifacts/local/signal-contract.log')
        elif args.action == 'stop-db':
            prefix = compose_prefix()
            run(prefix + ['--profile', 'test', 'stop'], env=database_environment(load_credentials()), timeout=60)
            print('Local containers stopped. No database volumes were removed.')
        return 0
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print('LOCAL_SETUP_ERROR: ' + scrub(str(error)), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
