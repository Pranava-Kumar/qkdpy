"""Comprehensive coverage tests for the HD-QKD protocol (hd_qkd.py).

Targets uncovered code paths in:
  - _generate_mubs(d)       - d=2, prime, prime-power-non-prime, non-prime-power
  - _is_prime_power(n)      - n<=1, prime, composite, actual prime power
  - _is_prime(n)            - n<=1, n=2/3, even, 6k+-1 check (25, 29, 35)
  - _construct_mubs_prime(p) - d=2 fallback, d=3/5/7 Weyl-Heisenberg, unitarity
  - prepare_states()        - dim 2 (qubit) and dim 4 (qudit) paths
  - measure_states()        - None/lost, Qudit instances, non-Qudit path
  - sift_keys()             - matching bases, mismatch, bob_bases=None
  - estimate_qber()          - <10 sifted, 0 errors, some errors
  - get_dimension_efficiency() - log2(d) for various d
  - get_basis_distribution()  - counts, total_qudits, dimension
  - Edge cases              - d=1, d=7, security_threshold=0, key_length=1
"""

import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from qkdpy.protocols.hd_qkd import HDQKD
from qkdpy.core.qudit import Qudit as RealQudit
from qkdpy.core import QuantumChannel as RealQuantumChannel


def _make_mock_channel():
    """Create a mock QuantumChannel that passes isinstance checks in base.py."""
    return MagicMock(spec=RealQuantumChannel)


# ===================================================================
#  Pure-math tests - no mocking needed beyond QuantumChannel for init
# ===================================================================

class TestHDQKDIsPrimePower(unittest.TestCase):
    """Cover _is_prime_power: n<=1, prime, composite, actual prime power."""

    def setUp(self):
        self._mock_channel = _make_mock_channel()

    def _make(self, dim=2):
        return HDQKD(self._mock_channel, key_length=10, dimension=dim)

    def test_leq_1_returns_false(self):
        proto = self._make()
        self.assertFalse(proto._is_prime_power(0))
        self.assertFalse(proto._is_prime_power(1))

    def test_prime_returns_true(self):
        proto = self._make()
        for n in (13, 17, 19, 23, 29, 31):
            with self.subTest(n=n):
                self.assertTrue(proto._is_prime_power(n))

    def test_composite_returns_false(self):
        proto = self._make()
        for n in (6, 10, 12, 14, 15, 18, 20, 21, 22, 26, 30):
            with self.subTest(n=n):
                self.assertFalse(proto._is_prime_power(n))

    def test_prime_power_returns_true(self):
        proto = self._make()
        cases = {8: 2, 9: 3, 16: 2, 25: 5, 27: 3, 32: 2, 49: 7}
        for n, base in cases.items():
            with self.subTest(n=n, base=base):
                self.assertTrue(
                    proto._is_prime_power(n),
                    "%d = %d^k should be a prime power" % (n, base),
                )

class TestHDQKDIsPrime(unittest.TestCase):
    """Cover _is_prime: n<=1, n=2/3, even, 6k+-1 check."""

    def setUp(self):
        self._mock_channel = _make_mock_channel()

    def _make(self, dim=2):
        return HDQKD(self._mock_channel, key_length=10, dimension=dim)

    def test_leq_1_returns_false(self):
        proto = self._make()
        self.assertFalse(proto._is_prime(0))
        self.assertFalse(proto._is_prime(1))

    def test_two_and_three_return_true(self):
        proto = self._make()
        self.assertTrue(proto._is_prime(2))
        self.assertTrue(proto._is_prime(3))

    def test_even_numbers_return_false(self):
        proto = self._make()
        for n in (4, 6, 8, 10, 100):
            with self.subTest(n=n):
                self.assertFalse(proto._is_prime(n))

    def test_multiples_of_3_return_false(self):
        proto = self._make()
        for n in (9, 15, 21, 27, 33, 99):
            with self.subTest(n=n):
                self.assertFalse(proto._is_prime(n))

    def test_6k_plus_minus_1_path(self):
        """Cover the while-loop (6k +/- 1) inside _is_prime."""
        proto = self._make()
        self.assertFalse(proto._is_prime(25))
        self.assertTrue(proto._is_prime(29))
        self.assertFalse(proto._is_prime(35))
        self.assertFalse(proto._is_prime(49))
        self.assertFalse(proto._is_prime(121))
        self.assertTrue(proto._is_prime(97))

class TestHDQKDGenerateMUBs(unittest.TestCase):
    """Cover every branch of _generate_mubs(d)."""

    def setUp(self):
        self._mock_channel = _make_mock_channel()

    def _make(self, dim=4):
        return HDQKD(self._mock_channel, key_length=10, dimension=dim)

    def test_d2_returns_3_qubit_mubs(self):
        proto = self._make(dim=2)
        mubs = proto._generate_mubs(2)
        self.assertEqual(len(mubs), 3)
        for i, m in enumerate(mubs):
            self.assertEqual(m.shape, (2, 2), msg="MUB %d shape mismatch" % i)
            self.assertTrue(
                np.allclose(m @ m.conj().T, np.eye(2), atol=1e-8),
                "MUB %d at d=2 is not unitary" % i,
            )

    def test_prime_dimension_3(self):
        proto = self._make(dim=3)
        mubs = proto._generate_mubs(3)
        self.assertEqual(len(mubs), 4)
        for m in mubs:
            self.assertEqual(m.shape, (3, 3))
            self.assertTrue(np.allclose(m @ m.conj().T, np.eye(3), atol=1e-8))

    def test_prime_dimension_5(self):
        proto = self._make(dim=5)
        mubs = proto._generate_mubs(5)
        self.assertEqual(len(mubs), 6)
        for m in mubs:
            self.assertEqual(m.shape, (5, 5))
            self.assertTrue(np.allclose(m @ m.conj().T, np.eye(5), atol=1e-8))

    def test_prime_dimension_7(self):
        proto = self._make(dim=7)
        mubs = proto._generate_mubs(7)
        self.assertEqual(len(mubs), 8)
        for m in mubs:
            self.assertEqual(m.shape, (7, 7))
            self.assertTrue(np.allclose(m @ m.conj().T, np.eye(7), atol=1e-8))

    def test_prime_power_non_prime_d4(self):
        """d=4 (2^2, not prime) hits _construct_mubs_prime_power else branch."""
        proto = self._make(dim=4)
        mubs = proto._generate_mubs(4)
        self.assertEqual(len(mubs), 5)
        for m in mubs:
            self.assertEqual(m.shape, (4, 4))
            self.assertTrue(np.allclose(m @ m.conj().T, np.eye(4), atol=1e-8))

    def test_prime_power_non_prime_d8(self):
        """d=8 (2^3, not prime)."""
        proto = self._make(dim=8)
        mubs = proto._generate_mubs(8)
        self.assertEqual(len(mubs), 9)
        for m in mubs:
            self.assertEqual(m.shape, (8, 8))
            self.assertTrue(np.allclose(m @ m.conj().T, np.eye(8), atol=1e-8))

    def test_non_prime_power_d6(self):
        """d=6 hits the non-prime-power Fourier+shift branch -> 4 MUBs."""
        proto = self._make(dim=6)
        mubs = proto._generate_mubs(6)
        self.assertEqual(len(mubs), 4)
        for m in mubs:
            self.assertEqual(m.shape, (6, 6))
            self.assertTrue(np.allclose(m @ m.conj().T, np.eye(6), atol=1e-8))

    def test_non_prime_power_d10(self):
        """d=10 also hits the fallback -> 4 MUBs."""
        proto = self._make(dim=10)
        mubs = proto._generate_mubs(10)
        self.assertEqual(len(mubs), 4)
        for m in mubs:
            self.assertEqual(m.shape, (10, 10))
            self.assertTrue(np.allclose(m @ m.conj().T, np.eye(10), atol=1e-8))

class TestHDQKDConstructMubsPrime(unittest.TestCase):
    """Cover _construct_mubs_prime: d=2 fallback, d=3/5/7 Weyl-Heisenberg."""

    def setUp(self):
        self._mock_channel = _make_mock_channel()

    def _make(self, dim=3):
        return HDQKD(self._mock_channel, key_length=10, dimension=dim)

    def test_d2_fallback(self):
        """d=2 returns the hardcoded 3 qubit MUBs."""
        proto = self._make(dim=3)
        mubs = proto._construct_mubs_prime(2)
        self.assertEqual(len(mubs), 3)
        for m in mubs:
            self.assertEqual(m.shape, (2, 2))
            self.assertTrue(np.allclose(m @ m.conj().T, np.eye(2), atol=1e-8))

    def test_d3_weyl_heisenberg(self):
        """d=3 builds Weyl-Heisenberg MUBs: 4 bases, each unitary."""
        proto = self._make(dim=3)
        mubs = proto._construct_mubs_prime(3)
        self.assertEqual(len(mubs), 4)
        self.assertTrue(np.allclose(mubs[0], np.eye(3), atol=1e-8))
        for i, m in enumerate(mubs):
            self.assertEqual(m.shape, (3, 3), msg="MUB %d shape" % i)
            self.assertTrue(
                np.allclose(m @ m.conj().T, np.eye(3), atol=1e-8),
                "MUB %d at d=3 is not unitary" % i,
            )

    def test_d5_weyl_heisenberg(self):
        """d=5: 6 bases (p+1), all unitary."""
        proto = self._make(dim=5)
        mubs = proto._construct_mubs_prime(5)
        self.assertEqual(len(mubs), 6)
        for i, m in enumerate(mubs):
            self.assertTrue(
                np.allclose(m @ m.conj().T, np.eye(5), atol=1e-8),
                "MUB %d at d=5 not unitary" % i,
            )

    def test_d7_weyl_heisenberg(self):
        """d=7: 8 bases (p+1), all unitary."""
        proto = self._make(dim=7)
        mubs = proto._construct_mubs_prime(7)
        self.assertEqual(len(mubs), 8)
        for i, m in enumerate(mubs):
            self.assertTrue(
                np.allclose(m @ m.conj().T, np.eye(7), atol=1e-8),
                "MUB %d at d=7 not unitary" % i,
            )

class TestHDQKDDimensionEfficiency(unittest.TestCase):
    """Cover get_dimension_efficiency."""

    def setUp(self):
        self._mock_channel = _make_mock_channel()

    def test_returns_log2_dimension(self):
        for d, expected in [(2, 1.0), (4, 2.0), (8, 3.0), (16, 4.0)]:
            with self.subTest(d=d):
                proto = HDQKD(
                    self._mock_channel, key_length=10, dimension=d
                )
                self.assertAlmostEqual(
                    proto.get_dimension_efficiency(), expected
                )

    def test_dim1_returns_zero(self):
        proto = HDQKD(self._mock_channel, key_length=10, dimension=1)
        self.assertAlmostEqual(proto.get_dimension_efficiency(), 0.0)


# ===================================================================
#  Protocol-operation tests (prepare, measure, sift, estimate, dist)
# ===================================================================

class BaseHDQKDTest(unittest.TestCase):
    """Shared setUp / tearDown for protocol-operation tests."""

    def setUp(self):
        self._mock_channel = _make_mock_channel()

    def _make(self, dim=4, key_length=100, security_threshold=0.15):
        return HDQKD(
            self._mock_channel,
            key_length=key_length,
            dimension=dim,
            security_threshold=security_threshold,
        )


class TestHDQKDPrepareStates(BaseHDQKDTest):
    """Cover prepare_states with dim=2 (Qubit path) and dim=4 (Qudit path)."""

    @patch("qkdpy.protocols.hd_qkd.secure_randint")
    @patch("qkdpy.protocols.hd_qkd.Qudit.computational_basis")
    def test_dim2_sets_symbols_and_bases(self, mock_comp_basis, mock_randint):
        """prepare_states with dimension 2 populates data correctly."""
        proto = self._make(dim=2, key_length=10)
        n = proto.num_qudits

        # secure_randint is called alternately: symbol, basis, symbol, basis, ...
        interleaved = []
        for i in range(n):
            interleaved.append(i % 2)   # symbol: 0, 1, 0, 1, ...
            interleaved.append(i % 3)   # basis:  0, 1, 2, 0, 1, 2, ...
        mock_randint.side_effect = interleaved

        mock_q = MagicMock()
        mock_comp_basis.return_value = mock_q

        qudits = proto.prepare_states()

        self.assertEqual(len(qudits), n)
        self.assertEqual(len(proto.alice_symbols), n)
        self.assertEqual(len(proto.alice_bases), n)
        self.assertEqual(proto.alice_symbols[0], 0)
        self.assertEqual(proto.alice_symbols[1], 1)
        self.assertEqual(proto.alice_bases[0], 0)
        self.assertEqual(proto.alice_bases[1], 1)
        self.assertEqual(mock_comp_basis.call_count, n)
        self.assertEqual(mock_q.apply_unitary.call_count, n)

    @patch("qkdpy.protocols.hd_qkd.secure_randint")
    @patch("qkdpy.protocols.hd_qkd.Qudit.computational_basis")
    def test_dim4_sets_symbols_and_bases(self, mock_comp_basis, mock_randint):
        """prepare_states with dimension 4 (prime-power non-prime)."""
        proto = self._make(dim=4, key_length=10)
        n = proto.num_qudits
        n_mubs = len(proto.mubs)

        interleaved = []
        for i in range(n):
            interleaved.append(i % 4)       # symbol: 0, 1, 2, 3, 0, ...
            interleaved.append(i % n_mubs)  # basis:  0, 1, 2, 3, 4, 0, ...
        mock_randint.side_effect = interleaved

        mock_q = MagicMock()
        mock_comp_basis.return_value = mock_q

        qudits = proto.prepare_states()

        self.assertEqual(len(qudits), n)
        self.assertEqual(proto.alice_symbols[0], 0)
        self.assertEqual(proto.alice_symbols[3], 3)
        self.assertEqual(proto.alice_bases[0], 0)
        self.assertEqual(proto.alice_bases[4], 4)

    @patch("qkdpy.protocols.hd_qkd.secure_randint")
    @patch("qkdpy.protocols.hd_qkd.Qudit.computational_basis")
    def test_each_qudit_created_from_computational_basis(
        self, mock_comp_basis, mock_randint
    ):
        """Every qudit originates as |symbol> in the computational basis."""
        proto = self._make(dim=3, key_length=4)
        n = proto.num_qudits

        mock_randint.return_value = 0
        mock_comp_basis.return_value = MagicMock()

        proto.prepare_states()

        self.assertEqual(mock_comp_basis.call_count, n)
        mock_comp_basis.assert_called_with(0, 3)

class TestHDQKDMeasureStates(BaseHDQKDTest):
    """Cover measure_states: None, Qudit instances, non-Qudit, mixed."""

    def test_none_qudits(self):
        """None entries mean lost qudits -> bob_results/bases are None."""
        proto = self._make(dim=4, key_length=10)
        qudits = [None, None]
        results = proto.measure_states(qudits)
        self.assertEqual(results, [])
        self.assertEqual(proto.bob_bases, [None, None])
        self.assertEqual(proto.bob_results, [None, None])

    def test_real_qudits_with_mocked_measure(self):
        """Real Qudit instances: measure/collapse_state are called."""
        proto = self._make(dim=4, key_length=10)

        qudits = []
        for i in range(3):
            q = RealQudit.computational_basis(0, 4)
            q.measure = MagicMock(return_value=i)
            q.collapse_state = MagicMock()
            qudits.append(q)

        with patch(
            "qkdpy.protocols.hd_qkd.secure_randint"
        ) as mock_randint:
            mock_randint.side_effect = [2, 1, 0]
            results = proto.measure_states(qudits)

        self.assertEqual(results, [0, 1, 2])
        self.assertEqual(proto.bob_bases, [2, 1, 0])
        self.assertEqual(proto.bob_results, [0, 1, 2])

        for q in qudits:
            q.measure.assert_called_once()
            q.collapse_state.assert_called_once()

    def test_non_qudit_objects(self):
        """isinstance(qudit, Qudit) is False -> result = 0."""
        proto = self._make(dim=4, key_length=10)

        qudits = ["not_a_qudit", 42, 3.14]

        with patch(
            "qkdpy.protocols.hd_qkd.secure_randint"
        ) as mock_randint:
            mock_randint.return_value = 0
            results = proto.measure_states(qudits)

        self.assertEqual(results, [0, 0, 0])
        self.assertEqual(proto.bob_results, [0, 0, 0])
        self.assertEqual(proto.bob_bases, [0, 0, 0])

    def test_mixed_none_real_and_other(self):
        """Mix of None, real Qudit, and non-Qudit objects."""
        proto = self._make(dim=4, key_length=10)

        real_q = RealQudit.computational_basis(0, 4)
        real_q.measure = MagicMock(return_value=2)
        real_q.collapse_state = MagicMock()

        qudits = [None, real_q, "string"]

        with patch(
            "qkdpy.protocols.hd_qkd.secure_randint"
        ) as mock_randint:
            mock_randint.side_effect = [0, 0]
            results = proto.measure_states(qudits)

        self.assertEqual(results, [2, 0])
        self.assertEqual(proto.bob_results, [None, 2, 0])
        self.assertEqual(proto.bob_bases, [None, 0, 0])

    def test_filtered_results_exclude_none(self):
        """Return value filters out None results."""
        proto = self._make(dim=4, key_length=10)
        qudits = [None, None, None]
        results = proto.measure_states(qudits)
        self.assertEqual(results, [])
        self.assertIsInstance(results, list)

class TestHDQKDSiftKeys(BaseHDQKDTest):
    """Cover sift_keys: matching, mismatch, bob_bases=None, alice_bases=None."""

    def test_matching_bases(self):
        """Bases that match are sifted; mismatching are discarded."""
        proto = self._make(dim=4, key_length=10)
        proto.num_qudits = 5
        proto.alice_symbols = [0, 1, 2, 3, 0]
        proto.alice_bases = [0, 1, 2, 0, 1]
        proto.bob_results = [0, 1, 3, 3, 0]
        proto.bob_bases = [0, 1, 3, 0, 1]

        alice_s, bob_s = proto.sift_keys()

        self.assertEqual(alice_s, [0, 1, 3, 0])
        self.assertEqual(bob_s, [0, 1, 3, 0])

    def test_all_mismatch(self):
        """No matching bases -> both sifted keys are empty."""
        proto = self._make(dim=4, key_length=10)
        proto.num_qudits = 3
        proto.alice_symbols = [0, 1, 2]
        proto.alice_bases = [0, 1, 2]
        proto.bob_results = [0, 1, 2]
        proto.bob_bases = [3, 4, 0]

        alice_s, bob_s = proto.sift_keys()
        self.assertEqual(alice_s, [])
        self.assertEqual(bob_s, [])

    def test_bob_bases_none_skipped(self):
        """Bob_bases[i] is None -> qudit was lost, skip."""
        proto = self._make(dim=4, key_length=10)
        proto.num_qudits = 4
        proto.alice_symbols = [0, 1, 2, 3]
        proto.alice_bases = [0, 1, 2, 0]
        proto.bob_results = [0, None, 2, 3]
        proto.bob_bases = [0, None, 2, 3]

        alice_s, bob_s = proto.sift_keys()
        self.assertEqual(alice_s, [0, 2])
        self.assertEqual(bob_s, [0, 2])

    def test_alice_bases_none_skipped(self):
        """Alice_bases[i] is None -> skip (defensive)."""
        proto = self._make(dim=4, key_length=10)
        proto.num_qudits = 2
        proto.alice_symbols = [0, 1]
        proto.alice_bases = [None, 0]
        proto.bob_results = [0, 1]
        proto.bob_bases = [None, 0]

        alice_s, bob_s = proto.sift_keys()
        self.assertEqual(alice_s, [1])
        self.assertEqual(bob_s, [1])

    def test_int_conversion(self):
        """sift_keys converts to int (handles numpy ints etc.)."""
        proto = self._make(dim=4, key_length=10)
        proto.num_qudits = 2
        proto.alice_symbols = [np.int64(0), np.int64(1)]
        proto.alice_bases = [0, 1]
        proto.bob_results = [0, 1]
        proto.bob_bases = [0, 1]

        alice_s, bob_s = proto.sift_keys()
        self.assertEqual(alice_s, [0, 1])
        self.assertEqual(bob_s, [0, 1])
        for val in alice_s + bob_s:
            self.assertIsInstance(val, int)

class TestHDQKDEstimateQBER(BaseHDQKDTest):
    """Cover estimate_qber: <10 bits, 0 errors, some errors."""

    def test_fewer_than_10_bits_returns_1(self):
        """Less than 10 sifted bits -> QBER = 1.0."""
        proto = self._make(dim=4, key_length=10)
        proto.num_qudits = 5
        proto.alice_symbols = [0] * 5
        proto.alice_bases = [0] * 5
        proto.bob_results = [0] * 5
        proto.bob_bases = [0] * 5

        self.assertAlmostEqual(proto.estimate_qber(), 1.0)

    def test_perfect_match_zero_errors(self):
        """All sifted symbols match -> QBER = 0.0."""
        proto = self._make(dim=4, key_length=100)
        n = 20
        proto.num_qudits = n
        proto.alice_symbols = [i % 4 for i in range(n)]
        proto.alice_bases = [0] * n
        proto.bob_results = [i % 4 for i in range(n)]
        proto.bob_bases = [0] * n

        self.assertAlmostEqual(proto.estimate_qber(), 0.0)

    def test_some_errors(self):
        """Some mismatches -> QBER = errors / total."""
        proto = self._make(dim=4, key_length=100)
        n = 20
        proto.num_qudits = n
        proto.alice_symbols = [0] * n
        proto.alice_bases = [0] * n
        proto.bob_results = [1 if i < 5 else 0 for i in range(n)]
        proto.bob_bases = [0] * n

        qber = proto.estimate_qber()
        self.assertAlmostEqual(qber, 5.0 / 20.0)

    def test_all_errors(self):
        """Every sifted symbol mismatches -> QBER = 1.0."""
        proto = self._make(dim=4, key_length=100)
        n = 15
        proto.num_qudits = n
        proto.alice_symbols = [i % 4 for i in range(n)]
        proto.alice_bases = [0] * n
        proto.bob_results = [(i + 1) % 4 for i in range(n)]
        proto.bob_bases = [0] * n

        self.assertAlmostEqual(proto.estimate_qber(), 1.0)

class TestHDQKDBasisDistribution(BaseHDQKDTest):
    """Cover get_basis_distribution."""

    def test_counts_match(self):
        proto = self._make(dim=4, key_length=10)
        proto.num_qudits = 10
        proto.alice_bases = [0, 1, 2, 0, 1, 2, 0, 1, 2, 0]
        proto.bob_bases = [0, 1, None, 0, 1, None, 0, 1, 2, 0]

        dist = proto.get_basis_distribution()

        self.assertEqual(dist["total_qudits"], 10)
        self.assertEqual(dist["dimension"], 4)
        self.assertEqual(dist["alice_bases"], {0: 4, 1: 3, 2: 3})
        self.assertEqual(dist["bob_bases"], {0: 4, 1: 3, 2: 1})

    def test_all_none(self):
        """All None bases -> empty distribution dicts."""
        proto = self._make(dim=4, key_length=10)
        proto.alice_bases = [None, None]
        proto.bob_bases = [None, None]
        proto.num_qudits = 2

        dist = proto.get_basis_distribution()

        self.assertEqual(dist["alice_bases"], {})
        self.assertEqual(dist["bob_bases"], {})
        self.assertEqual(dist["total_qudits"], 2)
        self.assertEqual(dist["dimension"], 4)

    def test_includes_correct_keys(self):
        proto = self._make(dim=8, key_length=5)
        proto.alice_bases = [0]
        proto.bob_bases = [0]
        proto.num_qudits = 1

        dist = proto.get_basis_distribution()
        self.assertIn("alice_bases", dist)
        self.assertIn("bob_bases", dist)
        self.assertIn("total_qudits", dist)
        self.assertIn("dimension", dist)
        self.assertEqual(dist["dimension"], 8)

class TestHDQKDEndToEnd(BaseHDQKDTest):
    """Short end-to-end flows with mocked internals."""

    @patch("qkdpy.protocols.hd_qkd.secure_randint")
    @patch("qkdpy.protocols.hd_qkd.Qudit.computational_basis")
    def test_prepare_sift_with_key_length_1(self, mock_cb, mock_randint):
        """key_length=1: prepare_states then sift_keys."""
        proto = self._make(dim=2, key_length=1)
        n_mubs = len(proto.mubs)

        # Interleaved: symbol, basis, symbol, basis, symbol, basis
        # alice_symbols becomes [0, 0, 0], alice_bases becomes [1, 0, 1]
        mock_randint.side_effect = [0, 1, 0, 0, 0, 1]
        mock_cb.return_value = MagicMock()
        proto.prepare_states()

        # Bob: only index 2 has matching basis (1 == 1)
        proto.bob_results = [0, 1, 1]
        proto.bob_bases = [2, 3, 1]

        alice_s, bob_s = proto.sift_keys()
        self.assertEqual(alice_s, [0])
        self.assertEqual(bob_s, [1])

    def test_full_flow_manual(self):
        """Manually drive prepare -> measure -> sift."""
        proto = self._make(dim=2, key_length=10)
        n = 20
        proto.num_qudits = n
        proto.alice_symbols = [i % 2 for i in range(n)]
        proto.alice_bases = [0] * n

        qudits = [None] * n
        results = proto.measure_states(qudits)
        self.assertEqual(results, [])
        self.assertEqual(len(proto.bob_bases), n)

        alice_s, bob_s = proto.sift_keys()
        self.assertEqual(alice_s, [])
        self.assertEqual(bob_s, [])


# ===================================================================
#  Edge cases
# ===================================================================

class TestHDQKDEdgeCases(BaseHDQKDTest):
    """dimension=1, dimension=7, security_threshold=0, key_length=1."""

    def test_dimension_1(self):
        """Minimal dimension = 1."""
        proto = self._make(dim=1, key_length=10)
        self.assertEqual(proto.dimension, 1)
        self.assertEqual(len(proto.mubs), 2)
        eff = proto.get_dimension_efficiency()
        self.assertAlmostEqual(eff, 0.0)

    def test_dimension_7(self):
        """d=7 (odd prime) -> _construct_mubs_prime -> 8 MUBs."""
        proto = self._make(dim=7, key_length=10)
        self.assertEqual(len(proto.mubs), 8)
        for m in proto.mubs:
            self.assertTrue(
                np.allclose(m @ m.conj().T, np.eye(7), atol=1e-8)
            )

    def test_security_threshold_zero(self):
        """security_threshold = 0.0."""
        proto = self._make(dim=4, key_length=10, security_threshold=0.0)
        self.assertEqual(proto._get_security_threshold(), 0.0)
        self.assertEqual(proto.security_threshold, 0.0)

    def test_key_length_1(self):
        """Minimal key_length = 1 -> num_qudits = 3."""
        proto = self._make(dim=4, key_length=1)
        self.assertEqual(proto.key_length, 1)
        self.assertEqual(proto.num_qudits, 3)

    def test_dimension_1_key_length_1(self):
        """Combine both minimal values."""
        proto = self._make(dim=1, key_length=1, security_threshold=0.0)
        self.assertEqual(proto.dimension, 1)
        self.assertEqual(proto.key_length, 1)
        self.assertEqual(proto.num_qudits, 3)
        self.assertEqual(proto._get_security_threshold(), 0.0)

    @patch("qkdpy.protocols.hd_qkd.secure_randint")
    @patch("qkdpy.protocols.hd_qkd.Qudit.computational_basis")
    def test_prepare_states_dim1(self, mock_cb, mock_randint):
        """prepare_states works at dimension 1."""
        proto = self._make(dim=1, key_length=3)
        n = proto.num_qudits

        mock_randint.side_effect = [0] * (n * 2)
        mock_cb.return_value = MagicMock()

        qudits = proto.prepare_states()

        self.assertEqual(len(qudits), n)
        self.assertEqual(proto.alice_symbols, [0] * n)
        self.assertEqual(mock_cb.call_count, n)
        mock_cb.assert_called_with(0, 1)


if __name__ == "__main__":
    unittest.main()
