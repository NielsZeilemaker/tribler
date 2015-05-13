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
        payload = message.payload
        return encode((payload.up, payload.down, payload.total_up, payload.total_down,
                       payload.sequence_number_requester, payload.previous_hash_requester,
                       payload.public_key_requester, payload.signature_requester)),

    def _decode_signature_request(self, placeholder, offset, data):
        try:
            offset, values = decode(data, offset)
            if len(values) != 8:
                raise ValueError
        except ValueError:
            raise DropPacket("Unable to decode the signature-request")

        up = values[0]
        if not isinstance(up, int):
            raise DropPacket("Invalid type up")

        down = values[1]
        if not isinstance(down, int):
            raise DropPacket("Invalid type down")

        total_up = values[2]
        if not isinstance(total_up, int):
            raise DropPacket("Invalid type total_up")

        total_down = values[3]
        if not isinstance(total_down, int):
            raise DropPacket("Invalid type total_down")

        sequence_number_requester = values[4]
        if not isinstance(sequence_number_requester, int):
            raise DropPacket("Invalid type sequence_number_requester")

        previous_hash_requester = values[5]
        if not isinstance(previous_hash_requester, str):
            raise DropPacket("invalid type previous hash")

        public_key_requester = values[6]
        if not isinstance(public_key_requester, str):
            raise DropPacket("Invalid public_key")

        signature_requester = values[7]
        if not isinstance(signature_requester, str):
            raise DropPacket("Invalid type signature_request")

        return offset, placeholder.meta.\
            payload.implement(up, down, total_up, total_down, sequence_number_requester,
                              previous_hash_requester, public_key_requester, signature_requester)

    def _encode_signature_response(self, message):
        # Encode a tuple containing the timestamp, the signature of the requester and the responder.
        # Return (encoding,)
        payload = message.payload
        return encode((payload.up, payload.down, payload.total_up, payload.total_down,
                       payload.sequence_number_requester, payload.previous_hash_requester,
                       payload.public_key_requester, payload.signature_requester, payload.sequence_number_responder,
                       payload.previous_hash_responder, payload.public_key_responder, payload.signature_responder)),

    def _decode_signature_response(self, placeholder, offset, data):
        try:
            offset, values = decode(data, offset)
            if len(values) != 12:
                raise ValueError
        except ValueError:
            raise DropPacket("Unable to decode the signature-response")

        up = values[0]
        if not isinstance(up, int):
            raise DropPacket("Invalid type up")

        down = values[1]
        if not isinstance(down, int):
            raise DropPacket("Invalid type down")

        total_up = values[2]
        if not isinstance(total_up, int):
            raise DropPacket("Invalid type total_up")

        total_down = values[3]
        if not isinstance(total_down, int):
            raise DropPacket("Invalid type total_down")

        sequence_number_requester = values[4]
        if not isinstance(sequence_number_requester, int):
            raise DropPacket("Invalid type sequence_number_requester")

        previous_hash_requester = values[5]
        if not isinstance(previous_hash_requester, str):
            raise DropPacket("Invalid type previous_hash_requester")

        public_key_requester = values[6]
        if not isinstance(public_key_requester, str):
            raise DropPacket("Invalid type public_key_requester")

        signature_requester = values[7]
        if not isinstance(signature_requester, str):
            raise DropPacket("Invalid type signature_request")

        sequence_number_responder = values[8]
        if not isinstance(sequence_number_responder, int):
            raise DropPacket("Invalid type sequence_number_requester")

        previous_hash_responder = values[9]
        if not isinstance(previous_hash_responder, str):
            raise DropPacket("Invalid type previous_hash_responder")

        public_key_responder = values[10]
        if not isinstance(public_key_responder, str):
            raise DropPacket("Invalid type public_key_responder")

        signature_responder = values[11]
        if not isinstance(signature_responder, str):
            raise DropPacket("Invalid type signature_request")

        return \
            offset, placeholder.meta.payload.implement(up, down, total_up, total_down,
                                                       sequence_number_requester, previous_hash_requester,
                                                       public_key_requester, signature_requester,
                                                       sequence_number_responder, previous_hash_responder,
                                                       public_key_responder, signature_responder)