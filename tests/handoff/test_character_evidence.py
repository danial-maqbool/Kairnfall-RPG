"""Wayfarer evidence rejects missing platforms, stale runs and unsafe pack records."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import character_delivery_contract as contract


class CharacterEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.sha = 'a' * 40
        self.evidence = {
            'schema': 1, 'currentTask': contract.WORKSTREAM,
            'repository': contract.REPOSITORY, 'persistentBranches': ['main'],
            'implementationBaseline': self.sha,
            'repositorySideCharacterRebuildImplemented': True,
            'repositorySideNewPlayerExperienceImplemented': True,
            'serverAuthoritative': True, 'oldSavesCompatible': True, 'temporaryToolingRemoved': True,
            'authorization': {'implementationAuthorized': True, 'publicationAuthorized': False,
                              'deploymentAuthorized': False, 'productionInfrastructureChanged': False},
            'releaseStatus': contract.RELEASE_STATUS, 'publicationReady': False, 'releasePublished': False,
            'deployed': False, 'humanArtApproval': False, 'humanUxApproval': False,
            'humanOnlyGates': ['Independent artistic and human gameplay acceptance'],
            'newOverworldRegions': 0, 'tutorialRewardsAdded': 8,
            'actorRuntimeSource': contract.ACTOR_SOURCE, 'actorHistoricalFallbacks': 0,
            'uiResolutionMatrix': contract.EXPECTED_UI_MATRIX.copy(),
            'characterAssetManifest': contract.PACK, 'historicalNewPlayerEvidence': contract.PREVIOUS,
            'historicalTask22Evidence': 'docs/handoff/TASK22_EVIDENCE.json',
            'actorEvidence': contract.COUNTS.copy(), 'nativeAcceptancePlatforms': ['linux', 'windows'],
            'implementationWorkflows': [
                {'name': name, 'runId': i + 1, 'headSha': self.sha, 'conclusion': 'success'}
                for i, name in enumerate(sorted(contract.REQUIRED_WORKFLOWS))],
        }
        self.jobs = [
            {'name': 'verify (ubuntu-latest, linux)', 'status': 'completed', 'conclusion': 'success'},
            {'name': 'verify (windows-latest, windows)', 'status': 'completed', 'conclusion': 'success'}]

    def test_complete_exact_head_evidence_is_valid(self):
        self.assertEqual(contract.validate_metadata(self.evidence), self.sha)
        contract.validate_native_jobs(self.jobs)

    def test_previous_workstream_and_missing_implementation_are_rejected(self):
        for key, value in (('currentTask', 'new-player-experience'),
                           ('repositorySideCharacterRebuildImplemented', False),
                           ('oldSavesCompatible', False), ('temporaryToolingRemoved', False)):
            e = deepcopy(self.evidence); e[key] = value
            with self.assertRaises(RuntimeError): contract.validate_metadata(e)

    def test_missing_duplicate_stale_and_failing_workflows_are_rejected(self):
        for mutation in ('missing', 'duplicate', 'stale', 'failed', 'boolean-id'):
            e = deepcopy(self.evidence); rows = e['implementationWorkflows']
            if mutation == 'missing': rows.pop()
            elif mutation == 'duplicate': rows[1] = rows[0]
            elif mutation == 'stale': rows[0]['headSha'] = 'b' * 40
            elif mutation == 'failed': rows[0]['conclusion'] = 'failure'
            else: rows[0]['runId'] = True
            with self.assertRaises(RuntimeError): contract.validate_metadata(e)

    def test_windows_cannot_be_replaced_by_more_linux_jobs(self):
        for jobs in ([], self.jobs[:1], [self.jobs[0], self.jobs[0]]):
            with self.assertRaises(RuntimeError): contract.validate_native_jobs(jobs)
        e = deepcopy(self.evidence); e['nativeAcceptancePlatforms'] = ['linux']
        with self.assertRaises(RuntimeError): contract.validate_metadata(e)

    def test_matrix_job_pending_skipped_or_failed_is_rejected(self):
        for status, conclusion in (('in_progress', None), ('completed', 'skipped'), ('completed', 'failure')):
            jobs = deepcopy(self.jobs); jobs[1].update(status=status, conclusion=conclusion)
            with self.assertRaises(RuntimeError): contract.validate_native_jobs(jobs)

    def test_actor_coverage_requires_real_integer_counts(self):
        for key in contract.COUNTS:
            for value in (0, True, contract.COUNTS[key] - 1):
                e = deepcopy(self.evidence); e['actorEvidence'][key] = value
                with self.assertRaises(RuntimeError): contract.validate_metadata(e)

    def test_source_fallback_and_manifest_identity_cannot_drift(self):
        for key, value in (('actorRuntimeSource', 'Grounded-2026 procedural construction'),
                           ('actorHistoricalFallbacks', 1), ('actorHistoricalFallbacks', False),
                           ('characterAssetManifest', 'other.json'),
                           ('historicalNewPlayerEvidence', 'other.json'),
                           ('persistentBranches', ['main', 'candidate']), ('uiResolutionMatrix', ['1280x720'])):
            e = deepcopy(self.evidence); e[key] = value
            with self.assertRaises(RuntimeError): contract.validate_metadata(e)

    def test_repository_completion_never_grants_human_or_release_approval(self):
        for key in ('publicationReady', 'releasePublished', 'deployed', 'humanArtApproval', 'humanUxApproval'):
            e = deepcopy(self.evidence); e[key] = True
            with self.assertRaises(RuntimeError): contract.validate_metadata(e)
        for key in ('publicationAuthorized', 'deploymentAuthorized', 'productionInfrastructureChanged'):
            e = deepcopy(self.evidence); e['authorization'][key] = True
            with self.assertRaises(RuntimeError): contract.validate_metadata(e)
        e = deepcopy(self.evidence); e['humanOnlyGates'] = []
        with self.assertRaises(RuntimeError): contract.validate_metadata(e)

    def test_pack_paths_cannot_escape_or_hide_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(contract.safe_path(root, 'people/body_0_0.png'), root / 'people/body_0_0.png')
            for value in ('../outside', '/absolute', 'people/../outside', 'people//body.png',
                          'people\\body.png', 'people/./body.png', 'C:/outside', ''):
                with self.assertRaises(RuntimeError): contract.safe_path(root, value)


if __name__ == '__main__':
    unittest.main()
