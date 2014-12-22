
from Tribler.dispersy.payload import Payload


class SignatureRequestPayload(Payload):
    """
    Payload for message to Request Signing a TimeStamp.
    """

    class Implementation(Payload.Implementation):

        def __init__(self, meta, timestamp, signature):
            """
            Creates the payload taking the timestamp from the system clock.
            """
            super(SignatureRequestPayload.Implementation, self).__init__(meta)

            self._timestamp = timestamp
            self._signature_requester = signature

        @property
        def timestamp(self):
            return self._timestamp

        @property
        def signature_requester(self):
            return self._signature_requester


class SignatureResponsePayload(Payload):
    """
    Payload for message that will respond to a Signature Request containing
    the Signature of {timestamp,signature_requester}.
    """

    class Implementation(Payload.Implementation):

        def __init__(self, meta, timestamp, signature_requester, signature):
            """
            Creates the payload containing the signature of {timestamp,signature_requester}
            by the recipient of the SignatureRequest.
            """
            super(SignatureResponsePayload.Implementation, self).__init__(meta)

            self._timestamp = timestamp
            self._signature_requester = signature_requester
            self._signature_responder = signature

        @property
        def timestamp(self):
            return self._timestamp

        @property
        def signature_requester(self):
            return self._signature_requester

        @property
        def signature_responder(self):
            return self._signature_responder