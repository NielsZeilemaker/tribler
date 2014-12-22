
from Tribler.Core.Utilities.encoding import encode, decode

from Tribler.dispersy.conversion import BinaryConversion
from Tribler.dispersy.message import DropPacket




class DoubleEntryConversion(BinaryConversion):

    def __init__(self, community):
        super(DoubleEntryConversion, self).__init__(community, "\x01")
        from Tribler.community.doubleentry.community import SIGNATURE_REQUEST
        from Tribler.community.doubleentry.community import SIGNATURE_RESPONSE
        # Define Request Signature.
        self.define_meta_message(chr(1), community.get_meta_message(SIGNATURE_REQUEST), lambda message: self._encode_decode(self._encode_signature_request, self._decode_signature_request, message), self._decode_signature_request)
        self.define_meta_message(chr(2), community.get_meta_message(SIGNATURE_RESPONSE), lambda message: self._encode_decode(self._encode_signature_response, self._decode_signature_response, message), self._decode_signature_response)

    def _encode_decode(self, encode, decode, message):
        result = encode(message)
        try:
            decode(None, 0, result)

        except DropPacket:
            raise
        except:
            pass
        return result

    def _encode_signature_request(self, message):
        # Encode a tuple containing the timestamp, the signature of the requester and the responder.
        # Return (encoding,)
        return encode((message.payload.timestamp, message.payload.signature_requester)),

    def _decode_signature_request(self, placeholder, offset, data):
        try:
            offset, values = decode(data, offset)
            if len(values) != 2:
                raise ValueError
        except ValueError:
            raise DropPacket("Unable to decode the signature-request")

        timestamp = values[0]
        if not isinstance(timestamp, float):
            raise DropPacket("Invalid type timestamp")

        signature_request = values[1]
        if not isinstance(signature_request, str):
            raise DropPacket("Invalid type signature_request")

        return offset, placeholder.meta.payload.implement(timestamp, signature_request)

    def _encode_signature_response(self, message):
        # Encode a tuple containing the timestamp, the signature of the requester and the responder.
        # Return (encoding,)
        return encode((message.payload.timestamp, message.payload.signature_requester,
                       message.payload.signature_responder)),

    def _decode_signature_response(self, placeholder, offset, data):
        try:
            offset, values = decode(data, offset)
            if len(values) != 3:
                raise ValueError
        except ValueError:
            raise DropPacket("Unable to decode the signature-response")

        timestamp = values[0]
        if not isinstance(timestamp, float):
            raise DropPacket("Invalid type timestamp")

        signature_request = values[1]
        if not isinstance(signature_request, str):
            raise DropPacket("Invalid type signature_request")

        signature_responder = values[2]
        if not isinstance(signature_responder, str):
            raise DropPacket("Invalid type signature_request")

        return offset, placeholder.meta.payload.implement(timestamp, signature_request, signature_responder)