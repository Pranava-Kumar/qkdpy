"""Extended quantum channels with additional noise models."""

import math
from collections.abc import Callable

import numpy as np

from .gates import (
    PauliX,
    PauliY,
    PauliZ,
)
from .qubit import Qubit
from .secure_random import secure_choice, secure_random


class ExtendedQuantumChannel:
    """Extended quantum channel with additional noise models."""

    def __init__(
        self,
        loss: float = 0.0,
        noise_model: str = "depolarizing",
        noise_level: float = 0.0,
        eavesdropper: Callable | None = None,
    ) -> None:
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
        if secure_random() < self.loss:
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
        if secure_random() < self.noise_level:
            # Apply a random non-trivial Pauli operator (X, Y, or Z).
            # Identity is deliberately excluded — the whole point of
            # depolarizing noise is *errors*, not "do nothing".  Including
            # Identity would make the effective noise rate 3/4 of the
            # configured level and produced false security estimates in
            # earlier versions (see commit aaa60d4).
            gates = [
                PauliX().matrix,
                PauliY().matrix,
                PauliZ().matrix,
            ]
            gate = secure_choice(gates)
            self.error_count += 1
            qubit.apply_gate(gate)
        return qubit

    def _bit_flip_noise(self, qubit: Qubit) -> Qubit:
        """Apply bit flip noise to a qubit."""
        if secure_random() < self.noise_level:
            qubit.apply_gate(PauliX().matrix)
            self.error_count += 1
        return qubit

    def _phase_flip_noise(self, qubit: Qubit) -> Qubit:
        """Apply phase flip noise to a qubit."""
        if secure_random() < self.noise_level:
            qubit.apply_gate(PauliZ().matrix)
            self.error_count += 1
        return qubit

    def _amplitude_damping_noise(self, qubit: Qubit) -> Qubit:
        """Apply amplitude damping noise to a qubit.

        Models energy decay from |1⟩ → |0⟩ at rate γ using the quantum
        trajectory method (stochastic Kraus operator unraveling).

        Kraus operators:
            K₀ = |0⟩⟨0| + √(1-γ) |1⟩⟨1|   (no-jump evolution)
            K₁ = √γ |0⟩⟨1|                 (quantum jump)

        The jump probability is ⟨ψ|K₁†K₁|ψ⟩ = γ|β|² and when no jump occurs
        the |1⟩ amplitude is damped by √(1-γ) with renormalisation.
        """
        gamma = self.noise_level
        if gamma <= 0.0:
            return qubit

        alpha, beta = qubit.state[0], qubit.state[1]
        prob_1 = abs(beta) ** 2

        if prob_1 > 0 and secure_random() < gamma:
            # Quantum jump: |1⟩ → |0⟩ (photon emission / energy decay)
            qubit._state = np.array([1.0 + 0.0j, 0.0 + 0.0j])
            self.error_count += 1
        elif gamma > 0 and prob_1 > 0:
            # No-jump evolution: damp |1⟩ amplitude by √(1-γ)
            scale = math.sqrt(1.0 - gamma)
            new_beta = scale * beta
            norm = math.sqrt(abs(alpha) ** 2 + abs(new_beta) ** 2)
            if norm > 0:
                qubit._state = np.array([alpha / norm, new_beta / norm])
        return qubit

    def _phase_damping_noise(self, qubit: Qubit) -> Qubit:
        """Apply phase damping noise to a qubit."""
        if secure_random() < self.noise_level:
            # Phase damping affects only the off-diagonal elements of the density matrix
            # This is a simplified model where we apply a phase flip with probability noise_level/2
            if secure_random() < self.noise_level / 2:
                qubit.apply_gate(PauliZ().matrix)
                self.error_count += 1
        return qubit

    def _generalized_amplitude_damping_noise(self, qubit: Qubit) -> Qubit:
        """Apply generalized amplitude damping noise to a qubit.

        Models energy decay and thermal excitation at rate γ with temperature
        parameter p (p=1 → T=0, p=0.5 → infinite temperature).

        Uses the quantum trajectory stochastic unraveling.

        Kraus operators (p = temperature parameter, γ = damping rate):
            K₀ = √p  [|0⟩⟨0| + √(1-γ) |1⟩⟨1|]   (no-jump, decay)
            K₁ = √p  √γ |0⟩⟨1|                    (jump, decay)
            K₂ = √(1-p) [√(1-γ)|0⟩⟨0| + |1⟩⟨1|]  (no-jump, excitation)
            K₃ = √(1-p) √γ |1⟩⟨0|                 (jump, excitation)

        The temperature parameter p is fixed at 0.5 (infinite temperature
        / maximally mixed steady state unless explicitly overridden).
        """
        gamma = self.noise_level
        if gamma <= 0.0:
            return qubit

        p = getattr(self, "temperature", 0.5)
        alpha, beta = qubit.state[0], qubit.state[1]
        prob_0 = abs(alpha) ** 2
        prob_1 = abs(beta) ** 2

        # Random choice between decay (branch 0) and excitation (branch 1)
        r = secure_random()
        if r < p:
            # Decay branch (zero-temperature-like)
            if prob_1 > 0 and secure_random() < gamma:
                # Jump: |1⟩ → |0⟩
                qubit._state = np.array([1.0 + 0.0j, 0.0 + 0.0j])
                self.error_count += 1
            elif gamma > 0 and prob_1 > 0:
                # No-jump: damp |1⟩ amplitude
                scale = math.sqrt(1.0 - gamma)
                new_beta = scale * beta
                norm = math.sqrt(abs(alpha) ** 2 + abs(new_beta) ** 2)
                if norm > 0:
                    qubit._state = np.array([alpha / norm, new_beta / norm])
        else:
            # Excitation branch (thermal)
            if prob_0 > 0 and secure_random() < gamma:
                # Jump: |0⟩ → |1⟩
                qubit._state = np.array([0.0 + 0.0j, 1.0 + 0.0j])
                self.error_count += 1
            elif gamma > 0 and prob_0 > 0:
                # No-jump: damp |0⟩ amplitude
                scale = math.sqrt(1.0 - gamma)
                new_alpha = scale * alpha
                norm = math.sqrt(abs(new_alpha) ** 2 + abs(beta) ** 2)
                if norm > 0:
                    qubit._state = np.array([new_alpha / norm, beta / norm])
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

    def set_eavesdropper(self, eavesdropper: Callable | None) -> None:
        """Set or remove an eavesdropper on the channel.

        Args:
            eavesdropper: Function representing an eavesdropping attack or None to remove
        """
        self.eavesdropper = eavesdropper
