import time
import logging
import base64

from Tribler.dispersy.authentication import MemberAuthentication
from Tribler.dispersy.resolution import PublicResolution
from Tribler.dispersy.distribution import FullSyncDistribution
from Tribler.dispersy.destination import CommunityDestination
from Tribler.dispersy.community import Community
from Tribler.dispersy.message import Message, DropMessage
from Tribler.dispersy.crypto import ECCrypto
from Tribler.dispersy.conversion import DefaultConversion

from Tribler.community.doubleentry.payload import SignatureRequestPayload, SignatureResponsePayload
from Tribler.community.doubleentry.conversion import DoubleEntryConversion

SIGNATURE_REQUEST = u"de_signature_request"
SIGNATURE_RESPONSE = u"de_signature_response"


class DoubleEntryCommunity(Community):

    def __init__(self, *args, **kwargs):
        super(DoubleEntryCommunity, self).__init__(*args, **kwargs)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._ec = None

    def initialize(self, a=None, b=None):
        super(DoubleEntryCommunity, self).initialize()

    def set_ec(self, ec):
        self._ec = ec

    @classmethod
    def get_master_members(cls, dispersy):
        # generated: Wed Dec  3 10:31:16 2014
        # curve: NID_sect571r1
        # len: 571 bits ~ 144 bytes signature
        # pub: 170 3081a7301006072a8648ce3d020106052b810400270381920004059f45b75d63f865e3c7b350bd3ccdc99dbfbf76fdfb524939f0702233ea9ea5d0536721cf9afbbec5693798e289b964fefc930961dfe1a7f71c445031434aba637bb93b947fb81603f649d4a08e5698e677059b9d3a441986c16f8da94d4aa2afbf10fe056cd65741108fe6a880606869ca81fdcb2db302ac15905d6e75f96b39ccdaf068bdbbda81a6356f53f7ce4e
        # pub-sha1 f66a50b35c4a0d45abd0052f574c5ecc233b8e54
        # -----BEGIN PUBLIC KEY-----
        # MIGnMBAGByqGSM49AgEGBSuBBAAnA4GSAAQFn0W3XWP4ZePHs1C9PM3Jnb+/dv37
        # Ukk58HAiM+qepdBTZyHPmvu+xWk3mOKJuWT+/JMJYd/hp/ccRFAxQ0q6Y3u5O5R/
        # uBYD9knUoI5WmOZ3BZudOkQZhsFvjalNSqKvvxD+BWzWV0EQj+aogGBoacqB/cst
        # swKsFZBdbnX5aznM2vBovbvagaY1b1P3zk4=
        # -----END PUBLIC KEY-----
        master_key = "3081a7301006072a8648ce3d020106052b81040027038192000406712a1e5381d030ae25697bd6626810af48ed5094e5faae18a8b91e482e60b8681b26bf6aca786ad81b207ffb5a755956b4d6353c9dc487eb1bfdd17b66bd0de444e01a375fcf3401177a7bb102da7c5f50ad9375fe4a1ae1baca9d47870f56c841169fc36c2b113bafbadacab9f2b3c7773b3d82a54cda8fbde41b9e0e571ba631997a8259cc78e7f262e933542b51"
        master_key_hex = master_key.decode("HEX")
        master = dispersy.get_member(public_key=master_key_hex)
        return [master]

    def initiate_meta_messages(self):
        return super(DoubleEntryCommunity, self).initiate_meta_messages() + [
            Message(self, SIGNATURE_REQUEST,
                    MemberAuthentication(),
                    PublicResolution(),
                    FullSyncDistribution(enable_sequence_number=False, synchronization_direction=u"DESC", priority=128),
                    CommunityDestination(node_count=1),
                    SignatureRequestPayload(),
                    self._check_signature_request,
                    self._on_signature_request),
            Message(self, SIGNATURE_RESPONSE,
                    MemberAuthentication(),
                    PublicResolution(),
                    FullSyncDistribution(enable_sequence_number=False, synchronization_direction=u"DESC", priority=128),
                    CommunityDestination(node_count=1),
                    SignatureResponsePayload(),
                    self._check_signature_response,
                    self._on_signature_response)]

    def initiate_conversions(self):
        return [DefaultConversion(self), DoubleEntryConversion(self)]

    def publish_signature_request_message(self):
        message = self.create_signature_request_message()
        self.dispersy.store_update_forward([message], True, True, True)

    def create_signature_request_message(self):
        meta = self.get_meta_message(SIGNATURE_REQUEST)

        timestamp = repr(time.time())
        public_key = ECCrypto().key_to_bin(self._ec.pub())
        signature = ECCrypto().create_signature(self._ec, timestamp)

        message = meta.impl(authentication=(self.my_member,),
                            distribution=(self.claim_global_time(),),
                            payload=(timestamp, public_key, signature))
        return message

    def publish_signature_response_message(self, signature_request):
        message = self.create_signature_response_message(signature_request)
        self._dispersy.store_update_forward([message], True, True, True)

    def create_signature_response_message(self, signature_request):
        self._logger.info("Sending signature response.")
        print("Sending signature response!")
        meta = self.get_meta_message(SIGNATURE_RESPONSE)
        # Create the part to be signed.
        timestamp = signature_request.payload.timestamp
        signature_requester = signature_request._payload.signature_requester
        request = timestamp + "." + signature_requester

        # Sign the request
        signature = ECCrypto().create_signature(self._ec, request)

        message = meta.impl(authentication=(self.my_member,),
                            distribution=(self.claim_global_time(),),
                            payload=(timestamp, signature_requester, signature))
        return message

    def validate_signature_request(self, message):
        # Check if the payload contains a valid public key.
        public_key_binary = message.payload.public_key
        # Validate if the key is a valid key.
        if ECCrypto().is_valid_public_bin(public_key_binary):
            # Convert the public key from the binary format to EC_PUB instance
            public_key = ECCrypto().key_from_public_bin(public_key_binary)
            # Validate the signature
            if ECCrypto().is_valid_signature(public_key, message.payload.timestamp,
                                            message.payload.signature_requester):
                # Pass on the message
                print("Received valid message")
                return True
            else:
                print("Signature of request is invalid")
                return False
        else:
            print("Public key invalid")
            return False

    def _check_signature_request(self, messages):
        self._logger.info("Received " + str(len(messages)) + " signature requests.")
        print("Received " + str(len(messages)) + " signature requests.")
        for message in messages:
            if self.validate_signature_request(message):
                yield message
            else:
                DropMessage(message, "Invalid signature request message")

    def _check_signature_response(self, messages):
        self._logger.info("Received " + str(len(messages)) + " signature requests.")
        print("Received " + str(len(messages)) + " signature responses.")
        for message in messages:
            # For now do no checking.

            yield message

    def _on_signature_request(self, messages):
        for message in messages:
            self.create_signature_response_message(message)

    def _on_signature_response(self, messages):
        pass


class DoubleEntrySettings(object):

    def __init__(self):
        self.socks_listen_ports = range(9000, 9000)
        self.swift_port = -1