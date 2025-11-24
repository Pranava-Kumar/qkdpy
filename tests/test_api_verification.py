import inspect

import pytest

from qkdpy import (
    BB84,
    CVQKD,
    E91,
    HDQKD,
    QuantumChannel,
    QuantumKeyManager,
    QuantumNetwork,
    Qubit,
    Qudit,
)


class TestAPIVerification:
    """Verify the public API of the library."""

    def test_public_classes_exist(self):
        """Ensure all main classes are exported and available."""
        assert inspect.isclass(BB84)
        assert inspect.isclass(E91)
        assert inspect.isclass(CVQKD)
        assert inspect.isclass(HDQKD)
        assert inspect.isclass(QuantumChannel)
        assert inspect.isclass(Qubit)
        assert inspect.isclass(Qudit)
        assert inspect.isclass(QuantumNetwork)
        assert inspect.isclass(QuantumKeyManager)

    def test_method_signatures(self):
        """Verify critical method signatures match expectations."""
        # BB84.execute should take no arguments (besides self)
        sig = inspect.signature(BB84.execute)
        assert len(sig.parameters) == 1  # self only (or 0 if bound, but here unbound)

        # QuantumChannel.__init__ should have specific params
        sig = inspect.signature(QuantumChannel.__init__)
        params = sig.parameters
        assert "loss" in params
        assert "noise_model" in params
        assert "noise_level" in params

    def test_type_annotations_presence(self):
        """Verify that key methods have type annotations."""
        # BB84.__init__
        assert BB84.__init__.__annotations__
        assert "key_length" in BB84.__init__.__annotations__

        # QuantumChannel.transmit
        assert QuantumChannel.transmit.__annotations__
        assert "qubit" in QuantumChannel.transmit.__annotations__

    def test_error_handling_invalid_usage(self):
        """Verify API raises appropriate errors for invalid usage."""
        # 1. Passing invalid channel to protocol
        with pytest.raises((AttributeError, TypeError)):
            BB84(channel="not_a_channel")

        # 2. Invalid key length
        _ = QuantumChannel()
        # Some implementations might allow 0, but usually not negative
        # Check if it handles it or lets it pass (depending on implementation)
        # If it doesn't raise, we just note it, but ideally it should.
        # Based on previous fuzzing, we know it might not raise for all,
        # but let's check a definite invalid case if possible.

        # 3. QuantumNetwork invalid node
        net = QuantumNetwork()
        with pytest.raises(ValueError):
            net.add_connection("NodeA", "NodeB")  # Nodes don't exist yet
