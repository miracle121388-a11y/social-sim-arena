from datetime import datetime, timezone
import unittest
from src.njusim.adapters.socialsim_arena import response, normal_crps


class ArenaContractTests(unittest.TestCase):
    def envelope(self, kind, **extra):
        return {'schema_version': 'ssa-agent-api-v2', 'request_id': 'offline-fixture-001',
                'optional_crosstabs': [], 'round': {'round_id': 'offline-fixture',
                'board_id': 'topline', 'target_type': kind, 'question': 'Non-scored fixture',
                'unit': 'fixture units', 'lock_at': '2099-01-01T00:00:00Z', 'context': {}, **extra}}

    def test_scalar_and_published_crps_example(self):
        self.assertEqual(response(self.envelope('continuous_normal'), {'mean': 34.5, 'sd': 1.})['forecast']['mean'], 34.5)
        self.assertAlmostEqual(normal_crps(34.5, 1., 35.), .331403531255, places=11)
        self.assertAlmostEqual(normal_crps(33., 1.5, 35.), 1.280900969803, places=11)

    def test_profile_exact_cells(self):
        req = self.envelope('profile_energy', cells=['a', 'b'])
        response(req, {'profile': {'a': {'mean': 1., 'sd': 2.}, 'b': {'mean': 2., 'sd': 1.}}})
        with self.assertRaises(ValueError):
            response(req, {'profile': {'a': {'mean': 1., 'sd': 2.}}})

    def test_ranking_and_rejected_degenerate_distribution(self):
        req = self.envelope('ranking_list', ranking={'length': 2, 'items': ['a', 'b']})
        response(req, {'ranking': ['b', 'a']})
        with self.assertRaises(ValueError):
            response(req, {'ranking': ['a', 'a']})
        with self.assertRaises(ValueError):
            response(self.envelope('continuous_normal'), {'mean': 1., 'sd': 0.})
        with self.assertRaises(ValueError):
            response(self.envelope('continuous_normal'), {'mean': float('nan'), 'sd': 1.})

    def test_expired_question_rejected(self):
        with self.assertRaises(ValueError):
            response(self.envelope('continuous_normal'), {'mean': 1., 'sd': 1.},
                     now=datetime(2100, 1, 1, tzinfo=timezone.utc))
