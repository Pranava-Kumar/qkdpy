"""Coverage tests for crypto modules."""
import os
import tempfile

import pytest

from qkdpy.crypto.authentication import QuantumAuth
from qkdpy.crypto.decryption import OneTimePadDecrypt
from qkdpy.crypto.encryption import OneTimePad


class TestOneTimePad:
    def test_encrypt_roundtrip(self):
        key = [1, 0] * 8
        ct, rem = OneTimePad.encrypt("Hi", key)
        assert len(ct) == 16

    def test_encrypt_key_too_short(self):
        with pytest.raises(ValueError, match="Key is too short"):
            OneTimePad.encrypt("Hello!", [0, 1])

    def test_text_bits_roundtrip(self):
        bits = OneTimePad._text_to_bits("A")
        assert bits == [0, 1, 0, 0, 0, 0, 0, 1]
        text = OneTimePad._bits_to_text(bits)
        assert text == "A"

    def test_bytes_bits_roundtrip(self):
        inp = bytes([10, 255])
        bits = OneTimePad._bytes_to_bits(inp)
        assert len(bits) == 16
        recovered = OneTimePad._bits_to_bytes(bits)
        assert recovered == inp

    def test_encrypt_file(self):
        key = [1] * 1024
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        tf.write(b"test data")
        p = tf.name
        tf.close()
        try:
            out, _ = OneTimePad.encrypt_file(p, key, p + ".custom")
            assert os.path.exists(out)
            os.unlink(out)
        finally:
            os.unlink(p)

    def test_encrypt_file_default_output(self):
        key = [1] * 1024
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        tf.write(b"data")
        p = tf.name
        tf.close()
        try:
            out, _ = OneTimePad.encrypt_file(p, key)
            assert os.path.exists(out)
            os.unlink(out)
        finally:
            os.unlink(p)

    def test_encrypt_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            OneTimePad.encrypt_file("/nonexistent/file.txt", [0, 1])


class TestOneTimePadDecrypt:
    def test_decrypt_roundtrip(self):
        key = [1, 0] * 8
        ct, _ = OneTimePad.encrypt("Hi", key)
        msg = OneTimePadDecrypt.decrypt(ct, key)
        assert msg == "Hi"

    def test_decrypt_key_too_short(self):
        with pytest.raises(ValueError):
            OneTimePadDecrypt.decrypt([1, 0, 1, 0], [0])

    def test_decrypt_file(self):
        key = [1] * 1024
        fd, p = tempfile.mkstemp(suffix=".bin")
        os.close(fd)
        try:
            with open(p, "wb") as f:
                f.write(b"hello world")
            enc, _ = OneTimePad.encrypt_file(p, key, p + ".enc")
            assert os.path.exists(enc)
            dec = OneTimePadDecrypt.decrypt_file(enc, key)
            assert os.path.exists(dec)
            with open(dec, "rb") as f:
                assert f.read() == b"hello world"
            os.unlink(enc)
            os.unlink(dec)
        finally:
            if os.path.exists(p):
                os.unlink(p)

    def test_decrypt_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            OneTimePadDecrypt.decrypt_file("/nonexistent/file.enc", [0, 1])


class TestQuantumAuth:
    def test_mac_all_algorithms(self):
        key = [1, 0] * 64
        for algo in ["sha256", "sha512", "sha1", "md5"]:
            m = QuantumAuth.generate_mac("msg", key, algo)
            assert isinstance(m, str) and len(m) > 0

    def test_mac_unsupported(self):
        with pytest.raises(ValueError, match="Unsupported hash algorithm"):
            QuantumAuth.generate_mac("h", [1, 0] * 64, "blake2b")

    def test_verify_mac(self):
        key = [1, 0] * 64
        mac = QuantumAuth.generate_mac("msg", key)
        assert QuantumAuth.verify_mac("msg", mac, key) is True
        assert QuantumAuth.verify_mac("bad", mac, key) is False

    def test_authenticator(self):
        k = [1, 0] * 64
        assert isinstance(QuantumAuth.generate_authenticator(k), str)
        assert isinstance(QuantumAuth.generate_authenticator(k, "chal"), str)

    def test_verify_authenticator(self):
        key = [1, 0] * 64
        a = QuantumAuth.generate_authenticator(key, "c123")
        assert QuantumAuth.verify_authenticator(key, "c123", a) is True
        assert QuantumAuth.verify_authenticator(key, "wrong", a) is False

    def test_key_fingerprint(self):
        fp = QuantumAuth.generate_key_fingerprint([1, 0] * 64)
        assert len(fp) == 64
        fp2 = QuantumAuth.generate_key_fingerprint([1, 0] * 64, "sha512")
        assert len(fp2) == 128

    def test_key_fingerprint_unsupported(self):
        with pytest.raises(ValueError, match="Unsupported hash algorithm"):
            QuantumAuth.generate_key_fingerprint([1, 0] * 64, "blake2b")

    def test_commitment(self):
        r = QuantumAuth.generate_commitment("val", [1, 0] * 64)
        assert "commitment" in r
        r2 = QuantumAuth.generate_commitment("val", [1, 0] * 64, nonce=42)
        assert r2["nonce"] == "42"

    def test_verify_commitment(self):
        key = [1, 0] * 64
        r = QuantumAuth.generate_commitment("my_value", key)
        assert QuantumAuth.verify_commitment("my_value", r["commitment"], key, r["nonce"]) is True
        assert QuantumAuth.verify_commitment("wrong", r["commitment"], key, r["nonce"]) is False
