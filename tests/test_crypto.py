import unittest

from qkdpy.core import QuantumChannel
from qkdpy.crypto import (
    OneTimePad,
    QuantumAuth,
    QuantumAuthentication,
    QuantumAuthenticator,
    QuantumKeyExchange,
    QuantumKeyValidation,
    QuantumRandomNumberGenerator,
    QuantumSideChannelProtection,
)


class TestCrypto(unittest.TestCase):

    def test_one_time_pad_creation(self):
        otp = OneTimePad()
        self.assertIsNotNone(otp)

    def test_one_time_pad_encrypt_decrypt(self):
        otp = OneTimePad()
        key = [int(b) for b in "0101010101010101010101010101010101010101"]
        message = "hello"
        encrypted_message, _ = otp.encrypt(message, key)
        self.assertIsNotNone(encrypted_message)
        decrypted_message = OneTimePad.decrypt(encrypted_message, key)
        self.assertEqual(decrypted_message, message)

    def test_quantum_auth_creation(self):
        qa = QuantumAuth()
        self.assertIsNotNone(qa)

    def test_quantum_authenticator_creation(self):
        channel = QuantumChannel()
        authenticator = QuantumAuthenticator(channel)
        self.assertIsNotNone(authenticator)

    def test_quantum_key_exchange_creation(self):
        channel = QuantumChannel()
        qke = QuantumKeyExchange(channel)
        self.assertIsNotNone(qke)

    def test_quantum_rng_creation(self):
        channel = QuantumChannel()
        qrng = QuantumRandomNumberGenerator(channel)
        self.assertIsNotNone(qrng)

    def test_quantum_authentication_creation(self):
        qa = QuantumAuthentication()
        self.assertIsNotNone(qa)

    def test_quantum_key_validation_creation(self):
        qkv = QuantumKeyValidation()
        self.assertIsNotNone(qkv)

    def test_quantum_side_channel_protection_creation(self):
        qscp = QuantumSideChannelProtection()
        self.assertIsNotNone(qscp)


if __name__ == "__main__":
    unittest.main()
