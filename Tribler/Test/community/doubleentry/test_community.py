import unittest

from Tribler.community.doubleentry.community import DoubleEntryCommunity
from Tribler.dispersy.crypto import ECCrypto

from Tribler.Test.community.doubleentry.test_persistence import TestBlock


class TestDoubleEntryCommunity(unittest.TestCase):
    """
    Test class to test helper methods of the Double Entry Community.
    very-low security keys are used to speed up tests and these are never used in production.
    """

    crypto = ECCrypto()

    def test_validate_signature_positive(self):
        # Arrange
        key = self.crypto.generate_key(u"very-low")
        public_key = self.crypto.key_to_bin(key.pub())
        payload = "testing valid signature"
        signature = self.crypto.create_signature(key, payload)
        # Act
        result = DoubleEntryCommunity.validate_signature(public_key, payload, signature)
        # Assert
        assert result

    def test_validate_signature_negative(self):
        # Arrange
        key = self.crypto.generate_key(u"very-low")
        public_key = self.crypto.key_to_bin(key.pub())
        correct_payload = "testing valid signature"
        incorrect_payload = "NOTCORRESPONDINGPAYLOADTOSIGNATURE"
        signature = self.crypto.create_signature(key, correct_payload)
        # Act
        result = DoubleEntryCommunity.validate_signature(public_key, incorrect_payload, signature)
        # Assert
        assert not result

    def test_validate_signature_incorrect_format(self):
        # Arrange
        key = self.crypto.generate_key(u"very-low")
        private_key_format = self.crypto.key_to_bin(key)
        payload = "testing valid signature"
        signature = self.crypto.create_signature(key, payload)
        # Act
        result = DoubleEntryCommunity.validate_signature(private_key_format, payload, signature)
        # Assert
        assert not result

    def test_hash_signature_response(self):
        # Arrange
        message = TestMessage(TestBlock())
        # Act
        result = DoubleEntryCommunity.hash_signature_response(message)
        # Assert
        self.assertEqual(result, message.payload.id)


class TestMessage:
    """
    Test Message that simulates a message used in the DoubleEntry community.
    """

    def __init__(self, payload):
        self.payload = payload



