"""Quantum channel simulation for QKD protocols."""

import math
import random
from collections.abc import Callable

import numpy as np

from .gate_utils import GateUtils
from .gates import Identity, PauliX, PauliY, PauliZ
from .qubit import Qubit


class QuantumChannel:
    """Simulates a quantum channel with various noise models and eavesdropping capabilities.

    This class allows simulation of quantum channels with different types of noise
    and potential eavesdropping attacks for QKD protocol analysis.
    """

    def __init__(
        self,
        loss: float = 0.0,
        noise_model: str = "depolarizing",
        noise_level: float = 0.0,
        eavesdropper: Callable | None = None,
    ):
        """Initialize a quantum channel.

        Args:
            loss: Probability of losing a qubit in the channel (0.0 to 1.0)
            noise_model: Type of noise ('depolarizing', 'bit_flip', 'phase_flip', 'amplitude_damping')
            noise_level: Intensity of the noise (0.0 to 1.0)
            eavesdropper: Optional function representing an eavesdropping attack

        """
        self.loss = max(0.0, min(1.0, loss))
        self.noise_model = noise_model
        self.noise_level = max(0.0, min(1.0, noise_level))
        self.eavesdropper = eavesdropper
        self.transmitted_count = 0
        self.lost_count = 0
        self.error_count = 0

        # Statistics for eavesdropping
        self.eavesdropped_count = 0
        self.eavesdropper_detected = False

    def transmit(self, qubit: Qubit) -> Qubit | None:
        """Transmit a qubit through the channel.

        Args:
            qubit: The qubit to transmit

        Returns:
            The received qubit or None if it was lost

        """
        self.transmitted_count += 1

        # Check if the qubit is lost
        if np.random.random() < self.loss:
            self.lost_count += 1
            return None

        # Apply eavesdropping if present
        if self.eavesdropper is not None:
            result = self.eavesdropper(qubit)
            if isinstance(result, tuple) and len(result) == 2:
                qubit, detected = result
                if detected:
                    self.eavesdropper_detected = True
            self.eavesdropped_count += 1

        # Apply noise based on the noise model
        if self.noise_model == "depolarizing":
            qubit = self._depolarizing_noise(qubit)
        elif self.noise_model == "bit_flip":
            qubit = self._bit_flip_noise(qubit)
        elif self.noise_model == "phase_flip":
            qubit = self._phase_flip_noise(qubit)
        elif self.noise_model == "amplitude_damping":
            qubit = self._amplitude_damping_noise(qubit)

        return qubit

    def transmit_batch(self, qubits: list[Qubit]) -> list[Qubit | None]:
        """Transmit a batch of qubits through the channel.

        Args:
            qubits: List of qubits to transmit

        Returns:
            List of received qubits (None for lost qubits)

        """
        return [self.transmit(qubit) for qubit in qubits]

    def _depolarizing_noise(self, qubit: Qubit) -> Qubit:
        """Apply depolarizing noise to a qubit."""
        if np.random.random() < self.noise_level:
            # Apply a random Pauli operator
            gate = random.choice(
                [
                    Identity().matrix,
                    PauliX().matrix,
                    PauliY().matrix,
                    PauliZ().matrix,
                ]
            )
            if not np.array_equal(gate, Identity().matrix):
                self.error_count += 1
            qubit.apply_gate(gate)
        return qubit

    def _bit_flip_noise(self, qubit: Qubit) -> Qubit:
        """Apply bit flip noise to a qubit."""
        if np.random.random() < self.noise_level:
            qubit.apply_gate(PauliX().matrix)
            self.error_count += 1
        return qubit

    def _phase_flip_noise(self, qubit: Qubit) -> Qubit:
        """Apply phase flip noise to a qubit."""
        if np.random.random() < self.noise_level:
            qubit.apply_gate(PauliZ().matrix)
            self.error_count += 1
        return qubit

    def _amplitude_damping_noise(self, qubit: Qubit) -> Qubit:
        """Apply amplitude damping noise to a qubit."""
        if np.random.random() < self.noise_level:
            gamma = self.noise_level
            if qubit.probabilities[1] > 0 and np.random.random() < gamma:
                # Simulate amplitude damping by collapsing to |0> with probability gamma
                qubit._state = np.array([1, 0], dtype=complex)
                self.error_count += 1
        return qubit

    def get_statistics(self) -> dict[str, int | float | bool]:
        """Get transmission statistics.

        Returns:
            Dictionary containing transmission statistics

        """
        stats = {
            "transmitted": self.transmitted_count,
            "lost": self.lost_count,
            "received": self.transmitted_count - self.lost_count,
            "errors": self.error_count,
            "loss_rate": self.lost_count / max(1, self.transmitted_count),
            "error_rate": self.error_count
            / max(1, self.transmitted_count - self.lost_count),
            "eavesdropped": self.eavesdropped_count,
            "eavesdropper_detected": self.eavesdropper_detected,
        }
        return stats

    def reset_statistics(self) -> None:
        """Reset all statistics counters."""
        self.transmitted_count = 0
        self.lost_count = 0
        self.error_count = 0
        self.eavesdropped_count = 0
        self.eavesdropper_detected = False

    def set_eavesdropper(self, eavesdropper: Callable | None) -> None:
        """Set or remove an eavesdropper on the channel.

        Args:
            eavesdropper: Function representing an eavesdropping attack or None to remove

        """
        self.eavesdropper = eavesdropper

    @staticmethod
    def intercept_resend_attack(
        qubit: Qubit, basis: str = "random"
    ) -> tuple[Qubit, bool]:
        """Implement an intercept-resend eavesdropping attack.

        Args:
            qubit: The qubit to attack
            basis: Basis to measure in ('computational', 'hadamard', 'circular', or 'random')

        Returns:
            Tuple of (new qubit, detected) where detected indicates if the attack was detected

        """
        if basis == "random":
            basis = random.choice(["computational", "hadamard", "circular"])

        # Make a copy of the original state
        original_state = qubit.state.copy()

        # Measure in the chosen basis
        measurement = qubit.measure(basis)

        # Prepare a new qubit in the measured state
        if basis == "computational":
            new_qubit = Qubit.zero() if measurement == 0 else Qubit.one()
        elif basis == "hadamard":
            new_qubit = Qubit.plus() if measurement == 0 else Qubit.minus()
        elif basis == "circular":
            if measurement == 0:
                new_qubit = Qubit(1 / math.sqrt(2), 1j / math.sqrt(2))
            else:
                new_qubit = Qubit(1 / math.sqrt(2), -1j / math.sqrt(2))

        # Check if the attack was detected by comparing with the original state
        # This is a simplified check - in reality, detection happens during protocol execution
        detected = not np.allclose(original_state, new_qubit.state)

        return new_qubit, detected

    @staticmethod
    def entanglement_attack(qubit: Qubit) -> tuple[Qubit, bool]:
        """Implement an entanglement-based eavesdropping attack.

        Args:
            qubit: The qubit to attack

        Returns:
            Tuple of (new qubit, detected) where detected indicates if the attack was detected

        """
        # This is a simplified version of an entanglement attack
        # In a full implementation, we would need to model entangled qubits

        # Apply a CNOT operation with the qubit as control and an ancilla as target
        # Here we'll simulate this with a probabilistic operation

        if np.random.random() < 0.5:  # 50% chance of entangling
            # Apply a random rotation to simulate the effect of entanglement
            theta = np.random.random() * np.pi
            phi = np.random.random() * 2 * np.pi
            gate = GateUtils.unitary_from_angles(theta, phi, 0)
            qubit.apply_gate(gate)

            # In this simplified model, we'll say the attack is detected 50% of the time
            detected = np.random.random() < 0.5
        else:
            detected = False

        return qubit, detected
