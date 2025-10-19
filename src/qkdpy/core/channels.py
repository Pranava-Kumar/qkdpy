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
        distance: float = 1.0,  # in km
        loss_coefficient: float = 0.2,  # dB/km
        dark_count_rate: float = 1e-6,  # Hz
        detector_efficiency: float = 0.1,  # 10%
        misalignment_error: float = 0.01,  # 1%
        phase_fluctuation_rate: float = 0.05,  # 5%
        polarization_drift_rate: float = 0.02,  # 2%
        temperature: float = 20.0,  # Celsius
        eavesdropper: Callable | None = None,
    ):
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

        # Calculate initial loss based on distance and loss coefficient
        self.loss = self._calculate_loss_from_distance()

        self.transmitted_count = 0
        self.lost_count = 0
        self.error_count = 0

        # Statistics for eavesdropping
        self.eavesdropped_count = 0
        self.eavesdropper_detected = False

        # Thermal noise contribution based on temperature
        self.thermal_noise_factor = self._calculate_thermal_noise()

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
        return min(1.0, max(0.0, loss_probability))

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

    def transmit(self, qubit: Qubit, timestamp: float = 0.0) -> Qubit | None:
        """Transmit a qubit through the channel with realistic effects.

        Args:
            qubit: The qubit to transmit
            timestamp: Time of transmission (used for temporal effects)

        Returns:
            The received qubit or None if it was lost

        """
        self.transmitted_count += 1

        # Check if the qubit is lost due to channel loss
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

        # Apply various realistic noise effects
        qubit = self._apply_polarization_drift(qubit, timestamp)
        qubit = self._apply_phase_fluctuations(qubit, timestamp)
        qubit = self._apply_misalignment_errors(qubit)
        qubit = self._apply_thermal_noise(qubit)

        return qubit

    def transmit_batch(
        self, qubits: list[Qubit], start_time: float = 0.0, pulse_interval: float = 1e-9
    ) -> list[Qubit | None]:
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

    def _apply_polarization_drift(self, qubit: Qubit, timestamp: float) -> Qubit:
        """Apply polarization drift over time to the qubit.

        Args:
            qubit: The qubit to apply polarization drift to
            timestamp: Current time for drift calculation

        Returns:
            The qubit with applied polarization drift

        """
        # Calculate drift based on time and drift rate
        drift_angle = (
            np.random.normal(0, self.polarization_drift_rate) * timestamp
        ) % (2 * np.pi)

        # Apply rotation to simulate polarization drift
        rotation_matrix = np.array(
            [
                [np.cos(drift_angle), -np.sin(drift_angle)],
                [np.sin(drift_angle), np.cos(drift_angle)],
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
        phase_shift = np.random.normal(0, self.phase_fluctuation_rate) * timestamp

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
        if np.random.random() < self.misalignment_error:
            # Apply small random rotation to simulate basis misalignment
            angle = np.random.uniform(-0.1, 0.1)  # Small angle in radians
            misalignment_matrix = np.array(
                [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
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
        if np.random.random() < self.thermal_noise_factor:
            # Apply random Pauli operator to simulate thermal noise
            gate = random.choice(
                [
                    Identity().matrix,
                    PauliX().matrix,
                    PauliY().matrix,
                    PauliZ().matrix,
                ]
            )

            # Only count as error if it's not identity
            if not np.array_equal(gate, Identity().matrix):
                self.error_count += 1
            qubit.apply_gate(gate)

        return qubit
