__author__ = 'norberhuis'

import unittest
import time

from Tribler.community.doubleentry.payload import RequestSignature

from Tribler.dispersy.crypto import ECCrypto


class TestPayload(unittest.TestCase):
    """
    Test the payloads of the DoubleEntry community
    """

    def setUp(self):
        self.crypto = ECCrypto()
        self.ec = self.crypto.generate_key(u'high')

    def test_RequestSignature_init(self):
        """
        Test creation of initializing a RequestSignaturePayload.
        :return:
        """
        # Act
        payload = RequestSignature.Implementation(self.ec)
        # Arrange
        self.assertAlmostEqual(time.time(), payload.timestamp, 0)
        self.assertTrue(self.crypto.is_valid_signature(self.ec, repr(payload.timestamp), payload.signatureInitiator))