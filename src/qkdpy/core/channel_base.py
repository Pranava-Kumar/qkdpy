"""Abstract base class for quantum channels.

Defines the interface that all quantum channel implementations must satisfy,
so that protocols can transmit through any channel (fiber, free-space,
atmospheric, etc.) without depending on a single concrete implementation.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

from .qubit import Qubit
from .qudit import Qudit


class ChannelBase(ABC):
    """Abstract interface for quantum channels.

    Every channel implementation must support transmitting individual qubits
    or qudits, batch transmission, and reporting transmission statistics.

    Subclasses that cannot handle high-dimensional qudits (dimension > 2)
    should override :meth:`transmit` and raise :class:`NotImplementedError`
    for qudit inputs rather than silently ignoring the noise model.
    """

    @abstractmethod
    def transmit(
        self, qubit: Qubit | Qudit, timestamp: float = 0.0
    ) -> Qubit | Qudit | None:
        """Transmit a single quantum state through the channel.

        Args:
            qubit: The quantum state (qubit or qudit) to transmit.
            timestamp: Time of transmission (used for temporal effects).

        Returns:
            The received quantum state, or ``None`` if the state was lost
            in the channel.
        """

    @abstractmethod
    def get_statistics(self) -> dict[str, int | float | bool]:
        """Return transmission statistics.

        Returns:
            Dictionary containing at minimum:
            - ``transmitted``: total states sent
            - ``lost``: states lost in the channel
            - ``received``: states successfully received
            - ``errors``: error count introduced by noise
            - ``loss_rate``: fraction of states lost
            - ``error_rate``: fraction of received states with errors
        """

    @abstractmethod
    def reset_statistics(self) -> None:
        """Reset all transmission statistics counters to zero."""

    def transmit_batch(
        self,
        qubits: list[Qubit | Qudit],
        start_time: float = 0.0,
        pulse_interval: float = 1e-9,
    ) -> list[Qubit | Qudit | None]:
        """Transmit a batch of quantum states through the channel.

        The default implementation calls :meth:`transmit` sequentially for
        each state. Subclasses may override this for parallel or more
        efficient batch processing.

        Args:
            qubits: List of quantum states to transmit.
            start_time: Starting time for the first state.
            pulse_interval: Time interval between consecutive states (seconds).

        Returns:
            List of received quantum states (``None`` for lost states).
        """
        results: list[Qubit | Qudit | None] = []
        for i, qubit in enumerate(qubits):
            timestamp = start_time + i * pulse_interval
            results.append(self.transmit(qubit, timestamp))
        return results

    def set_eavesdropper(  # noqa: B027 — intentionally a no-op; subclasses override if needed
        self,
        eavesdropper: Callable[[Qubit | Qudit], tuple[Qubit | Qudit, bool]] | None,
    ) -> None:
        """Set or remove an eavesdropper on the channel.

        The default implementation is a no-op. Subclasses that support
        eavesdropping should override this.

        Args:
            eavesdropper: Callable representing the attack, or ``None`` to remove.
        """
