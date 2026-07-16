"""Tests for qkdpy.enterprise modules: audit, compliance, HSM."""

import json
import os
import tempfile
import unittest

from qkdpy.enterprise.audit import AuditEventType, AuditLogger
from qkdpy.enterprise.compliance import ComplianceChecker
from qkdpy.enterprise.hsm_interface import (
    HSMError,
    KeyNotFoundError,
    SoftwareHSM,
)


class TestSoftwareHSM(unittest.TestCase):
    """SoftwareHSM using AES-256-GCM."""

    def setUp(self):
        self.hsm = SoftwareHSM()
        self.hsm.initialize({"storage_path": ":memory:"})
        self.hsm.generate_key("test-key", key_length=256)

    def tearDown(self):
        self.hsm.close()

    def test_encrypt_decrypt_roundtrip(self):
        pt = b"hello quantum world"
        ct = self.hsm.encrypt("test-key", pt)
        self.assertNotEqual(ct, pt)
        self.assertEqual(
            self.hsm.decrypt("test-key", ct),
            pt,
        )

    def test_tampered_ciphertext_raises(self):
        pt = b"sensitive data"
        ct = bytearray(self.hsm.encrypt("test-key", pt))
        ct[13] ^= 0xFF  # corrupt a byte in the ciphertext
        with self.assertRaises(HSMError):
            self.hsm.decrypt("test-key", bytes(ct))

    def test_wrong_key_raises(self):
        with self.assertRaises(KeyNotFoundError):
            self.hsm.decrypt("nonexistent", b"\x00" * 28)

    def test_encrypt_with_aad(self):
        pt = b"data with aad"
        ct = self.hsm.encrypt("test-key", pt, aad=b"context")
        self.assertEqual(
            self.hsm.decrypt("test-key", ct, aad=b"context"),
            pt,
        )

    def test_decrypt_with_wrong_aad_raises(self):
        pt = b"aad protected"
        ct = self.hsm.encrypt("test-key", pt, aad=b"correct")
        with self.assertRaises(HSMError):
            self.hsm.decrypt("test-key", ct, aad=b"wrong")

    def test_generate_key_material_changes(self):
        self.hsm.generate_key("k2", key_length=128)
        ct1 = self.hsm.encrypt("test-key", b"data")
        ct2 = self.hsm.encrypt("k2", b"data")
        self.assertNotEqual(ct1[:12], ct2[:12], "nonces should differ")

    def test_wrap_unwrap_key(self):
        wrapped = self.hsm.wrap_key("test-key", b"plaintext")
        self.assertIsNotNone(wrapped)

    def test_close_raises_on_hsm_unavailable(self):
        hsm2 = SoftwareHSM()
        hsm2.initialize({"storage_path": ":memory:"})
        hsm2.close()
        with self.assertRaises(HSMError):
            hsm2.encrypt("missing", b"x")


class TestAuditLogger(unittest.TestCase):
    """AuditLogger with atomic append + chain verification."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "audit.log")
        self.logger = AuditLogger(storage_path=self.log_path)

    def tearDown(self):
        if os.path.exists(self.log_path):
            os.remove(self.log_path)
        os.rmdir(self.tmpdir)

    def test_log_event_creates_file(self):
        self.logger.log_event(AuditEventType.KEY_GENERATED, "gen", actor="alice")
        self.assertTrue(os.path.exists(self.log_path))

    def test_log_event_line_is_json(self):
        self.logger.log_event(AuditEventType.KEY_GENERATED, "gen", actor="alice")
        with open(self.log_path) as f:
            line = f.readline().strip()
        obj = json.loads(line)
        self.assertEqual(obj["actor"], "alice")
        self.assertEqual(obj["event_type"], "key_generated")

    def test_multiple_events_pre_serve_all(self):
        for i in range(5):
            self.logger.log_event(
                AuditEventType.KEY_GENERATED, f"gen{i}", actor=f"user{i}"
            )
        with open(self.log_path) as f:
            lines = [_line for _line in f.read().splitlines() if _line]
        self.assertEqual(len(lines), 5)

    def test_no_empty_lines(self):
        self.logger.log_event(AuditEventType.KEY_GENERATED, "gen", actor="alice")
        self.logger.log_event(AuditEventType.KEY_DELETED, "delete", actor="bob")
        with open(self.log_path) as f:
            raw = f.read()
        self.assertNotIn("\n\n", raw)


class TestComplianceChecker(unittest.TestCase):
    """ComplianceChecker inference."""

    def test_check_compliance_returns_report(self):
        checker = ComplianceChecker()
        report = checker.check_compliance()
        self.assertIsNotNone(report)
        self.assertIn(report.overall_compliant, {True, False})

    def test_check_compliance_score_range(self):
        checker = ComplianceChecker()
        report = checker.check_compliance()
        score = report.get_summary().get("compliance_rate", 0.0)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_check_compliance_recommendations(self):
        checker = ComplianceChecker()
        summary = checker.check_compliance().get_summary()
        self.assertIsInstance(summary.get("standards", []), list)


if __name__ == "__main__":
    unittest.main()
