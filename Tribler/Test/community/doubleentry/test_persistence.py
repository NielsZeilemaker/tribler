import unittest
import os
import time
import random

from hashlib import sha1
from os import path

from Tribler.dispersy.crypto import ECCrypto

from Tribler.community.doubleentry.persistence import Persistence
from Tribler.community.doubleentry.persistence import GENESIS_ID
from Tribler.community.doubleentry.persistence import DATABASEPATH

from Tribler.dispersy.dispersydatabase import DispersyDatabase

class TestPersistence(unittest.TestCase):
    """
    Tests the Persister for DoubleEntry community.
    """

    def __init__(self, *args, **kwargs):
        super(TestPersistence, self).__init__(*args, **kwargs)
        self.public_key = "own_key"
        dispersy = TestDispersy()

        self.persistence = Persistence(dispersy)

    def tearDown(self):
        self.persistence.db.close()
        os.remove(path.join(os.path.dirname(os.path.abspath(__file__)), DATABASEPATH))

    def test_genesis_block(self):
        # Act
        result = self.persistence.get_previous_id()
        # Assert
        assert(result == GENESIS_ID)

    def test_add_block(self):
        # Arrange
        db = self.persistence
        block1 = TestBlock()
        # Act
        db.add_block(block1.id, block1)
        # Assert
        assert(db.get_previous_id() == block1.id)
        assert(db.get(block1.id).timestamp == block1.timestamp)

    def test_add_two_blocks(self):
        # Arrange
        db = self.persistence
        block1 = TestBlock()
        block2 = TestBlock()
        # Act
        db.add_block(block1.id, block1)
        db.add_block(block2.id, block2)
        # Assert
        assert(db.get_previous_id() == block2.id)
        assert(db.get(block2.id).timestamp == block2.timestamp)

    def test_contains_block_id_positive(self):
        # Arrange
        db = self.persistence
        block1 = TestBlock()
        db.add_block(block1.id, block1)
        # Assert & Act
        assert db.contains(block1.id)

    def test_contains_block_id_negative(self):
        # Arrange
        db = self.persistence
        # Assert & Act
        assert not db.contains("NONEXISTINGID")

    def test_contains_signature_pk_positive(self):
        # Arrange
        db = self.persistence
        block1 = TestBlock()
        db.add_block(block1.id, block1)
        # Assert & Act
        assert db.contains_signature(block1.signature_requester, block1.public_key_requester)

    def test_contains_signature_pk_false(self):
        # Arrange
        db = self.persistence
        block1 = TestBlock()
        # Assert & Act
        assert not db.contains_signature(block1.signature_requester, block1.public_key_requester)


class TestBlock:
    """
    Test Class that simulates a block message used in DoubleEntry.
    Also used in other test files for DoubleEntry.
    """

    def __init__(self):
        self._timestamp = time.time()
        crypto = ECCrypto()
        key_requester = crypto.generate_key(u"very-low")
        key_responder = crypto.generate_key(u"very-low")

        # A random hash is generated for the previous hash. It is only used to test if a hash can be persisted.
        self.previous_hash_requester = sha1(repr(random.randint(0, 100000))).digest()
        self.signature_requester = crypto.create_signature(key_requester, self.timestamp)
        self.public_key_requester = crypto.key_to_bin(key_requester.pub())

        # A random hash is generated for the previous hash. It is only used to test if a hash can be persisted.
        self.previous_hash_responder = sha1(repr(random.randint(100001, 200000))).digest()
        self.signature_responder = crypto.create_signature(key_responder, self.timestamp)
        self.public_key_responder = crypto.key_to_bin(key_responder.pub())


    @property
    def id(self):
        return self.generate_hash()

    @property
    def timestamp(self):
        return repr(self._timestamp)

    def generate_hash(self):
        # Explicit way of building the data for the hash is used.
        # This because it is used to validate a test result in test_community
        # and it is easier to read for the programmer this way.
        data = self.timestamp + "." + self.previous_hash_requester + "." + self.public_key_requester + "." + self.signature_requester + "." + self. previous_hash_responder + "." + self.public_key_responder + "." + self.signature_responder
        return sha1(data).digest()


class TestDispersy:

    working_directory = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        database_filename = u"test.db"
        database_directory = os.path.join(self.working_directory, u"sqlite")
        if not os.path.isdir(database_directory):
            os.makedirs(database_directory)
        database_filename = os.path.join(database_directory, database_filename)
        self.database = DispersyDatabase(database_filename)

    def close_database(self):
        self.database.close(False)

if __name__ == "__main__":
    unittest.main()