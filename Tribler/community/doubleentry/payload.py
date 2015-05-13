from Tribler.dispersy.payload import Payload


class SignatureRequestPayload(Payload):
    """
    Payload for message to Request Signing a TimeStamp.
    """

    class Implementation(Payload.Implementation):
        def __init__(self, meta, up, down, total_up, total_down,
                     sequence_number_requester, previous_hash, public_key, signature):
            """
            Creates the payload taking the timestamp from the system clock.
            """
            super(SignatureRequestPayload.Implementation, self).__init__(meta)

            self._up = up
            self._down = down
            self._total_up = total_up
            self._total_down = total_down

            self._sequence_number_requester = sequence_number_requester
            self._previous_hash_requester = previous_hash
            self._public_key_requester = public_key
            self._signature_requester = signature

        @property
        def up(self):
            return self._up

        @property
        def down(self):
            return self._down

        @property
        def total_up(self):
            return self._total_up

        @property
        def total_down(self):
            return self._total_down

        @property
        def sequence_number_requester(self):
            return self._sequence_number_requester

        @property
        def previous_hash_requester(self):
            return self._previous_hash_requester

        @property
        def public_key_requester(self):
            return self._public_key_requester

        @property
        def signature_requester(self):
            return self._signature_requester

        def signature_data_requester(self):
            return encode_signing_format(
                (self._up, self._down, self.total_up, self.total_down, self._sequence_number_requester,
                 self.previous_hash_requester, self._public_key_requester))


class SignatureResponsePayload(Payload):
    """
    Payload for message that will respond to a Signature Request containing
    the Signature of {timestamp,signature_requester}.
    """

    class Implementation(Payload.Implementation):
        def __init__(self, meta, up, down, total_up, total_down, sequence_number_requester,
                     previous_hash_requester, public_key_requester, signature_requester,
                     sequence_number_responder, previous_hash_responder, public_key_responder, signature_responder):
            """
            Creates the payload containing the signature of {timestamp,signature_requester}
            by the recipient of the SignatureRequest.
            """
            super(SignatureResponsePayload.Implementation, self).__init__(meta)

            self._up = up
            self._down = down
            self._total_up = total_up
            self._total_down = total_down
            """ Set the partial signature of the requester in the payload of the message."""
            self._sequence_number_requester = sequence_number_requester
            self._previous_hash_requester = previous_hash_requester
            self._public_key_requester = public_key_requester
            self._signature_requester = signature_requester
            """ Set the partial signature of the responder in the payload of the message."""
            self._sequence_number_responder = sequence_number_responder
            self._previous_hash_responder = previous_hash_responder
            self._public_key_responder = public_key_responder
            self._signature_responder = signature_responder

        @property
        def up(self):
            return self._up

        @property
        def down(self):
            return self._down

        @property
        def total_up(self):
            return self._total_up

        @property
        def total_down(self):
            return self._total_down

        @property
        def sequence_number_requester(self):
            return self._sequence_number_requester

        @property
        def previous_hash_requester(self):
            return self._previous_hash_requester

        @property
        def public_key_requester(self):
            return self._public_key_requester

        @property
        def signature_requester(self):
            return self._signature_requester

        @property
        def sequence_number_responder(self):
            return self._sequence_number_responder

        @property
        def previous_hash_responder(self):
            return self._previous_hash_responder

        @property
        def public_key_responder(self):
            return self._public_key_responder

        @property
        def signature_responder(self):
            return self._signature_responder

        def signature_data_requester(self):
            return encode_signing_format(
                (self._up, self._down, self.total_up, self.total_down, self.sequence_number_requester,
                 self.previous_hash_requester, self._public_key_requester))

        def signature_data_responder(self):
            return encode_signing_format(
                (self._up, self._down, self.total_up, self.total_down, self._sequence_number_requester,
                 self.previous_hash_requester, self._public_key_requester, self.signature_requester,
                 self._sequence_number_responder, self._previous_hash_responder, self._public_key_responder))


def encode_signing_format(data):
    """
    Prepare a iterable for singing.
    :param data: Iterable with objects transformable to string
    :return: string to be signed containing the data.
    """
    return ".".join(map(str, data))