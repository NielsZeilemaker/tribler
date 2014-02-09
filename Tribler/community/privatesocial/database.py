from os import path
from time import time
from binascii import hexlify
from Tribler.dispersy.database import Database

LATEST_VERSION = 1

schema = u"""
CREATE TABLE friendsync(
 sync_id integer PRIMARY KEY,
 global_time integer,
 keyhash text
);

CREATE TABLE friends(
 id integer PRIMARY KEY AUTOINCREMENT NOT NULL,
 name text,
 key text,
 keyhash text
 );
 
 CREATE TABLE my_keys(
 id integer PRIMARY KEY AUTOINCREMENT NOT NULL,
 key text,
 keyhash text,
 inserted real
 );
 
CREATE TABLE option(key TEXT PRIMARY KEY, value BLOB);
INSERT INTO option(key, value) VALUES('database_version', '""" + str(LATEST_VERSION) + """');
"""

class FriendDatabase(Database):
    if __debug__:
        __doc__ = schema

    def __init__(self, dispersy):
        self._dispersy = dispersy

        if self._dispersy._database._file_path == u":memory:":
            super(FriendDatabase, self).__init__(u":memory:")
        else:
            super(FriendDatabase, self).__init__(path.join(dispersy.working_directory, u"sqlite", u"friendsync.db"))

    def open(self):
        self._dispersy.database.attach_commit_callback(self.commit)
        return super(FriendDatabase, self).open()

    def close(self, commit=True):
        self._dispersy.database.detach_commit_callback(self.commit)
        return super(FriendDatabase, self).close(commit)

    def check_database(self, database_version):
        assert isinstance(database_version, unicode)
        assert database_version.isdigit()
        assert int(database_version) >= 0
        database_version = int(database_version)

        # setup new database with current database_version
        if database_version < 1:
            self.executescript(schema)
            self.commit()

        else:
            # upgrade to version 2
            if database_version < 2:
                # there is no version 2 yet...
                # if __debug__: dprint("upgrade database ", database_version, " -> ", 2)
                # self.executescript(u"""UPDATE option SET value = '2' WHERE key = 'database_version';""")
                # self.commit()
                # if __debug__: dprint("upgrade database ", database_version, " -> ", 2, " (done)")
                pass

        return LATEST_VERSION

    def get_database_stats(self):
        stats_dict = {}

        for tablename, in list(self.execute(u'SELECT name FROM sqlite_master WHERE type = "table"')):
            count, = self.execute(u"SELECT COUNT(*) FROM " + tablename).next()
            stats_dict[str(tablename)] = count
        return stats_dict

    def add_message(self, sync_id, global_time, keyhash):
        _keyhash = buffer(str(keyhash))
        self.execute(u"INSERT INTO friendsync (sync_id, global_time, keyhash) VALUES (?,?,?) ", (sync_id, global_time, _keyhash))

    def add_friend(self, name, key, keyhash):
        _name = unicode(name)
        _key = buffer(self._dispersy.crypto.key_to_bin(key.pub()))
        _keyhash = buffer(str(keyhash))
        self.execute(u"INSERT INTO friends (name, key, keyhash) VALUES (?,?,?)", (_name, _key, _keyhash))

    def get_friend(self, name):
        return self._converted_keys(self.execute(u"SELECT id, key, keyhash FROM friends WHERE name = ?", (unicode(name),))).next()

    def get_friend_by_hash(self, keyhash):
        _keyhash = buffer(str(keyhash))
        return self._converted_keys(self.execute(u"SELECT id, key, keyhash FROM friends WHERE keyhash = ?", (_keyhash,))).next()

    def get_friend_keys(self):
        return list(self._converted_keys(self.execute(u"SELECT name, key, keyhash FROM friends")))

    def add_my_key(self, key, keyhash):
        _key = buffer(self._dispersy.crypto.key_to_bin(key))
        _keyhash = buffer(str(keyhash))
        self.execute(u"INSERT INTO my_keys (key, keyhash, inserted) VALUES (?,?,?)", (_key, _keyhash, time()))

    def get_my_keys(self):
        return list(self._converted_keys(self.execute(u"SELECT key, keyhash FROM my_keys ORDER BY inserted DESC"), mykeys=True))

    def _converted_keys(self, keylist, mykeys=False):
        did_yield = False
        for keytuple in keylist:
            if len(keytuple) == 3:
                yield keytuple[0], (self._dispersy.crypto.key_from_private_bin(str(keytuple[1])) if mykeys else self._dispersy.crypto.key_from_public_bin(str(keytuple[1]))), long(str(keytuple[2]))
            else:
                yield (self._dispersy.crypto.key_from_private_bin(str(keytuple[0])) if mykeys else self._dispersy.crypto.key_from_public_bin(str(keytuple[0]))), long(str(keytuple[1]))
            did_yield = True

        if not did_yield:
            yield None, None

LATEST_TEXT_VERSION = 1

textschema = u"""
CREATE TABLE posts(
 from_id integer,
 header text,
 message text
)
CREATE TABLE option(key TEXT PRIMARY KEY, value BLOB);
INSERT INTO option(key, value) VALUES('database_version', '""" + str(LATEST_TEXT_VERSION) + """');
"""
class TextDatabase(Database):
    if __debug__:
        __doc__ = textschema

    def __init__(self, dispersy, friend_db):
        self._dispersy = dispersy
        self._friend_db = friend_db

        if self._dispersy._database._file_path == u":memory:":
            super(TextDatabase, self).__init__(u":memory:")
        else:
            super(TextDatabase, self).__init__(path.join(dispersy.working_directory, u"sqlite", u"textsync.db"))

    def open(self):
        self._dispersy.database.attach_commit_callback(self.commit)
        return super(TextDatabase, self).open()

    def close(self, commit=True):
        self._dispersy.database.detach_commit_callback(self.commit)
        return super(TextDatabase, self).close(commit)

    def check_database(self, database_version):
        assert isinstance(database_version, unicode)
        assert database_version.isdigit()
        assert int(database_version) >= 0
        database_version = int(database_version)

        # setup new database with current database_version
        if database_version < 1:
            self.executescript(textschema)
            self.commit()

        else:
            # upgrade to version 2
            if database_version < 2:
                # there is no version 2 yet...
                # if __debug__: dprint("upgrade database ", database_version, " -> ", 2)
                # self.executescript(u"""UPDATE option SET value = '2' WHERE key = 'database_version';""")
                # self.commit()
                # if __debug__: dprint("upgrade database ", database_version, " -> ", 2, " (done)")
                pass

        return LATEST_TEXT_VERSION

    def add_message(self, friendmid, text):
        #mids are sha1(asfasf).digest(), we need to convert them to hex and then long
        friendkeyhash = long(hexlify(friendmid),16)
        friend_id,_,_ = self._friend_db.get_friend_by_hash(friendkeyhash)
        
        if text.startswith('/'):
            if text.startswith('/post'):
                _,header,message = text.split(' ', 2)
                
                header = unicode(header)
                message = unicode(message)
                self.execute(u"INSERT INTO posts (from_id, header, message) VALUES (?,?,?)", (friend_id, header, message)