__author__ = 'norberhuis'

import time

from Tribler.dispersy.payload import Payload
from Tribler.dispersy.crypto import ECCrypto


class RequestSignature(Payload):

    class Implementation(Payload.Implementation):

        def __init__(self, ec):
            # Get the current timestamp.
            self.timestamp = time.time()

            # Sign the timestamp
            self._sign_timestamp(ec)

        def _sign_timestamp(self, ec):
            crypto = ECCrypto()
            # Convert the timestamp to str.
            data = repr(self.timestamp)
            self.signatureInitiator = crypto.create_signature(ec, data)