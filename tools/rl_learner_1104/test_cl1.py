import unittest
import torch
from rl_learner_1104.cl1 import CampPointer, preprocess


class CL1Tests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(1104)
        self.model = CampPointer()
        self.x = torch.zeros(2, 448, dtype=torch.int16)
        self.x[:, 224:416] = torch.randint(0, 10, (2, 192), dtype=torch.int16)
        self.x[:, 224:416:16] = 1

    def forward(self, x):
        return self.model(x, self.model.initial_state(len(x)), torch.ones(len(x), dtype=torch.bool))[0]

    def test_ids_unused_and_dimensions(self):
        expected = self.forward(self.x)
        self.x[:, 47] = 30000
        self.x[:, 15] = 31000  # recorder fuel, not stable policy input
        torch.testing.assert_close(expected, self.forward(self.x))
        self.assertTrue(torch.isfinite(preprocess(self.x)[2]).all())

    def test_pointer_permutation(self):
        p = torch.randperm(12)
        y = self.x.clone()
        y[:, 224:416] = self.x[:, 224:416].reshape(2, 12, 16)[:, p].reshape(2, 192)
        a, b = self.forward(self.x), self.forward(y)
        torch.testing.assert_close(a[:, :12][:, p], b[:, :12])
        torch.testing.assert_close(a[:, 12], b[:, 12])

    def test_absent_padding_and_none_legal(self):
        self.x[:, 224:416:16] = 0
        scores = self.forward(self.x)
        self.assertTrue(torch.isneginf(scores[:, :12]).all())
        self.assertTrue(torch.isfinite(scores[:, 12]).all())
        changed = self.x.clone()
        changed[:, 225:416] = 30000
        changed[:, 224:416:16] = 0
        torch.testing.assert_close(scores[:, 12], self.forward(changed)[:, 12])

    def test_hidden_reset(self):
        a, _ = self.model(self.x, self.model.initial_state(2), torch.ones(2, dtype=torch.bool))
        b, _ = self.model(self.x, torch.randn(2, 16), torch.ones(2, dtype=torch.bool))
        torch.testing.assert_close(a, b)


if __name__ == '__main__':
    unittest.main()
