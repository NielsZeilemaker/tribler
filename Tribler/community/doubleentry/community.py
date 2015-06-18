import logging
import base64
import random
from hashlib import sha1

from Tribler.dispersy.authentication import DoubleMemberAuthentication
from Tribler.dispersy.resolution import PublicResolution
from Tribler.dispersy.distribution import DirectDistribution
from Tribler.dispersy.destination import CandidateDestination
from Tribler.dispersy.community import Community
from Tribler.dispersy.message import Message
from Tribler.dispersy.crypto import ECCrypto
from Tribler.dispersy.conversion import DefaultConversion

from Tribler.community.doubleentry.payload import SignaturePayload
from Tribler.community.doubleentry.conversion import DoubleEntryConversion
from Tribler.community.doubleentry.database import DoubleEntryDB

SIGNATURE = u"signature"

class DoubleEntryCommunity(Community):
    """
    Community prototype for reputation based tamper proof interaction history.
    """

    def __init__(self, *args, **kwargs):
        super(DoubleEntryCommunity, self).__init__(*args, **kwargs)
        self._logger = logging.getLogger(self.__class__.__name__)

        self._ec = self.my_member.private_key
        self._public_key = ECCrypto().key_to_bin(self._ec.pub())
        self.persistence = DoubleEntryDB(self.dispersy.working_directory)

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
            Message(self, SIGNATURE,
                    DoubleMemberAuthentication(allow_signature_func=self.allow_signature),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    SignaturePayload(),
                    self.check_signature_response,
                    self.on_signature_response)]

    def initiate_conversions(self):
        return [DefaultConversion(self), DoubleEntryConversion(self)]

    def publish_signature_request_message(self, candidate):
        """
        Creates and sends out signature_request message.
        """
        self._logger.info("Sending signature request.")
        message = self.create_signature_request_message(candidate)
        self.dispersy.store_update_forward([message], False, False, True)

    def create_signature_request_message(self, candidate):
        """
        Create a signature request message using the current time stamp.
        :return: Signature_request message ready for distribution.
        """
        
        # Instantiate the data
        # TODO
        up = 1
        down = 2
        total_up = 3
        total_down = 4
        
        # Instantiate the personal information
        sequence_number_requester = self.persistence.get_latest_sequence_number(self._public_key)
        previous_hash_requester = self.persistence.get_previous_id()
        payload = (up, down, total_up, total_down, sequence_number_requester, previous_hash_requester)
        
        meta = self.get_meta_message(SIGNATURE)
        message = meta.impl(authentication=(self.my_member,),
                            distribution=(self.claim_global_time(),),
                            destination=(candidate,),
                            payload=payload)
        return message
    
    
    def allow_signature_request(self, message):
        """
        We've received a signature request message, we must return either: 
            a. a modified version of message (because we're adding our own values) 
            b. None (if we want to drop this message).
        """
        payload = message.payload
        
        sequence_number_responder = self.persistence.get_latest_sequence_number(self._public_key)
        previous_hash_responder = self.persistence.get_previous_id()
        
        payload = (payload.up, payload.down, 
                   payload.total_up, payload.total_down, 
                   payload.sequence_number_requester, payload.previous_hash_requester,
                   sequence_number_responder, previous_hash_responder)
        
        meta = self.get_meta_message(SIGNATURE)
        message = meta.impl(authentication=(message.authentication.members,),
                            distribution=(message.distribution.global_time,),
                            payload=payload)
        return message
    
    
    def allow_signature_response(self, request, response, modified):
        """
        We've received a signature repsonse message, we must return either:
            a. True, if we accept this message
            b. False, if not (because of inconsistencies in the payload)
        """
        
        if request.payload.sequence_number_requester == response.payload.sequence_number_requester and \
            request.payload.previous_hash_requester == response.payload.previous_hash_requester:
            
            #our values did not change, accept
            self.persist_signature_response(response)
            return True
        return False

    def next_candidate(self):
        return self.candidates[random.choice(self.candidates.keys())]

    def persist_signature_response(self, message):
        """
        Persist the signature response message.
        A hash will be created from the message and this will be used as an unique identifier.
        :param message:
        """
        message_hash = self.hash_signature_response(message)
        self._logger.info("Persisting sr: %s." % base64.encodestring(message_hash))
        self.persistence.add_block(message_hash, message.payload)

    @staticmethod
    def hash_signature_response(message):
        """
        Create a hash of a signature response message.
        :param message: The message a hash has to be taken from
        :return: Hash
        """
        # Create the hash using SHA1.
        return sha1(message.payload.packet).digest()

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