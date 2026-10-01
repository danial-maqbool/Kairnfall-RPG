"""Filesystem/runner boundaries without Godot, builds, servers or player data.

Every file is synthetic and confined to one disposable workspace directory.
Native calls are mocked; these tests do not constitute native acceptance.
"""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import run_improvement_native_qa as qa


class ImprovementNativeQaTests(unittest.TestCase):
    def setUp(self):
        self.workspace = qa.ROOT.resolve()
        container = self.workspace / 'artifacts'
        self.assertTrue(container.resolve().is_relative_to(self.workspace))
        container.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='improvement-qa-unit-', dir=container)
        self.root = Path(self.temporary.name).resolve()
        self.client = self.root / 'client'
        self.out = self.root / 'artifacts/qa'
        self.stage = self.out / 'native-client'
        self.user = self.out / 'Kairnfall-Classic-QA'
        self.context = ExitStack()
        for name, value in (('ROOT', self.root), ('CLIENT', self.client), ('OUT', self.out),
                            ('STAGE', self.stage), ('USER_DIR', self.user)):
            self.context.enter_context(patch.object(qa, name, value))
        self.context.enter_context(redirect_stdout(StringIO()))
        self.context.enter_context(redirect_stderr(StringIO()))

    def tearDown(self):
        self.context.close()
        # Verify the absolute cleanup target before TemporaryDirectory recurses.
        self.assertTrue(self.root.is_relative_to(self.workspace / 'artifacts'))
        self.temporary.cleanup()

    def file(self, relative, data=b'fixture'):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_path_guard_rejects_escape_link_and_resolved_parent_with_diagnostics(self):
        self.assertEqual(qa.workspace_path(self.out / 'results/a.json'), self.out / 'results/a.json')
        outside = self.root.parent / 'outside-unit-scope'
        with self.assertRaisesRegex(RuntimeError, 'requested path is outside'):
            qa.workspace_path(outside, purpose='test output')
        with patch.object(qa, 'linklike', return_value=True), self.assertRaisesRegex(RuntimeError, 'symlink or junction'):
            qa.workspace_path(self.out / 'link')
        with patch.object(Path, 'resolve', return_value=outside), self.assertRaisesRegex(RuntimeError, 'resolved output directory'):
            qa.workspace_path(self.out / 'nested/a.json')
        try:
            qa.workspace_path(outside, purpose='guard evidence')
        except RuntimeError as failure:
            self.assertIn('guard evidence', str(failure))
            self.assertIn(repr(str(outside)), str(failure))
            self.assertIn(repr(str(self.root)), str(failure))

    def test_inventory_refuses_linked_resource_entries(self):
        folder = self.root / 'resources'
        folder.mkdir()
        self.file('resources/ordinary.png')
        with patch.object(qa, 'linklike', side_effect=lambda path: path.name == 'ordinary.png'):
            with self.assertRaisesRegex(RuntimeError, 'linked QA resources'):
                qa.files_under(folder)
        self.assertEqual(qa.files_under(folder), [folder / 'ordinary.png'])

    def test_environment_overrides_child_paths_without_changing_input_or_process_environment(self):
        original = dict(os.environ)
        supplied = {'APPDATA': 'personal-data', 'XDG_DATA_HOME': 'personal-xdg', 'UNCHANGED': 'value'}
        isolated = qa.isolated_environment(supplied)
        self.assertEqual(supplied['APPDATA'], 'personal-data')
        self.assertEqual(dict(os.environ), original)
        self.assertEqual(isolated['UNCHANGED'], 'value')
        for name in ('APPDATA', 'LOCALAPPDATA', 'XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME'):
            path = Path(isolated[name])
            self.assertTrue(path.is_relative_to(self.root))
            self.assertTrue(path.is_dir())
        self.assertEqual(isolated['APPDATA'], str(self.out))

    def test_project_overlay_changes_only_application_keys(self):
        source = '[application]\nconfig/name="Ordinary"\nconfig/use_custom_user_dir=false\n\n[display]\nwindow/size=12\n'
        changed = qa.set_application_setting(source, 'config/name', '"Kairnfall-Classic-QA"')
        changed = qa.set_application_setting(changed, 'config/custom_user_dir_name', '"Kairnfall-Classic-QA"')
        self.assertEqual(changed.count('config/name='), 1)
        self.assertIn('config/name="Kairnfall-Classic-QA"', changed)
        self.assertIn('config/custom_user_dir_name="Kairnfall-Classic-QA"', changed)
        self.assertTrue(changed.endswith('[display]\nwindow/size=12\n'))
        with self.assertRaisesRegex(RuntimeError, 'no application section'):
            qa.set_application_setting('[display]\nx=1\n', 'config/name', '"QA"')

    def test_source_hashing_rejects_a_file_changed_during_read(self):
        source = self.file('client/Scripts/Example.cs', b'before')
        original = qa.digest
        def changed(path):
            value = original(path)
            path.write_bytes(b'changed length')
            return value
        with patch.object(qa, 'digest', side_effect=changed), self.assertRaisesRegex(RuntimeError, 'changed while hashing'):
            qa.source_record(source)

    def test_freshness_rejects_newer_inputs_and_keeps_compiler_provenance_limit_explicit(self):
        source = self.file('src/Kairnfall.Core/Example.cs')
        dll = self.file('client/' + qa.ASSEMBLIES.as_posix() + '/Kairnfall.Core.dll')
        os.utime(source, ns=(10_000_000_000, 10_000_000_000))
        os.utime(dll, ns=(20_000_000_000, 20_000_000_000))
        fresh = qa.assembly_freshness({'Kairnfall.Core.dll': [source]})
        self.assertEqual(fresh['status'], 'no-newer-inputs-detected')
        self.assertIn('does not prove compilation correspondence', fresh['method'])
        os.utime(source, ns=(30_000_000_000, 30_000_000_000))
        stale = qa.assembly_freshness({'Kairnfall.Core.dll': [source]})
        self.assertEqual(stale['status'], 'stale')
        self.assertEqual(stale['assemblies'][0]['newerInputs'], ['src/Kairnfall.Core/Example.cs'])

    def test_cache_reuse_retains_prior_stage_bytes_after_live_source_changes(self):
        source = self.file('client/Assets/items/one.png', b'first pixels')
        first, second = self.out / 'first', self.out / 'second'
        (first / 'Assets/items').mkdir(parents=True)
        (second / 'Assets/items').mkdir(parents=True)
        resources = qa.ResourceCache()
        one = qa.copy_resource(source, first, resources)
        first_target = first / source.relative_to(self.client)
        self.assertEqual(one['sourceSha256'], one['copiedSha256'])
        self.assertEqual(first_target.read_bytes(), b'first pixels')
        source.write_bytes(b'new live pixels')
        two = qa.copy_resource(source, second, resources)
        self.assertNotEqual(one['sourceSha256'], two['sourceSha256'])
        self.assertEqual(first_target.read_bytes(), b'first pixels')
        self.assertEqual((second / source.relative_to(self.client)).read_bytes(), b'new live pixels')

    def test_corrupt_content_addressed_cache_fails_closed(self):
        source = self.file('client/Assets/test.png', b'pixels')
        record = qa.source_record(source)
        resources = qa.ResourceCache()
        cache = resources.root / record['sha256'][:2] / record['sha256']
        cache.parent.mkdir(parents=True)
        cache.write_bytes(b'wrong bytes')
        with self.assertRaisesRegex(RuntimeError, 'cache failed its content hash'):
            resources.prepared(source, record)

    def fixture(self, *, text=None, failure=None, engine='', suite='InputContract', payload=None):
        run = self.out / ('run-' + str(len(list(self.out.glob('run-*'))) if self.out.exists() else 0))
        run.mkdir(parents=True)
        def execute(args, *, env, timeout, log, check_godot_errors):
            self.assertTrue(check_godot_errors)
            self.assertEqual(timeout, 30)
            self.assertEqual(env['KAIRNFALL_QA_USER_DIR'], str(self.user))
            self.assertTrue(Path(env['KAIRNFALL_PERF_OUTPUT']).is_relative_to(run))
            log.parent.mkdir(parents=True, exist_ok=True)
            output = text if text is not None else qa.GUARD_MARKER + str(self.user) + '\n' + qa.SUITE_MARKERS[suite] + ' passed\n'
            log.write_text(output, encoding='utf-8')
            engine_log = Path(args[args.index('--log-file') + 1])
            engine_log.write_text(engine, encoding='utf-8')
            if payload is not None:
                target = Path(env['KAIRNFALL_PERF_OUTPUT'])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(payload), encoding='utf-8')
            if failure:
                raise RuntimeError(failure)
        with patch.object(qa.dev, 'run', side_effect=execute):
            result = qa.execute_fixture(suite, Path('synthetic-godot'), {}, run, False, 30)
        self.assertTrue(Path(result['log']).is_file())
        return result

    def test_zero_exit_engine_errors_missing_guard_and_missing_completion_fail(self):
        good = self.fixture()
        self.assertEqual(good['status'], 'passed')
        for text, engine in (
            (qa.GUARD_MARKER + str(self.user) + '\nINPUT_CONTRACT: passed\nERROR: failed frame\n', ''),
            (None, 'SCRIPT ERROR: failed frame'),
            ('INPUT_CONTRACT: passed\n', ''),
            (qa.GUARD_MARKER + str(self.user) + '\n', ''),
        ):
            result = self.fixture(text=text, engine=engine)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['exitCode'], 0)
            self.assertIsNotNone(result['error'])

    def test_timeout_and_nonzero_exit_preserve_failed_fixture_evidence(self):
        timeout = self.fixture(failure='godot timed out after 30 seconds.')
        self.assertEqual(timeout['status'], 'failed')
        self.assertTrue(timeout['timedOut'])
        self.assertIsNone(timeout['exitCode'])
        nonzero = self.fixture(failure='godot failed with exit code 7.')
        self.assertEqual(nonzero['status'], 'failed')
        self.assertEqual(nonzero['exitCode'], 7)

    def test_failed_fixture_leaves_subsequent_selected_fixtures_explicitly_unrun(self):
        result = {'status': 'failed', 'error': 'synthetic failure'}
        with patch.object(sys, 'argv', ['qa', '--headless', 'InputContract', 'ControlRulesContract']), \
                patch.object(qa.dev, 'godot_path', return_value=Path('synthetic-godot')), \
                patch.object(qa, 'isolation_probe', return_value={'status': 'passed'}), \
                patch.object(qa, 'stage_client'), \
                patch.object(qa, 'execute_fixture', return_value=result) as execute:
            self.assertEqual(qa.main(), 1)
        execute.assert_called_once()
        reports = list((self.out / 'runs').glob('*/native-results.json'))
        self.assertEqual(len(reports), 1)
        payload = json.loads(reports[0].read_text(encoding='utf-8'))
        self.assertEqual(payload['status'], 'failed')
        self.assertEqual(payload['results']['InputContract']['status'], 'failed')
        self.assertEqual(payload['results']['ControlRulesContract']['status'], 'not-run')
        self.assertFalse(payload['serverStarted'])
        self.assertFalse(payload['databaseStarted'])

    def test_cli_refuses_live_suites_headless_character_and_unbounded_timeout(self):
        for args in (['Smoke'], ['--headless', 'CharacterPresentationContract'], ['--timeout', '999999']):
            with patch.object(sys, 'argv', ['qa', *args]), patch.object(qa.dev, 'godot_path') as native:
                with self.assertRaises(SystemExit):
                    qa.main()
                native.assert_not_called()

    def test_performance_report_rejects_48_key_objects_instead_of_schedule_arrays(self):
        payload = {'schema': 1, 'syntheticMotion': {str(i): {} for i in range(48)},
                   'legacySyntheticMotion': {str(i): {} for i in range(48)}}
        result = self.fixture(suite='PerformanceMotionDiagnosticsContract', payload=payload)
        self.assertEqual(result['status'], 'failed')

    def test_performance_report_rejects_missing_native_scenarios_and_false_gpu_approval(self):
        payload = {'schema': 1, 'syntheticMotion': [{}] * 48, 'legacySyntheticMotion': [{}] * 48,
                   'reports': [], 'windowsGpuPerformanceApproved': True, 'sixtyFpsApproved': True}
        result = self.fixture(suite='PerformanceMotionDiagnosticsContract', payload=payload)
        self.assertEqual(result['status'], 'failed')

    def performance_payload(self):
        return {'schema': 1, 'reports': [{'FrameIntervalMs': {'Count': 20}} for _ in range(11)],
                'syntheticMotion': [{'MaxForwardLeadTiles': .46} for _ in range(48)],
                'legacySyntheticMotion': [{} for _ in range(48)],
                'windowsGpuPerformanceApproved': False, 'sixtyFpsApproved': False}

    def test_performance_report_accepts_retained_ci_shape_and_preserves_hash_evidence(self):
        payload = self.performance_payload()
        self.assertTrue(qa.validate_performance_report(payload))
        result = self.fixture(suite='PerformanceMotionDiagnosticsContract', payload=payload)
        self.assertEqual(result['status'], 'passed')
        self.assertTrue(result['fixtureReportValid'])
        self.assertEqual(result['fixtureReportSha256'], qa.digest(Path(result['fixtureReport'])))

    def test_performance_report_rejects_boolean_schema_untyped_rows_counts_flags_and_bounds(self):
        for key, value in (('schema', True), ('schema', 1.0), ('schema', '1'),
                           ('reports', [{}] * 10), ('reports', [None] * 11),
                           ('syntheticMotion', []), ('legacySyntheticMotion', [{}] * 47),
                           ('legacySyntheticMotion', [0] * 48),
                           ('windowsGpuPerformanceApproved', 0), ('windowsGpuPerformanceApproved', True),
                           ('sixtyFpsApproved', None), ('sixtyFpsApproved', True)):
            with self.subTest(key=key, value=value):
                payload = self.performance_payload()
                payload[key] = value
                self.assertFalse(qa.validate_performance_report(payload))
        for count in (True, 10, 11.0, None):
            payload = self.performance_payload()
            payload['reports'][0]['FrameIntervalMs']['Count'] = count
            self.assertFalse(qa.validate_performance_report(payload))
        for lead in (True, None, .471, float('nan'), float('inf'), -float('inf'), -10**400):
            payload = self.performance_payload()
            payload['syntheticMotion'][0]['MaxForwardLeadTiles'] = lead
            self.assertFalse(qa.validate_performance_report(payload))
        for malformed in (None, [], {}, {'schema': 1}):
            self.assertFalse(qa.validate_performance_report(malformed))


if __name__ == '__main__':
    unittest.main()
