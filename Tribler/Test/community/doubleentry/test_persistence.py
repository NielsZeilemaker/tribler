import unittest

from hashlib import sha1
from hashlib import sha224
from hashlib import sha256

from Tribler.community.doubleentry.persistence import InMemoryDB
from Tribler.community.doubleentry.persistence import GENESIS_ID


class TestInMemoryDB(unittest.TestCase):
    """
    Tests the Persister for DoubleEntry community.
    """

    public_key = "own_key"

    @staticmethod
    def test_genesis_block():
        # Act
        result = InMemoryDB(TestInMemoryDB.public_key).previous_id
        # Assert
        assert(result == GENESIS_ID)

    def test_add_block(self):
        # Arrange
        db = InMemoryDB(TestInMemoryDB.public_key)
        block1 = TestBlock("123")
        # Act
        db.add_block(block1.id, block1)
        # Assert
        assert(db.previous_id == block1.id)
        assert(db.get(block1.id).payload.timestamp == block1.payload.timestamp)

    def test_add_two_blocks(self):
        # Arrange
        db = InMemoryDB(TestInMemoryDB.public_key)
        block1 = TestBlock("123")
        block2 = TestBlock("345")
        # Act
        db.add_block(block1.id, block1)
        db.add_block(block2.id, block2)
        # Assert
        assert(db.previous_id == block2.id)
        assert(db.get(block2.id).payload.timestamp == block2.payload.timestamp)

    def test_contains_block_id_positive(self):
        # Arrange
        db = InMemoryDB(TestInMemoryDB.public_key)
        block1 = TestBlock("123")
        db.add_block(block1.id, block1)
        # Assert & Act
        assert db.contains(block1.id)

    def test_contains_block_id_negative(self):
        # Arrange
        db = InMemoryDB(TestInMemoryDB.public_key)
        # Assert & Act
        assert not db.contains(sha1("123"))

    def test_contains_signature_pk_positive(self):
        # Arrange
        db = InMemoryDB(TestInMemoryDB.public_key)
        block1 = TestBlock("123")
        db.add_block(block1.id, block1)
        # Assert & Act
        assert db.contains_signature(block1.payload.signature_requester, block1.payload.public_key_requester)


    def test_contains_signature_pk_false(self):
        # Arrange
        db = InMemoryDB(TestInMemoryDB.public_key)
        block1 = TestBlock("123")
        # Assert & Act
        assert not db.contains_signature(block1.payload.signature_requester, block1.payload.public_key_requester)


class TestBlock:

    def __init__(self, payload):
        self.payload = TestPayload(payload, sha224(payload), sha256(payload))
        self.id = sha1(payload)


class TestPayload:

    def __init__(self, timestamp, signature_requester, public_key_requester):
        self.timestamp = timestamp
        self.signature_requester = signature_requester
        self.public_key_requester = public_key_requester


if __name__ == "__main__":
    unittest.main()