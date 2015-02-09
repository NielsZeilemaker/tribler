
from Tribler.dispersy.payload import Payload


class SignatureRequestPayload(Payload):
    """
    Payload for message to Request Signing a TimeStamp.
    """

    class Implementation(Payload.Implementation):

        def __init__(self, meta, timestamp, previous_hash, public_key, signature):
            """
            Creates the payload taking the timestamp from the system clock.
            """
            super(SignatureRequestPayload.Implementation, self).__init__(meta)

            self._timestamp = timestamp
            self._previous_hash_requester = previous_hash
            self._public_key_requester = public_key
            self._signature_requester = signature

        @property
        def timestamp(self):
            return self._timestamp

        @property
        def previous_hash_requester(self):
            return self._previous_hash_requester

        @property
        def public_key_requester(self):
            return self._public_key_requester

        @property
        def signature_requester(self):
            return self._signature_requester


class SignatureResponsePayload(Payload):
    """
    Payload for message that will respond to a Signature Request containing
    the Signature of {timestamp,signature_requester}.
    """

    class Implementation(Payload.Implementation):

        def __init__(self, meta, timestamp, public_key_requester, signature_requester, public_key_responder, signature):
            """
            Creates the payload containing the signature of {timestamp,signature_requester}
            by the recipient of the SignatureRequest.
            """
            super(SignatureResponsePayload.Implementation, self).__init__(meta)

            self._timestamp = timestamp
            self._public_key_requester = public_key_requester
            self._signature_requester = signature_requester

            self._public_key_responder = public_key_responder
            self._signature_responder = signature

        @property
        def timestamp(self):
            return self._timestamp

        @property
        def public_key_requester(self):
            return self._public_key_requester

        @property
        def signature_requester(self):
            return self._signature_requester

        @property
        def public_key_responder(self):
            return self._public_key_responder

        @property
        def signature_responder(self):
            return self._signature_responder