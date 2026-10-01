#!/usr/bin/env python3
"""Stage and run offline native fixtures without player settings, saves or services.

Run with the existing .venv Python. By default, reuse the already built Debug
client; --build explicitly requests a local --no-restore build. Headless checks
do not approve pixels or physical input. --graphical also runs character frames.
No server/database is started, no assets are regenerated and nothing is fetched.

The installed GodotSharp documentation places custom user directories below
%APPDATA% on Windows or XDG_DATA_HOME on Linux. Only the child process receives
workspace data/config/cache paths, and the custom directory name stays relative.
A cheap pure-GDScript probe verifies the exact user:// location before staging;
the same guard runs again before any C# fixture/Main scene is loaded.
"""
from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from threading import Lock
import time
import uuid

import local_dev as dev

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'client'
OUT = ROOT / 'artifacts/improvement-pass-2026-10-01'
STAGE = OUT / 'native-client'
USER_DIR = OUT / 'Kairnfall-Classic-QA'
ASSEMBLIES = Path('.godot/mono/temp/bin/Debug')
COPY_WORKERS = 4
HEADLESS_SUITES = (
    'ClassicExperienceContract', 'ControlRulesContract', 'PlayerExperienceContract',
    'WindowsScaleContract', 'InputContract', 'CompactItemCardContract',
)
SUITE_MARKERS = {
    'ClassicExperienceContract': 'CLASSIC_EXPERIENCE_CONTRACT:',
    'ControlRulesContract': 'CONTROL_RULES_CONTRACT:',
    'PlayerExperienceContract': 'PLAYER_EXPERIENCE_CONTRACT:',
    'WindowsScaleContract': 'WINDOWS_SCALE_CONTRACT:',
    'InputContract': 'INPUT_CONTRACT:',
    'CompactItemCardContract': 'COMPACT_ITEM_CARD_CONTRACT:',
    'CharacterPresentationContract': 'CHARACTER_NATIVE_CONTRACT:',
    'PerformanceMotionDiagnosticsContract': 'PERFORMANCE_MOTION_DIAGNOSTICS:',
}
ENGINE_ERROR = re.compile(r'(?m)(?:^|\s)(?:ERROR:|SCRIPT ERROR:|Unhandled exception)')
GUARD_MARKER = 'IMPROVEMENT_QA_USER_DIR_VERIFIED: '


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        result = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def workspace_path(path: Path, *, purpose: str = 'QA output') -> Path:
    # Guard the directory containing the output entry. A regular cache file can
    # have several hardlink names; resolving its leaf is not directory authority.
    # Resolve parent directories to retain symlink/junction escape detection, and
    # refuse a linked leaf instead of silently writing through it.
    requested = Path(os.path.abspath(path))
    resolved_directory = None
    reason = None
    if not requested.is_relative_to(ROOT):
        reason = 'requested path is outside the workspace'
    elif linklike(requested):
        reason = 'output entry is a symlink or junction'
    else:
        directory = requested if requested.is_dir() else requested.parent
        resolved_directory = directory.resolve()
        if not resolved_directory.is_relative_to(ROOT):
            reason = 'resolved output directory is outside the workspace'
    if reason:
        raise RuntimeError(
            'QA output must remain inside the calling workspace. '
            + f'Purpose={purpose!r}; reason={reason}; requested={str(requested)!r}; '
            + f'resolvedDirectory={str(resolved_directory) if resolved_directory is not None else None!r}; '
            + f'workspace={str(ROOT)!r}')
    return requested


def linklike(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


class Progress:
    def __init__(self, label: str, total: int | None = None):
        self.label, self.total = label, total
        self.last_time, self.last_count = time.monotonic(), 0
        self.show(0)

    def show(self, count: int) -> None:
        print(f'QA {self.label}: {count}' + (f'/{self.total}' if self.total is not None else '') + ' files', flush=True)

    def update(self, count: int) -> None:
        now = time.monotonic()
        if count - self.last_count >= 500 or now - self.last_time >= 10 or count == self.total:
            self.show(count)
            self.last_time, self.last_count = now, count


def bounded_map(operation, paths: list[Path], label: str):
    """Four workers, at most eight pending operations; no eager 35k-future queue."""
    progress = Progress(label, len(paths))
    iterator, completed = iter(paths), 0
    with ThreadPoolExecutor(max_workers=COPY_WORKERS) as workers:
        pending = set()
        for _ in range(COPY_WORKERS * 2):
            path = next(iterator, None)
            if path is not None:
                pending.add(workers.submit(operation, path))
        while pending:
            ready, pending = wait(pending, timeout=10, return_when=FIRST_COMPLETED)
            if not ready:
                progress.update(completed)
            for future in ready:
                yield future.result()
                completed += 1
                progress.update(completed)
                path = next(iterator, None)
                if path is not None:
                    pending.add(workers.submit(operation, path))


def files_under(folder: Path) -> list[Path]:
    """Never follow linked directories into another checkout or personal data."""
    if linklike(folder):
        raise RuntimeError('Refusing a linked QA resource root: ' + str(folder))
    if not folder.is_dir():
        raise RuntimeError('Required prepared resources are missing: ' + str(folder))
    found: list[Path] = []
    progress = Progress('inventory ' + folder.relative_to(ROOT).as_posix())
    for current, directories, names in os.walk(folder, followlinks=False):
        for name in directories:
            if linklike(Path(current) / name):
                raise RuntimeError('Refusing linked QA resources: ' + str(Path(current) / name))
        for name in names:
            path = Path(current) / name
            if linklike(path):
                raise RuntimeError('Refusing linked QA resources: ' + str(path))
            found.append(path)
            progress.update(len(found))
    return sorted(found)


def client_files() -> list[Path]:
    # Copy gameplay resources and runtime caches, not editor preferences, driver
    # caches, credentials, local configuration or a prior QA result directory.
    paths = [p for p in CLIENT.iterdir() if p.is_file() and p.suffix in
             {'.godot', '.tscn', '.tres', '.csproj', '.sln'}]
    for name in ('Scripts', 'Tests', 'Assets'):
        paths.extend(files_under(CLIENT / name))
    if (CLIENT / 'Data').exists():
        paths.extend(files_under(CLIENT / 'Data'))
    paths.extend(files_under(CLIENT / '.godot/imported'))
    paths.extend(files_under(CLIENT / ASSEMBLIES))
    for name in ('.gdignore', 'uid_cache.bin', 'global_script_class_cache.cfg'):
        path = CLIENT / '.godot' / name
        if path.is_file():
            paths.append(path)
    return sorted(set(paths))


def core_sources() -> list[Path]:
    folder = ROOT / 'src/Kairnfall.Core'
    return sorted(p for p in files_under(folder)
                  if p.suffix in {'.cs', '.csproj'} and not {'bin', 'obj'}.intersection(p.relative_to(folder).parts))


def compilation_inputs(paths: list[Path], core: list[Path]) -> dict[str, list[Path]]:
    shared = [ROOT / name for name in ('Directory.Build.props', 'Directory.Build.targets', 'global.json')
              if (ROOT / name).is_file()]
    return {'Kairnfall.Client.dll': sorted(set(core + shared + [p for p in paths if p.suffix in {'.cs', '.csproj'}])),
            'Kairnfall.Core.dll': sorted(set(core + shared))}


def assembly_freshness(inputs: dict[str, list[Path]]) -> dict[str, object]:
    records, stale = [], []
    for name, sources in inputs.items():
        assembly = CLIENT / ASSEMBLIES / name
        modified = assembly.stat().st_mtime_ns
        newer = [p.relative_to(ROOT).as_posix() for p in sources if p.stat().st_mtime_ns > modified]
        records.append({'assembly': name, 'sha256': digest(assembly), 'modifiedNs': modified, 'newerInputs': newer})
        stale.extend(newer)
    result = {'method': 'Input modification times versus local Debug DLLs; detects stale builds, does not prove compilation correspondence.',
              'status': 'stale' if stale else 'no-newer-inputs-detected', 'assemblies': records}
    return result


def source_record(path: Path) -> dict[str, object]:
    before = path.stat()
    value = digest(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError('Source changed while hashing: ' + path.relative_to(ROOT).as_posix())
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': after.st_size, 'sha256': value, 'modifiedNs': after.st_mtime_ns}


class ResourceCache:
    """Verify each private read-only content blob once per staging invocation."""
    def __init__(self):
        self.root = workspace_path(OUT / 'immutable-resources')
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        self.directories: set[str] = set()
        self.blobs: dict[str, Future] = {}

    def prepared(self, source: Path, record: dict[str, object]) -> Path | None:
        sha = str(record['sha256'])
        with self.lock:
            future = self.blobs.get(sha)
            owner = future is None
            if owner:
                future = Future()
                self.blobs[sha] = future
        if not owner:
            return future.result()
        try:
            with self.lock:
                if sha[:2] not in self.directories:
                    directory = workspace_path(self.root / sha[:2],
                                               purpose='immutable cache directory for ' + source.relative_to(CLIENT).as_posix())
                    directory.mkdir(parents=True, exist_ok=True)
                    self.directories.add(sha[:2])
            cache = self.root / sha[:2] / sha
            if linklike(cache):
                raise RuntimeError('Refusing a linked immutable cache entry: ' + str(cache))
            if not cache.exists():
                temporary = cache.with_name(cache.name + '-' + uuid.uuid4().hex + '.tmp')
                try:
                    shutil.copy2(source, temporary)
                    if digest(temporary) != sha:
                        raise RuntimeError('Source changed while caching: ' + str(source))
                    try:
                        os.link(temporary, cache)
                    except FileExistsError:
                        pass
                    except OSError:
                        future.set_result(None)
                        return None
                finally:
                    if temporary.exists():
                        temporary.chmod(stat.S_IREAD | stat.S_IWRITE)
                        temporary.unlink()  # This invocation's generated temp only.
            if digest(cache) != sha:
                raise RuntimeError('Immutable QA cache failed its content hash: ' + str(cache))
            cache.chmod(stat.S_IREAD)
            future.set_result(cache)
            return cache
        except Exception as failure:
            future.set_exception(failure)
            raise


def copy_resource(source: Path, staging: Path, resources: ResourceCache) -> dict[str, object]:
    if linklike(source):
        raise RuntimeError('Refusing a linked native resource: ' + str(source))
    before = source_record(source)
    relative = source.relative_to(CLIENT)
    target = staging / relative
    storage = 'byte-copy'
    copied = None
    immutable = relative.parts[0] == 'Assets' or relative.parts[:2] == ('.godot', 'imported')
    if immutable:
        # Hardlink only a private content-addressed read-only blob, never a live
        # source file or another tested stage. Native reimport attempts fail
        # instead of mutating earlier evidence through a shared writable inode.
        cache = resources.prepared(source, before)
        if cache is not None:
            try:
                os.link(cache, target)
                if not os.path.samefile(cache, target):
                    raise RuntimeError('Staged hardlink does not identify the verified cache blob: ' + relative.as_posix())
                storage = 'read-only-content-cache-hardlink'
                copied = before['sha256']  # Verified blob plus actual file identity.
            except OSError:
                shutil.copy2(cache, target)
                storage = 'byte-copy-hardlinks-unavailable'
        else:
            shutil.copy2(source, target)
            storage = 'byte-copy-hardlinks-unavailable'
    else:
        shutil.copy2(source, target)
    if copied is None:
        copied = digest(target)
    if copied != before['sha256']:
        raise RuntimeError('Staged bytes differ from source: ' + relative.as_posix())
    return {'path': relative.as_posix(), 'bytes': before['bytes'], 'sourceModifiedNs': before['modifiedNs'],
            'sourceSha256': before['sha256'], 'copiedSha256': copied, 'storage': storage}


def write_json(path: Path, value: object) -> None:
    workspace_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


def source_revision() -> dict[str, object]:
    # Only revision/path metadata is captured; no diff, environment or settings.
    result: dict[str, object] = {}
    for key, args in (('head', ['rev-parse', 'HEAD']),
                      ('branch', ['branch', '--show-current']),
                      ('workingTree', ['status', '--short'])):
        process = subprocess.run(['git', '-c', 'core.quotepath=false', *args], cwd=ROOT,
                                 capture_output=True, text=True, encoding='utf-8',
                                 errors='replace', timeout=15)
        result[key] = process.stdout.strip() if process.returncode == 0 else None
        if process.returncode:
            result[key + 'Status'] = 'unavailable'
    return result


def set_application_setting(project: str, key: str, value: str) -> str:
    match = re.search(r'(?m)^\[application\]\s*$', project)
    if match is None:
        raise RuntimeError('The staged native project has no application section.')
    end = re.search(r'(?m)^\[', project[match.end():])
    stop = match.end() + end.start() if end else len(project)
    section = project[match.end():stop]
    expression = re.compile(r'(?m)^' + re.escape(key) + r'=.*$')
    replacement = key + '=' + value
    section = expression.sub(lambda _: replacement, section) if expression.search(section) else '\n' + replacement + section
    return project[:match.end()] + section + project[stop:]


GUARD_SOURCE = '''extends Node
@export var fixture_scene: String = ""
@export var verify_only: bool = false

func _ready() -> void:
    var expected := OS.get_environment("KAIRNFALL_QA_USER_DIR").replace("\\\\", "/").simplify_path().trim_suffix("/")
    var actual := ProjectSettings.globalize_path("user://").replace("\\\\", "/").simplify_path().trim_suffix("/")
    var same := actual == expected
    if OS.get_name() == "Windows":
        same = actual.to_lower() == expected.to_lower()
    if expected.is_empty() or not expected.is_absolute_path() or not same:
        push_error("IMPROVEMENT_QA_ISOLATION: user:// did not resolve to the requested workspace directory; fixture was not loaded. Expected=" + expected + " actual=" + actual)
        get_tree().quit(3)
        return
    print("IMPROVEMENT_QA_USER_DIR_VERIFIED: " + actual)
    if verify_only:
        get_tree().quit(0)
        return
    if not fixture_scene.begins_with("res://Tests/") or not fixture_scene.ends_with(".tscn"):
        push_error("IMPROVEMENT_QA_ISOLATION: invalid offline fixture scene.")
        get_tree().quit(3)
        return
    var scene = load(fixture_scene) as PackedScene
    if scene == null:
        push_error("IMPROVEMENT_QA_ISOLATION: requested fixture was not available.")
        get_tree().quit(3)
        return
    get_tree().root.add_child.call_deferred(scene.instantiate())
'''


def isolated_environment(env: dict[str, str]) -> dict[str, str]:
    # These are child-process overrides, never changes to Windows account paths.
    # The exact native result is guarded; documentation alone is not acceptance.
    directories = {'APPDATA': OUT, 'LOCALAPPDATA': OUT / 'platform-cache',
                   'XDG_DATA_HOME': OUT, 'XDG_CONFIG_HOME': OUT / 'platform-config',
                   'XDG_CACHE_HOME': OUT / 'platform-cache'}
    for directory in set(directories.values()):
        workspace_path(directory).mkdir(parents=True, exist_ok=True)
    return env | {name: str(directory) for name, directory in directories.items()}


def isolation_probe(godot: Path, env: dict[str, str], run_dir: Path) -> dict[str, object]:
    project = workspace_path(run_dir / 'isolation-probe')
    project.mkdir(parents=True)
    (project / 'project.godot').write_text(
        '[application]\nconfig/name="Kairnfall-Classic-QA"\n'
        'config/use_custom_user_dir=true\nconfig/custom_user_dir_name="Kairnfall-Classic-QA"\n', encoding='utf-8')
    (project / 'Isolation.gd').write_text(GUARD_SOURCE, encoding='utf-8')
    (project / 'Isolation.tscn').write_text(
        '[gd_scene load_steps=2 format=3]\n\n'
        '[ext_resource type="Script" path="res://Isolation.gd" id="1"]\n\n'
        '[node name="ImprovementQaIsolation" type="Node"]\nscript = ExtResource("1")\nverify_only = true\n', encoding='utf-8')
    log, engine_log = run_dir / 'logs/isolation-probe.log', run_dir / 'logs/isolation-probe-engine.log'
    try:
        dev.run([godot, '--headless', '--path', project, '--audio-driver', 'Dummy',
                 '--log-file', engine_log, 'res://Isolation.tscn'],
                env=env | {'KAIRNFALL_QA_USER_DIR': str(USER_DIR)}, timeout=30, log=log, check_godot_errors=True)
        output = log.read_text(encoding='utf-8', errors='replace')
        engine = engine_log.read_text(encoding='utf-8', errors='replace') if engine_log.exists() else ''
        if GUARD_MARKER not in output or ENGINE_ERROR.search(output + '\n' + engine):
            raise RuntimeError('Workspace user-directory isolation probe lacked a clean verification marker.')
        result = {'status': 'passed', 'fixtureLoaded': False, 'expectedUserDirectory': str(USER_DIR),
                  'method': 'Relative custom directory with child-process APPDATA/XDG_DATA_HOME; exact native user:// guard.',
                  'log': str(log), 'engineLog': str(engine_log)}
    except RuntimeError as failure:
        result = {'status': 'failed', 'fixtureLoaded': False, 'expectedUserDirectory': str(USER_DIR),
                  'error': str(failure), 'log': str(log), 'engineLog': str(engine_log)}
        write_json(run_dir / 'isolation-probe.json', result)
        raise
    write_json(run_dir / 'isolation-probe.json', result)
    return result


def stage_client(run_dir: Path, suites: list[str]) -> dict[str, object]:
    started = time.monotonic()
    paths = client_files()
    core = core_sources()
    inputs = compilation_inputs(paths, core)
    for name in ('Kairnfall.Client.dll', 'Kairnfall.Core.dll',
                 'Kairnfall.Client.deps.json', 'Kairnfall.Client.runtimeconfig.json'):
        if not (CLIENT / ASSEMBLIES / name).is_file():
            raise RuntimeError('Build the Debug client before staging; missing runtime file: ' + name)
    catalog = CLIENT / 'Assets/catalog.json'
    canonical = ROOT / 'content/catalog.json'
    if not canonical.is_file() or digest(canonical) != digest(catalog):
        raise RuntimeError('Normal client/server generated catalogs differ. Prepare matching ordinary assets before QA.')
    if json.loads(catalog.read_text(encoding='utf-8')).get('classicTutorial') is not None:
        raise RuntimeError('This runner requires the ordinary catalog, not an optional tutorial-world overlay.')
    staging = workspace_path(OUT / ('staging-' + uuid.uuid4().hex))
    staging.mkdir(parents=True)
    manifest: dict[str, object] = {
        'createdUtc': timestamp(), 'sourceRoot': str(ROOT), 'stagedClient': str(STAGE),
        'temporaryStage': str(staging), 'status': 'staging',
        'requestedUserDirectory': str(USER_DIR), 'revision': source_revision(),
        'copyPolicy': 'Prepared client resources/imports use read-only content-addressed blobs when hardlinks are available; sources and assemblies are independent byte copies. Editor/local/player data excluded.',
        'files': [], 'coreSourceHashes': [], 'buildInputHashes': [], 'overlays': [],
        'assemblyFreshness': assembly_freshness(inputs),
    }
    write_json(run_dir / 'copy-manifest.json', manifest)
    try:
        if manifest['assemblyFreshness']['status'] == 'stale':
            raise RuntimeError('Debug DLLs predate C# or build inputs; rebuild before --skip-build. See assemblyFreshness in the retained manifest.')
        extra = sorted(set(core + inputs['Kairnfall.Client.dll'] + [canonical]).difference(paths))
        for record in bounded_map(source_record, extra, 'source baseline'):
            manifest['buildInputHashes'].append(record)
            if ROOT / record['path'] in core:
                manifest['coreSourceHashes'].append(record)
        resources = ResourceCache()
        for parent in sorted({(staging / path.relative_to(CLIENT)).parent for path in paths}):
            workspace_path(parent).mkdir(parents=True, exist_ok=True)
        for record in bounded_map(lambda path: copy_resource(path, staging, resources), paths, 'staging'):
            manifest['files'].append(record)
        # A second full content/inventory pass catches edits after an individual
        # file was copied, not merely edits during that file's copy operation.
        expected = {'client/' + record['path']: (record['sourceSha256'], record['bytes']) for record in manifest['files']}
        expected.update({record['path']: (record['sha256'], record['bytes']) for record in manifest['buildInputHashes']})
        for record in bounded_map(source_record, sorted(set(paths + extra)), 'source verification'):
            if expected.get(record['path']) != (record['sha256'], record['bytes']):
                raise RuntimeError('Source changed during QA staging: ' + record['path'])
        if paths != client_files() or core != core_sources():
            raise RuntimeError('Native source/resource inventory changed during QA staging; retry after integration finishes.')
        manifest['assemblyFreshnessAfterStaging'] = assembly_freshness(inputs)
        if manifest['assemblyFreshnessAfterStaging']['status'] == 'stale':
            raise RuntimeError('C# or build inputs changed after compilation; staged native fixtures were not launched.')
        manifest['sourceVerification'] = {'status': 'passed', 'files': len(expected), 'completedUtc': timestamp(),
                                          'method': 'Second complete SHA-256 content pass plus unchanged client/Core file inventories.'}
    except (OSError, RuntimeError, ValueError) as failure:
        manifest['status'], manifest['stagingError'] = 'failed', str(failure)
        write_json(run_dir / 'copy-manifest.json', manifest)
        raise
    manifest['files'].sort(key=lambda record: record['path'])
    manifest['coreSourceHashes'].sort(key=lambda record: record['path'])
    manifest['buildInputHashes'].sort(key=lambda record: record['path'])
    linked = [record for record in manifest['files'] if record['storage'] == 'read-only-content-cache-hardlink']
    manifest['resourceSharing'] = {'linkedFiles': len(linked), 'sharedBytes': sum(record['bytes'] for record in linked),
                                   'independentCopies': len(manifest['files']) - len(linked),
                                   'uniqueVerifiedCacheBlobs': sum(future.result() is not None for future in resources.blobs.values()),
                                   'verification': 'Source bytes hashed twice; private read-only blobs hashed once per unique content; staged hardlinks checked for matching file identity.'}
    manifest['stagingAndVerificationSeconds'] = round(time.monotonic() - started, 3)
    project = staging / 'project.godot'
    original_hash = digest(project)
    text = project.read_text(encoding='utf-8')
    text = set_application_setting(text, 'config/name', json.dumps('Kairnfall-Classic-QA'))
    text = set_application_setting(text, 'config/use_custom_user_dir', 'true')
    text = set_application_setting(text, 'config/custom_user_dir_name', json.dumps('Kairnfall-Classic-QA'))
    project.write_text(text, encoding='utf-8')
    manifest['overlays'].append({'path': 'project.godot', 'sourceSha256': original_hash,
                                 'stagedSha256': digest(project), 'purpose': 'QA project name and guarded workspace user directory.'})
    guard = staging / 'Tests/ImprovementQaIsolation.gd'
    guard.write_text(GUARD_SOURCE, encoding='utf-8')
    manifest['overlays'].append({'path': guard.relative_to(staging).as_posix(), 'stagedSha256': digest(guard)})
    for suite in suites:
        if not (staging / 'Tests' / (suite + '.tscn')).is_file():
            raise RuntimeError('The selected offline scene is missing: ' + suite)
        wrapper = staging / 'Tests' / ('ImprovementQa_' + suite + '.tscn')
        wrapper.write_text('[gd_scene load_steps=2 format=3]\n\n'
                           '[ext_resource type="Script" path="res://Tests/ImprovementQaIsolation.gd" id="1"]\n\n'
                           '[node name="ImprovementQaIsolation" type="Node"]\n'
                           'script = ExtResource("1")\n'
                           'fixture_scene = "res://Tests/' + suite + '.tscn"\n', encoding='utf-8')
        manifest['overlays'].append({'path': wrapper.relative_to(staging).as_posix(), 'stagedSha256': digest(wrapper)})
    manifest['status'] = 'staged'
    write_json(run_dir / 'copy-manifest.json', manifest)
    # Retain every older stage and failed staging directory. No recursive deletes.
    if STAGE.exists():
        if linklike(STAGE):
            raise RuntimeError('Refusing to replace a linked native QA stage.')
        STAGE.rename(workspace_path(run_dir / 'previous-native-client'))
    staging.rename(STAGE)
    if USER_DIR.exists():
        if linklike(USER_DIR):
            raise RuntimeError('Refusing a linked native QA preferences directory.')
        USER_DIR.rename(workspace_path(run_dir / 'previous-qa-preferences'))
    USER_DIR.mkdir(parents=True, exist_ok=True)
    return manifest


def validate_performance_report(payload: object) -> bool:
    """Retained CI's bounded report checks; no GPU/60 FPS approval is inferred."""
    if not isinstance(payload, dict) or type(payload.get('schema')) is not int or payload['schema'] != 1:
        return False
    for key, count in (('reports', 11), ('syntheticMotion', 48), ('legacySyntheticMotion', 48)):
        rows = payload.get(key)
        if not isinstance(rows, list) or len(rows) != count or not all(isinstance(row, dict) for row in rows):
            return False
    if payload.get('windowsGpuPerformanceApproved') is not False or payload.get('sixtyFpsApproved') is not False:
        return False
    for row in payload['reports']:
        interval = row.get('FrameIntervalMs')
        if not isinstance(interval, dict) or type(interval.get('Count')) is not int or interval['Count'] <= 10:
            return False
    for row in payload['syntheticMotion']:
        lead = row.get('MaxForwardLeadTiles')
        if type(lead) not in (int, float):
            return False
        try:
            if not math.isfinite(lead) or lead > .47:
                return False
        except OverflowError:
            return False
    return True


def execute_fixture(suite: str, godot: Path, env: dict[str, str], run_dir: Path,
                    graphical: bool, timeout: int) -> dict[str, object]:
    log = run_dir / 'logs' / (suite + '.log')
    engine_log = run_dir / 'logs' / (suite + '-engine.log')
    screenshots = run_dir / 'frames' / suite
    screenshots.mkdir(parents=True, exist_ok=True)
    fixture_report = workspace_path(run_dir / 'results' / (suite + '-report.json'))
    suite_env = env | {'KAIRNFALL_SCREENSHOTS': str(screenshots), 'KAIRNFALL_QA_USER_DIR': str(USER_DIR),
                       'KAIRNFALL_PERF_OUTPUT': str(fixture_report)}
    args = [godot, '--verbose', '--path', STAGE, '--max-fps', '60',
            '--rendering-method', 'gl_compatibility', '--audio-driver', 'Dummy',
            '--log-file', engine_log, 'res://Tests/ImprovementQa_' + suite + '.tscn']
    if not graphical:
        args.insert(1, '--headless')
    started = time.monotonic()
    error = None
    exit_code = 0
    try:
        dev.run(args, env=suite_env, timeout=timeout, log=log, check_godot_errors=True)
    except RuntimeError as failure:
        error = str(failure)
        match = re.search(r'failed with exit code (-?\d+)', error)
        exit_code = int(match.group(1)) if match else 0 if 'despite a zero exit code' in error else None
    output = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
    engine = engine_log.read_text(encoding='utf-8', errors='replace') if engine_log.exists() else ''
    marker = SUITE_MARKERS[suite]
    summary = [line for line in output.splitlines() if marker in line and 'passed' in line.lower()]
    isolation = GUARD_MARKER in output
    errors = bool(ENGINE_ERROR.search(output + '\n' + engine))
    passed = error is None and not errors and isolation and bool(summary)
    fixture_report_valid = None
    if suite == 'PerformanceMotionDiagnosticsContract':
        try:
            payload = json.loads(fixture_report.read_text(encoding='utf-8'))
            fixture_report_valid = validate_performance_report(payload)
        except (OSError, ValueError, TypeError):
            fixture_report_valid = False
        if not fixture_report_valid:
            passed = False
            if error is None:
                error = ('Motion JSON report failed the retained bounded contract: schema 1, eleven native reports, '
                         '48 before/after schedules, sample/lead bounds and explicit unapproved GPU/60 FPS flags.')
    if not passed and error is None:
        error = 'Native completion/isolation marker missing or engine error recorded; acceptance failed.'
    result = {'status': 'passed' if passed else 'failed', 'exitCode': exit_code,
              'timedOut': bool(error and 'timed out' in error), 'engineErrors': errors,
              'fixtureSettingsLocationVerified': isolation, 'seconds': round(time.monotonic() - started, 3),
              'mode': 'graphical' if graphical else 'headless', 'summary': summary,
              'error': error, 'log': str(log), 'engineLog': str(engine_log),
              'fixtureReport': str(fixture_report) if fixture_report.is_file() else None,
              'fixtureReportSha256': digest(fixture_report) if fixture_report.is_file() else None,
              'fixtureReportValid': fixture_report_valid,
              'screenshots': [str(p) for p in sorted(screenshots.glob('*.png'))]}
    write_json(run_dir / 'results' / (suite + '.json'), result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--headless', action='store_true', help='Offline rules/UI checks; default mode.')
    mode.add_argument('--graphical', action='store_true', help='Render native fixtures and retain screenshots.')
    build = parser.add_mutually_exclusive_group()
    build.add_argument('--build', action='store_true', help='Explicitly build the local Debug client with --no-restore.')
    build.add_argument('--skip-build', action='store_true', help='Reuse already-built Debug assemblies; default behavior.')
    parser.add_argument('--stage-only', action='store_true', help='Create the exact stage after the isolation probe; no game fixtures launched.')
    parser.add_argument('--isolation-only', action='store_true', help='Verify workspace user:// with a tiny GDScript project; no staging, build, or fixtures.')
    parser.add_argument('--timeout', type=int, default=180, help='Finite per-fixture timeout, 30-600 seconds.')
    parser.add_argument('suites', nargs='*', help='Selected offline fixture names; no live/server suites.')
    args = parser.parse_args()
    if args.isolation_only and (args.build or args.stage_only or args.suites):
        parser.error('--isolation-only cannot be combined with --build, --stage-only, or fixture names.')
    if not 30 <= args.timeout <= 600:
        parser.error('--timeout must be between 30 and 600 seconds.')
    suites = list(dict.fromkeys(args.suites or HEADLESS_SUITES + (('CharacterPresentationContract',) if args.graphical else ())))
    invalid = set(suites).difference(SUITE_MARKERS)
    if invalid:
        parser.error('Unknown or live suite refused: ' + ', '.join(sorted(invalid)))
    if not args.graphical and 'CharacterPresentationContract' in suites:
        parser.error('CharacterPresentationContract requires --graphical; headless runs cannot inspect rendered equipment frames.')
    for path in (OUT, STAGE, USER_DIR):
        workspace_path(path)
    run_dir = workspace_path(OUT / 'runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]))
    run_dir.mkdir(parents=True)
    report = {'createdUtc': timestamp(), 'scope': 'Offline native fixtures; no account, server, database, save or release acceptance.',
              'mode': 'graphical' if args.graphical else 'headless', 'buildRequested': args.build,
              'assemblyProvenance': 'Offline source build requested in this run.' if args.build else 'Existing Debug build copied; no source-to-assembly correspondence is claimed.',
              'serverStarted': False, 'databaseStarted': False, 'networkDownloadsRequested': False,
              'stagedClient': str(STAGE), 'requestedUserDirectory': str(USER_DIR),
              'manifest': str(run_dir / 'copy-manifest.json'),
              'absoluteUserDirectorySemantics': 'Unverified until native isolation guard passes.',
              'selectedSuites': suites, 'results': {name: {'status': 'not-run'} for name in suites}}
    env = {key: value for key, value in os.environ.items() if not key.startswith('KAIRNFALL_')}
    env.update({'DOTNET_CLI_TELEMETRY_OPTOUT': '1', 'DOTNET_SKIP_FIRST_TIME_EXPERIENCE': '1'})
    env = isolated_environment(env)
    exit_code = 1
    try:
        godot = dev.godot_path()
        report['godotBinary'] = str(godot)
        report['isolationProbe'] = isolation_probe(godot, env, run_dir)
        report['absoluteUserDirectorySemantics'] = 'Relative custom name plus workspace platform-data environment verified by native guard.'
        if args.isolation_only:
            report.update({'status': 'isolation-only-passed', 'manifest': None, 'selectedSuites': [], 'results': {},
                           'assemblyProvenance': 'Not applicable; no client assemblies or game fixtures loaded.'})
            return 0
        if args.build:
            dev.run([dev.command('dotnet'), 'build', 'client/Kairnfall.Client.csproj', '-c', 'Debug', '--no-restore'],
                    env=env, timeout=600, log=run_dir / 'logs/client-build.log')
        stage_client(run_dir, suites)
        report['manifest'] = str(run_dir / 'copy-manifest.json')
        if args.stage_only:
            report['status'] = 'staged-only'
            exit_code = 0
        else:
            for suite in suites:
                report['results'][suite] = execute_fixture(suite, godot, env, run_dir, args.graphical, args.timeout)
                write_json(run_dir / 'native-results.json', report)
                if report['results'][suite]['status'] != 'passed':
                    break
            complete = all(result['status'] == 'passed' for result in report['results'].values())
            report['status'] = 'passed' if complete else 'failed'
            exit_code = 0 if complete else 1
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as failure:
        report['status'] = 'failed'
        report['harnessError'] = str(failure)
        print('Native QA failed: ' + str(failure), file=sys.stderr)
    finally:
        report['completedUtc'] = timestamp()
        write_json(run_dir / 'native-results.json', report)
        print('Retained native QA evidence: ' + str(run_dir))
    return exit_code


if __name__ == '__main__':
    # Native labels can contain symbols outside Windows' legacy console page.
    # Preserve UTF-8 logs and reach engine-error screening after printing them.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    raise SystemExit(main())
