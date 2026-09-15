"""Evidence cannot promote a stale, partial or falsely successful implementation."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import documentation_contract as contract


class OnboardingEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.sha = 'a' * 40
        self.evidence = {
            'schema': 1, 'currentTask': 'new-player-experience',
            'repository': contract.REPOSITORY, 'persistentBranches': ['main'],
            'implementationBaseline': self.sha, 'repositorySideNewPlayerExperienceImplemented': True,
            'authorization': {'implementationAuthorized': True, 'publicationAuthorized': False,
                              'deploymentAuthorized': False, 'productionInfrastructureChanged': False},
            'releaseStatus': contract.RELEASE_STATUS, 'publicationReady': False,
            'releasePublished': False, 'deployed': False, 'humanOnlyGates': ['Human release acceptance'],
            'historicalTask22Evidence': 'docs/handoff/TASK22_EVIDENCE.json',
            'temporaryToolingRemoved': True, 'newOverworldRegions': 0,
            'tutorialRewardsAdded': False, 'serverAuthoritative': True,
            'implementationWorkflows': [
                {'name': name, 'runId': index + 1, 'headSha': self.sha, 'conclusion': 'success'}
                for index, name in enumerate(sorted(contract.REQUIRED_WORKFLOWS))],
        }
        self.row = self.evidence['implementationWorkflows'][0]
        self.remote = {'id': self.row['runId'], 'name': self.row['name'], 'head_sha': self.sha,
                       'head_branch': 'main', 'status': 'completed', 'conclusion': 'success',
                       'event': 'push', 'repository': {'full_name': contract.REPOSITORY}}

    def test_complete_exact_head_metadata_is_valid(self):
        self.assertEqual(contract.validate_metadata(self.evidence), self.sha)
        contract.validate_remote_run(self.row, self.remote, self.sha)

    def test_old_task_is_not_silently_promoted(self):
        self.evidence['currentTask'] = 22
        with self.assertRaises(RuntimeError):
            contract.validate_metadata(self.evidence)

    def test_missing_or_duplicate_workflow_is_rejected(self):
        for rows in (self.evidence['implementationWorkflows'][:-1],
                     [self.row] * len(contract.REQUIRED_WORKFLOWS)):
            e = deepcopy(self.evidence); e['implementationWorkflows'] = rows
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(e)

    def test_stale_success_and_false_run_ids_are_rejected(self):
        for key, value in (('headSha', 'b' * 40), ('conclusion', 'failure'), ('runId', True)):
            e = deepcopy(self.evidence); e['implementationWorkflows'][0][key] = value
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(e)

    def test_publication_and_deployment_remain_unauthorized(self):
        for key in ('publicationAuthorized', 'deploymentAuthorized', 'productionInfrastructureChanged'):
            e = deepcopy(self.evidence); e['authorization'][key] = True
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(e)
        for key in ('publicationReady', 'releasePublished', 'deployed'):
            e = deepcopy(self.evidence); e[key] = True
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(e)

    def test_reward_and_footprint_boundary_is_enforced(self):
        for key, value in (('tutorialRewardsAdded', True), ('newOverworldRegions', 1),
                           ('serverAuthoritative', False), ('temporaryToolingRemoved', False),
                           ('persistentBranches', ['main', 'feature'])):
            e = deepcopy(self.evidence); e[key] = value
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(e)

    def test_remote_failure_pending_wrong_head_and_wrong_identity_are_rejected(self):
        for key, value in (('status', 'in_progress'), ('conclusion', 'failure'),
                           ('conclusion', 'cancelled'), ('head_sha', 'b' * 40),
                           ('head_branch', 'candidate'), ('id', 999999),
                           ('name', 'Unrelated'), ('event', 'pull_request')):
            actual = deepcopy(self.remote); actual[key] = value
            with self.assertRaises(RuntimeError):
                contract.validate_remote_run(self.row, actual, self.sha)

    def test_remote_repository_must_match(self):
        self.remote['repository']['full_name'] = 'other/repository'
        with self.assertRaises(RuntimeError):
            contract.validate_remote_run(self.row, self.remote, self.sha)

    def test_human_release_gates_cannot_be_erased(self):
        self.evidence['humanOnlyGates'] = []
        with self.assertRaises(RuntimeError):
            contract.validate_metadata(self.evidence)

    def test_workflows_and_guard_edits_invalidate_the_baseline(self):
        with patch.object(contract, 'git', return_value=self.sha) as call:
            self.assertEqual(contract.latest_implementation_commit(), self.sha)
        arguments = call.call_args.args
        self.assertIn(':(exclude)docs/**', arguments)
        self.assertIn(':(exclude)HANDOFF.md', arguments)
        self.assertFalse(any('.github' in arg or 'documentation_contract.py' in arg or '.ci/' in arg for arg in arguments))


if __name__ == '__main__':
    unittest.main()
