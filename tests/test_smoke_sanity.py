from qkdpy.core import QuantumChannel
from qkdpy.protocols import BB84, CVQKD, E91, HDQKD


class TestSmokeSanity:
    """Smoke and Sanity tests for QKDpy."""

    def test_smoke_bb84(self):
        """Smoke test for BB84 protocol."""
        channel = QuantumChannel(loss=0.1, noise_level=0.05)
        bb84 = BB84(channel, key_length=50)
        results = bb84.execute()
        assert "final_key" in results
        assert "qber" in results
        assert isinstance(results["final_key"], list)

    def test_smoke_e91(self):
        """Smoke test for E91 protocol."""
        channel = QuantumChannel(loss=0.1, noise_level=0.05)
        e91 = E91(channel, key_length=50)
        results = e91.execute()
        assert "final_key" in results
        assert isinstance(results["final_key"], list)

    def test_smoke_cv_qkd(self):
        """Smoke test for CV-QKD protocol."""
        channel = QuantumChannel(loss=0.1, noise_level=0.05)
        cv = CVQKD(channel, key_length=50)
        results = cv.execute()
        assert "final_key" in results
        assert isinstance(results["final_key"], list)

    def test_smoke_hd_qkd(self):
        """Smoke test for HD-QKD protocol."""
        channel = QuantumChannel(loss=0.1, noise_level=0.05)
        hd = HDQKD(channel, key_length=50, dimension=4)
        results = hd.execute()
        assert "final_key" in results
        assert isinstance(results["final_key"], list)

    def test_sanity_csprng_integration(self):
        """Sanity check that CSPRNG is integrated and working."""
        # We can't easily check internal calls, but we can check that
        # repeated executions produce different keys (basic randomness check)
        channel = QuantumChannel()
        bb84_1 = BB84(channel, key_length=20)
        res1 = bb84_1.execute()

        bb84_2 = BB84(channel, key_length=20)
        res2 = bb84_2.execute()

        assert (
            res1["final_key"] != res2["final_key"]
        ), "Keys should be random and different"

    def test_sanity_privacy_amplification(self):
        """Sanity check for privacy amplification with new secure seeding."""
        channel = QuantumChannel()
        bb84 = BB84(channel, key_length=50)
        # Manually trigger privacy amplification
        key = [1, 0, 1, 0] * 25
        leak = 10
        amplified = bb84.privacy_amplification(key, leak)
        assert len(amplified) < len(key)
        assert isinstance(amplified, list)
