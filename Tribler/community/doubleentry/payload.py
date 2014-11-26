__author__ = 'norberhuis'

import time

from Tribler.dispersy.payload import Payload
from Tribler.dispersy.crypto import ECCrypto


class RequestSignature(Payload):
    """
    Payload for message to Request Signing a TimeStamp.
    """

    class Implementation(Payload.Implementation):

        def __init__(self, ec):
            """
            Creates the payload taking the timestamp from the system clock.
            :param ec: Elliptic Curve Key Object to be used to sign the timestamp
            """
            # Get the current timestamp.
            self.timestamp = time.time()

            # Sign the timestamp
            self._sign_timestamp(ec)

        def _sign_timestamp(self, ec):
            """
            Signs the timestamp and saves the signature in signatureRequester.
            :param ec: Elliptic Curve Key Object to be used to sign the timestamp.
            :return:
            """
            crypto = ECCrypto()
            # Convert the timestamp to str.
            data = repr(self.timestamp)
            self.signatureRequester = crypto.create_signature(ec, data)


class SignatureResponse(Payload):
    """
    Payload for message that will respond to a Signature Request containing
    the Signature of {timestamp,signature_requester}.
    """

    class Implementation(Payload.Implementation):

        def __init__(self, ec, request):
            """
            Creates the payload containing the signature of {timestamp,signature_requester}
            by the recipient of the SignatureRequest.
            :param ec: Elliptic Curve Key Object to be used to sign the timestamp
            :param request: original SignatureRequest.
            """
            crypto = ECCrypto()
            # Convert the timestamp to str and concatenate the requester signature
            data = repr(request.timestamp) + request.signatureRequester
            self.signatureResponder = crypto.create_signature(ec, data)