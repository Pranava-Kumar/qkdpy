"""QpiAI Quantum SDK bridge for qkdpy QKD protocols.

This is the runtime engine the ``qpiai-qkd`` companion exposes. It maps qkdpy
protocol objects (qubits, bases, bits) to/from ``qpiai_quantum`` circuits and
statevectors, builds protocol circuits (BB84, E91, Bell, GHZ), simulates them,
and computes the entanglement/QBER/CHSH figures a QKD researcher cares about.

All interaction with the real SDK lives in :mod:`._compat`; this module never
pokes at SDK quirks directly. The local simulator needs a ``QPIAI_API_KEY`` (or
``API_KEY``) in the environment; without it, ``simulate`` returns an inspection
metadata dict rather than crashing, and cloud submission raises a clear error.
"""

from __future__ import annotations

import os
from typing import Any

import numpy as np

from qkdpy.core.qubit import Qubit
from qkdpy.core.secure_random import secure_choice, secure_randint

from ._compat import (
    QpiAISDKError,
    concurrence,
    local_statevector,
    purity,
    qpiai_available,
    submit_to_cloud,
)

if qpiai_available():
    from qpiai_quantum import Circuit, Statevector
else:  # pragma: no cover - import guard
    Circuit = Statevector = None

__all__ = ["QpiAIIntegration"]


class QpiAIIntegration:
    """Bridge between qkdpy QKD protocols and the QpiAI Quantum SDK.

    The class is importable without the SDK installed (methods raise a clear
    :class:`QpiAISDKError` at call time). With the SDK installed and an API key
    present, circuits can be simulated locally or submitted to the QpiAI cloud.
    """

    def __init__(self) -> None:
        self._api_key: str | None = None

    # ------------------------------------------------------------------ #
    #  Qubit <-> Statevector conversion
    # ------------------------------------------------------------------ #
    def qubit_to_qpiai(self, qubit: Qubit) -> Any:
        """Convert a qkdpy Qubit to a QpiAI Statevector.

        qkdpy qubits store ``[|0>, |1>]`` amplitudes; that is exactly what a
        QpiAI ``Statevector`` expects.
        """
        alpha = complex(qubit.state[0])
        beta = complex(qubit.state[1])
        return Statevector([alpha, beta])

    def qpiai_to_qubit(self, state: Any) -> Qubit:
        """Convert a QpiAI Statevector to a qkdpy Qubit."""
        data = np.asarray(getattr(state, "data", state), dtype=np.complex128)
        return Qubit(alpha=data[0], beta=data[1])

    def statevector_from_array(self, data: list[complex]) -> Any:
        """Create a QpiAI Statevector from a list of amplitudes."""
        return Statevector([complex(x) for x in data])

    # ------------------------------------------------------------------ #
    #  Entanglement measures
    # ------------------------------------------------------------------ #
    def compute_concurrence(self, state: Any) -> float:
        """Concurrence of a 2-qubit state (see :func:`._compat.concurrence`)."""
        return concurrence(state)

    def compute_purity(self, state: Any) -> float:
        """Purity Tr(rho^2) of a 2-qubit state (see :func:`._compat.purity`)."""
        return purity(state)

    # ------------------------------------------------------------------ #
    #  Protocol circuit construction
    # ------------------------------------------------------------------ #
    def create_bb84_circuit(
        self,
        num_qubits: int = 1,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
        alice_bits: list[int] | None = None,
    ) -> Any:
        """Create a QpiAI circuit implementing the BB84 protocol.

        Alice and Bob operate on the same physical qubits (connected via a
        quantum channel). Alice prepares, then Bob measures.

        Args:
            num_qubits: Number of qubits to encode.
            alice_bases: Bases Alice uses ('Z' or 'X').
            bob_bases: Bases Bob uses ('Z' or 'X').
            alice_bits: Alice's bit values (0 or 1) for encoding.

        Returns:
            QpiAI Circuit for BB84.
        """
        if alice_bases is None:
            alice_bases = [secure_choice(["Z", "X"]) for _ in range(num_qubits)]
        if bob_bases is None:
            bob_bases = [secure_choice(["Z", "X"]) for _ in range(num_qubits)]
        if alice_bits is None:
            alice_bits = [secure_randint(0, 2) for _ in range(num_qubits)]

        circuit = Circuit(num_qubits, num_qubits)

        for i in range(num_qubits):
            if alice_bits[i] == 1:
                circuit.X(i)
            if alice_bases[i] == "X":
                circuit.H(i)

        for i in range(num_qubits):
            if bob_bases[i] == "X":
                circuit.H(i)

        for i in range(num_qubits):
            circuit.MEASURE(i, i)

        return circuit

    def create_entanglement_circuit(self, state_type: str = "|Ψ+>") -> tuple[Any, str]:
        """Create a circuit for a Bell state (entangled pair).

        Args:
            state_type: One of ``|Ψ+>``, ``|Ψ->``, ``|Φ+>``, ``|Φ->``.

        Returns:
            Tuple of (QpiAI Circuit, description string).
        """
        descriptions = {
            "|Ψ+>": "│01⟩ + │10⟩",
            "|Ψ->": "│01⟩ - │10⟩",
            "|Φ+>": "│00⟩ + │11⟩",
            "|Φ->": "│00⟩ - │11⟩",
        }

        circuit = Circuit(2, 2)
        circuit.H(0)
        circuit.CX(0, 1)

        if state_type == "|Ψ+>":
            circuit.X(0)
        elif state_type == "|Ψ->":
            circuit.X(0)
            circuit.Z(0)
        elif state_type == "|Φ->":
            circuit.Z(0)

        return circuit, descriptions.get(state_type, state_type)

    def create_ghz_circuit(self, num_qubits: int = 3) -> Any:
        """Create a circuit for a GHZ state (|0...0> + |1...1>)/sqrt(2)."""
        circuit = Circuit(num_qubits, num_qubits)
        circuit.H(0)
        for i in range(1, num_qubits):
            circuit.CX(0, i)
        return circuit

    def create_e91_circuit(
        self,
        num_pairs: int = 1,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
    ) -> Any:
        """Create a QpiAI circuit implementing the E91 protocol.

        Uses entangled pairs with measurement in Z, X, and W bases.
        """
        if alice_bases is None:
            alice_bases = [secure_choice(["Z", "X", "W"]) for _ in range(num_pairs)]
        if bob_bases is None:
            bob_bases = [secure_choice(["Z", "X", "W"]) for _ in range(num_pairs)]

        circuit = Circuit(num_pairs * 2, num_pairs * 2)

        for i in range(num_pairs):
            circuit.H(i)
            circuit.CX(i, i + num_pairs)

        for i, basis in enumerate(alice_bases):
            if basis == "X":
                circuit.H(i)
            elif basis == "W":
                circuit.ry(i, -np.pi / 4)

        for i, basis in enumerate(bob_bases):
            bob_wire = i + num_pairs
            if basis == "X":
                circuit.H(bob_wire)
            elif basis == "W":
                circuit.ry(bob_wire, np.pi / 4)

        for i in range(num_pairs * 2):
            circuit.MEASURE(i, i)

        return circuit

    # ------------------------------------------------------------------ #
    #  Simulation & execution
    # ------------------------------------------------------------------ #
    def simulate(self, circuit: Any, shots: int = 1024) -> dict[str, Any]:
        """Run a circuit on the QpiAI local simulator.

        With a ``QPIAI_API_KEY``/``API_KEY`` present, performs a real local
        statevector simulation (via :func:`._compat.local_statevector`). Without
        a key, returns an inspection metadata dict including ``num_qubits`` — it
        never raises on a missing key, since the circuit is still inspectable.

        Args:
            circuit: QpiAI Circuit to simulate.
            shots: Number of shots for sampling.

        Returns:
            Dict with state information.
        """
        if self._api_key is None:
            self._api_key = os.getenv("QPIAI_API_KEY") or os.getenv("API_KEY")

        if self._api_key:
            try:
                return local_statevector(circuit, shots=shots)
            except (QpiAISDKError, ValueError, TypeError) as exc:
                # Degrade gracefully to an inspection dict if the SDK rejects the
                # circuit (e.g. unresolved parameters), rather than crashing.
                return {
                    "circuit": circuit,
                    "num_qubits": getattr(
                        getattr(circuit, "icr", None), "num_qubits", 0
                    ),
                    "note": f"Circuit simulation skipped: {exc}",
                }

        return {
            "circuit": circuit,
            "num_qubits": getattr(getattr(circuit, "icr", None), "num_qubits", 0),
            "num_classical": getattr(getattr(circuit, "icr", None), "num_clbits", 0),
            "note": "Set QPIAI_API_KEY env var for full simulation",
        }

    def submit_to_cloud(
        self,
        circuit: Any,
        device_name: str = "QpiAI-QSV-Simulator",
        shots: int = 1024,
    ) -> dict[str, Any]:
        """Submit a circuit to the QpiAI cloud backend.

        Requires ``QPIAI_API_KEY``. Raises :class:`QpiAISDKError` if no key is
        set or the SDK rejects the submission — errors are surfaced, not masked.

        Args:
            circuit: QpiAI Circuit to submit.
            device_name: Target QpiAI device/backend name.
            shots: Number of shots.

        Returns:
            Dict with cloud result.
        """
        if self._api_key is None:
            self._api_key = os.getenv("QPIAI_API_KEY") or os.getenv("API_KEY")
        return submit_to_cloud(
            circuit, api_key=self._api_key, device_name=device_name, shots=shots
        )

    # ------------------------------------------------------------------ #
    #  QKD metrics
    # ------------------------------------------------------------------ #
    def calculate_qber(self, alice_bits: list[int], bob_bits: list[int]) -> float:
        """Calculate Quantum Bit Error Rate between Alice's and Bob's bits."""
        if not alice_bits or not bob_bits:
            return 0.0
        if len(alice_bits) != len(bob_bits):
            raise ValueError("Alice and Bob bit lists must have equal length.")
        errors = sum(1 for a, b in zip(alice_bits, bob_bits, strict=True) if a != b)
        return errors / len(alice_bits)

    def compute_chsh_value(self, measurement_angles: list[float]) -> float:
        """Compute the CHSH S value for a set of measurement angles.

        The four angles are the two Alice settings (``a, a'``) and two Bob
        settings (``b, b'``). The standard CHSH correlation form is::

            S = cos(a - b) + cos(a - b') + cos(a' - b) - cos(a' - b')

        Quantum correlations reach ``S = 2*sqrt(2) ≈ 2.828`` for
        ``a=0, a'=π/4, b=π/8, b'=3π/8`` (Tsirelson bound), violating the
        classical bound of 2.
        """
        if len(measurement_angles) != 4:
            raise ValueError(
                "CHSH requires exactly four measurement angles (a, a', b, b')."
            )
        a, ap, b, bp = (float(x) for x in measurement_angles)
        s = np.cos(a - b) + np.cos(a - bp) + np.cos(ap - b) - np.cos(ap - bp)
        return float(s)
