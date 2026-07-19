"""QKD protocol <-> QpiAI circuit mapping surface.

Thin, researcher-facing facade over :class:`bridge.QpiAIIntegration`. This is
the "protocols implemented" anchor for the companion: every protocol qkdpy
supports is mapped here to a QpiAI circuit and the QKD figures a researcher
needs (QBER, CHSH, concurrence, purity).
"""

from __future__ import annotations

from typing import Any

from .bridge import QpiAIIntegration
from .interchange import (
    InterchangeStandard,
    ProtocolExchange,
    ProtocolType,
)

__all__ = ["Protocols"]


class Protocols:
    """Build protocol circuits and compute QKD figures via the QpiAI bridge."""

    def __init__(self, integration: QpiAIIntegration | None = None) -> None:
        self.integration = integration or QpiAIIntegration()

    # --- Circuit builders ------------------------------------------------- #
    def bb84(
        self,
        num_qubits: int = 1,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
        alice_bits: list[int] | None = None,
    ) -> Any:
        """BB84 prepare-and-measure protocol circuit."""
        return self.integration.create_bb84_circuit(
            num_qubits=num_qubits,
            alice_bases=alice_bases,
            bob_bases=bob_bases,
            alice_bits=alice_bits,
        )

    def e91(
        self,
        num_pairs: int = 1,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
    ) -> Any:
        """E91 entanglement-based protocol circuit."""
        return self.integration.create_e91_circuit(
            num_pairs=num_pairs, alice_bases=alice_bases, bob_bases=bob_bases
        )

    def bell(self, state_type: str = "|Φ+>") -> tuple[Any, str]:
        """Maximally entangled Bell-pair circuit + description."""
        return self.integration.create_entanglement_circuit(state_type=state_type)

    def ghz(self, num_qubits: int = 3) -> Any:
        """GHZ multi-party entangled state circuit."""
        return self.integration.create_ghz_circuit(num_qubits=num_qubits)

    # --- Metrics ---------------------------------------------------------- #
    def qber(self, alice_bits: list[int], bob_bits: list[int]) -> float:
        """Quantum Bit Error Rate between Alice and Bob."""
        return self.integration.calculate_qber(alice_bits, bob_bits)

    def chsh(self, measurement_angles: list[float]) -> float:
        """CHSH S value (quantum bound 2√2 ≈ 2.828)."""
        return self.integration.compute_chsh_value(measurement_angles)

    def concurrence(self, state: Any) -> float:
        """Concurrence of an entangled 2-qubit state."""
        return self.integration.compute_concurrence(state)

    def purity(self, state: Any) -> float:
        """Purity Tr(rho^2) of a 2-qubit state."""
        return self.integration.compute_purity(state)

    # --- Interchange ------------------------------------------------------ #
    def exchange(
        self,
        protocol: ProtocolType,
        *,
        alice_bases: list[str] | None = None,
        bob_bases: list[str] | None = None,
        alice_bits: list[int] | None = None,
        bob_bits: list[int] | None = None,
        concurrence: float | None = None,
        qber: float | None = None,
        chsh: float | None = None,
        metadata: dict[str, Any] | None = None,
        standard: InterchangeStandard = InterchangeStandard.ETSI_GS_QKD_014,
    ) -> ProtocolExchange:
        """Capture a protocol run as an ETSI-tagged interchange document."""
        return ProtocolExchange(
            protocol=protocol,
            standard=standard,
            alice_bases=alice_bases or [],
            bob_bases=bob_bases or [],
            alice_bits=alice_bits or [],
            bob_bits=bob_bits or [],
            concurrence=concurrence,
            qber=qber,
            chsh=chsh,
            metadata=metadata or {},
        )
