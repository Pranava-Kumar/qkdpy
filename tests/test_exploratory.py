import random

import pytest

from qkdpy.core import QuantumChannel
from qkdpy.core.secure_random import secure_choice, secure_randint
from qkdpy.protocols import BB84, CVQKD, E91


class TestExploratory:
    """Exploratory testing using random simulations."""

    def test_random_protocol_execution(self):
        """Randomly select parameters and execute protocols to find edge cases."""
        protocols = [BB84, E91, CVQKD]

        for _ in range(10):  # Run 10 random simulations
            # Random channel parameters
            loss = random.uniform(0.0, 0.5)
            noise_level = random.uniform(0.0, 0.2)
            noise_model = secure_choice(["depolarizing", "bit_flip", "phase_flip"])

            channel = QuantumChannel(
                loss=loss, noise_model=noise_model, noise_level=noise_level
            )

            # Random protocol
            ProtocolClass = secure_choice(protocols)
            key_length = secure_randint(10, 100)

            try:
                protocol = ProtocolClass(channel, key_length=key_length)
                results = protocol.execute()

                # Basic sanity checks on results
                assert isinstance(results, dict)
                if results.get("is_secure"):
                    assert len(results["final_key"]) > 0
            except Exception as e:
                pytest.fail(
                    f"Exploratory test failed for {ProtocolClass.__name__} with loss={loss}, noise={noise_level}: {e}"
                )
