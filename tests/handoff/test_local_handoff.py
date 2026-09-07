from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import local_dev as dev
import complete_skill_icons as icons


class HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))

    def test_all_sixty_skills_have_valid_renderable_sources(self):
        self.assertEqual(len(self.catalog['skills']), 60)
        for skill in self.catalog['skills']:
            with self.subTest(skill=skill['id']):
                kind, source = icons.select_source(skill, self.catalog)
                image = icons.ability_icon(source) if kind == 'ability' else icons.item_icon(source)
                self.assertEqual(image.mode, 'RGBA')
                self.assertEqual(image.size, (32, 32))
                self.assertIsNotNone(image.getchannel('A').getbbox())

    def test_unknown_skill_fails_instead_of_using_placeholder(self):
        with self.assertRaises(ValueError):
            icons.select_source({'id': 'missing_skill', 'category': 'Utility'}, self.catalog)

    def test_missing_explicit_item_source_fails(self):
        with self.assertRaises(ValueError):
            icons.select_source({'id': 'mining', 'category': 'Gathering'}, {'items': [], 'abilities': []})

    def test_private_credentials_are_distinct_and_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            private = Path(temporary) / 'private'
            missing_volume = subprocess.CompletedProcess([], 1, b'', b'')
            with patch.object(dev, 'PRIVATE', private), patch.object(dev, 'command', return_value='docker'), \
                    patch.object(dev.subprocess, 'run', return_value=missing_volume):
                first = dev.load_credentials()
                encoded = (private / 'database.json').read_bytes()
                second = dev.load_credentials()
            self.assertNotEqual(first['development'], first['testing'])
            self.assertEqual(len(first['development']), 64)
            self.assertEqual(first, second)
            self.assertEqual(encoded, (private / 'database.json').read_bytes())

    def test_existing_volume_without_password_is_not_reset(self):
        with tempfile.TemporaryDirectory() as temporary:
            private = Path(temporary) / 'private'
            volume_exists = subprocess.CompletedProcess([], 0, b'[]', b'')
            with patch.object(dev, 'PRIVATE', private), patch.object(dev, 'command', return_value='docker'), \
                    patch.object(dev.subprocess, 'run', return_value=volume_exists):
                with self.assertRaisesRegex(RuntimeError, 'credential file is missing'):
                    dev.load_credentials()
            self.assertFalse((private / 'database.json').exists())

    def test_invalid_password_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            private = Path(temporary)
            path = private / 'database.json'
            path.write_text('{"schema":99}', encoding='utf-8')
            before = path.read_bytes()
            with patch.object(dev, 'PRIVATE', private):
                with self.assertRaises(RuntimeError):
                    dev.load_credentials()
            self.assertEqual(before, path.read_bytes())

    def test_test_database_does_not_inherit_game_database(self):
        data = {'development': '1' * 64, 'testing': '2' * 64}
        with patch.dict(dev.os.environ, {'KAIRNFALL_DB': 'production', 'KAIRNFALL_TEST_DB': 'unsafe'}, clear=True), \
                patch.object(dev, 'compose_prefix', return_value=['docker', 'compose']), \
                patch.object(dev, 'load_credentials', return_value=data), patch.object(dev, 'run', return_value='') as run:
            env, _ = dev.start_database(testing=True)
        self.assertNotIn('KAIRNFALL_DB', env)
        self.assertIn('Port=55433;', env['KAIRNFALL_TEST_DB'])
        self.assertIn('Database=kairnfall_test;', env['KAIRNFALL_TEST_DB'])
        self.assertEqual(env['ASPNETCORE_ENVIRONMENT'], 'Testing')
        self.assertTrue(any('test-postgres' in call.args[0] for call in run.call_args_list))
        for call in run.call_args_list:
            self.assertNotIn(data['testing'], ' '.join(map(str, call.args[0])))
            self.assertNotIn(data['development'], ' '.join(map(str, call.args[0])))

    def test_game_database_does_not_inherit_test_database(self):
        data = {'development': '1' * 64, 'testing': '2' * 64}
        with patch.dict(dev.os.environ, {'KAIRNFALL_TEST_DB': 'unsafe'}, clear=True), \
                patch.object(dev, 'compose_prefix', return_value=['docker', 'compose']), \
                patch.object(dev, 'load_credentials', return_value=data), patch.object(dev, 'run', return_value=''):
            env, _ = dev.start_database(testing=False)
        self.assertNotIn('KAIRNFALL_TEST_DB', env)
        self.assertIn('Port=55432;', env['KAIRNFALL_DB'])
        self.assertIn('Database=kairnfall;', env['KAIRNFALL_DB'])
        self.assertEqual(env['ASPNETCORE_URLS'], 'http://127.0.0.1:5077')

    def test_nonzero_native_result_fails_and_logs_are_redacted(self):
        result = subprocess.CompletedProcess(['tool'], 17, 'Password=private-value; failure\n', '')
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'run.log'
            with patch.object(dev.subprocess, 'run', return_value=result), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, 'exit code 17'):
                    dev.run(['tool'], log=target)
            self.assertNotIn('private-value', target.read_text(encoding='utf-8'))
            self.assertIn('[REDACTED]', target.read_text(encoding='utf-8'))

    def test_environment_secrets_are_redacted(self):
        text = dev.scrub('db-secret bearer-secret', {'PGPASSWORD': 'db-secret', 'ACCESS_TOKEN': 'bearer-secret'})
        self.assertNotIn('db-secret', text)
        self.assertNotIn('bearer-secret', text)

    def test_zero_exit_godot_errors_fail_acceptance_and_preserve_log(self):
        for stream in ('stdout', 'stderr'):
            for error in ('ERROR: 2 resources still in use at exit.',
                          'SCRIPT ERROR: Invalid call.', 'Unhandled exception: native bridge failure'):
                with self.subTest(stream=stream, error=error), tempfile.TemporaryDirectory() as temporary:
                    result = subprocess.CompletedProcess(['godot'], 0,
                        error if stream == 'stdout' else '', error if stream == 'stderr' else '')
                    target = Path(temporary) / 'godot.log'
                    with patch.object(dev.subprocess, 'run', return_value=result), contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaisesRegex(RuntimeError, 'Godot reported'):
                            dev.run(['godot'], log=target, check_godot_errors=True)
                    self.assertIn(error, target.read_text(encoding='utf-8'))

    def test_git_excludes_local_state_and_generated_output(self):
        paths = ['.local/database.json', '.venv/config', '.tools/editor.zip',
                 'artifacts/private.log', 'client/Assets/catalog.json', 'client/Data/catalog.json', 'build/client/game.pck']
        # Binary NUL-separated paths avoid Windows newline translation and Git quoting.
        result = subprocess.run(['git', 'check-ignore', '--no-index', '-z', '--stdin'], cwd=ROOT,
                                input=('\0'.join(paths) + '\0').encode('utf-8'),
                                capture_output=True, check=True)
        actual = {entry.decode('utf-8') for entry in result.stdout.split(b'\0') if entry}
        self.assertEqual(actual, set(paths))

    def test_compose_is_local_and_test_storage_is_separate(self):
        text = (ROOT / 'compose.local.yml').read_text(encoding='utf-8')
        for expected in ('127.0.0.1:55432:5432', '127.0.0.1:55433:5432',
                         'realm:/var/lib/postgresql', 'tests:/var/lib/postgresql',
                         'KAIRNFALL_DEV_PASSWORD', 'KAIRNFALL_TEST_PASSWORD'):
            self.assertIn(expected, text)
        self.assertNotIn('0.0.0.0', text)
        self.assertNotIn('POSTGRES_HOST_AUTH_METHOD: trust', text)

    def test_database_test_wrapper_requires_explicit_opt_in(self):
        wrapper = (ROOT / 'Test-Kairnfall-Local.ps1').read_text(encoding='utf-8')
        self.assertIn('[switch]$WithDatabase', wrapper)
        self.assertIn("$env:KAIRNFALL_ALLOW_DB_TESTS = '1'", wrapper)
        self.assertIn('finally', wrapper)

    def test_security_and_native_client_repairs_are_retained(self):
        self.assertTrue((ROOT / 'tests/Kairnfall.SecurityTests/Kairnfall.SecurityTests.csproj').is_file())
        ui = (ROOT / 'client/Scripts/Ui.cs').read_text(encoding='utf-8')
        self.assertIn('new ActionButton', ui)
        self.assertTrue((ROOT / 'client/Tests/SignalContract.tscn').is_file())
        core = '\n'.join(path.read_text(encoding='utf-8') for path in (ROOT / 'src/Kairnfall.Core').glob('*.cs'))
        self.assertIn('ApprovedFingerprint', core)
        self.assertIn('SplitStack', core)

    def test_source_generation_sequence_includes_skill_completion(self):
        text = (ROOT / 'tools/local_dev.py').read_text(encoding='utf-8')
        start = text.index('def assets()')
        end = text.index('def compose_prefix()', start)
        body = text[start:end]
        self.assertLess(body.index('build_game_assets.py'), body.index('complete_skill_icons.py'))
        self.assertLess(body.index('complete_skill_icons.py'), body.index('validate_game_assets.py'))

    def test_readme_and_handoff_document_links_exist(self):
        for name in ('README.md', 'HANDOFF.md'):
            text = (ROOT / name).read_text(encoding='utf-8')
            for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
                if '://' not in target and not target.startswith('#'):
                    self.assertTrue((ROOT / target.split('#', 1)[0]).is_file(), (name, target))
        for name in ('docs/requirements/ACCEPTED_REQUIREMENTS.md', 'docs/handoff/LOCAL_AGENT_PROMPT.md',
                     'docs/handoff/SOURCE_PROVENANCE.json', 'docs/QA_MATRIX.md', 'docs/FINAL_AUDIT.md'):
            self.assertTrue((ROOT / name).is_file(), name)


if __name__ == '__main__':
    unittest.main()
