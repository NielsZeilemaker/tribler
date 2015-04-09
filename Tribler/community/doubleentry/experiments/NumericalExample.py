from Tribler.dispersy.crypto import ECCrypto
"""
File containing experiments
"""


class NumericalExample:

    def __init__(self, double_entry_community):
        self._community = double_entry_community

    def perform_experiment(self):
        self.save_key_to_file(self._community.get_key())

        message = self._community.create_signature_request_message()

        self.save_payload_to_file(message.payload.timestamp)
        self.save_signature_to_file(message.payload.signature_requester)

    @staticmethod
    def save_key_to_file(ec):
        pem = ECCrypto().key_to_pem(ec)
        f = open("key.pem", 'w')
        f.write(pem)
        f.close()

    @staticmethod
    def save_payload_to_file(payload):
        f = open("payload", 'w')
        f.write(payload)
        f.close()

    @staticmethod
    def save_signature_to_file(signature):
        f = open("signature", 'w')
        f.write(signature)
        f.close()







