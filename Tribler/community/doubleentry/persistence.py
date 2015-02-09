__author__ = 'norberhuis'

GENESIS_ID = "GENESIS_ID"


class InMemoryDB:

    def __init__(self):
        self._dict = {}
        self._previous_id = GENESIS_ID

    def add_block(self, block_id, block):
        self._dict[block_id] = block
        self._previous_id = block_id

    @property
    def previous_id(self):
        return self._previous_id
