"""Broad-pass evidence rejects stale, replayed, partial and unauthorized proof.

Fixtures here are structural examples, never claimed to be real Actions runs.
"""
from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
from io import StringIO
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import documentation_contract as router
import improvement_delivery_contract as contract


def metadata_fixture():
    """An offline schema example for the eventual verified evidence sync."""
    sha = 'a' * 40
    rows = []
    for index, (name, (path, prefixes)) in enumerate(sorted(contract.WORKFLOWS.items())):
        run_id = 1000 + index
        names = sorted(contract.NATIVE_JOBS.get(name, {'verify'}))
        rows.append({
            'name': name, 'workflowPath': path, 'workflowId': 100 + index,
            'runId': run_id, 'runAttempt': 1, 'repository': contract.REPOSITORY,
            'headBranch': 'main', 'headSha': sha, 'event': 'push',
            'status': 'completed', 'conclusion': 'success',
            'jobs': [{
                'id': 10000 + index * 10 + job_index, 'name': job_name,
                'runId': run_id, 'runAttempt': 1, 'headSha': sha,
                'status': 'completed', 'conclusion': 'success',
            } for job_index, job_name in enumerate(names)],
            'artifacts': [{
                'id': 20000 + index * 10 + artifact_index, 'name': prefix + sha,
                'sizeBytes': 512, 'digest': 'sha256:' + 'b' * 64,
                'expired': False, 'runId': run_id, 'headSha': sha, 'headBranch': 'main',
            } for artifact_index, prefix in enumerate(prefixes)],
        })
    return {
        'schema': 1, 'currentTask': contract.WORKSTREAM, 'statusDate': '2026-10-01',
        'repository': contract.REPOSITORY, 'persistentBranches': ['main'],
        'startingMain': contract.STARTING_MAIN, 'implementationBaseline': sha,
        'repositorySideBatchComplete': True, 'serverAuthoritative': True,
        'oldSavesCompatible': True, 'temporaryToolingRemoved': True,
        'wholeGameComplete': False, 'publicationReady': False,
        'releasePublished': False, 'deployed': False,
        'performanceTargetClaimed': False, 'windowsGpuPerformanceApproved': False,
        'sixtyFpsApproved': False, 'releaseStatus': contract.RELEASE_STATUS,
        'authorization': {
            'implementationAuthorized': True, 'publicationAuthorized': False,
            'deploymentAuthorized': False, 'productionInfrastructureChanged': False,
        },
        'humanAcceptance': 'not-run', 'humanOnlyGates': ['Owner Windows gameplay, art, audio and feel acceptance'],
        'nativeAcceptancePlatforms': ['linux', 'windows'],
        'historicalEvidenceBlobs': deepcopy(contract.HISTORICAL_BLOBS),
        'changedPaths': ['src/Kairnfall.Core/RealmCombat.cs', 'tools/improvement_delivery_contract.py'],
        'implementationWorkflows': rows,
    }


def remote_fixture(row):
    run = {
        'id': row['runId'], 'name': row['name'], 'workflow_id': row['workflowId'],
        'path': row['workflowPath'], 'run_attempt': row['runAttempt'],
        'repository': {'full_name': row['repository']}, 'head_sha': row['headSha'],
        'head_branch': row['headBranch'], 'event': row['event'],
        'status': row['status'], 'conclusion': row['conclusion'],
    }
    workflow = {'id': row['workflowId'], 'name': row['name'], 'path': row['workflowPath'], 'state': 'active'}
    jobs = [{
        'id': item['id'], 'name': item['name'], 'run_id': item['runId'],
        'run_attempt': item['runAttempt'], 'head_sha': item['headSha'],
        'status': item['status'], 'conclusion': item['conclusion'],
        # Conditional OS steps are allowed to be skipped, unlike whole jobs.
        'steps': [{'name': 'Other platform', 'status': 'completed', 'conclusion': 'skipped'}],
    } for item in row['jobs']]
    artifacts = [{
        'id': item['id'], 'name': item['name'], 'size_in_bytes': item['sizeBytes'],
        'digest': item['digest'], 'expired': item['expired'],
        'workflow_run': {'id': item['runId'], 'head_sha': item['headSha'], 'head_branch': item['headBranch']},
    } for item in row['artifacts']]
    return run, workflow, jobs, artifacts


class ImprovementEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.evidence = metadata_fixture()
        self.sha = self.evidence['implementationBaseline']
        self.row = next(row for row in self.evidence['implementationWorkflows']
                        if row['name'] == 'Client performance and motion diagnostics')
        self.remote, self.workflow, self.jobs, self.artifacts = remote_fixture(self.row)

    def test_complete_schema_and_real_api_shapes_accept_exact_identity(self):
        self.assertEqual(contract.validate_metadata(self.evidence), self.sha)
        self.assertEqual(len(contract.WORKFLOWS), 16)
        for row in self.evidence['implementationWorkflows']:
            run, workflow, jobs, artifacts = remote_fixture(row)
            contract.validate_remote_run(row, run, workflow, self.sha)
            contract.validate_remote_jobs(row, jobs, self.sha)
            contract.validate_remote_artifacts(row, artifacts, self.sha)

    def test_malformed_source_repository_date_and_workstream_are_rejected(self):
        for key, value in (
            ('schema', True), ('schema', 2), ('currentTask', 'smoothness-performance-polish'),
            ('startingMain', 'c' * 40), ('implementationBaseline', 'a' * 39),
            ('implementationBaseline', 'A' * 40), ('repository', 'other/repo'),
            ('persistentBranches', ['main', 'candidate']), ('statusDate', '2026-02-30'),
            ('statusDate', '20261001'), ('statusDate', None),
        ):
            with self.subTest(key=key, value=value):
                changed = deepcopy(self.evidence)
                changed[key] = value
                with self.assertRaises(RuntimeError):
                    contract.validate_metadata(changed)

    def test_release_whole_game_and_human_approval_cannot_be_inferred(self):
        for key in ('repositorySideBatchComplete', 'serverAuthoritative', 'oldSavesCompatible', 'temporaryToolingRemoved'):
            changed = deepcopy(self.evidence)
            changed[key] = False
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)
        for key in ('wholeGameComplete', 'publicationReady', 'releasePublished', 'deployed',
                    'performanceTargetClaimed', 'windowsGpuPerformanceApproved', 'sixtyFpsApproved'):
            changed = deepcopy(self.evidence)
            changed[key] = True
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)
        for key, value in (('humanAcceptance', 'approved'), ('humanOnlyGates', []),
                           ('nativeAcceptancePlatforms', ['windows']), ('releaseStatus', 'APPROVED')):
            changed = deepcopy(self.evidence)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)
        for key in ('publicationAuthorized', 'deploymentAuthorized', 'productionInfrastructureChanged'):
            changed = deepcopy(self.evidence)
            changed['authorization'][key] = True
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)

    def test_missing_duplicate_replayed_wrongpath_or_skipped_workflows_are_rejected(self):
        mutations = (
            ('workflowPath', '.github/workflows/visual-review.yml'), ('workflowId', True),
            ('runId', True), ('runAttempt', 0), ('repository', 'other/repo'),
            ('headBranch', 'candidate'), ('headSha', 'c' * 40), ('event', 'pull_request'),
            ('status', 'in_progress'), ('conclusion', 'skipped'), ('conclusion', 'failure'),
        )
        for key, value in mutations:
            changed = deepcopy(self.evidence)
            changed['implementationWorkflows'][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)
        for mutation in ('missing', 'duplicate', 'replayed-run', 'replayed-workflow'):
            changed = deepcopy(self.evidence)
            rows = changed['implementationWorkflows']
            if mutation == 'missing':
                rows.pop()
            elif mutation == 'duplicate':
                rows[1] = deepcopy(rows[0])
            else:
                key = 'runId' if mutation == 'replayed-run' else 'workflowId'
                rows[1][key] = rows[0][key]
                if key == 'runId':
                    for item in rows[1]['jobs'] + rows[1]['artifacts']:
                        item['runId'] = rows[1]['runId']
            with self.subTest(mutation=mutation), self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)

    def test_private_generated_traversal_and_unauthorized_paths_are_rejected(self):
        for path in ('../src/a.cs', '/src/a.cs', 'C:/src/a.cs', 'src\\a.cs', 'src//a.cs',
                     './src/a.cs', 'src/./a.cs', 'src/../a.cs', 'client/.godot/a.dll',
                     'src/bin/a.dll', 'src/.env', 'docs/backups/a.sql', 'saves/owner.json',
                     'src/newline\nfile.cs', 'src/nul\0file.cs',
                     'artifacts/result.json', '.github/workflows/acceptance-dispatch.yml',
                     'production/server.yml', 'unknown/file.txt'):
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                contract.validate_path(path)
        for path in ('client/Scripts/GameRoot.cs', 'src/Kairnfall.Server/Program.cs',
                     'content_src/opening_journey.py', 'art/original.png',
                     'docs/handoff/IMPROVEMENT_VERIFICATION.md', 'HANDOFF.md'):
            contract.validate_path(path)
        for paths in ([], ['src/a.cs', 'src/a.cs'], ['tools/a.py', 'src/a.cs']):
            changed = deepcopy(self.evidence)
            changed['changedPaths'] = paths
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)

    def test_historical_task_and_checkpoint_bytes_cannot_be_rebased(self):
        contract.validate_archive_blobs(deepcopy(contract.HISTORICAL_BLOBS))
        for path in contract.HISTORICAL_BLOBS:
            blobs = deepcopy(contract.HISTORICAL_BLOBS)
            blobs[path] = 'c' * 40
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                contract.validate_archive_blobs(blobs)
            changed = deepcopy(self.evidence)
            changed['historicalEvidenceBlobs'] = blobs
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)
        original = (contract.ROOT / 'docs/handoff/CURRENT_EVIDENCE.json').read_bytes()
        if b'"currentTask": "smoothness-performance-polish"' in original:
            self.assertEqual(contract.blob_identity(original), contract.HISTORICAL_BLOBS[contract.CHECKPOINT3_ARCHIVE])
        self.assertNotEqual(contract.blob_identity(b'{}\n'), contract.blob_identity(b'{}\r\n'))

    def test_job_identity_attempt_completion_duplicates_and_native_coverage(self):
        for key, value in (('id', True), ('name', ''), ('runId', 99), ('runAttempt', 2),
                           ('headSha', 'c' * 40), ('status', 'queued'), ('conclusion', 'skipped')):
            jobs = deepcopy(self.row['jobs'])
            jobs[0][key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                contract.validate_jobs(self.row, jobs, self.sha)
        for jobs in ([], self.row['jobs'][:1], [self.row['jobs'][0], self.row['jobs'][0]]):
            with self.assertRaises(RuntimeError):
                contract.validate_jobs(self.row, jobs, self.sha)
        changed = deepcopy(self.evidence)
        rows = changed['implementationWorkflows']
        rows[1]['jobs'][0]['id'] = rows[0]['jobs'][0]['id']
        with self.assertRaises(RuntimeError):
            contract.validate_metadata(changed)

    def test_artifact_id_digest_source_expiry_and_replay_are_rejected(self):
        for key, value in (('id', True), ('name', 'wrong-source'), ('name', {}), ('sizeBytes', 0),
                           ('digest', 'b' * 64), ('digest', None), ('expired', True),
                           ('runId', 9), ('headSha', 'c' * 40), ('headBranch', 'candidate')):
            artifacts = deepcopy(self.row['artifacts'])
            artifacts[0][key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                contract.validate_artifacts(self.row, artifacts, self.sha)
        for artifacts in (None, [], self.row['artifacts'][:1], self.row['artifacts'] * 2):
            with self.assertRaises(RuntimeError):
                contract.validate_artifacts(self.row, artifacts, self.sha)
        changed = deepcopy(self.evidence)
        rows = [row for row in changed['implementationWorkflows'] if row['artifacts']]
        rows[1]['artifacts'][0]['id'] = rows[0]['artifacts'][0]['id']
        with self.assertRaises(RuntimeError):
            contract.validate_metadata(changed)

    def test_live_run_wrong_path_workflow_attempt_repository_head_and_completion(self):
        for key, value in (('id', 99), ('name', 'different'), ('workflow_id', 99),
                           ('path', '.github/workflows/client.yml'), ('run_attempt', 2),
                           ('repository', {'full_name': 'other/repo'}), ('head_sha', 'c' * 40),
                           ('head_branch', 'candidate'), ('event', 'pull_request'),
                           ('status', 'in_progress'), ('conclusion', 'skipped')):
            actual = deepcopy(self.remote)
            actual[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                contract.validate_remote_run(self.row, actual, self.workflow, self.sha)
        for key, value in (('id', 99), ('name', 'different'), ('path', '.github/workflows/client.yml'),
                           ('state', 'disabled_manually')):
            workflow = deepcopy(self.workflow)
            workflow[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                contract.validate_remote_run(self.row, self.remote, workflow, self.sha)

    def test_live_job_inventory_must_equal_the_complete_successful_attempt(self):
        for key, value in (('id', 999), ('name', 'different'), ('run_attempt', 2),
                           ('head_sha', 'c' * 40), ('conclusion', 'skipped')):
            jobs = deepcopy(self.jobs)
            jobs[0][key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                contract.validate_remote_jobs(self.row, jobs, self.sha)
        for jobs in (self.jobs[:1], self.jobs + [self.jobs[0]], None, [None]):
            with self.assertRaises(RuntimeError):
                contract.validate_remote_jobs(self.row, jobs, self.sha)

    def test_live_artifact_inventory_cannot_substitute_ids_bytes_or_digests(self):
        for key, value in (('id', 999), ('size_in_bytes', 999), ('digest', 'sha256:' + 'c' * 64),
                           ('expired', True), ('workflow_run', {'id': 9, 'head_sha': self.sha, 'head_branch': 'main'})):
            artifacts = deepcopy(self.artifacts)
            artifacts[0][key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                contract.validate_remote_artifacts(self.row, artifacts, self.sha)
        for artifacts in ([], self.artifacts[:1], self.artifacts * 2, None, [None]):
            with self.assertRaises(RuntimeError):
                contract.validate_remote_artifacts(self.row, artifacts, self.sha)

    def history_git(self, delivery_paths='docs/SESSION_STATUS.md\0HANDOFF.md', dirty='', untracked=''):
        def git(*args):
            if args[0] == 'merge-base':
                return ''
            if args[0] == 'diff':
                return dirty if args[-1] == 'HEAD' else '\0'.join(self.evidence['changedPaths'])
            if args[0] == 'ls-files':
                return untracked
            if args[0] == 'rev-list':
                return 'd' * 40
            if args[0] == 'diff-tree':
                return delivery_paths
            raise AssertionError(args)
        return git

    def test_docs_only_delivery_keeps_exact_latest_implementation_and_inventory(self):
        with patch.object(contract, 'latest_implementation_commit', return_value=self.sha), \
                patch.object(contract, 'git', side_effect=self.history_git()):
            contract.validate_history(self.evidence, self.sha)
        with patch.object(contract, 'latest_implementation_commit', return_value='c' * 40):
            with self.assertRaisesRegex(RuntimeError, 'stale'):
                contract.validate_history(self.evidence, self.sha)
        changed = deepcopy(self.evidence)
        changed['changedPaths'].append('tools/unrecorded.py')
        with patch.object(contract, 'latest_implementation_commit', return_value=self.sha), \
                patch.object(contract, 'git', side_effect=self.history_git()):
            with self.assertRaisesRegex(RuntimeError, 'diff'):
                contract.validate_history(changed, self.sha)

    def test_delivery_rejects_implementation_edits_even_when_reverted(self):
        for path in ('client/Scripts/GameRoot.cs', 'tools/improvement_delivery_contract.py',
                     'tests/handoff/test_improvement_evidence.py', 'README.md',
                     '.github/workflows/documentation-contract.yml'):
            with self.subTest(path=path), \
                    patch.object(contract, 'latest_implementation_commit', return_value=self.sha), \
                    patch.object(contract, 'git', side_effect=self.history_git(path)):
                with self.assertRaisesRegex(RuntimeError, 'non-documentation'):
                    contract.validate_history(self.evidence, self.sha)

    def test_uncommitted_tracked_or_untracked_source_is_not_exact_head_proof(self):
        for dirty, untracked in (('client/Scripts/GameRoot.cs', ''),
                                 ('', 'src/Kairnfall.Core/NewRule.cs')):
            with patch.object(contract, 'latest_implementation_commit', return_value=self.sha), \
                    patch.object(contract, 'git', side_effect=self.history_git(dirty=dirty, untracked=untracked)):
                with self.assertRaisesRegex(RuntimeError, 'Uncommitted'):
                    contract.validate_history(self.evidence, self.sha)
        with patch.object(contract, 'latest_implementation_commit', return_value=self.sha), \
                patch.object(contract, 'git', side_effect=self.history_git(
                    dirty='HANDOFF.md', untracked='docs/handoff/IMPROVEMENT_VERIFICATION.md')):
            contract.validate_history(self.evidence, self.sha)

    def validation_context(self, ci, token=''):
        context = ExitStack()
        root = MagicMock()
        path = root.__truediv__.return_value
        path.exists.return_value = False
        path.read_bytes.return_value = b'{}'
        path.read_text.return_value = '\n'.join([
            self.sha, 'CURRENT_EVIDENCE.json', contract.RELEASE_STATUS, contract.WORKSTREAM,
            self.evidence['statusDate'],
            *[str(row['runId']) + row['name'] + row['workflowPath']
              for row in self.evidence['implementationWorkflows']],
        ])
        context.enter_context(patch.object(contract, 'ROOT', root))
        context.enter_context(patch.object(contract, 'validate_history'))
        context.enter_context(patch.object(contract, 'validate_archive_blobs'))
        context.enter_context(patch.dict(os.environ, {'CI': ci, 'GITHUB_TOKEN': token}))
        return context

    def test_offline_mode_never_calls_actions_and_ci_fails_without_token(self):
        output = StringIO()
        with self.validation_context('false'), patch.object(contract, 'api_get') as get, redirect_stdout(output):
            self.assertEqual(contract.validate(self.evidence), 0)
            get.assert_not_called()
        self.assertIn('offline-structure-only', output.getvalue())
        self.assertNotIn('live-actions-verified', output.getvalue())
        with self.validation_context('true'), patch.object(contract, 'api_get') as get:
            with self.assertRaisesRegex(RuntimeError, 'read-only Actions token'):
                contract.validate(self.evidence)
            get.assert_not_called()

    def test_ci_checks_all_run_workflow_attempt_job_and_artifact_inventories(self):
        rows = self.evidence['implementationWorkflows']
        by_run = {row['runId']: row for row in rows}
        by_workflow = {row['workflowId']: row for row in rows}
        def get(path, token):
            self.assertEqual(token, 'fixture-token')
            parts = path.split('/')
            if parts[1] == 'workflows':
                return remote_fixture(by_workflow[int(parts[2])])[1]
            row = by_run[int(parts[2])]
            run, _, jobs, artifacts = remote_fixture(row)
            if len(parts) == 3:
                return run
            if parts[3] == 'attempts':
                self.assertEqual(parts[4], str(row['runAttempt']))
                return {'total_count': len(jobs), 'jobs': jobs}
            self.assertTrue(parts[3].startswith('artifacts?'))
            return {'total_count': len(artifacts), 'artifacts': artifacts}
        output = StringIO()
        with self.validation_context('true', 'fixture-token'), \
                patch.object(contract, 'api_get', side_effect=get) as calls, redirect_stdout(output):
            self.assertEqual(contract.validate(self.evidence), 0)
            self.assertEqual(calls.call_count, 4 * len(contract.WORKFLOWS))
        self.assertIn('live-actions-verified', output.getvalue())

    def test_paginated_api_inventory_requires_stable_complete_counts(self):
        pages = [{'total_count': 2, 'jobs': [{'id': 1}]}, {'total_count': 2, 'jobs': [{'id': 2}]}]
        with patch.object(contract, 'api_get', side_effect=pages) as get:
            self.assertEqual(contract.api_inventory('actions/runs/1/jobs', 'jobs', 'test-token'), [{'id': 1}, {'id': 2}])
            self.assertEqual(get.call_args_list[1].args[0], 'actions/runs/1/jobs?per_page=100&page=2')
        for pages in (
            [{'total_count': 1, 'jobs': []}],
            [{'total_count': 1, 'jobs': [{'id': 1}, {'id': 2}]}],
            [{'total_count': 2, 'jobs': [{'id': 1}]}, {'total_count': 3, 'jobs': [{'id': 2}]}],
            [{'total_count': True, 'jobs': []}],
        ):
            with patch.object(contract, 'api_get', side_effect=pages), self.assertRaises(RuntimeError):
                contract.api_inventory('actions/runs/1/jobs', 'jobs', 'test-token')

    def test_router_adds_new_workstream_without_changing_historical_routes(self):
        with patch.object(router.json, 'loads', return_value=self.evidence), \
                patch.object(contract, 'validate', return_value=0) as validate:
            self.assertEqual(router.main(), 0)
            validate.assert_called_once_with(self.evidence)
        import smoothness_delivery_contract as smoothness
        old = {'currentTask': smoothness.WORKSTREAM}
        with patch.object(router.json, 'loads', return_value=old), \
                patch.object(smoothness, 'validate', return_value=0) as validate:
            self.assertEqual(router.main(), 0)
            validate.assert_called_once_with(old)
        self.assertEqual(router.WORKSTREAM, 'new-player-experience')
        self.assertEqual(smoothness.CHECKPOINT3_STARTING_MAIN, '192c8b50ce6ecac11e6327189af6208dd26c7944')
        self.assertNotIn('src/Kairnfall.Server/Program.cs', smoothness.CHECKPOINT3_ALLOWED_PATHS)


if __name__ == '__main__':
    unittest.main()
