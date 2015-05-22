import logging
from hashlib import sha1

from Tribler.Test.test_doubleentry_utilities import TestBlock, DoubleEntryTestCase
from Tribler.community.doubleentry.conversion import DoubleEntryConversion
from Tribler.community.doubleentry.community import SIGNATURE_REQUEST, SIGNATURE_RESPONSE
from Tribler.community.doubleentry.payload import SignatureRequestPayload, SignatureResponsePayload
from Tribler.dispersy.community import Community
from Tribler.dispersy.authentication import NoAuthentication
from Tribler.dispersy.resolution import PublicResolution
from Tribler.dispersy.distribution import DirectDistribution
from Tribler.dispersy.destination import CandidateDestination
from Tribler.dispersy.message import Message
from Tribler.dispersy.conversion import DefaultConversion
from Tribler.dispersy.crypto import ECCrypto


class TestConversion(DoubleEntryTestCase):

    def __init__(self, *args, **kwargs):
        super(TestConversion, self).__init__(*args, **kwargs)
        self.community = TestCommunity()

    def test_encoding_decoding_signature_request(self):
        # Arrange
        converter = DoubleEntryConversion(self.community)

        meta = self.community.get_meta_message(SIGNATURE_REQUEST)
        block = TestBlock()

        message = meta.impl(distribution=(self.community.claim_global_time(),),
                            payload=block.get_signature_request_tuple())
        # Act
        encoded_message = converter._encode_signature_request(message)[0]
        result = converter._decode_signature_request(TestPlaceholder(meta), 0, encoded_message)[1]
        # Assert
        self.assertEqual_request(block, result)

    def test_encoding_decoding_signature_response(self):
        # Arrange
        converter = DoubleEntryConversion(self.community)

        meta = self.community.get_meta_message(SIGNATURE_RESPONSE)
        block = TestBlock()

        message = meta.impl(distribution=(self.community.claim_global_time(),),
                            payload=block.get_signature_response_tuple())
        # Act
        encoded_message = converter._encode_signature_response(message)[0]
        result = converter._decode_signature_response(TestPlaceholder(meta), 0, encoded_message)[1]
        # Assert
        self.assertEqual_block(block, result)


class TestPlaceholder:

    def __init__(self, meta):
        self.meta = meta


# noinspection PyMissingConstructor
class TestCommunity(Community):

    crypto = ECCrypto()

    def __init__(self):
        self.key = self.crypto.generate_key(u"very-low")
        self.pk = self.crypto.key_to_bin(self.key.pub())

        self.meta_message_cache = {}

        self._cid = sha1(self.pk).digest()
        self._meta_messages = {}
        self._initialize_meta_messages()

        self._global_time = 0
        self._do_pruning = False
        self._logger = logging.getLogger(self.__class__.__name__)

        self._conversions = self.initiate_conversions()

    def initiate_meta_messages(self):
        return super(TestCommunity, self).initiate_meta_messages() + [
            Message(self, SIGNATURE_REQUEST,
                    NoAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    SignatureRequestPayload(),
                    self._not_implemented,
                    self._not_implemented),
            Message(self, SIGNATURE_RESPONSE,
                    NoAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    SignatureResponsePayload(),
                    self._not_implemented,
                    self._not_implemented)]

    @staticmethod
    def _not_implemented(self):
        return

    def initiate_conversions(self):
        return [DefaultConversion(self), DoubleEntryConversion(self)]