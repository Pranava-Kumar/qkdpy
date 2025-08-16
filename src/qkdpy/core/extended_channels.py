"""Extended quantum channel models with additional noise types."""

import random

import numpy as np

from .gates import Identity, PauliX, PauliY, PauliZ
from .qubit import Qubit


class ExtendedQuantumChannel:
    """Extended quantum channel with additional noise models."""

    def __init__(
        self,
        loss: float = 0.0,
        noise_model: str = "depolarizing",
        noise_level: float = 0.0,
        eavesdropper=None,
    ):
        """Initialize an extended quantum channel.

        Args:
            loss: Probability of losing a qubit in the channel (0.0 to 1.0)
            noise_model: Type of noise ('depolarizing', 'bit_flip', 'phase_flip',
                         'amplitude_damping', 'phase_damping', 'generalized_amplitude_damping')
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
        elif self.noise_model == "phase_damping":
            qubit = self._phase_damping_noise(qubit)
        elif self.noise_model == "generalized_amplitude_damping":
            qubit = self._generalized_amplitude_damping_noise(qubit)

        return qubit

    def _depolarizing_noise(self, qubit: Qubit) -> Qubit:
        """Apply depolarizing noise to a qubit."""
        if np.random.random() < self.noise_level:
            # Apply a random Pauli operator
            gates = [
                Identity().matrix,
                PauliX().matrix,
                PauliY().matrix,
                PauliZ().matrix,
            ]
            gate = random.choice(gates)
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

    def _phase_damping_noise(self, qubit: Qubit) -> Qubit:
        """Apply phase damping noise to a qubit."""
        if np.random.random() < self.noise_level:
            # Phase damping affects only the off-diagonal elements of the density matrix
            # This is a simplified model where we apply a phase flip with probability noise_level/2
            if np.random.random() < self.noise_level / 2:
                qubit.apply_gate(PauliZ().matrix)
                self.error_count += 1
        return qubit

    def _generalized_amplitude_damping_noise(self, qubit: Qubit) -> Qubit:
        """Apply generalized amplitude damping noise to a qubit."""
        if np.random.random() < self.noise_level:
            # This combines amplitude damping with a thermal environment
            # We'll model this as a combination of amplitude damping and bit flip
            if np.random.random() < 0.5:
                # Apply amplitude damping
                gamma = self.noise_level
                if qubit.probabilities[1] > 0 and np.random.random() < gamma:
                    qubit._state = np.array([1, 0], dtype=complex)
                    self.error_count += 1
            else:
                # Apply bit flip
                qubit.apply_gate(PauliX().matrix)
                self.error_count += 1
        return qubit

    def get_statistics(self) -> dict:
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

    def set_eavesdropper(self, eavesdropper) -> None:
        """Set or remove an eavesdropper on the channel.

        Args:
            eavesdropper: Function representing an eavesdropping attack or None to remove
        """
        self.eavesdropper = eavesdropper
