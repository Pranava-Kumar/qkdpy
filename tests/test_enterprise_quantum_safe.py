"""Tests for the quantum-safe migration toolkit (PREMIUM tier)."""
import unittest

from qkdpy.enterprise.quantum_safe import (
    CryptoAlgorithmType,
    CryptoAsset,
    CryptoInventoryReport,
    MigrationPhase,
    QuantumResistance,
    QuantumSafeAssessment,
    classic_enterprise_profile,
    generate_roadmap,
)


class TestCryptoInventoryReport(unittest.TestCase):
    """CryptoInventoryReport data class."""

    def test_empty_inventory(self):
        """Empty inventory has zero risk."""
        report = CryptoInventoryReport(
            scanned_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
            assets=[],
        )
        self.assertEqual(report.total_assets, 0)
        self.assertEqual(report.risk_score, 0.0)
        self.assertEqual(report.vulnerable_count, 0)

    def test_risk_score_all_safe(self):
        """Inventory with only safe assets has zero risk."""
        safe = [
            CryptoAsset(name="AES-256", algorithm_type=CryptoAlgorithmType.SYMMETRIC, key_size_bits=256, resistance=QuantumResistance.SAFE, location="storage"),
            CryptoAsset(name="SHA-3", algorithm_type=CryptoAlgorithmType.HASH, key_size_bits=256, resistance=QuantumResistance.SAFE, location="integrity"),
        ]
        report = CryptoInventoryReport(
            scanned_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
            assets=safe,
        )
        self.assertEqual(report.risk_score, 0.0)

    def test_risk_score_all_vulnerable(self):
        """Inventory with only vulnerable assets has risk_score 1.0."""
        vuln = [
            CryptoAsset(name="RSA-2048", algorithm_type=CryptoAlgorithmType.ASYMMETRIC, key_size_bits=2048, resistance=QuantumResistance.VULNERABLE, location="tls"),
            CryptoAsset(name="DH-2048", algorithm_type=CryptoAlgorithmType.KEY_EXCHANGE, key_size_bits=2048, resistance=QuantumResistance.VULNERABLE, location="vpn"),
        ]
        report = CryptoInventoryReport(
            scanned_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
            assets=vuln,
        )
        self.assertAlmostEqual(report.risk_score, 1.0)

    def test_risk_score_mixed(self):
        """Mixed inventory produces intermediate risk score."""
        mixed = [
            CryptoAsset(name="RSA-2048", algorithm_type=CryptoAlgorithmType.ASYMMETRIC, key_size_bits=2048, resistance=QuantumResistance.VULNERABLE, location="tls"),
            CryptoAsset(name="AES-128", algorithm_type=CryptoAlgorithmType.SYMMETRIC, key_size_bits=128, resistance=QuantumResistance.MIGRATE_SOON, location="vpn"),
            CryptoAsset(name="AES-256", algorithm_type=CryptoAlgorithmType.SYMMETRIC, key_size_bits=256, resistance=QuantumResistance.SAFE, location="storage"),
        ]
        report = CryptoInventoryReport(
            scanned_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
            assets=mixed,
        )
        # (1.0 + 0.5 + 0.0) / 3 = 0.5
        self.assertAlmostEqual(report.risk_score, 0.5)

    def test_get_summary(self):
        """get_summary returns correct fields."""
        report = classic_enterprise_profile()
        summary = report.get_summary()
        for key in ("total_assets", "vulnerable_count", "risk_score", "system_description"):
            self.assertIn(key, summary)
        self.assertGreater(summary["vulnerable_count"], 0)


class TestClassicEnterpriseProfile(unittest.TestCase):
    """Preset enterprise crypto profile."""

    def test_returns_non_empty_inventory(self):
        """classic_enterprise_profile returns assets."""
        profile = classic_enterprise_profile()
        self.assertGreater(profile.total_assets, 0)
        self.assertGreater(profile.vulnerable_count, 0)

    def test_contains_rsa(self):
        """Profile contains vulnerable RSA assets."""
        profile = classic_enterprise_profile()
        rsa = [a for a in profile.assets if "RSA" in a.name]
        self.assertTrue(rsa)
        for a in rsa:
            self.assertEqual(a.resistance, QuantumResistance.VULNERABLE)

    def test_contains_aes256(self):
        """Profile contains safe AES-256 assets."""
        profile = classic_enterprise_profile()
        aes256 = [a for a in profile.assets if "AES-256" in a.name]
        self.assertTrue(aes256)
        for a in aes256:
            self.assertEqual(a.resistance, QuantumResistance.SAFE)


class TestGenerateRoadmap(unittest.TestCase):
    """Migration roadmap generation."""

    def test_default_inventory(self):
        """generate_roadmap works without explicit inventory."""
        roadmap = generate_roadmap()
        self.assertGreater(len(roadmap.steps), 0)
        self.assertIsNotNone(roadmap.target_completion)

    def test_phases_in_order(self):
        """Roadmap phases appear in correct order."""
        inv = classic_enterprise_profile()
        roadmap = generate_roadmap(inv)
        expected_order = [
            MigrationPhase.ASSESS,
            MigrationPhase.ASSESS,
            MigrationPhase.PLAN,
            MigrationPhase.PLAN,
            MigrationPhase.PILOT,
            MigrationPhase.PILOT,
            MigrationPhase.MIGRATE,
            MigrationPhase.MIGRATE,
            MigrationPhase.VERIFY,
        ]
        phases = [s.phase for s in roadmap.steps]
        self.assertEqual(phases, expected_order)

    def test_steps_have_effort_estimate(self):
        """Every roadmap step has a non-empty effort estimate."""
        roadmap = generate_roadmap()
        for step in roadmap.steps:
            self.assertTrue(step.estimated_effort, f"Step {step.title} missing effort")

    def test_get_summary(self):
        """get_summary returns expected keys."""
        roadmap = generate_roadmap()
        summary = roadmap.get_summary()
        for key in ("target_completion", "total_steps", "risk_score", "vulnerable_assets"):
            self.assertIn(key, summary)


class TestQuantumSafeAssessment(unittest.TestCase):
    """Full assessment combining inventory and roadmap."""

    def test_assessment_from_profile(self):
        """Create assessment from enterprise profile and generated roadmap."""
        inv = classic_enterprise_profile()
        rm = generate_roadmap(inv)
        assessment = QuantumSafeAssessment(inventory=inv, roadmap=rm)
        self.assertIs(assessment.inventory, inv)
        self.assertIs(assessment.roadmap, rm)

    def test_to_dict(self):
        """to_dict returns serialisable output."""
        assessment = QuantumSafeAssessment(
            inventory=classic_enterprise_profile(),
            roadmap=generate_roadmap(),
        )
        d = assessment.to_dict()
        for key in ("assessed_at", "inventory", "roadmap", "recommendations"):
            self.assertIn(key, d)
        self.assertIsInstance(d["recommendations"], list)
        self.assertGreater(len(d["recommendations"]), 0)


if __name__ == "__main__":
    unittest.main()
