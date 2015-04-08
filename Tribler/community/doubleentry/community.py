import time
import logging
import base64
from hashlib import sha1

from Tribler.dispersy.authentication import MemberAuthentication
from Tribler.dispersy.resolution import PublicResolution
from Tribler.dispersy.distribution import DirectDistribution
from Tribler.dispersy.destination import CandidateDestination
from Tribler.dispersy.community import Community
from Tribler.dispersy.message import Message, DropMessage
from Tribler.dispersy.crypto import ECCrypto
from Tribler.dispersy.conversion import DefaultConversion

from Tribler.community.doubleentry.payload import SignatureRequestPayload, SignatureResponsePayload
from Tribler.community.doubleentry.conversion import DoubleEntryConversion
from Tribler.community.doubleentry.database import Persistence

SIGNATURE_REQUEST = u"de_signature_request"
SIGNATURE_RESPONSE = u"de_signature_response"


class DoubleEntryCommunity(Community):
    """
    Community prototype for reputation based tamper proof interaction history.
    """

    def __init__(self, *args, **kwargs):
        super(DoubleEntryCommunity, self).__init__(*args, **kwargs)
        self._logger = logging.getLogger(self.__class__.__name__)

        self._ec = self._my_member._ec
        self._public_key = ECCrypto().key_to_bin(self._ec.pub())
        self.persistence = Persistence(self.dispersy.working_directory)
        self.candidate_queue = []

    def initialize(self, a=None, b=None):
        super(DoubleEntryCommunity, self).initialize()

    @classmethod
    def get_master_members(cls, dispersy):
        # generated: Wed Dec  3 10:31:16 2014
        # curve: NID_sect571r1
        # len: 571 bits ~ 144 bytes signature
        # pub: 170  3081a7301006072a8648ce3d020106052b810400270381920004059f45b75d63f865e3c7b350bd3ccdc99dbfbf76f
        #           dfb524939f070223c3ea9ea5d0536721cf9afbbec5693798e289b964fefc930961dfe1a7f71c445031434aba637bb9
        #           3b947fb81603f649d4a08e5698e677059b9d3a441986c16f8da94d4aa2afbf10fe056cd65741108fe6a880606869c
        #           a81fdcb2db302ac15905d6e75f96b39ccdaf068bdbbda81a6356f53f7ce4e
        # pub-sha1 f66a50b35c4a0d45abd0052f574c5ecc233b8e54
        # -----BEGIN PUBLIC KEY-----
        # MIGnMBAGByqGSM49AgEGBSuBBAAnA4GSAAQFn0W3XWP4ZePHs1C9PM3Jnb+/dv37
        # Ukk58HAiM+qepdBTZyHPmvu+xWk3mOKJuWT+/JMJYd/hp/ccRFAxQ0q6Y3u5O5R/
        # uBYD9knUoI5WmOZ3BZudOkQZhsFvjalNSqKvvxD+BWzWV0EQj+aogGBoacqB/cst
        # swKsFZBdbnX5aznM2vBovbvagaY1b1P3zk4=
        # -----END PUBLIC KEY-----
        master_key = "3081a7301006072a8648ce3d020106052b810400270381920004059f45b75d63f865e3c7b350bd3ccdc99dbfbf76f" + \
                     "dfb524939f0702233ea9ea5d0536721cf9afbbec5693798e289b964fefc930961dfe1a7f71c445031434aba637bb9" + \
                     "3b947fb81603f649d4a08e5698e677059b9d3a441986c16f8da94d4aa2afbf10fe056cd65741108fe6a880606869c" + \
                     "a81fdcb2db302ac15905d6e75f96b39ccdaf068bdbbda81a6356f53f7ce4e"
        master_key_hex = master_key.decode("HEX")
        master = dispersy.get_member(public_key=master_key_hex)
        return [master]

    def initiate_meta_messages(self):
        return super(DoubleEntryCommunity, self).initiate_meta_messages() + [
            Message(self, SIGNATURE_REQUEST,
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    SignatureRequestPayload(),
                    self._check_signature_request,
                    self._on_signature_request),
            Message(self, SIGNATURE_RESPONSE,
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    SignatureResponsePayload(),
                    self._check_signature_response,
                    self._on_signature_response)]

    def initiate_conversions(self):
        return [DefaultConversion(self), DoubleEntryConversion(self)]

    def publish_signature_request_message(self, candidate):
        """
        Creates and sends out signature_request message.
        """
        self._logger.info("Sending signature request.")
        message = self.create_signature_request_message(candidate)
        self.dispersy.store_update_forward([message], True, True, True)

    def create_signature_request_message(self, candidate):
        """
        Create a signature request message using the current time stamp.
        :return: Signature_request message ready for distribution.
        """
        meta = self.get_meta_message(SIGNATURE_REQUEST)

        timestamp = repr(time.time())
        previous_hash_requester = self.persistence.get_previous_id()
        public_key_requester = self._public_key
        signature = ECCrypto().create_signature(self._ec, timestamp)

        message = meta.impl(authentication=(self.my_member,),
                            distribution=(self.claim_global_time(),),
                            destination=(candidate,),
                            payload=(timestamp, previous_hash_requester, public_key_requester, signature))
        return message

    def validate_signature_request(self, signature_request):
        """
        Validates if the signature_request message contains correct signatures and public keys.
        :param signature_request: The message that needs to be checked.
        :return: Boolean containing the truth value of the validity of the message.
        """
        payload = signature_request.payload
        # Check if the request is not already processed.
        return (not self.persistence.contains_signature(payload.signature_requester, payload.public_key_requester) and
                # Check if the request is valid
                self.validate_signature(payload.public_key_requester, payload.timestamp, payload.signature_requester))

    def _check_signature_request(self, messages):
        """
        Generator that generates a list of correct signature_request messages from a list of messages.
        :param messages: Potential valid signature_request messages.
        :return: Series of correct signature_request messages
        """
        self._logger.info("Received " + str(len(messages)) + " signature requests.")
        for message in messages:
            if self.validate_signature_request(message):
                self._logger.info("Received valid request.")
                yield message
            else:
                DropMessage(message, "Invalid signature request message")

    def _on_signature_request(self, messages):
        """
        Handles behaviour of the community when it receives a signature_request message.
        It will send out a signature response
        :param messages: Signature_request messages that needs to be handled.
        """
        for message in messages:
            # Check if the messages are not from ourselves.
            if message.payload.public_key_requester != self._public_key:
                self.publish_signature_response_message(message)

    def next_candidate(self):
        return self.candidate_queue.pop()

    def publish_signature_response_message(self, signature_request):
        """
        Creates and sends out signature_response message for a signature_request message.
        The message is also locally persisted.
        :param signature_request: signature_request message that needs to be responded to.
        """
        self._logger.info("Sending signature response.")
        message = self.create_signature_response_message(signature_request)
        self.persist_signature_response(message)
        self._dispersy.store_update_forward([message], True, True, True)

    def create_signature_response_message(self, signature_request):
        """
        Create a signature response message for a signature_request message.
        :param signature_request: signature_request message that needs to be responded to.
        :return: Signature_response message ready for distribution.
        """
        meta = self.get_meta_message(SIGNATURE_RESPONSE)

        # Create the part to be signed.
        timestamp = signature_request.payload.timestamp
        previous_hash_requester = signature_request.payload.previous_hash_requester
        public_key_requester = signature_request.payload.public_key_requester
        signature_requester = signature_request.payload.signature_requester
        request = timestamp + "." + public_key_requester + "." + signature_requester
        # Create the personal part of the message.
        previous_hash_responder = self.persistence.get_previous_id()
        public_key_responder = ECCrypto().key_to_bin(self._ec.pub())
        # Sign the request.
        signature = ECCrypto().create_signature(self._ec, request)

        message = meta.impl(authentication=(self.my_member,),
                            distribution=(self.claim_global_time(),),
                            destination=(signature_request.candidate,),
                            payload=(timestamp, previous_hash_requester, public_key_requester, signature_requester,
                                     previous_hash_responder, public_key_responder, signature))
        return message

    def validate_signature_response(self, signature_response):
        """
        Validates if the signature_response message contains correct signatures and public keys.
        :param signature_response: The message that needs to be checked.
        :return: Boolean containing the truth value of the validity of the message.
        """
        payload = signature_response.payload
        # Check if the request part is valid.
        valid_request = self.validate_signature(payload.public_key_requester, payload.timestamp,
                                                payload.signature_requester)
        # Check if the response part is valid.
        valid_response = self.validate_signature(
            payload.public_key_responder,
            payload.timestamp + "." + payload.public_key_requester + "." + payload.signature_requester,
            payload.signature_responder)
        # Both have to be valid.
        return valid_request and valid_response

    def _check_signature_response(self, messages):
        """
        Generator that generates a list of correct signature_response messages from a list of messages.
        :param messages: Potential valid signature_response messages.
        :return: Series of correct signature_response messages
        """
        self._logger.info("Received " + str(len(messages)) + " signature responses.")
        for message in messages:
            # For now do no checking.
            if self.validate_signature_response(message):
                self._logger.info("Received valid response")
                yield message
            else:
                DropMessage(message, "Invalid signature response message")

    def _on_signature_response(self, messages):
        """
        Handles behaviour of the community when it receives a signature_response message.
        It persist the signature response.
        :param messages: Signature_response messages that needs to be handled.
        """
        for message in messages:
            # Check if the messages are not from ourselves.
            if message.payload.public_key_responder != self._public_key:
                self.persist_signature_response(message)

    def persist_signature_response(self, message):
        """
        Persist the signature response message.
        A hash will be created from the message and this will be used as an unique identifier.
        :param message:
        """
        message_hash = self.hash_signature_response(message)
        self._logger.info("Persisting sr: %s." % base64.encodestring(message_hash))
        self.persistence.add_block(message_hash, message.payload)

    def on_introduction_response(self, messages):
        super(DoubleEntryCommunity, self).on_introduction_response(messages)
        for message in messages:
            self._logger.info("in on_introduction_response: Saving %s candidate.", message.candidate)
            self.candidate_queue.append(message.candidate)

    @staticmethod
    def hash_signature_response(message):
        """
        Create a hash of a signature response message.
        :param message: The message a hash has to be taken from
        :return: Hash
        """
        payload = message.payload
        # Prepare the data to be signed separated by '.'
        data = (payload.timestamp,
                payload.previous_hash_requester, payload.public_key_requester, payload.signature_requester,
                payload.previous_hash_responder, payload.public_key_responder, payload.signature_responder)
        data = ".".join(data)
        # Create the hash using SHA1.
        return sha1(data).digest()

    @staticmethod
    def validate_signature(public_key_binary, payload, signature):
        """
        Utility method that uses a pk in binary to check
        if the pk has been used to create the signature for the payload.
        :param public_key_binary: Public Key in binary format.
        :param payload: string that has to be signed.
        :param signature: string that contains the signature.
        :return: Boolean that contains the truth value if the signature and public key correspond.
        """
        # Check if the payload contains a valid public key
        if ECCrypto().is_valid_public_bin(public_key_binary):
            # Convert the public key from the binary format to EC_PUB instance
            public_key = ECCrypto().key_from_public_bin(public_key_binary)
            # Check the signature
            return ECCrypto().is_valid_signature(public_key, payload, signature)
        else:
            # Invalid public key.
            return False

    def get_key(self):
        return self._ec

    def unload_community(self):
        self._logger.debug("Unloading the DoubleEntry Community.")
        super(DoubleEntryCommunity, self).unload_community()
        # Close the persistence layer
        self.persistence.close()

class DoubleEntrySettings(object):
    """
    Class that contains settings for the double entry community.
    """

    def __init__(self):
        self.socks_listen_ports = range(9000, 9000)
        self.dispersy_port = -1