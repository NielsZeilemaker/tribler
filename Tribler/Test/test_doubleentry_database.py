import unittest
import os
import random

from Tribler.Test.test_doubleentry_utilities import TestBlock, DoubleEntryTestCase
from Tribler.community.doubleentry.database import DoubleEntryDB
from Tribler.community.doubleentry.database import GENESIS_ID, DATABASE_DIRECTORY, DATABASE_PATH
from Tribler.community.doubleentry.database import encode_db, decode_db


class TestEncodingDatabase(unittest.TestCase):
    """
    Test the encoding methods for the database.
    """

    def test_encoding_decoding_int(self):
        # Arrange
        integer = random.randint(0, 20)
        # Act
        result = decode_db(encode_db(integer))
        # Assert
        self.assertEquals(integer, result)

    def test_encoding_decoding_str(self):
        # Arrange
        string = "test string"
        # Act
        result = decode_db(encode_db(string))
        # Assert
        self.assertEquals(string, result)

    def test_encoding_unknown_type(self):
        # Arrange
        unknown_type = complex(random.randint(0, 20))
        # Act
        self.assertRaises(TypeError, encode_db, unknown_type)


class TestDatabase(DoubleEntryTestCase):
    """
    Tests the Database for DoubleEntry community.
    """

    def __init__(self, *args, **kwargs):
        super(TestDatabase, self).__init__(*args, **kwargs)

        self.public_key = "own_key"
        self.persistence = None

    def setUp(self, **kwargs):
        super(TestDatabase, self).setUp(**kwargs)
        path = os.path.join(self.getStateDir(), DATABASE_DIRECTORY)
        if not os.path.exists(path):
            os.makedirs(path)
        self.persistence = DoubleEntryDB(self.getStateDir())

    def tearDown(self, **kwargs):
        self.persistence.close()
        os.remove(os.path.join(self.getStateDir(), DATABASE_PATH))
        os.rmdir(os.path.join(self.getStateDir(), DATABASE_DIRECTORY))

    def test_genesis_block(self):
        # Act
        result = self.persistence.get_previous_id()
        # Assert
        self.assertEquals(result, GENESIS_ID)

    def test_add_block(self):
        # Arrange
        db = self.persistence
        block1 = TestBlock()
        # Act
        db.add_block(block1.id, block1)
        # Assert
        self.assertEquals(db.get_previous_id(), block1.id)
        result = db.get(block1.id)

    def test_add_two_blocks(self):
        # Arrange
        db = self.persistence
        block1 = TestBlock()
        block2 = TestBlock()
        # Act
        db.add_block(block1.id, block1)
        db.add_block(block2.id, block2)
        # Assert
        self.assertEquals(db.get_previous_id(), block2.id)
        result = db.get(block2.id)
        super(TestDatabase, self).assertEqual_block(block2, result)

    def test_contains_block_id_positive(self):
        # Arrange
        db = self.persistence
        block1 = TestBlock()
        db.add_block(block1.id, block1)
        # Act & Assert
        self.assertTrue(db.contains(block1.id))

    def test_contains_block_id_negative(self):
        # Arrange
        db = self.persistence
        # Act & Assert
        self.assertFalse(db.contains("NON EXISTING ID"))

    def test_contains_signature_pk_positive(self):
        # Arrange
        db = self.persistence
        block1 = TestBlock()
        db.add_block(block1.id, block1)
        # Act & Assert
        self.assertTrue(db.contains_signature(block1.signature_requester, block1.public_key_requester))

    def test_contains_signature_pk_false(self):
        # Arrange
        db = self.persistence
        block1 = TestBlock()
        # Act & Assert
        self.assertFalse(db.contains_signature(block1.signature_requester, block1.public_key_requester))

    def test_get_sequence_number_not_existing(self):
        # Arrange
        db = self.persistence
        # Act & Assert
        self.assertEquals(db.get_latest_sequence_number("NON EXISTING KEY"), -1)

    def test_get_sequence_number_public_key_requester(self):
        # Arrange
        # Make sure that there is a responder block with a lower sequence number.
        # To test that it will look for both responder and requester.
        db = self.persistence
        block1 = TestBlock()
        db.add_block(block1.id, block1)
        block2 = TestBlock()
        block2.public_key_responder = block1.public_key_requester
        block2.sequence_number_responder = block1.sequence_number_requester-5
        db.add_block(block2.id, block2)
        # Act & Assert
        self.assertEquals(db.get_latest_sequence_number(block1.public_key_requester), block1.sequence_number_requester)

    def test_get_sequence_number_public_key_responder(self):
        # Arrange
        # Make sure that there is a requester block with a lower sequence number.
        # To test that it will look for both responder and requester.
        db = self.persistence
        block1 = TestBlock()
        db.add_block(block1.id, block1)
        block2 = TestBlock()
        block2.public_key_requester = block1.public_key_responder
        block2.sequence_number_requester = block1.sequence_number_responder-5
        db.add_block(block2.id, block2)
        # Act & Assert
        self.assertEquals(db.get_latest_sequence_number(block1.public_key_responder), block1.sequence_number_responder)


if __name__ == '__main__':
    unittest.main()