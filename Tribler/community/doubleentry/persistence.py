import base64

GENESIS_ID = "GENESIS_ID"


class InMemoryDB:

    def __init__(self, public_key):
        self._hash_dict = {}
        self._signature_dict = {}
        self._previous_id = GENESIS_ID
        self._pk = public_key

    def add_block(self, block_id, block):
        self._hash_dict[block_id] = block
        self._signature_dict[(block.payload.signature_requester, block.payload.public_key_requester)] = block_id
        self._previous_id = block_id

    @property
    def previous_id(self):
        return self._previous_id

    def get(self, block_id):
        return self._hash_dict[block_id]

    def get_keys(self):
        return self._hash_dict.keys()

    def contains(self, block_id):
        return block_id in self._hash_dict

    def contains_signature(self, signature_requester, public_key_requester):
        return (signature_requester, public_key_requester) in self._signature_dict

    def toString(self):
        result = "Headnode:"
        node_id = self._previous_id
        while node_id != GENESIS_ID:
            node = self._hash_dict[node_id]
            result += base64.encodestring(node_id[:5]) + ":\n" + \
                      "req = " + base64.encodestring(node.payload.public_key_requester[:5]) + "\n" + \
                      "res = " + base64.encodestring(node.payload.public_key_responder[:5]) + "\n" + \
                      "||\n"
            if node.payload.public_key_responder:
                node_id = node.payload.previous_hash_responder
            else:
                node_id = node.payload.previous_hash_requester

        result += "GENESIS_BLOCK"
        return result





