__author__ = 'norberhuis'

import unittest
import time

from Tribler.community.doubleentry.payload import RequestSignature, SignatureResponse

from Tribler.dispersy.crypto import ECCrypto


class TestPayload(unittest.TestCase):
    """
    Test the payloads of the DoubleEntry community
    """

    _SECURITY_LEVEL = u'high'

    def setUp(self):
        self.crypto = ECCrypto()
        self.ec = self.crypto.generate_key(self._SECURITY_LEVEL)

    def test_requestsignature_init(self):
        """
        Test initializing a RequestSignaturePayload.
        """
        # Act
        payload = RequestSignature.Implementation(self.ec)
        # Assert
        self.assertAlmostEqual(time.time(), payload.timestamp, 0)
        self.assertTrue(self.crypto.is_valid_signature(self.ec, repr(payload.timestamp), payload.signatureRequester))

    def test_signaturerepsonse_init(self):
        """
        Test initializing a SignatureResponsePayload
        """
        # Arrange
        # Create different key resembling the requester.
        requester_ec = self.crypto.generate_key(self._SECURITY_LEVEL)
        request = RequestSignature.Implementation(requester_ec)
        # Act
        payload = SignatureResponse.Implementation(self.ec, request)
        # Assert
        data = repr(request.timestamp) + request.signatureRequester
        self.assertTrue(self.crypto.is_valid_signature(self.ec, data, payload.signatureResponder))