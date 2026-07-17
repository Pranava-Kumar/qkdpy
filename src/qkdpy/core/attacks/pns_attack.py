"""Photon Number Splitting (PNS) attack simulation.

The PNS attack targets prepare-and-measure QKD using a **weak coherent source**
(WCS), where each pulse follows a Poisson distribution over photon number
``P(n) = mu^n e^{-mu} / n!``. For small mean photon number ``mu`` most pulses are
vacuum or single-photon, but a small fraction ``P(n >= 2)`` are multi-photon.

Eve's optimal beam-splitter strategy (LoS2005 / Scarani2009):

* Multi-photon pulses (``n >= 2``): Eve transparently splits off one photon
  with a weak beam splitter and keeps it, letting the rest continue to Bob.
  This is **undetectable** at the channel-loss level -- Bob still sees the
  pulse with only the expected loss. Eve stores the stolen photon and measures
  it in the correct basis later, obtaining full key information on those pulses.
* Single-photon pulses (``n == 1``): Eve cannot split these without being
  detected, so she **blocks** them. Bob sees elevated loss, which is the
  tell-tale signature of PNS but is hard to distinguish from benign channel
  loss.

The net effect is a reduction in the secure key rate and, if the parties do not
use decoy states, Eve learns the multi-photon fraction of the key.

This module models the attack as a ``Callable`` compatible with
``QuantumChannel.set_eavesdropper`` / ``ExtendedQuantumChannel.set_eavesdropper``.
Because those hooks only pass a ``Qubit``/``Qudit`` (not pulse metadata), the
attack estimates the photon number per pulse from the configured mean photon
number ``mu`` and the Poisson statistics, then applies the beam-splitter rule.
"""

from collections.abc import Callable

from ..qubit import Qubit
from ..qudit import Qudit
from ..secure_random import secure_random

# Qubit/ qudit type accepted by the channel eavesdropper hook.
_Pulse = Qubit | Qudit


def _poisson_pmf(mu: float, n: int) -> float:
    """Poisson probability mass function P(n) for mean ``mu``."""
    import math

    return math.exp(-mu) * (mu**n) / math.factorial(n)


class PNSAttack:
    """Stateful Photon Number Splitting attack.

    Instances are callable ``(qubit) -> (qubit, detected)`` so they can be
    passed directly to ``QuantumChannel.set_eavesdropper``. The returned
    ``detected`` flag is ``True`` when the pulse was single-photon and blocked
    by Eve (the only case where Eve reveals her presence as loss); multi-photon
    pulses are forwarded and reported as ``detected = False`` because the
    beam-splitter intervention is stealthy.

    Args:
        mean_photon_number: Mean photon number ``mu`` of the weak coherent
            source. Drives the Poisson pulse-number distribution.
        beam_splitter_transmission: Probability that Eve's tapping beam
            splitter forwards the residual pulse to Bob for a multi-photon
            pulse (the stolen photon is always retained).
        block_single_photon: When True (default), single-photon pulses are
            blocked by Eve (raising Bob's loss). When False, Eve lets them pass
            (stronger attack, but only viable if she has an alternative way to
            avoid detection -- kept for analysis).
    """

    def __init__(
        self,
        mean_photon_number: float = 0.1,
        beam_splitter_transmission: float = 0.99,
        block_single_photon: bool = True,
    ) -> None:
        """Initialize the PNS attack with source statistics."""
        self.mean_photon_number = mean_photon_number
        self.beam_splitter_transmission = beam_splitter_transmission
        self.block_single_photon = block_single_photon

        # Per-pulse probabilities derived from the Poisson distribution.
        self.vacuum_probability = _poisson_pmf(mean_photon_number, 0)
        self.single_photon_probability = _poisson_pmf(mean_photon_number, 1)
        self.multi_photon_probability = 1.0 - (
            self.vacuum_probability + self.single_photon_probability
        )

        # Statistics accumulated across transmitted pulses.
        self.pulses_seen = 0
        self.single_photons_blocked = 0
        self.multi_photons_split = 0
        self.vacuum_pulses = 0
        self.detected_events = 0

    def reset_statistics(self) -> None:
        """Reset accumulated attack statistics."""
        self.pulses_seen = 0
        self.single_photons_blocked = 0
        self.multi_photons_split = 0
        self.vacuum_pulses = 0
        self.detected_events = 0

    def __call__(self, qubit: _Pulse) -> tuple[_Pulse | None, bool]:
        """Apply the PNS beam-splitter strategy to a transmitted pulse.

        Returns:
            Tuple of ``(qubit, detected)`` where ``qubit`` is the forwarded
            state (or ``None`` if the pulse was blocked) and ``detected`` is
            ``True`` when Eve blocked a single-photon pulse.
        """
        self.pulses_seen += 1

        # Decide the photon number of this pulse from the Poisson distribution.
        r = secure_random()
        if r < self.vacuum_probability:
            self.vacuum_pulses += 1
            # Vacuum: nothing to split, forward an independent copy so the
            # caller's source object cannot be mutated through the forwarded one.
            return qubit.clone(), False

        if r < self.vacuum_probability + self.single_photon_probability:
            # Single photon: cannot be split without detection.
            if self.block_single_photon:
                self.single_photons_blocked += 1
                self.detected_events += 1
                return None, True  # Blocked -> Bob sees loss.
            return qubit.clone(), False

        # Multi-photon: Eve keeps one, forwards the rest with the beam splitter.
        self.multi_photons_split += 1
        if secure_random() < self.beam_splitter_transmission:
            # Stealthy: only elevated loss is visible. Return a clone so the
            # residual pulse Eve forwards is decoupled from the source.
            return qubit.clone(), False
        # Rare: Eve's tap also drops the residual pulse (counts as loss).
        self.detected_events += 1
        return None, True

    def fraction_compromised(self) -> float:
        """Fraction of non-vacuum pulses whose key bits Eve can learn.

        Only multi-photon pulses leak information to Eve under this attack;
        single photons are blocked (lost, not learned). With decoy states the
        parties detect the inflated ``Y_{multi}`` yield and abort or trim the
        key, which is exactly what ``DecoyStateBB84`` guards against.
        """
        non_vacuum = self.single_photon_probability + self.multi_photon_probability
        if non_vacuum <= 0.0:
            return 0.0
        return self.multi_photon_probability / non_vacuum

    def as_callable(self) -> Callable[[_Pulse], tuple[_Pulse | None, bool]]:
        """Return self as a plain callable for ``set_eavesdropper``."""
        return self


def photon_number_splitting_attack(
    qubit: _Pulse,
    mean_photon_number: float = 0.1,
    beam_splitter_transmission: float = 0.99,
    block_single_photon: bool = True,
) -> tuple[_Pulse | None, bool]:
    """Stateless PNS attack compatible with ``QuantumChannel`` staticmethods.

    Mirrors ``QuantumChannel.intercept_resend_attack`` so callers can plug it in
    without instantiating :class:`PNSAttack`. Internally it instantiates a
    throwaway :class:`PNSAttack` per call, so per-pulse statistics are not
    accumulated; build a :class:`PNSAttack` instance when you need counters.
    """
    attack = PNSAttack(
        mean_photon_number=mean_photon_number,
        beam_splitter_transmission=beam_splitter_transmission,
        block_single_photon=block_single_photon,
    )
    return attack(qubit)
