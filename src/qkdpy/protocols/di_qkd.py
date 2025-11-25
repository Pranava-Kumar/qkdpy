from collections.abc import Sequence
from typing import Any

import numpy as np

from ..core import QuantumChannel, Qubit
from ..core.gates import Ry
from ..core.multiqubit import MultiQubitState
from ..core.secure_random import secure_randint, secure_random
from .base import BaseProtocol


class DeviceIndependentQKD(BaseProtocol):
    """Implementation of a device-independent QKD protocol (based on CHSH).

    This implementation simulates a true entanglement-based protocol using
    MultiQubitState to represent Bell pairs. It verifies security through
    the violation of the CHSH inequality.
    """

    def __init__(
        self,
        channel: QuantumChannel,
        key_length: int = 100,
        security_threshold: float = 2.0,  # CHSH value > 2.0 implies quantum correlations
    ):
        """Initialize the device-independent QKD protocol.

        Args:
            channel: Quantum channel for qubit transmission
            key_length: Desired length of the final key
            security_threshold: Minimum Bell inequality violation for security
        """
        super().__init__(channel, key_length)

        self.security_threshold = security_threshold

        # We need a significant number of pairs for statistical significance in CHSH test
        self.num_pairs = max(key_length * 20, 2000)

        # Measurement settings (angles for Ry rotations)
        # We use 3 settings to allow for both Key Generation and CHSH Test
        # Index 0: Key Generation (Aligned bases)
        # Index 1, 2: CHSH Test Bases

        # Alice:
        # 0: 0 (Key)
        # 1: 0 (CHSH A0)
        # 2: pi/2 (CHSH A1)
        self.alice_angles = [0.0, 0.0, np.pi / 2]

        # Bob:
        # 0: 0 (Key)
        # 1: pi/4 (CHSH B0)
        # 2: -pi/4 (CHSH B1)
        self.bob_angles = [0.0, np.pi / 4, -np.pi / 4]

        # Data storage
        self.alice_settings: list[int] = []
        self.bob_settings: list[int] = []
        self.alice_results: list[int] = []
        self.bob_results: list[int] = []

    def prepare_states(self) -> list[Qubit | Any]:
        """Prepare quantum states.

        In this entanglement-based protocol, we generate pairs on demand
        during the 'measure' phase to simulate the source distributing them.
        We return placeholders to satisfy the interface.
        """
        return [Qubit.zero()] * self.num_pairs

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

        # Pre-generate settings for efficiency (using secure random)
        # 0, 1, or 2 for setting choice
        self.alice_settings = [secure_randint(0, 3) for _ in range(self.num_pairs)]
        self.bob_settings = [secure_randint(0, 3) for _ in range(self.num_pairs)]

        for i in range(self.num_pairs):
            # 1. Create a Bell pair (|00> + |11>) / sqrt(2)
            bell_pair = MultiQubitState.ghz(2)

            # 2. Simulate Channel Transmission (Loss and Noise)
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
            a_setting = self.alice_settings[i]
            angle_a = self.alice_angles[a_setting]

            if angle_a != 0:
                rot_gate_a = Ry(-angle_a).matrix
                bell_pair.apply_gate(rot_gate_a, 0)

            res_a, collapsed_state = bell_pair.measure(0)
            self.alice_results.append(res_a)

            # 4. Bob Measures
            if collapsed_state is None:
                self.bob_results.append(-1)
                continue

            b_setting = self.bob_settings[i]
            angle_b = self.bob_angles[b_setting]

            if angle_b != 0:
                rot_gate_b = Ry(-angle_b).matrix
                collapsed_state.apply_gate(rot_gate_b, 0)

            res_b, _ = collapsed_state.measure(0)
            self.bob_results.append(res_b)

        return [r if r != -1 else 0 for r in self.bob_results]

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift keys for key generation.

        We only use results where both Alice and Bob chose setting 0 (Key Generation).
        """
        alice_sifted = []
        bob_sifted = []

        for i in range(len(self.alice_results)):
            if self.alice_results[i] != -1 and self.bob_results[i] != -1:
                # Check for Key Generation match (Setting 0 for both)
                if self.alice_settings[i] == 0 and self.bob_settings[i] == 0:
                    alice_sifted.append(self.alice_results[i])
                    bob_sifted.append(self.bob_results[i])

        return alice_sifted, bob_sifted

    def test_bell_inequality(self) -> dict[str, float]:
        """Calculate CHSH statistic S using settings 1 and 2."""
        # We use indices 1 and 2 for the CHSH test
        # Alice 1 -> 0 (A0), Alice 2 -> pi/2 (A1)
        # Bob 1 -> pi/4 (B0), Bob 2 -> -pi/4 (B1)

        counts = {}

        for i in range(len(self.alice_results)):
            if self.alice_results[i] == -1:
                continue

            a_idx = self.alice_settings[i]
            b_idx = self.bob_settings[i]

            # Only consider CHSH settings (1 and 2)
            if a_idx == 0 or b_idx == 0:
                continue

            # Map 1->0, 2->1 for easier logic
            a = a_idx - 1
            b = b_idx - 1

            res_a = self.alice_results[i]
            res_b = self.bob_results[i]

            key = (a, b)
            if key not in counts:
                counts[key] = {"match": 0, "total": 0}

            counts[key]["total"] += 1
            if res_a == res_b:
                counts[key]["match"] += 1

        correlations = {}
        for a in [0, 1]:
            for b in [0, 1]:
                if (a, b) in counts and counts[(a, b)]["total"] > 0:
                    match_prob = counts[(a, b)]["match"] / counts[(a, b)]["total"]
                    correlations[(a, b)] = 2 * match_prob - 1
                else:
                    correlations[(a, b)] = 0.0

        # Calculate S
        # S = E(0,0) + E(0,1) + E(1,0) - E(1,1)
        e00 = correlations.get((0, 0), 0)
        e01 = correlations.get((0, 1), 0)
        e10 = correlations.get((1, 0), 0)
        e11 = correlations.get((1, 1), 0)

        s_value = e00 + e01 + e10 - e11

        return {"s_value": s_value, "e00": e00, "e01": e01, "e10": e10, "e11": e11}

    def estimate_qber(self) -> float:
        """Estimate QBER."""
        # For DI-QKD, QBER is less relevant than S-value, but we can calculate
        # the raw mismatch rate of the sifted key.
        alice, bob = self.sift_keys()
        if not alice:
            return 1.0

        mismatches = sum(1 for a, b in zip(alice, bob, strict=False) if a != b)
        return mismatches / len(alice)

    def _get_security_threshold(self) -> float:
        return self.security_threshold

    def execute(self) -> dict:
        self.reset()

        # 1. Prepare & Measure (simulated together)
        self.measure_states([Qubit.zero()] * self.num_pairs)

        # 2. Bell Test
        bell_stats = self.test_bell_inequality()
        self.is_secure = abs(bell_stats["s_value"]) > self.security_threshold

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
