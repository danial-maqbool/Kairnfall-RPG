"""Smoothness delivery evidence rejects stale, fake, partial or wrong-platform proof."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import smoothness_delivery_contract as contract


class SmoothnessEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.sha = 'a' * 40
        self.evidence = {
            'schema': 1,
            'statusDate': '2026-09-20',
            'currentTask': contract.WORKSTREAM,
            'checkpoint': contract.CHECKPOINT,
            'repository': contract.REPOSITORY,
            'persistentBranches': ['main'],
            'startingMain': contract.STARTING_MAIN,
            'implementationBaseline': self.sha,
            'preservedCombatBaseline': contract.PRESERVED_COMBAT_BASELINE,
            'preservedCombatDelivery': contract.PRESERVED_COMBAT_DELIVERY,
            'historicalCombatEvidence': contract.PREVIOUS,
            'repositorySideCheckpoint0Complete': True,
            'serverAuthoritative': True,
            'oldSavesCompatible': True,
            'temporaryToolingRemoved': True,
            'gameplaySourceChangedInCheckpoint0': False,
            'combatBalanceChanged': False,
            'movementSpeedChanged': False,
            'tickFrequencyChanged': False,
            'publicationReady': False,
            'releasePublished': False,
            'deployed': False,
            'performanceTargetClaimed': False,
            'authorization': {
                'implementationAuthorized': True,
                'publicationAuthorized': False,
                'deploymentAuthorized': False,
                'productionInfrastructureChanged': False,
            },
            'releaseStatus': contract.RELEASE_STATUS,
            'nativeAcceptancePlatforms': ['linux', 'windows'],
            'humanOnlyGates': ['Owner Windows performance and feel acceptance'],
            'implementationWorkflows': [
                {
                    'name': name,
                    'runId': index + 1,
                    'headSha': self.sha,
                    'conclusion': 'success',
                }
                for index, name in enumerate(sorted(contract.REQUIRED_WORKFLOWS))
            ],
        }
        self.row = self.evidence['implementationWorkflows'][0]
        self.remote = {
            'id': self.row['runId'],
            'name': self.row['name'],
            'head_sha': self.sha,
            'head_branch': 'main',
            'status': 'completed',
            'conclusion': 'success',
            'event': 'push',
            'repository': {'full_name': contract.REPOSITORY},
        }
        self.jobs = [
            {
                'name': 'verify (ubuntu-latest, linux)',
                'status': 'completed',
                'conclusion': 'success',
            },
            {
                'name': 'verify (windows-latest, windows)',
                'status': 'completed',
                'conclusion': 'success',
            },
        ]

    def test_complete_exact_head_metadata_is_valid(self):
        self.assertEqual(contract.validate_metadata(self.evidence), self.sha)
        contract.validate_remote_run(self.row, self.remote, self.sha)
        contract.validate_native_jobs(self.jobs)

    def test_stale_wrong_repository_branch_and_workstream_are_rejected(self):
        for key, value in (
            ('currentTask', 'combat-feel-pass'),
            ('checkpoint', 1),
            ('repository', 'other/repository'),
            ('persistentBranches', ['main', 'smoothness']),
            ('startingMain', 'b' * 40),
            ('preservedCombatBaseline', 'b' * 40),
            ('preservedCombatDelivery', 'b' * 40),
            ('historicalCombatEvidence', 'other.json'),
        ):
            changed = deepcopy(self.evidence)
            changed[key] = value
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)

    def test_fabricated_completion_and_unauthorized_claims_are_rejected(self):
        for key in (
            'repositorySideCheckpoint0Complete',
            'serverAuthoritative',
            'oldSavesCompatible',
            'temporaryToolingRemoved',
        ):
            changed = deepcopy(self.evidence)
            changed[key] = False
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)
        for key in (
            'gameplaySourceChangedInCheckpoint0',
            'combatBalanceChanged',
            'movementSpeedChanged',
            'tickFrequencyChanged',
            'publicationReady',
            'releasePublished',
            'deployed',
            'performanceTargetClaimed',
        ):
            changed = deepcopy(self.evidence)
            changed[key] = True
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)
        for key in (
            'publicationAuthorized',
            'deploymentAuthorized',
            'productionInfrastructureChanged',
        ):
            changed = deepcopy(self.evidence)
            changed['authorization'][key] = True
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)

    def test_missing_duplicate_stale_failed_and_fake_runs_are_rejected(self):
        for mutation in ('missing', 'duplicate', 'stale', 'failed', 'boolean-id'):
            changed = deepcopy(self.evidence)
            rows = changed['implementationWorkflows']
            if mutation == 'missing':
                rows.pop()
            elif mutation == 'duplicate':
                rows[1] = deepcopy(rows[0])
            elif mutation == 'stale':
                rows[0]['headSha'] = 'b' * 40
            elif mutation == 'failed':
                rows[0]['conclusion'] = 'failure'
            else:
                rows[0]['runId'] = True
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)

    def test_remote_pending_failed_wrong_head_identity_or_repository_is_rejected(self):
        for key, value in (
            ('status', 'in_progress'),
            ('conclusion', 'failure'),
            ('conclusion', 'cancelled'),
            ('head_sha', 'b' * 40),
            ('head_branch', 'candidate'),
            ('id', 999999),
            ('name', 'Unrelated workflow'),
            ('event', 'pull_request'),
        ):
            actual = deepcopy(self.remote)
            actual[key] = value
            with self.assertRaises(RuntimeError):
                contract.validate_remote_run(self.row, actual, self.sha)
        actual = deepcopy(self.remote)
        actual['repository']['full_name'] = 'other/repository'
        with self.assertRaises(RuntimeError):
            contract.validate_remote_run(self.row, actual, self.sha)

    def test_native_platform_coverage_rejects_missing_duplicate_pending_or_failed_jobs(self):
        for jobs in (
            [],
            self.jobs[:1],
            [self.jobs[0], deepcopy(self.jobs[0])],
        ):
            with self.assertRaises(RuntimeError):
                contract.validate_native_jobs(jobs)
        for status, conclusion in (
            ('in_progress', None),
            ('completed', 'skipped'),
            ('completed', 'failure'),
        ):
            jobs = deepcopy(self.jobs)
            jobs[1].update(status=status, conclusion=conclusion)
            with self.assertRaises(RuntimeError):
                contract.validate_native_jobs(jobs)
        changed = deepcopy(self.evidence)
        changed['nativeAcceptancePlatforms'] = ['linux']
        with self.assertRaises(RuntimeError):
            contract.validate_metadata(changed)

    def test_human_gates_cannot_be_erased(self):
        changed = deepcopy(self.evidence)
        changed['humanOnlyGates'] = []
        with self.assertRaises(RuntimeError):
            contract.validate_metadata(changed)


if __name__ == '__main__':
    unittest.main()
