import unittest
import numpy as np
import torch

from closure_evaluate import no_batch_select, summarize
from prepare_and_cache import SocialSimulator, SocioVerse_Campus
from supplemental_rules import SupplementalStressSimulator


class ClosureContracts(unittest.TestCase):
    def test_stress_copy_preserves_original_when_disabled(self):
        theta = torch.tensor([[.9, .8, .12], [.4, .7, .42]])
        events = SocioVerse_Campus.events('test')
        base = SocialSimulator(n_agents=32, n_seeds=2)
        extension = SupplementalStressSimulator(n_agents=32, n_seeds=2)
        for transport in (False, True):
            a = base.run(theta, events, 123, misspecified=transport)
            b = extension.run(theta, events, 123, misspecified=transport)
            for key in a:
                self.assertTrue(torch.equal(a[key], b[key]), key)

    def test_new_rules_change_settled_truth_with_capacity_preserved(self):
        sim = SupplementalStressSimulator(n_agents=48, n_seeds=4)
        theta = torch.tensor([[.6, .95, .05]])
        events = torch.tensor([[3, 1, 1, 0, .8, 1, 7]])
        base = sim.run(theta, events, 17)['Trajectories']
        for stress in ('waiting', 'propagation', 'both'):
            shifted = sim.run(theta, events, 17, stress=stress)['Trajectories']
            self.assertFalse(torch.equal(base, shifted))
            self.assertLessEqual(float(shifted[..., 0].max()), 3/48)

    def test_no_batch_dedup_keeps_distinct_records_and_cost_limit(self):
        torch.manual_seed(53)
        w = torch.ones(7)/7
        query = {'P_records': torch.rand(7, 9), 'Trajectories': torch.rand(7, 2, 1, 4, 3)}
        mask = torch.ones(9, dtype=torch.bool)
        mask[0] = False
        costs = torch.tensor([1., 2., 1., 2., 3., 1., 1., 2., 1.])
        selected = no_batch_select(w, query, mask, costs, 2, 2)
        self.assertTrue(mask[selected].all())
        self.assertEqual(len(selected), len(selected.unique()))
        self.assertLessEqual(float(costs[selected].sum()), 2)

    def test_bootstrap_resamples_world_axis_and_preserves_events(self):
        x = np.array([[1., 10.], [3., 30.], [5., 50.]])
        indices = np.array([[0, 0, 0], [2, 2, 2]])
        out = summarize(x, indices)
        self.assertEqual(out['mean'], [3., 30.])
        self.assertEqual(out['n_independent_worlds'], 3)
        self.assertAlmostEqual(out['ci95_low'][1], 10*out['ci95_low'][0])


if __name__ == '__main__':
    unittest.main()
