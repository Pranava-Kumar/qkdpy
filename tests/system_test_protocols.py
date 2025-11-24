import numpy as np

from qkdpy.core.channels import QuantumChannel
from qkdpy.protocols.bb84 import BB84
from qkdpy.protocols.e91 import E91


class TestSystemProtocols:
    """System tests for end-to-end protocol execution."""

    def test_bb84_end_to_end(self):
        """Test full BB84 protocol execution."""
        # Create channel with some loss but low noise
        channel = QuantumChannel(distance=10.0, loss_coefficient=0.2)

        # Initialize BB84 protocol (single instance manages both Alice and Bob)
        bb84 = BB84(channel=channel, key_length=100)

        # 1. Alice prepares qubits
        alice_qubits = bb84.prepare_states()
        assert len(alice_qubits) >= 100

        # 2. Transmission (simulate channel effect)
        # In a real scenario, we'd pass qubits through channel.
        # Here, we need to see if BB84 class handles transmission or if we need to do it.
        # Looking at BB84.measure_states, it takes 'states' as input.

        bob_received_qubits = []
        for q in alice_qubits:
            bob_received_qubits.append(channel.transmit(q))

        # 3. Bob measures
        bb84.measure_states(bob_received_qubits)

        # 4. Sifting
        alice_key, bob_key = bb84.sift_keys()

        # Keys should match (with low noise)
        # Note: Sifting might return empty if no bases matched, but with 300 qubits (3x key_length),
        # we expect ~150 matches.
        assert len(alice_key) == len(bob_key)
        assert len(alice_key) > 0

        # Check QBER
        errors = sum(a != b for a, b in zip(alice_key, bob_key, strict=False))
        qber = errors / len(alice_key)
        assert qber < 0.11  # Should be below threshold

    def test_e91_end_to_end(self):
        """Test full E91 protocol execution."""
        # Create channel
        channel = QuantumChannel(distance=5.0)

        # Initialize E91 protocol
        e91 = E91(channel=channel, key_length=100)

        # 1. Prepare entangled states (Alice keeps one, sends one to Bob)
        # prepare_states returns the list of qubits sent to Bob
        qubits_to_bob = e91.prepare_states()

        # 2. Transmission
        bob_received_qubits = []
        for q in qubits_to_bob:
            bob_received_qubits.append(channel.transmit(q))

        # 3. Bob measures (and Alice measures her half internally during prepare_states/measure_states?)
        # Wait, e91.measure_states takes qubits received by Bob.
        # Alice's measurement seems to happen in prepare_states or implicitly.
        # Checking E91 code: prepare_states populates self.alice_results.
        e91.measure_states(bob_received_qubits)

        # 4. Sifting
        alice_key, bob_key = e91.sift_keys()

        assert len(alice_key) == len(bob_key)
        assert len(alice_key) > 0

        # Check QBER
        qber = e91.estimate_qber()
        assert (
            qber < 0.15
        )  # E91 might have slightly higher QBER due to simulation artifacts

    def test_bb84_high_noise(self):
        """Test BB84 under high noise conditions."""
        # Channel with high noise
        channel = QuantumChannel(
            distance=10.0, noise_model="depolarizing", noise_level=0.5
        )

        bb84 = BB84(channel=channel, key_length=100)

        qubits = bb84.prepare_states()
        received = [channel.transmit(q) for q in qubits]
        bb84.measure_states(received)

        alice_key, bob_key = bb84.sift_keys()

        # Check QBER - should be high
        if len(alice_key) > 0:
            errors = sum(a != b for a, b in zip(alice_key, bob_key, strict=False))
            qber = errors / len(alice_key)
            assert qber > 0.15  # Expect high error rate

    def test_bb84_eavesdropping(self):
        """Test BB84 with an intercept-resend eavesdropper."""
        # Create channel with an eavesdropper
        # We need to define an eavesdropper function or object
        # Looking at QuantumChannel init: eavesdropper: Callable | None = None

        def intercept_resend_eve(qubit):
            # Eve measures in random basis and resends
            basis = np.random.choice(["computational", "hadamard"])
            measurement = qubit.measure(
                basis
            )  # This gets the result but doesn't collapse
            qubit.collapse_state(measurement, basis)  # Explicitly collapse state
            return qubit

        channel = QuantumChannel(distance=10.0, eavesdropper=intercept_resend_eve)

        bb84 = BB84(channel=channel, key_length=100)

        # Run protocol
        qubits = bb84.prepare_states()
        received = [channel.transmit(q) for q in qubits]
        bb84.measure_states(received)

        alice_key, bob_key = bb84.sift_keys()

        # Intercept-resend introduces ~25% error rate
        if len(alice_key) > 0:
            errors = sum(a != b for a, b in zip(alice_key, bob_key, strict=False))
            qber = errors / len(alice_key)
            assert qber > 0.20  # Should be significantly high (theoretically ~0.25)
