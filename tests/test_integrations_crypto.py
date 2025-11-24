import numpy as np
import pytest

from qkdpy.core.channels import QuantumChannel
from qkdpy.crypto.enhanced_security import QuantumKeyValidation
from qkdpy.crypto.key_exchange import QuantumKeyExchange
from qkdpy.integrations.qiskit_integration import QISKIT_AVAILABLE, QiskitIntegration


class TestQiskitIntegration:
    @pytest.mark.skipif(not QISKIT_AVAILABLE, reason="Qiskit not installed")
    def test_create_e91_circuit(self):
        integration = QiskitIntegration()
        circuit = integration.create_e91_circuit(num_pairs=2)
        assert circuit.num_qubits == 4  # 2 pairs * 2 qubits/pair
        assert circuit.num_clbits == 4  # 2 pairs * 2 clbits/pair (alice + bob)

    @pytest.mark.skipif(not QISKIT_AVAILABLE, reason="Qiskit not installed")
    def test_simulate_e91_with_qiskit(self):
        integration = QiskitIntegration()
        alice_bits, bob_bits, alice_bases, bob_bases = (
            integration.simulate_e91_with_qiskit(num_pairs=5)
        )
        assert len(alice_bits) == 5
        assert len(bob_bits) == 5
        assert len(alice_bases) == 5
        assert len(bob_bases) == 5

    @pytest.mark.skipif(not QISKIT_AVAILABLE, reason="Qiskit not installed")
    def test_convert_channel_loss(self):
        integration = QiskitIntegration()
        channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.0)
        noise_model = integration.convert_channel_to_qiskit(channel)
        # Check if noise model is not empty (hard to inspect internal structure easily, but we can check if it runs)
        assert noise_model is not None


class TestEnhancedSecurity:
    def test_statistical_randomness_test(self):
        # Generate a pseudo-random key
        key = np.random.randint(0, 2, 1000).tolist()
        results = QuantumKeyValidation.statistical_randomness_test(key)

        assert "frequency_test_p_value" in results
        assert "block_frequency_stat" in results
        assert "runs_test_p_value" in results
        assert results["block_frequency_stat"] is not None

    def test_statistical_randomness_test_short_key(self):
        key = [0, 1, 0, 1] * 10  # 40 bits
        results = QuantumKeyValidation.statistical_randomness_test(key)
        # Block frequency test requires >= 128 bits
        assert results["block_frequency_stat"] is None


class TestKeyExchange:
    def test_rotate_key(self):
        channel = QuantumChannel(loss=0.0, noise_level=0.0)
        exchange = QuantumKeyExchange(channel)

        # Initiate and complete a session
        session_id = exchange.initiate_key_exchange("Alice", "Bob", key_length=10)
        assert session_id is not None

        success = exchange.execute_key_exchange(session_id)
        assert success

        old_key = exchange.get_shared_key(session_id)
        assert old_key is not None

        # Rotate key
        rotation_success = exchange.rotate_key(session_id, new_key_length=20)
        assert rotation_success

        new_key = exchange.get_shared_key(session_id)
        assert new_key is not None
        assert (
            len(new_key) >= 20
        )  # Might be slightly less due to sifting/privacy amp, but usually close to requested
        assert new_key != old_key

        session_info = exchange.get_session_info(session_id)
        assert "last_rotation_time" in session_info
