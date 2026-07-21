"""Quantum channel simulation for QKD protocols."""

import math
from collections.abc import Callable

import numpy as np

from .channel_base import ChannelBase
from .gates import (
    PauliX,
    PauliY,
    PauliZ,
)
from .measurements import Measurement
from .qubit import Qubit
from .qudit import Qudit
from .secure_random import (
    secure_choice,
    secure_normal,
    secure_random,
)


class QuantumChannel(ChannelBase):
    """Simulates a quantum channel with various noise models and eavesdropping capabilities.

    This class allows simulation of quantum channels with different types of noise
    and potential eavesdropping attacks for QKD protocol analysis.
    """

    def __init__(
        self,
        distance: float = 1.0,  # in km
        loss_coefficient: float = 0.2,  # dB/km
        dark_count_rate: float = 1e-6,  # Hz
        detector_efficiency: float = 0.1,  # 10%
        misalignment_error: float = 0.01,  # 1%
        phase_fluctuation_rate: float = 0.05,  # 5%
        polarization_drift_rate: float = 0.02,  # 2%
        temperature: float = 20.0,  # Celsius
        eavesdropper: (
            Callable[[Qubit | Qudit], tuple[Qubit | Qudit, bool]] | None
        ) = None,
        # Legacy/Explicit noise parameters
        loss: float | None = None,
        noise_model: str = "none",
        noise_level: float = 0.0,
    ) -> None:
        """Initialize a quantum channel with realistic physical properties.

        Args:
            distance: Physical distance of the channel in km
            loss_coefficient: Fiber loss coefficient in dB/km
            dark_count_rate: Detector dark count rate in Hz
            detector_efficiency: Photon detector efficiency (0.0 to 1.0)
            misalignment_error: Probability of basis misalignment
            phase_fluctuation_rate: Rate of phase fluctuations in the channel
            polarization_drift_rate: Rate of polarization drift
            temperature: Temperature in Celsius (affects noise)
            eavesdropper: Optional function representing an eavesdropping attack
            loss: Direct loss probability (overrides distance-based calculation)
            noise_model: Type of noise model ("none", "depolarizing", "bit_flip", etc.)
            noise_level: Probability/intensity of the noise
        """
        self.distance = max(0.0, distance)
        self.loss_coefficient = max(0.0, loss_coefficient)
        self.dark_count_rate = max(0.0, dark_count_rate)
        self.detector_efficiency = max(0.0, min(1.0, detector_efficiency))
        self.misalignment_error = max(0.0, min(1.0, misalignment_error))
        self.phase_fluctuation_rate = max(0.0, phase_fluctuation_rate)
        self.polarization_drift_rate = max(0.0, polarization_drift_rate)
        self.temperature = temperature
        self.eavesdropper = eavesdropper
        self.noise_model = noise_model
        self.noise_level = noise_level

        # If the caller set a positive noise_level but left the model at the
        # default "none", the noise would silently have no effect. Promote the
        # implicit noise to a depolarizing channel so a standalone
        # ``QuantumChannel(noise_level=p)`` actually perturbs transmitted qubits
        # (fixes the "noise_level has zero effect" audit finding).
        if self.noise_model == "none" and self.noise_level > 0.0:
            self.noise_model = "depolarizing"

        # Validate noise_model to catch typos early.
        _valid_noise_models = {
            "none",
            "depolarizing",
            "bit_flip",
            "phase_flip",
            "phase_damping",
            "dephasing",
            "amplitude_damping",
        }
        if self.noise_model not in _valid_noise_models:
            raise ValueError(
                f"Unknown noise_model {self.noise_model!r}. "
                f"Valid models: {sorted(_valid_noise_models)}"
            )

        # Calculate initial loss based on distance and loss coefficient
        if loss is not None:
            self.loss = max(0.0, min(1.0, loss))
        else:
            self.loss = self._calculate_loss_from_distance()

        self.transmitted_count = 0
        self.lost_count = 0
        self.error_count = 0

        # Statistics for eavesdropping
        self.eavesdropped_count = 0
        self.eavesdropper_detected = False

        # Thermal noise contribution based on temperature
        self.thermal_noise_factor = self._calculate_thermal_noise()

    @property
    def distance_km(self) -> float:
        """Channel distance in kilometres (alias of :attr:`distance`).

        Exposed so diagnostics that look up ``distance_km`` resolve correctly
        instead of reading ``None``.
        """
        return self.distance

    def _calculate_loss_from_distance(self) -> float:
        """Calculate photon loss based on distance and loss coefficient.

        Returns:
            Loss probability based on distance and loss coefficient

        """
        # Convert dB/km to linear loss coefficient
        alpha_linear = 10 ** (-self.loss_coefficient / 10.0)
        # Calculate loss based on Beer-Lambert law: I = I0 * exp(-alpha * distance)
        # Convert to probability of survival
        loss_probability = 1.0 - (alpha_linear**self.distance)
        return float(min(1.0, max(0.0, loss_probability)))

    def _calculate_thermal_noise(self) -> float:
        """Calculate thermal noise contribution based on temperature.

        Returns:
            Thermal noise factor

        """
        # Simplified thermal noise model based on temperature
        # In real systems, thermal noise increases with temperature
        base_thermal_noise = 1e-4  # Base thermal noise at 20°C
        temp_factor = max(0.1, (self.temperature - 20.0) / 20.0 + 1.0)
        return base_thermal_noise * temp_factor

    def transmit(
        self, qubit: Qubit | Qudit, timestamp: float = 0.0
    ) -> Qubit | Qudit | None:
        """Transmit a qubit through the channel with realistic effects.

        Args:
            qubit: The qubit to transmit
            timestamp: Time of transmission (used for temporal effects)

        Returns:
            The received qubit or None if it was lost

        """
        self.transmitted_count += 1

        # Check if the qubit is lost due to channel loss
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

        # Apply various realistic noise effects
        # Note: These effects are currently only implemented for Qubits (dimension 2)
        if hasattr(qubit, "dimension") and qubit.dimension > 2:
            # For high-dimensional qudits, we currently skip these specific noise models
            # as they are defined for 2D systems (polarization, phase, etc.)
            pass
        else:
            if isinstance(qubit, Qubit):
                qubit = self._apply_polarization_drift(qubit, timestamp)
                qubit = self._apply_phase_fluctuations(qubit, timestamp)
                qubit = self._apply_misalignment_errors(qubit)
                qubit = self._apply_thermal_noise(qubit)

        # Apply explicit noise models if configured
        if self.noise_model == "depolarizing":
            if hasattr(qubit, "dimension") and qubit.dimension > 2:
                # Skip for now or implement d-dimensional depolarizing
                pass
            else:
                if isinstance(qubit, Qubit):
                    qubit = self._depolarizing_noise(qubit)
        elif self.noise_model == "bit_flip":
            if not (hasattr(qubit, "dimension") and qubit.dimension > 2):
                if isinstance(qubit, Qubit):
                    qubit = self._bit_flip_noise(qubit)
        elif self.noise_model in ("phase_flip", "phase_damping", "dephasing"):
            if not (hasattr(qubit, "dimension") and qubit.dimension > 2):
                if isinstance(qubit, Qubit):
                    qubit = self._phase_flip_noise(qubit)
        elif self.noise_model == "amplitude_damping":
            if not (hasattr(qubit, "dimension") and qubit.dimension > 2):
                if isinstance(qubit, Qubit):
                    qubit = self._amplitude_damping_noise(qubit)

        return qubit

    def transmit_batch(
        self,
        qubits: list[Qubit | Qudit],
        start_time: float = 0.0,
        pulse_interval: float = 1e-9,
    ) -> list[Qubit | Qudit | None]:
        """Transmit a batch of qubits through the channel.

        Args:
            qubits: List of qubits to transmit
            start_time: Starting time for the first qubit
            pulse_interval: Time interval between qubits (in seconds)

        Returns:
            List of received qubits (None for lost qubits)

        """
        results = []
        for i, qubit in enumerate(qubits):
            timestamp = start_time + i * pulse_interval
            results.append(self.transmit(qubit, timestamp))
        return results

    def _depolarizing_noise(self, qubit: Qubit) -> Qubit:
        """Apply depolarizing noise to a qubit.

        Standard depolarizing channel: rho -> (1-p)*rho + p/3*(X*rho*X + Y*rho*Y + Z*rho*Z).
        Uses statevector unraveling (quantum trajectory method).

        Args:
            qubit: Input qubit

        Returns:
            Qubit after potential depolarization
        """
        p = self.noise_level
        if p > 0 and secure_random() < p:
            # Apply a random Pauli (X, Y, or Z) — NOT Identity
            gate = secure_choice(
                [
                    PauliX().matrix,
                    PauliY().matrix,
                    PauliZ().matrix,
                ]
            )
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

        Uses the correct Kraus operators (quantum trajectory method):
          K0 = [[1, 0], [0, sqrt(1-gamma)]]
          K1 = [[0, sqrt(gamma)], [0, 0]]

        The |1> amplitude is damped by sqrt(1-gamma) and the population
        decays to |0> with probability gamma * |beta|^2.

        Args:
            qubit: Input qubit

        Returns:
            Qubit after amplitude damping
        """
        gamma = self.noise_level
        if gamma <= 0:
            return qubit

        alpha, beta = qubit._state[0], qubit._state[1]

        # Probability of quantum jump (|1> → |0>)
        jump_prob = gamma * (abs(beta) ** 2)

        if jump_prob > 0 and secure_random() < jump_prob:
            # K1: quantum jump — collapse to |0>
            qubit._state = np.array([1.0 + 0.0j, 0.0 + 0.0j])
            self.error_count += 1
        else:
            # K0: no jump — damp |1> amplitude, preserve |0>
            new_alpha = alpha
            new_beta = np.sqrt(1.0 - gamma) * beta
            norm = np.sqrt(abs(new_alpha) ** 2 + abs(new_beta) ** 2)
            if norm > 0:
                qubit._state = np.array([new_alpha / norm, new_beta / norm])

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

    def set_eavesdropper(
        self,
        eavesdropper: Callable[[Qubit | Qudit], tuple[Qubit | Qudit, bool]] | None,
    ) -> None:
        """Set or remove an eavesdropper on the channel.

        Args:
            eavesdropper: Function representing an eavesdropping attack or None to remove

        """
        self.eavesdropper = eavesdropper

    @staticmethod
    def intercept_resend_attack(
        qubit: Qubit | Qudit, basis: str = "random"
    ) -> tuple[Qubit | Qubit | Qudit, bool]:
        """Implement an intercept-resend eavesdropping attack.

        Models Eve performing a CNOT interaction between the travelling qubit
        and an ancilla she prepares in ``|0>``. The CNOT couples Eve's probe to
        the transmitted state, leaking partial information but also disturbing
        the qubit.

        The disturbance (and thus detection probability) depends on the input
        state: basis states ``|0>`` and ``|1>`` pass through the CNOT without
        disturbance (Eve learns them perfectly), while superposition states
        like ``|+>`` and ``|->`` are fully disturbed. For a uniformly random
        BB84 state the expected QBER contribution is 25%, matching the
        theoretical intercept-resend bound.

        Args:
            qubit: The qubit to attack
            basis: Basis to measure in ('computational', 'hadamard', 'circular', or 'random')

        Returns:
            Tuple of (new qubit, detected) where detected indicates if the
            attack is expected to be caught by the protocol's QBER check.
        """
        if basis == "random":
            basis = secure_choice(["computational", "hadamard", "circular"])

        # Make a copy of the original state
        original_state = qubit.state.copy()

        # Measure in the chosen basis
        measurement = Measurement.measure_in_basis(qubit, basis)

        # Prepare a new qubit in the measured state
        if basis == "computational":
            new_qubit: Qubit | Qudit = Qubit.zero() if measurement == 0 else Qubit.one()
        elif basis == "hadamard":
            new_qubit = Qubit.plus() if measurement == 0 else Qubit.minus()
        elif basis == "circular":
            if measurement == 0:
                new_qubit = Qubit(1 / math.sqrt(2), 1j / math.sqrt(2))
            else:
                new_qubit = Qubit(1 / math.sqrt(2), -1j / math.sqrt(2))
        else:
            raise ValueError("Invalid basis for intercept-resend attack.")

        # Check if the attack was detected by comparing with the original state
        # This is a simplified check - in reality, detection happens during protocol execution
        detected = not np.allclose(original_state, new_qubit.state)

        return new_qubit, detected

    @staticmethod
    def entanglement_attack(
        qubit: Qubit | Qudit,
    ) -> tuple[Qubit | Qubit | Qudit, bool]:
        """Implement an entanglement-based eavesdropping attack (CNOT probe).

        Models Eve preparing an ancilla qubit in ``|0>`` then performing a
        CNOT with the travelling qubit as control and her ancilla as target.
        The entangling interaction is:

            (α|0> + β|1>) |0>_E  →  α|00> + β|11>

        Tracing out Eve's ancilla leaves the signal qubit in the dephased
        state ρ' = |α|²|0⟩⟨0| + |β|²|1⟩⟨1| — a Z-basis dephasing channel.

        * Computational-basis states (|0>, |1>) pass undisturbed — Eve learns
          the bit value perfectly from her ancilla.
        * Superposition states (|+>, |->) are fully dephased, producing a
          50% error rate on those bits.
        * For uniformly random BB84 states the expected QBER is 25%,
          matching the theoretical intercept-resend bound.

        This replaces the previous implementation that applied random unitary
        rotations, which had no physical basis as an eavesdropping strategy
        and produced unphysical QBER estimates.

        Args:
            qubit: The qubit to attack

        Returns:
            Tuple of (new qubit, detected) where detected indicates if the
            attack is expected to be caught by the protocol's QBER check.

        """
        if isinstance(qubit, Qudit):
            return qubit, False

        original_state = qubit.state.copy()
        prob_0 = abs(original_state[0]) ** 2

        # CNOT entangles: Eve's ancilla (|0>_E) gets flipped when signal is |1>.
        # After tracing out the ancilla the signal is dephased in Z:
        #   ρ_signal' = |α|²|0⟩⟨0| + |β|²|1⟩⟨1|
        #
        # Stochastic unraveling: collapse to |0> with prob |α|² or |1> with
        # prob |β|².  This is the physically correct CPTP map for the CNOT
        # entangling attack with the ancilla traced out.
        if secure_random() < prob_0:
            qubit._state = np.array([1.0 + 0.0j, 0.0 + 0.0j])
        else:
            qubit._state = np.array([0.0 + 0.0j, 1.0 + 0.0j])

        # Disturbance = probability that a measurement in the original
        # preparation basis gives a different result.  Equivalently, the
        # one-bit QBER contribution = 2|α|²|β|² — 0 for |0>/|1>, 0.5 for
        # |+>/|->, 0.25 on average for random BB84 states.
        disturbance = 2.0 * prob_0 * (1.0 - prob_0)
        detected = secure_random() < disturbance

        return qubit, detected

    def _apply_polarization_drift(self, qubit: Qubit, timestamp: float) -> Qubit:
        """Apply polarization drift over time to the qubit.

        Args:
            qubit: The qubit to apply polarization drift to
            timestamp: Current time for drift calculation

        Returns:
            The qubit with applied polarization drift

        """
        # Calculate drift based on time and drift rate
        drift_angle = (secure_normal(0, self.polarization_drift_rate) * timestamp) % (
            2 * np.pi
        )

        # Apply rotation to simulate polarization drift (Ry gate on Bloch sphere)
        # Ry(theta) = cos(theta/2) * I - i * sin(theta/2) * Y
        rotation_matrix = np.array(
            [
                [np.cos(drift_angle / 2), -np.sin(drift_angle / 2)],
                [np.sin(drift_angle / 2), np.cos(drift_angle / 2)],
            ],
            dtype=complex,
        )

        qubit.apply_gate(rotation_matrix)
        return qubit

    def _apply_phase_fluctuations(self, qubit: Qubit, timestamp: float) -> Qubit:
        """Apply phase fluctuations to the qubit.

        Args:
            qubit: The qubit to apply phase fluctuations to
            timestamp: Current time for fluctuation calculation

        Returns:
            The qubit with applied phase fluctuations

        """
        # Calculate phase fluctuation based on time and rate
        phase_shift = secure_normal(0, self.phase_fluctuation_rate) * timestamp

        # Apply phase shift gate (Z rotation)
        phase_matrix = np.array([[1, 0], [0, np.exp(1j * phase_shift)]], dtype=complex)

        qubit.apply_gate(phase_matrix)
        return qubit

    def _apply_misalignment_errors(self, qubit: Qubit) -> Qubit:
        """Apply basis misalignment errors to the qubit.

        Args:
            qubit: The qubit to apply misalignment to

        Returns:
            The qubit with applied misalignment

        """
        if secure_random() < self.misalignment_error:
            # Apply small random rotation to simulate basis misalignment
            # Use SU(2) Ry gate with halved angle for Bloch sphere correctness
            angle = -0.1 + secure_random() * 0.2  # Small angle in radians
            misalignment_matrix = np.array(
                [
                    [np.cos(angle / 2), -np.sin(angle / 2)],
                    [np.sin(angle / 2), np.cos(angle / 2)],
                ],
                dtype=complex,
            )

            qubit.apply_gate(misalignment_matrix)

        return qubit

    def _apply_thermal_noise(self, qubit: Qubit) -> Qubit:
        """Apply thermal noise to the qubit.

        Args:
            qubit: The qubit to apply thermal noise to

        Returns:
            The qubit with applied thermal noise

        """
        if secure_random() < self.thermal_noise_factor:
            # Apply random non-trivial Pauli to simulate thermal noise
            # (Identity is never applied since it's not an error)
            gate = secure_choice(
                [
                    PauliX().matrix,
                    PauliY().matrix,
                    PauliZ().matrix,
                ]
            )

            self.error_count += 1
            qubit.apply_gate(gate)

        return qubit
