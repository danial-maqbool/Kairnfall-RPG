"""Combat delivery evidence rejects stale runs, authority drift and fake approval."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import combat_delivery_contract as contract


class CombatEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.sha = 'a' * 40
        self.evidence = {
            'schema': 1,
            'currentTask': contract.WORKSTREAM,
            'repository': contract.REPOSITORY,
            'persistentBranches': ['main'],
            'startingMain': contract.STARTING_MAIN,
            'implementationBaseline': self.sha,
            'repositorySideCombatFeelImplemented': True,
            'serverAuthoritative': True,
            'oldSavesCompatible': True,
            'temporaryToolingRemoved': True,
            'clientPredictsDamage': False,
            'combatBalanceChanged': False,
            'authorization': {
                'implementationAuthorized': True,
                'publicationAuthorized': False,
                'deploymentAuthorized': False,
                'productionInfrastructureChanged': False,
            },
            'releaseStatus': contract.RELEASE_STATUS,
            'publicationReady': False,
            'releasePublished': False,
            'deployed': False,
            'humanCombatFeelApproval': False,
            'humanOnlyGates': ['Human combat feel and gameplay acceptance'],
            'historicalCharacterEvidence': contract.PREVIOUS,
            'basicAttackBufferSeconds': contract.BASIC_BUFFER,
            'abilityBufferSeconds': contract.ABILITY_BUFFER,
            'selectedTargetGrace': contract.TARGET_GRACE,
            'combatEvidence': {
                'bufferedBasicAttack': True,
                'lockedQueuedAbilityIntent': True,
                'stickyExplicitTargets': True,
                'threatAwareAutoTarget': True,
                'authoritativeTargetSummary': True,
                'urgentTelegraphPresentation': True,
                'accurateDamageAttributionBoundary': True,
            },
            'implementationWorkflows': [
                {'name': name, 'runId': i + 1, 'headSha': self.sha, 'conclusion': 'success'}
                for i, name in enumerate(sorted(contract.REQUIRED_WORKFLOWS))
            ],
        }

    def test_complete_exact_head_metadata_is_valid(self):
        self.assertEqual(contract.validate_metadata(self.evidence), self.sha)

    def test_wrong_task_branch_or_starting_main_is_rejected(self):
        for key, value in (
            ('currentTask', 'character-rebuild'),
            ('persistentBranches', ['main', 'combat']),
            ('startingMain', 'b' * 40),
            ('repositorySideCombatFeelImplemented', False),
            ('serverAuthoritative', False),
            ('oldSavesCompatible', False),
            ('temporaryToolingRemoved', False),
        ):
            value_copy = deepcopy(self.evidence)
            value_copy[key] = value
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(value_copy)

    def test_prediction_balance_and_release_claims_are_rejected(self):
        for key in ('clientPredictsDamage', 'combatBalanceChanged', 'publicationReady',
                    'releasePublished', 'deployed', 'humanCombatFeelApproval'):
            value = deepcopy(self.evidence)
            value[key] = True
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(value)
        for key in ('publicationAuthorized', 'deploymentAuthorized', 'productionInfrastructureChanged'):
            value = deepcopy(self.evidence)
            value['authorization'][key] = True
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(value)

    def test_buffer_and_target_bounds_cannot_drift(self):
        for key, value in (
            ('basicAttackBufferSeconds', .8),
            ('abilityBufferSeconds', .8),
            ('selectedTargetGrace', 6),
            ('historicalCharacterEvidence', 'other.json'),
        ):
            changed = deepcopy(self.evidence)
            changed[key] = value
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)

    def test_each_combat_feature_is_required(self):
        for key in self.evidence['combatEvidence']:
            changed = deepcopy(self.evidence)
            changed['combatEvidence'][key] = False
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)

    def test_missing_duplicate_stale_and_failed_workflows_are_rejected(self):
        for mutation in ('missing', 'duplicate', 'stale', 'failed', 'boolean-id'):
            changed = deepcopy(self.evidence)
            rows = changed['implementationWorkflows']
            if mutation == 'missing':
                rows.pop()
            elif mutation == 'duplicate':
                rows[1] = rows[0]
            elif mutation == 'stale':
                rows[0]['headSha'] = 'b' * 40
            elif mutation == 'failed':
                rows[0]['conclusion'] = 'failure'
            else:
                rows[0]['runId'] = True
            with self.assertRaises(RuntimeError):
                contract.validate_metadata(changed)

    def test_human_only_gates_cannot_be_erased(self):
        changed = deepcopy(self.evidence)
        changed['humanOnlyGates'] = []
        with self.assertRaises(RuntimeError):
            contract.validate_metadata(changed)


if __name__ == '__main__':
    unittest.main()
