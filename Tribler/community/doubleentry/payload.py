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
            Signs the timestamp and saves the signature in signatureInitiator.
            :param ec: Elliptic Curve Key Object to be used to sign the timestamp.
            :return:
            """

            crypto = ECCrypto()
            # Convert the timestamp to str.
            data = repr(self.timestamp)
            self.signatureInitiator = crypto.create_signature(ec, data)