"""Quantum measurement operations for QKD protocols."""

import math

import numpy as np

from .gate_utils import GateUtils
from .gates import QuantumGate
from .qubit import Qubit


class Measurement:
    """Provides various quantum measurement operations for QKD protocols.

    This class implements different measurement bases and strategies used in
    quantum key distribution protocols.
    """

    @staticmethod
    def measure_in_basis(qubit: Qubit, basis: str = "computational") -> int:
        """Measure a qubit in the specified basis.

        Args:
            qubit: The qubit to measure
            basis: Measurement basis ('computational', 'hadamard', 'circular')

        Returns:
            Measurement result (0 or 1)

        """
        return qubit.measure(basis)

    @staticmethod
    def measure_batch_in_basis(
        qubits: list[Qubit], basis: str = "computational"
    ) -> list[int]:
        """Measure a batch of qubits in the specified basis.

        Args:
            qubits: List of qubits to measure
            basis: Measurement basis ('computational', 'hadamard', 'circular')

        Returns:
            List of measurement results (0 or 1 for each qubit)

        """
        return [Measurement.measure_in_basis(q, basis) for q in qubits]

    @staticmethod
    def measure_in_random_basis(
        qubit: Qubit, bases: list[str] = None
    ) -> tuple[int, str]:
        """Measure a qubit in a randomly chosen basis.

        Args:
            qubit: The qubit to measure
            bases: List of bases to choose from (default: ['computational', 'hadamard'])

        Returns:
            Tuple of (measurement result, chosen basis)

        """
        if bases is None:
            bases = ["computational", "hadamard"]

        basis = np.random.choice(bases)
        result = Measurement.measure_in_basis(qubit, basis)
        return result, basis

    @staticmethod
    def measure_batch_in_random_bases(
        qubits: list[Qubit], bases: list[str] = None
    ) -> tuple[list[int], list[str]]:
        """Measure a batch of qubits in randomly chosen bases.

        Args:
            qubits: List of qubits to measure
            bases: List of bases to choose from (default: ['computational', 'hadamard'])

        Returns:
            Tuple of (measurement results, chosen bases)

        """
        if bases is None:
            bases = ["computational", "hadamard"]

        results = []
        chosen_bases = []

        for qubit in qubits:
            basis = np.random.choice(bases)
            result = Measurement.measure_in_basis(qubit, basis)
            results.append(result)
            chosen_bases.append(basis)

        return results, chosen_bases

    @staticmethod
    def measure_state_fidelity(qubit: Qubit, target_state: np.ndarray) -> float:
        """Measure the fidelity between a qubit state and a target state.

        Args:
            qubit: The qubit to measure
            target_state: The target state vector

        Returns:
            Fidelity value between 0 and 1

        """
        state = qubit.state
        # Fidelity = |<ψ|φ>|^2
        fidelity = abs(np.vdot(state, target_state)) ** 2
        return fidelity

    @staticmethod
    def measure_bloch_coordinates(qubit: Qubit) -> tuple[float, float, float]:
        """Measure the Bloch sphere coordinates of a qubit.

        Args:
            qubit: The qubit to measure

        Returns:
            Tuple of (x, y, z) coordinates on the Bloch sphere

        """
        return qubit.bloch_vector()

    @staticmethod
    def measure_density_matrix(qubit: Qubit) -> np.ndarray:
        """Measure the density matrix of a qubit.

        Args:
            qubit: The qubit to measure

        Returns:
            2x2 density matrix

        """
        return qubit.density_matrix()

    @staticmethod
    def measure_purity(qubit: Qubit) -> float:
        """Measure the purity of a qubit state.

        Args:
            qubit: The qubit to measure

        Returns:
            Purity value (1 for pure states, <1 for mixed states)

        """
        rho = qubit.density_matrix()
        purity = np.real(np.trace(rho @ rho))
        return purity

    @staticmethod
    def measure_von_neumann_entropy(qubit: Qubit) -> float:
        """Measure the von Neumann entropy of a qubit state.

        Args:
            qubit: The qubit to measure

        Returns:
            Von Neumann entropy value

        """
        rho = qubit.density_matrix()
        eigenvalues = np.linalg.eigvalsh(rho)

        # Remove eigenvalues that are effectively zero
        eigenvalues = eigenvalues[eigenvalues > 1e-10]

        # Calculate entropy: S = -∑(λ * log2(λ))
        entropy = -np.sum(eigenvalues * np.log2(eigenvalues))
        return entropy

    @staticmethod
    def measure_observable(qubit: Qubit, observable: np.ndarray) -> float:
        """Measure the expectation value of an observable.

        Args:
            qubit: The qubit to measure
            observable: Hermitian matrix representing the observable

        Returns:
            Expectation value of the observable

        Raises:
            ValueError: If the observable is not Hermitian

        """
        if not GateUtils.is_hermitian(observable):
            raise ValueError("Observable must be Hermitian")

        rho = qubit.density_matrix()
        expectation = np.real(np.trace(rho @ observable))
        return expectation

    @staticmethod
    def measure_bell_state(qubit1: Qubit, qubit2: Qubit) -> str:
        """Measure which Bell state two qubits are in.

        Args:
            qubit1: First qubit
            qubit2: Second qubit

        Returns:
            String representing the Bell state ('Φ+', 'Φ-', 'Ψ+', 'Ψ-')

        """
        # Create the combined state
        state = np.kron(qubit1.state, qubit2.state)

        # Bell states
        phi_plus = np.array([1, 0, 0, 1]) / math.sqrt(2)
        phi_minus = np.array([1, 0, 0, -1]) / math.sqrt(2)
        psi_plus = np.array([0, 1, 1, 0]) / math.sqrt(2)
        psi_minus = np.array([0, 1, -1, 0]) / math.sqrt(2)

        # Calculate fidelities
        fid_phi_plus = abs(np.vdot(state, phi_plus)) ** 2
        fid_phi_minus = abs(np.vdot(state, phi_minus)) ** 2
        fid_psi_plus = abs(np.vdot(state, psi_plus)) ** 2
        fid_psi_minus = abs(np.vdot(state, psi_minus)) ** 2

        # Find the Bell state with the highest fidelity
        fidelities = {
            "Φ+": fid_phi_plus,
            "Φ-": fid_phi_minus,
            "Ψ+": fid_psi_plus,
            "Ψ-": fid_psi_minus,
        }

        return max(fidelities, key=fidelities.get)

    @staticmethod
    def quantum_state_tomography(
        qubit: Qubit, num_measurements: int = 1000
    ) -> dict[str, float]:
        """Perform quantum state tomography to reconstruct the density matrix.

        Args:
            qubit: The qubit to measure
            num_measurements: Number of measurements to perform for each basis

        Returns:
            Dictionary containing the reconstructed density matrix elements

        """
        # Make a copy of the qubit to avoid modifying the original
        qubit_copy = Qubit(qubit.state[0], qubit.state[1])

        # Measurements in different bases
        results_x = []
        results_y = []
        results_z = []

        for _ in range(num_measurements):
            # Reset the qubit to its original state
            qubit_copy._state = qubit.state.copy()

            # Measure in X basis (Hadamard)
            qubit_copy.apply_gate(QuantumGate.H())
            result_x = qubit_copy.measure("computational")
            qubit_copy.collapse_state(result_x, "computational")
            results_x.append(result_x)

            # Reset and measure in Y basis
            qubit_copy._state = qubit.state.copy()
            qubit_copy.apply_gate(QuantumGate.H())
            qubit_copy.apply_gate(QuantumGate.S())
            result_y = qubit_copy.measure("computational")
            qubit_copy.collapse_state(result_y, "computational")
            results_y.append(result_y)

            # Reset and measure in Z basis
            qubit_copy._state = qubit.state.copy()
            result_z = qubit_copy.measure("computational")
            qubit_copy.collapse_state(result_z, "computational")
            results_z.append(result_z)

        # Calculate expectation values
        exp_x = 1 - 2 * np.mean(results_x)  # Convert from 0/1 to +1/-1
        exp_y = 1 - 2 * np.mean(results_y)
        exp_z = 1 - 2 * np.mean(results_z)

        # Reconstruct density matrix from expectation values
        # ρ = (I + <X>X + <Y>Y + <Z>Z) / 2
        identity = np.eye(2)
        pauli_x = np.array([[0, 1], [1, 0]])
        pauli_y = np.array([[0, -1j], [1j, 0]])
        pauli_z = np.array([[1, 0], [0, -1]])

        rho = (identity + exp_x * pauli_x + exp_y * pauli_y + exp_z * pauli_z) / 2

        # Return the density matrix elements
        return {
            "rho_00": rho[0, 0],
            "rho_01": rho[0, 1],
            "rho_10": rho[1, 0],
            "rho_11": rho[1, 1],
            "exp_x": exp_x,
            "exp_y": exp_y,
            "exp_z": exp_z,
        }
