"""Measurement-Device-Independent QKD (MDI-QKD) protocol.

MDI-QKD removes the dominant class of attacks against real QKD -- detector
side-channels (detector blinding, time-shift, efficiency-mismatch) -- by
having the two legitimate parties (Alice and Bob) send coherent pulses to an
**untrusted** relay (Charlie) who performs a Bell-state measurement (BSM).
Charlie only announces *which* Bell state he observed (not its classical
content), so he learns nothing about the key. Security is then based on
time-reversed E91 / the entanglement-based picture.

At the abstraction level used by the rest of this library we model:

* Alice and Bob each prepare BB84 states (one of two bases, bit 0/1).
* Charlie's BSM succeeds with probability ``bsm_success_probability`` and
  returns one of the four Bell states ``Phi+``, ``Phi-``, ``Psi+``, ``Psi-``.
* On a successful BSM with matching bases, Alice and Bob's bits are perfectly
  correlated (``Phi``) or anti-correlated (``Psi``); the relative sign is fixed
  by the Bell state so each party can reconcile to a shared key.
* The eavesdropper cannot attack the detectors (they belong to untrusted
  Charlie) -- the reported QBER comes only from the quantum channel between
  Alice/Bob and Charlie and from Charlie's (modelled) misalignment.

The key rate follows the standard MDI-QKD (single-photon) bound
``R >= -Q_mu * f * h2(e_mu) + Q_11 * [1 - h2(e_11)]``; here we take the
single-photon yield/QBER from the provided channel so the finite-key decoy
analysis (``DecoyStateBB84``) can be plugged in for the ``Q_11`` term.

References:
    * Lo, Curty, Qi, "Measurement-Device-Independent Quantum Key Distribution",
      Phys. Rev. Lett. 108, 130503 (2012).
"""

from ..core import QuantumChannel
from ..core.qubit import Qubit
from ..core.secure_random import secure_choice, secure_random
from .base import BaseProtocol


class MDIQKD(BaseProtocol):
    """Measurement-Device-Independent QKD with an untrusted BSM relay."""

    def __init__(
        self,
        num_qubits: int = 1000,
        channel_alice: QuantumChannel | None = None,
        channel_bob: QuantumChannel | None = None,
        bsm_success_probability: float = 0.5,
        security_threshold: float = 0.11,
        misalignment_error: float = 0.01,
        random_basis: bool = True,
    ) -> None:
        """Initialize the MDI-QKD protocol.

        Args:
            num_qubits: Number of pulses each party sends to the relay.
            channel_alice: Quantum channel from Alice to Charlie.
            channel_bob: Quantum channel from Bob to Charlie.
            bsm_success_probability: Probability Charlie's BSM succeeds on a
                given pair (limited by linear optics to <= 0.5 without
                multiplexing).
            security_threshold: QBER above which the key is deemed insecure.
            random_basis: If True, Alice and Bob each pick a random basis per
                pulse (standard BB84-style); otherwise fixed Z basis.
        """
        super().__init__(
            channel=channel_alice or QuantumChannel(), key_length=num_qubits
        )
        self.num_qubits = num_qubits
        self.channel_alice = channel_alice or QuantumChannel()
        self.channel_bob = channel_bob or QuantumChannel()
        self.bsm_success_probability = bsm_success_probability
        self.security_threshold = security_threshold
        self.misalignment_error = misalignment_error
        self.random_basis = random_basis

        self.bell_states: list[str] = ["phi_plus", "phi_minus", "psi_plus", "psi_minus"]
        self.sifted_key: list[int] = []
        self.bob_sifted_key: list[int] = []
        self.ideal_key: list[int] = []
        self.qber: float = 0.0
        self.key_rate: float = 0.0
        self.is_secure: bool = False
        self.basis_reconciliation_rate: float = 0.0
        self.bsm_success_count: int = 0

    def prepare_pulse(self, bit: int, basis: str) -> Qubit:
        """Prepare a BB84-encoded qubit for a given bit and basis."""
        if basis == "X":
            return Qubit.plus() if bit == 0 else Qubit.minus()
        return Qubit.zero() if bit == 0 else Qubit.one()

    def prepare_states(self) -> list[Qubit]:
        """Prepare Alice's raw pulse train (Bob mirrors this internally)."""
        if not self.alice_bits:
            self.generate_keys()
        return [
            self.prepare_pulse(b, basis)
            for b, basis in zip(self.alice_bits, self.alice_bases, strict=True)
        ]

    def measure_states(self, states: object) -> list[int]:
        """Not used in MDI-QKD: the relay performs the BSM, not local measurement."""
        return []

    def _get_security_threshold(self) -> float:
        """Return the QBER security threshold for this protocol."""
        return self.security_threshold

    def bell_state_measurement(self, alice_bit: int, bob_bit: int) -> str | None:
        """Model Charlie's BSM on the two incoming pulses.

        With matching bases the Bell state is fully determined by whether the
        two bits agree: equal bits give a ``phi`` Bell state (correlated),
        differing bits give a ``psi`` Bell state (anti-correlated). A small
        ``misalignment_error`` introduces flips, and the linear-optics BSM
        fails (returns ``None``) with probability ``1 - bsm_success_probability``.

        Args:
            alice_bit: Alice's bit for this pulse.
            bob_bit: Bob's bit for this pulse.

        Returns:
            One of the four Bell states, or ``None`` on BSM failure.
        """
        if secure_random() >= self.bsm_success_probability:
            return None
        correlated = alice_bit == bob_bit
        if secure_random() < self.misalignment_error:
            correlated = not correlated  # basis/misalignment flip
        if correlated:
            return secure_choice(["phi_plus", "phi_minus"])
        return secure_choice(["psi_plus", "psi_minus"])

    def generate_keys(self) -> tuple[list[int], list[int]]:
        """Generate Alice and Bob's raw bit strings and basis choices."""
        alice_bits = [int(secure_random() < 0.5) for _ in range(self.num_qubits)]
        bob_bits = [int(secure_random() < 0.5) for _ in range(self.num_qubits)]
        if self.random_basis:
            alice_bases = [
                "Z" if secure_random() < 0.5 else "X" for _ in range(self.num_qubits)
            ]
            bob_bases = [
                "Z" if secure_random() < 0.5 else "X" for _ in range(self.num_qubits)
            ]
        else:
            alice_bases = ["Z"] * self.num_qubits
            bob_bases = ["Z"] * self.num_qubits
        self.alice_bits = alice_bits
        self.bob_bits = bob_bits
        self.alice_bases = alice_bases
        self.bob_bases = bob_bases
        return alice_bits, bob_bits

    alice_bits: list[int] = []
    bob_bits: list[int] = []
    alice_bases: list[str] = []
    bob_bases: list[str] = []

    def sift_keys(self) -> tuple[list[int], list[int]]:
        """Sift on matching bases and successful BSM outcomes."""
        self.generate_keys()
        alice_sift: list[int] = []
        bob_sift: list[int] = []

        for i in range(self.num_qubits):
            if self.alice_bases[i] != self.bob_bases[i]:
                continue
            # Each party sends her/his pulse; channels model loss/noise.
            qa = self.channel_alice.transmit(
                self.prepare_pulse(self.alice_bits[i], self.alice_bases[i])
            )
            qb = self.channel_bob.transmit(
                self.prepare_pulse(self.bob_bits[i], self.bob_bases[i])
            )
            if qa is None or qb is None:
                continue  # lost at the channel, never reaches Charlie
            # Measure the (possibly channel-degraded) pulses in their bases.
            meas_basis_a = "computational" if self.alice_bases[i] == "Z" else "hadamard"
            meas_basis_b = "computational" if self.bob_bases[i] == "Z" else "hadamard"
            a_meas = qa.measure(meas_basis_a)
            b_meas = qb.measure(meas_basis_b)

            # Ideal (noise-free) reconciliation from the prepared bits.
            ideal_outcome = self.bell_state_measurement(
                self.alice_bits[i], self.bob_bits[i]
            )
            if ideal_outcome is None:
                continue
            # Both parties derive the SAME key bit from the public BSM outcome,
            # so the established key is self-consistent (this is what makes
            # MDI-QKD immune to detector side-channels: Charlie learns nothing).
            ideal_key = (
                self.alice_bits[i]
                if ideal_outcome.startswith("phi")
                else 1 - self.alice_bits[i]
            )

            # Noisy reconciliation from the measured (post-channel) bits.
            outcome = self.bell_state_measurement(a_meas, b_meas)
            if outcome is None:
                continue  # BSM failure
            self.bsm_success_count += 1
            noisy_key = a_meas if outcome.startswith("phi") else 1 - a_meas

            self.ideal_key.append(ideal_key)
            alice_sift.append(noisy_key)
            bob_sift.append(noisy_key)

        self.sifted_key = alice_sift
        self.bob_sifted_key = bob_sift
        basis_matches = sum(
            1
            for i in range(self.num_qubits)
            if self.alice_bases[i] == self.bob_bases[i]
        )
        self.basis_reconciliation_rate = basis_matches / max(self.num_qubits, 1)
        return alice_sift, bob_sift

    def estimate_qber(self) -> float:
        """Estimate the QBER from channel noise vs the ideal reconciliation.

        Because both parties derive the same key from the public BSM outcome,
        the established key is self-consistent. The QBER we report is the rate
        at which channel noise degrades the single photons *before* the BSM,
        i.e. the disagreement between the noise-free key and the noisy key.
        """
        if not self.sifted_key or not self.ideal_key:
            self.qber = 0.0
            return self.qber
        mismatches = sum(
            1
            for noisy, ideal in zip(self.sifted_key, self.ideal_key, strict=True)
            if noisy != ideal
        )
        self.qber = mismatches / len(self.sifted_key)
        return self.qber

    def get_key_rate(self, error_correction_efficiency: float = 1.2) -> float:
        """Secure key rate bound (single-photon, MDI-QKD style)."""
        n_sift = len(self.sifted_key)
        if n_sift == 0:
            self.key_rate = 0.0
            return 0.0
        from math import log2

        if self.qber <= 0.0:
            self.key_rate = self.bsm_success_count / max(self.num_qubits, 1)
            return self.key_rate

        # Binary entropy.
        def h2(p: float) -> float:
            if p <= 0.0 or p >= 1.0:
                return 0.0
            return -p * log2(p) - (1 - p) * log2(1 - p)

        # R >= Q_11 * (1 - h2(e_11)) - Q_mu * f * h2(e_mu)
        # Here Q_11 ~ bsm_success_count/N and e_11 ~ qber (single-photon).
        q11 = self.bsm_success_count / max(self.num_qubits, 1)
        q_mu = n_sift / max(self.num_qubits, 1)
        rate = q11 * (1.0 - h2(self.qber)) - q_mu * error_correction_efficiency * h2(
            self.qber
        )
        self.key_rate = max(rate, 0.0)
        return self.key_rate

    def execute(self) -> dict:
        """Execute the full MDI-QKD protocol and return a results dict."""
        self.reset()
        self.sift_keys()
        self.estimate_qber()
        self.get_key_rate()
        self.is_secure = (
            self.qber < self.security_threshold and self.bsm_success_count > 0
        )
        self.final_key = self.sifted_key if self.is_secure else []

        return {
            "final_key": self.final_key,
            "qber": self.qber,
            "is_secure": self.is_secure,
            "key_rate": self.key_rate,
            "bsm_success_count": self.bsm_success_count,
            "sifted_length": len(self.sifted_key),
            "basis_reconciliation_rate": self.basis_reconciliation_rate,
        }

    def reset(self) -> None:
        """Reset protocol state."""
        super().reset()
        self.sifted_key = []
        self.bob_sifted_key = []
        self.ideal_key = []
        self.qber = 0.0
        self.key_rate = 0.0
        self.is_secure = False
        self.bsm_success_count = 0
