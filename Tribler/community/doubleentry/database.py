""" This file contains everything related to persistence for DoubleEntry.
"""
import base64

from os import path

from Tribler.dispersy.database import Database


def encode_db(string):
    """ Encodes a string in database encoding"""
    return unicode(base64.encodestring(string))


def decode_db(string):
    """ Decodes a string in database encoding"""
    return base64.decodestring(string.encode('ascii', 'replace'))

""" Path to the database location + dispersy._workingdirectory"""
DATABASE_PATH = path.join(u"sqlite", u"doubleentry.db")
""" ID of the first block of the chain. """
GENESIS_ID = "GENESIS_ID"
""" Version to keep track if the db schema needs to be updated."""
LATEST_DB_VERSION = 1
""" Schema for the DoubleEntry DB."""
schema = u"""
CREATE TABLE IF NOT EXISTS double_entry(
 block_hash			        text PRIMARY KEY,
 previous_hash_requester	text NOT NULL,
 public_key_requester		text NOT NULL,
 signature_requester		text NOT NULL,
 previous_hash_responder	text NOT NULL,
 public_key_responder		text NOT NULL,
 signature_responder		text NOT NULL,
 payload			        text NOT NULL
);

CREATE TABLE option(key TEXT PRIMARY KEY, value BLOB);
INSERT INTO option(key, value) VALUES('database_version', '""" + str(LATEST_DB_VERSION) + u"""');
INSERT INTO option(key, value) VALUES('previous_id', '""" + encode_db(GENESIS_ID) + u"""');
"""

cleanup = u"DELETE FROM double_entry;" \
          u"UPDATE `option` SET value = '" + encode_db(GENESIS_ID) + \
          u"' WHERE key == 'previous_id';"


class Persistence:
    """
    Persistence layer for the DoubleEntry Community.
    """
    def __init__(self, working_directory):
        """
        Sets up the persistence layer ready for use.
        :param working_directory: Path to the working directory
        that will contain the the db at workingdirectory/DATABASE_PATH
        :return:
        """
        self._working_directory = working_directory
        self.db = None

    def add_block(self, block_id, block):
        """
        Persist a block under a block_id
        :param block_id: The ID the block is saved under. This is the hash of the block.
        :param block: The data that will be saved.
        """
        self._init_database()
        data = tuple(map(encode_db,
                         (block_id,
                          block.previous_hash_requester, block.public_key_requester, block.signature_requester,
                          block.previous_hash_responder, block.public_key_responder, block.signature_responder,
                          block.timestamp)))

        self.db.execute(
            u"INSERT INTO double_entry (block_hash, previous_hash_requester, public_key_requester, "
            u"signature_requester, previous_hash_responder, public_key_responder, signature_responder, payload) "
            u"values(?,?,?,?,?,?,?,?)",
            data)

        self._set_previous_id(block_id)

    def _set_previous_id(self, block_id):
        """
        Update the id of the latest block chain.
        :param block_id: The id of the block
        """
        self._init_database()
        self.db.execute(u"UPDATE `option` SET value = '" + encode_db(block_id) +
                        u"' WHERE key == 'previous_id';")

    def get_previous_id(self):
        """
        Get the id of the latest block in the chain.
        :return: block_id
        """
        self._init_database()

        db_result = self.db.execute(u"SELECT value FROM `option`  WHERE key == 'previous_id' LIMIT 0,1").fetchone()[0]

        return decode_db(db_result)

    def get(self, block_id):
        """
        Returns a block saved in the persistence
        :param block_id: The id of the block that needs to be retrieved.
        :return:
        """
        self._init_database()

        db_result = self.db.execute(u"SELECT previous_hash_requester, public_key_requester, signature_requester,"
                                    u" previous_hash_responder, public_key_responder, signature_responder, payload"
                                    u" FROM `double_entry` WHERE block_hash = '" +
                                    encode_db(block_id) + u"' LIMIT 0,1").fetchone()
        # Decode the DB format and create a DB block
        return DatabaseBlock([decode_db(x) for x in db_result])

    def get_ids(self):
        """
        Get all the IDs saved in the persistence layer.
        :return: list of ids.
        """
        self._init_database()

        db_result = self.db.execute(u"SELECT block_hash from double_entry").fetchall()
        # Unpack the db_result tuples and decode the results.
        return [decode_db(x[0]) for x in db_result]

    def contains(self, block_id):
        """
        Check if a block is existent in the persistence layer.
        :param block_id: The id t hat needs to be checked.
        :return: True if the block exists, else false.
        """
        self._init_database()

        db_result = self.db.execute(u"SELECT block_hash from double_entry where block_hash == '" +
                                    encode_db(block_id) + u"' LIMIT 0,1").fetchone()
        return db_result is not None

    def contains_signature(self, signature_requester, public_key_requester):
        """
        Check if a block is existent in the persistence layer based on a signature and public key pair.
        :param signature_requester: The id t hat needs to be checked.
        :return: True if the block exists, else false.
        """
        self._init_database()

        db_result = self.db.execute(u"SELECT block_hash from double_entry "
                                    u"where public_key_requester = '" + encode_db(public_key_requester) +
                                    u"' and signature_requester == '" + encode_db(signature_requester) +
                                    u"' LIMIT 0,1").fetchone()
        return db_result is not None

    def _init_database(self):
        """
        :return: Initiate the database and setup the connection.
        """
        if self.db is None:
            self.db = DoubleEntryDB(self._working_directory)
            self.db.open()

    def close(self):
        """
        Close the persistence
        """
        if self.db:
            self.db.close()


class DoubleEntryDB(Database):
    """ Connection layer to SQLiteDB.
    Ensures a proper DB schema on startup.
    """

    def __init__(self, working_directory):
        super(DoubleEntryDB, self).__init__(path.join(working_directory, DATABASE_PATH))

    def open(self, initial_statements=True, prepare_visioning=True):
        return super(DoubleEntryDB, self).open(initial_statements, prepare_visioning)

    def close(self, commit=True):
        return super(DoubleEntryDB, self).close(commit)

    def cleanup(self):
        self.executescript(cleanup)

    def check_database(self, database_version):
        """
        Ensure the proper schema is used by the database.
        :param database_version: Current version of the database.
        :return:
        """
        assert isinstance(database_version, unicode)
        assert database_version.isdigit()
        assert int(database_version) >= 0
        database_version = int(database_version)

        if database_version < 1:
            self.executescript(schema)
            self.commit()

        return LATEST_DB_VERSION


class DatabaseBlock:
    """ DataClass for a block that comes out of the DB.
    """

    def __init__(self, data):
        """ Set the partial signature of the requester of the block."""
        self.previous_hash_requester = data[0]
        self.public_key_requester = data[1]
        self.signature_requester = data[2]
        """ Set the partial signature of the responder of the block."""
        self.previous_hash_responder = data[3]
        self.public_key_responder = data[4]
        self.signature_responder = data[5]
        """ Set the payload of the block """
        self.timestamp = data[6]