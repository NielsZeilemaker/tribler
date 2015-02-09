__author__ = 'norberhuis'

GENESIS_ID = "GENESIS_ID"


class InMemoryDB:

    def __init__(self):
        self._hash_dict = {}
        self._signature_dict = {}
        self._previous_id = GENESIS_ID

    def add_block(self, block_id, block):
        self._hash_dict[block_id] = block
        self._hash_dict[block.payload.signature_requester] = block_id
        self._previous_id = block_id

    @property
    def previous_id(self):
        return self._previous_id

    def get(self, block_id):
        return self._hash_dict[block_id]

    def contains(self, block_id):
        return block_id in self._hash_dict