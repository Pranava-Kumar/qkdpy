"""E91 QKD protocol implementation."""

from collections.abc import Sequence
from typing import Any

import numpy as np

from ..core import QuantumChannel, Qubit
from ..core.gates import Ry
from ..core.multiqubit import MultiQubitState
from ..core.secure_random import secure_randint, secure_random
from .base import BaseProtocol


class E91(BaseProtocol):
    """Implementation of the E91 quantum key distribution protocol.

    E91 is a QKD protocol proposed by Artur Ekert in 1991, based on quantum
    entanglement and Bell's inequality. This implementation uses true
    entangled state simulation via MultiQubitState.
    """

    def __init__(
        self,
        channel: QuantumChannel,
        key_length: int = 100,
        security_threshold: float = 0.1,
    ):
        """Initialize the E91 protocol.

        Args:
            channel: Quantum channel for qubit transmission
            key_length: Desired length of the final key
            security_threshold: Maximum QBER value considered secure

        """
        super().__init__(channel, key_length)

        # E91-specific parameters
        # Alice's measurement angles: 0, pi/4, pi/2
        self.alice_angles = [0.0, np.pi / 4, np.pi / 2]

        # Bob's measurement angles: pi/4, pi/2, 3pi/4
        # Note: For key generation, we need matching bases.
        # Alice 0 (0) matches Bob ? No.
        # Alice pi/4 matches Bob pi/4.
        # Alice pi/2 matches Bob pi/2.
        # So we have 2 matching bases for key generation.
        self.bob_angles = [np.pi / 4, np.pi / 2, 3 * np.pi / 4]

        self.security_threshold = security_threshold

        # Number of entangled pairs to generate
        self.num_pairs = max(key_length * 5, 500)

        # Data storage
        self.alice_settings: list[int] = []
        self.bob_settings: list[int] = []
        self.alice_results: list[int] = []
        self.bob_results: list[int] = []

    def prepare_states(self) -> list[Qubit | Any]:
        """Prepare entangled quantum states.

        In this simulation, we generate pairs on demand during measurement.
        Returns placeholders.
        """
        return [Qubit.zero() for _ in range(self.num_pairs)]

    def measure_states(self, states: Sequence[Qubit | Any | None]) -> list[int]:
        """Distribute and measure entangled states.

        Args:
            states: Placeholders

        Returns:
            List of Bob's measurement results
        """
        self.alice_settings = []
        self.bob_settings = []
        self.alice_results = []
        self.bob_results = []

        # Pre-generate settings
        self.alice_settings = [secure_randint(0, 3) for _ in range(self.num_pairs)]
        self.bob_settings = [secure_randint(0, 3) for _ in range(self.num_pairs)]

        for i in range(self.num_pairs):
            # 1. Create a Bell pair (|00> + |11>) / sqrt(2)
            bell_pair = MultiQubitState.ghz(2)

            # 2. Simulate Channel Transmission
            if secure_random() < self.channel.loss:
                self.alice_results.append(-1)
                self.bob_results.append(-1)
                continue

            if (
                self.channel.noise_model == "depolarizing"
                and secure_random() < self.channel.noise_level
            ):
                gate_idx = secure_randint(0, 4)
                if gate_idx == 1:  # X
                    bell_pair.apply_gate(np.array([[0, 1], [1, 0]], dtype=complex), 1)
                elif gate_idx == 2:  # Y
                    bell_pair.apply_gate(
                        np.array([[0, -1j], [1j, 0]], dtype=complex), 1
                    )
                elif gate_idx == 3:  # Z
                    bell_pair.apply_gate(np.array([[1, 0], [0, -1]], dtype=complex), 1)

            # 3. Alice Measures
            a_idx = self.alice_settings[i]
            angle_a = self.alice_angles[a_idx]

            if angle_a != 0:
                bell_pair.apply_gate(Ry(-angle_a).matrix, 0)

            res_a, collapsed_state = bell_pair.measure(0)
            self.alice_results.append(res_a)

            # 4. Bob Measures
            if collapsed_state is None:
                self.bob_results.append(-1)
                continue

            b_idx = self.bob_settings[i]
            angle_b = self.bob_angles[b_idx]

            if angle_b != 0:
                collapsed_state.apply_gate(Ry(-angle_b).matrix, 0)

            res_b, _ = collapsed_state.measure(0)
            self.bob_results.append(res_b)

        return [r if r != -1 else 0 for r in self.bob_results]

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift keys for key generation.

        We keep bits where Alice and Bob used the same measurement basis (angle).
        Matching pairs:
        - Alice pi/4 (idx 1) and Bob pi/4 (idx 0)
        - Alice pi/2 (idx 2) and Bob pi/2 (idx 1)
        """
        alice_sifted = []
        bob_sifted = []

        for i in range(len(self.alice_results)):
            if self.alice_results[i] == -1 or self.bob_results[i] == -1:
                continue

            a_idx = self.alice_settings[i]
            b_idx = self.bob_settings[i]

            angle_a = self.alice_angles[a_idx]
            angle_b = self.bob_angles[b_idx]

            # Check for matching angles (within small tolerance)
            if abs(angle_a - angle_b) < 1e-6:
                alice_sifted.append(self.alice_results[i])
                bob_sifted.append(self.bob_results[i])

        return alice_sifted, bob_sifted

    def estimate_qber(self) -> float:
        """Estimate QBER."""
        alice_sifted, bob_sifted = self.sift_keys()
        if not alice_sifted:
            return 1.0

        errors = sum(
            1 for a, b in zip(alice_sifted, bob_sifted, strict=False) if a != b
        )
        return errors / len(alice_sifted)

    def test_bell_inequality(self) -> dict[str, Any]:
        """Test CHSH inequality.

        We use the non-matching bases for the CHSH test.
        Standard Ekert91 uses:
        Alice: 0 (A1), pi/4 (A2), pi/2 (A3)
        Bob: pi/4 (B1), pi/2 (B2), 3pi/4 (B3)

        S = E(A1, B1) - E(A1, B3) + E(A3, B1) + E(A3, B3)
        Angles:
        A1=0, B1=pi/4 -> diff=pi/4 -> E ~ 0.707
        A1=0, B3=3pi/4 -> diff=3pi/4 -> E ~ -0.707
        A3=pi/2, B1=pi/4 -> diff=pi/4 -> E ~ 0.707
        A3=pi/2, B3=3pi/4 -> diff=pi/4 -> E ~ 0.707

        S = 0.707 - (-0.707) + 0.707 + 0.707 = 2.828
        """
        # Map indices to A1, A3, B1, B3
        # A1: idx 0 (0)
        # A3: idx 2 (pi/2)
        # B1: idx 0 (pi/4)
        # B3: idx 2 (3pi/4)

        pairs = [(0, 0), (0, 2), (2, 0), (2, 2)]  # A1, B1  # A1, B3  # A3, B1  # A3, B3

        correlations = {}

        for a_target, b_target in pairs:
            matches = 0
            total = 0

            for i in range(len(self.alice_results)):
                if self.alice_results[i] == -1:
                    continue

                if (
                    self.alice_settings[i] == a_target
                    and self.bob_settings[i] == b_target
                ):
                    total += 1
                    if self.alice_results[i] == self.bob_results[i]:
                        matches += 1

            if total > 0:
                match_prob = matches / total
                # E = P(match) - P(mismatch) = 2*P(match) - 1
                correlations[(a_target, b_target)] = 2 * match_prob - 1
            else:
                correlations[(a_target, b_target)] = 0.0

        e_a1_b1 = correlations.get((0, 0), 0)
        e_a1_b3 = correlations.get((0, 2), 0)
        e_a3_b1 = correlations.get((2, 0), 0)
        e_a3_b3 = correlations.get((2, 2), 0)

        s_value = e_a1_b1 - e_a1_b3 + e_a3_b1 + e_a3_b3

        return {
            "s_value": s_value,
            "is_violated": abs(s_value) > 2.0,
            "estimated_qber": 0.5 * (1 - abs(s_value) / (2 * np.sqrt(2))),
            "correlation_values": correlations,
        }

    def execute(self) -> dict:
        """Execute the E91 protocol."""
        self.reset()

        # 1. Prepare & Measure (simulated together)
        # We pass empty list or list of Nones, doesn't matter as measure_states ignores input
        self.measure_states([Qubit.zero()] * self.num_pairs)

        # 2. Bell Test
        bell_stats = self.test_bell_inequality()
        self.is_secure = bell_stats["is_violated"]

        # 3. Sift
        alice_key, bob_key = self.sift_keys()

        # 4. Finalize
        self.final_key = alice_key[: self.key_length]
        self.qber = self.estimate_qber()
        self.is_complete = True

        return {
            "final_key": self.final_key,
            "qber": self.qber,
            "is_secure": self.is_secure,
            "bell_test": bell_stats,
            "raw_key_length": len(alice_key),
        }

    def _get_security_threshold(self) -> float:
        return self.security_threshold
