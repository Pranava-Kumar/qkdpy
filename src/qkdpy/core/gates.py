"""Quantum gate implementations for qubit manipulation."""

import math

import numpy as np


class QuantumGate:
    """Base class for quantum gates."""

    def __init__(self, matrix: np.ndarray):
        self._matrix = matrix

    @property
    def matrix(self) -> np.ndarray:
        return self._matrix

    def __call__(self) -> np.ndarray:
        return self._matrix


class Identity(QuantumGate):
    """Identity gate."""

    def __init__(self):
        super().__init__(np.array([[1, 0], [0, 1]], dtype=complex))


class PauliX(QuantumGate):
    """Pauli-X gate (bit flip)."""

    def __init__(self):
        super().__init__(np.array([[0, 1], [1, 0]], dtype=complex))


class PauliY(QuantumGate):
    """Pauli-Y gate."""

    def __init__(self):
        super().__init__(np.array([[0, -1j], [1j, 0]], dtype=complex))


class PauliZ(QuantumGate):
    """Pauli-Z gate (phase flip)."""

    def __init__(self):
        super().__init__(np.array([[1, 0], [0, -1]], dtype=complex))


class Hadamard(QuantumGate):
    """Hadamard gate."""

    def __init__(self):
        super().__init__(np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2))


class S(QuantumGate):
    """Phase gate (sqrt(Z))."""

    def __init__(self):
        super().__init__(np.array([[1, 0], [0, 1j]], dtype=complex))


class SDag(QuantumGate):
    """Adjoint of phase gate."""

    def __init__(self):
        super().__init__(np.array([[1, 0], [0, -1j]], dtype=complex))


class T(QuantumGate):
    """π/8 gate (sqrt(S))."""

    def __init__(self):
        super().__init__(np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex))


class TDag(QuantumGate):
    """Adjoint of π/8 gate."""

    def __init__(self):
        super().__init__(
            np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex)
        )


class Rx(QuantumGate):
    """Rotation around X-axis."""

    def __init__(self, theta: float):
        super().__init__(
            np.array(
                [
                    [np.cos(theta / 2), -1j * np.sin(theta / 2)],
                    [-1j * np.sin(theta / 2), np.cos(theta / 2)],
                ],
                dtype=complex,
            )
        )


class Ry(QuantumGate):
    """Rotation around Y-axis."""

    def __init__(self, theta: float):
        super().__init__(
            np.array(
                [
                    [np.cos(theta / 2), -np.sin(theta / 2)],
                    [np.sin(theta / 2), np.cos(theta / 2)],
                ],
                dtype=complex,
            )
        )


class Rz(QuantumGate):
    """Rotation around Z-axis."""

    def __init__(self, theta: float):
        super().__init__(
            np.array(
                [[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]],
                dtype=complex,
            )
        )


class CNOT(QuantumGate):
    """Controlled-NOT gate."""

    def __init__(self):
        super().__init__(
            np.array(
                [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex
            )
        )


class CZ(QuantumGate):
    """Controlled-Z gate."""

    def __init__(self):
        super().__init__(
            np.array(
                [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]], dtype=complex
            )
        )


class SWAP(QuantumGate):
    """SWAP gate."""

    def __init__(self):
        super().__init__(
            np.array(
                [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex
            )
        )
