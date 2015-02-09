from Tribler.Core.Utilities.encoding import encode, decode

from Tribler.dispersy.conversion import BinaryConversion
from Tribler.dispersy.message import DropPacket


class DoubleEntryConversion(BinaryConversion):
    """
    Class that handles all encoding and decoding of DoubleEntry messages.
    """

    def __init__(self, community):
        super(DoubleEntryConversion, self).__init__(community, "\x01")
        from Tribler.community.doubleentry.community import SIGNATURE_REQUEST
        from Tribler.community.doubleentry.community import SIGNATURE_RESPONSE

        # Define Request Signature.
        self.define_meta_message(chr(1), community.get_meta_message(SIGNATURE_REQUEST),
                                 self._encode_signature_request, self._decode_signature_request)
        self.define_meta_message(chr(2), community.get_meta_message(SIGNATURE_RESPONSE),
                                 self._encode_signature_response, self._decode_signature_response)

    def _encode_signature_request(self, message):
        """
        Encode a signature_request message.
        :param message: The message to be encoded.
        :return: encoded signature request message.
        """
        return encode((message.payload.timestamp, message.payload.previous_hash_requester,
                       message.payload.public_key_requester, message.payload.signature_requester)),

    def _decode_signature_request(self, placeholder, offset, data):
        try:
            offset, values = decode(data, offset)
            if len(values) != 4:
                raise ValueError
        except ValueError:
            raise DropPacket("Unable to decode the signature-request")

        timestamp = values[0]
        if not isinstance(timestamp, str):
            raise DropPacket("Invalid type timestamp")

        previous_hash = values[1]
        if not isinstance(previous_hash, str):
            raise DropPacket("invalid type previous hash")

        public_key = values[2]
        if not isinstance(timestamp, str):
            raise DropPacket("Invalid public_key")

        signature_request = values[3]
        if not isinstance(signature_request, str):
            raise DropPacket("Invalid type signature_request")

        return offset, placeholder.meta.payload.implement(timestamp, previous_hash, public_key, signature_request)

    def _encode_signature_response(self, message):
        # Encode a tuple containing the timestamp, the signature of the requester and the responder.
        # Return (encoding,)
        return encode((message.payload.timestamp, message.payload.public_key_requester, 
                       message.payload.signature_requester, message.payload.public_key_responder,
                       message.payload.signature_responder)),

    def _decode_signature_response(self, placeholder, offset, data):
        try:
            offset, values = decode(data, offset)
            if len(values) != 5:
                raise ValueError
        except ValueError:
            raise DropPacket("Unable to decode the signature-response")

        timestamp = values[0]
        if not isinstance(timestamp, str):
            raise DropPacket("Invalid type timestamp")

        public_key_requester = values[1]
        if not isinstance(public_key_requester, str):
            raise DropPacket("Invalid type public_key_requester")

        signature_requester = values[2]
        if not isinstance(signature_requester, str):
            raise DropPacket("Invalid type signature_request")

        public_key_responder = values[3]
        if not isinstance(public_key_responder, str):
            raise DropPacket("Invalid type public_key_responder")

        signature_responder = values[4]
        if not isinstance(signature_responder, str):
            raise DropPacket("Invalid type signature_request")

        return offset, placeholder.meta.payload.implement(timestamp, public_key_requester, signature_requester,
                                                          public_key_responder, signature_responder)