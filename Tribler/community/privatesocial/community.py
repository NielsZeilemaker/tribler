# Written by Niels Zeilemaker
import sys

from conversion import SocialConversion
from payload import TextPayload
from collections import defaultdict
from hashlib import sha1
from binascii import hexlify
from time import time
from random import sample, shuffle

from Tribler.dispersy.authentication import MemberAuthentication, \
    NoAuthentication
from Tribler.dispersy.community import Community
from Tribler.dispersy.conversion import DefaultConversion
from Tribler.dispersy.destination import CandidateDestination, \
    CommunityDestination
from Tribler.dispersy.distribution import FullSyncDistribution
from Tribler.dispersy.message import Message
from Tribler.dispersy.resolution import PublicResolution
from Tribler.dispersy.tool.lencoder import log
from Tribler.community.privatesocial.payload import EncryptedPayload
from Tribler.community.privatesemantic.community import PoliForwardCommunity, \
    HForwardCommunity, PForwardCommunity, ForwardCommunity, \
    TasteBuddy

from random import choice
from Tribler.dispersy.member import Member
from database import FriendDatabase
from Tribler.community.privatesemantic.conversion import long_to_bytes
from Tribler.community.privatesemantic.crypto.ecutils import OpenSSLCurves
from Tribler.community.privatesemantic.crypto.ecelgamal import encrypt_str
from Tribler.community.privatesemantic.crypto.elgamalcrypto import ElgamalCrypto
from Tribler.community.privatesocial.database import TextDatabase

DEBUG = False
DEBUG_VERBOSE = False
ENCRYPTION = True

class SocialCommunity(Community):
    
    @classmethod
    def get_master_members(cls, dispersy):
#generated: Sun Feb 09 17:09:18 2014
#curve: NID_sect571r1
#len: 571 bits ~ 144 bytes signature
#pub: 170 3081a7301006072a8648ce3d020106052b810400270381920004054fe4cf46de9e1b9fb3b64d91a3319b0c68e136a7ea87acb0b989e7637310c1f1e45db6c74d8207fa9da9cae937de9eb32ef96d97513cd586ce623f940b9895744bc4e40aea12ca046edcac02b1e9f850ee55a7195cecee8783012fdf1f0fd24dc501c4d99cedafa677fd494a01c04eefca8b52e87e3a99160009449bfe6baad88230b4e7445df60b9f2f2ee9f16b6a
#pub-sha1 b9b0c066db8351d5e222a7859d8cc48709f20d55
#-----BEGIN PUBLIC KEY-----
#MIGnMBAGByqGSM49AgEGBSuBBAAnA4GSAAQFT+TPRt6eG5+ztk2RozGbDGjhNqfq
#h6ywuYnnY3MQwfHkXbbHTYIH+p2pyuk33p6zLvltl1E81YbOYj+UC5iVdEvE5Arq
#EsoEbtysArHp+FDuVacZXOzuh4MBL98fD9JNxQHE2Zztr6Z3/UlKAcBO78qLUuh+
#OpkWAAlEm/5rqtiCMLTnRF32C58vLunxa2o=
#-----END PUBLIC KEY-----
        master_key = "3081a7301006072a8648ce3d020106052b810400270381920004054fe4cf46de9e1b9fb3b64d91a3319b0c68e136a7ea87acb0b989e7637310c1f1e45db6c74d8207fa9da9cae937de9eb32ef96d97513cd586ce623f940b9895744bc4e40aea12ca046edcac02b1e9f850ee55a7195cecee8783012fdf1f0fd24dc501c4d99cedafa677fd494a01c04eefca8b52e87e3a99160009449bfe6baad88230b4e7445df60b9f2f2ee9f16b6a".decode("HEX")
        master = dispersy.get_member(master_key)
        return [master]
    
    def __init__(self, dispersy, master, integrate_with_tribler=True, encryption=ENCRYPTION, log_text=None):
        assert isinstance(dispersy.crypto, ElgamalCrypto)

        super(SocialCommunity, self).__init__(dispersy, master)
        self.integrate_with_tribler = integrate_with_tribler
        self.encryption = bool(encryption)
        self.log_text = log_text

        self._friend_db = FriendDatabase(dispersy)
        self._friend_db.open()
        
        self._text_db = TextDatabase(dispersy, self._friend_db)
        self._text_db.open()

        # never sync while taking a step, only sync with friends
        self._orig_send_introduction_request = self.send_introduction_request
        self.send_introduction_request = lambda destination, introduce_me_to = None, allow_sync = True, advice = True: self._orig_send_introduction_request(destination, introduce_me_to, False, True)

        self.friend_sync_id = dispersy.callback.register(self.sync_with_friends)
        self._pending_callbacks.append(self.friend_sync_id)

        # replace _get_packets_for_bloomfilters
        self._orig__get_packets_for_bloomfilters = self._dispersy._get_packets_for_bloomfilters
        self._dispersy._get_packets_for_bloomfilters = self._get_packets_for_bloomfilters

    def unload_community(self):
        super(SocialCommunity, self).unload_community()
        self._friend_db.close()
        self._text_db.close()

    def initiate_meta_messages(self):
        # TODO replace with modified full sync
        return [Message(self, u"text", MemberAuthentication(encoding="sha1"), PublicResolution(), FullSyncDistribution(enable_sequence_number=False, synchronization_direction=u"DESC", priority=128), CommunityDestination(node_count=0), TextPayload(), self._dispersy._generic_timeline_check, self.on_text),
                Message(self, u"encrypted", MemberAuthentication(encoding="sha1"), PublicResolution(), FullSyncDistribution(enable_sequence_number=False, synchronization_direction=u"DESC", priority=128), CommunityDestination(node_count=0), EncryptedPayload(), self._dispersy._generic_timeline_check, self.on_encrypted)]

    def initiate_conversions(self):
        return [DefaultConversion(self), SocialConversion(self)]

    @property
    def dispersy_sync_skip_enable(self):
        return False

    @property
    def dispersy_sync_cache_enable(self):
        return False

    def sync_with_friends(self):
        while True:
            tbs = list(self.yield_taste_buddies())
            shuffle(tbs)

            if tbs:
                interval = max(300 / float(len(tbs)), 5.0)
                for tb in tbs:
                    self._orig_send_introduction_request(tb.candidate, None, True, False)
                    yield interval
            else:
                yield 15.0

    def new_taste_buddy(self, tb):
        if tb.overlap:
            self.dispersy.callback.replace_register(self.friend_sync_id, self.sync_with_friends)

    def _get_packets_for_bloomfilters(self, community, requests, include_inactive=True):
        if community != self:
            for message, packet in self._orig__get_packets_for_bloomfilters(community, requests, include_inactive):
                yield message, packet
        else:
            for message, time_low, time_high, offset, modulo in requests:

                tb = self.is_taste_buddy(message.candidate)
                if tb and tb.overlap:
                    if DEBUG_VERBOSE:
                        print >> sys.stderr, "GOT sync-request from", message.candidate, tb

                    keyhashes = tuple(buffer(str(overlapping_friend)) for overlapping_friend in tb.overlap)
                    sync_ids = self._friend_db.execute(u"SELECT sync_id FROM friendsync WHERE global_time BETWEEN ? AND ? AND (global_time + ?) % ? = 0 AND keyhash in (" + ", ".join("?" * len(keyhashes)) + ")",
                                                       (time_low, time_high, offset, modulo) + keyhashes)

                    sync_ids = tuple(str(sync_id) for sync_id, in sync_ids)
                    yield message, ((str(packet),) for packet, in self._dispersy._database.execute(u"SELECT packet FROM sync WHERE undone = 0 AND id IN (" + ",".join(sync_ids) + ") ORDER BY global_time DESC"))

                elif DEBUG:
                    print >> sys.stderr, "GOT sync-request from, ignoring", message.candidate

    def _select_and_fix(self, request_cache, syncable_messages, global_time, to_select, higher=True):
        tb = self.is_taste_buddy(request_cache.helper_candidate)
        if tb and tb.overlap:
            if DEBUG_VERBOSE:
                print >> sys.stderr, "SELECTING packets for", request_cache.helper_candidate, tb

            keyhashes = tuple(buffer(str(overlapping_friend)) for overlapping_friend in tb.overlap)

            # first select_and_fix based on friendsync table
            if higher:
                data = list(self._friend_db.execute(u"SELECT global_time, sync_id FROM friendsync WHERE global_time > ? AND keyhash in (" + ", ".join("?" * len(keyhashes)) + ") ORDER BY global_time ASC LIMIT ?",
                                                        (global_time,) + keyhashes + (to_select + 1,)))
            else:
                data = list(self._friend_db.execute(u"SELECT global_time, sync_id FROM friendsync WHERE global_time < ? AND keyhash in (" + ", ".join("?" * len(keyhashes)) + ") ORDER BY global_time DESC LIMIT ?",
                                                        (global_time,) + keyhashes + (to_select + 1,)))

            fixed = False
            if len(data) > to_select:
                fixed = True

                # if last 2 packets are equal, then we need to drop those
                global_time = data[-1][0]
                del data[-1]
                while data and data[-1][0] == global_time:
                    del data[-1]

            # next get actual packets from sync table, friendsync does not contain any non-syncable_messages hence this variable isn't used
            sync_ids = tuple(str(sync_id) for _, sync_id in data)
            if higher:
                data = list(self._dispersy._database.execute(u"SELECT global_time, packet FROM sync WHERE undone = 0 AND id IN (" + ",".join(sync_ids) + ") ORDER BY global_time ASC"))
            else:
                data = list(self._dispersy._database.execute(u"SELECT global_time, packet FROM sync WHERE undone = 0 AND id IN (" + ",".join(sync_ids) + ") ORDER BY global_time DESC"))

            if not higher:
                data.reverse()

            return data, fixed
        return [], False

    def _dispersy_claim_sync_bloom_filter_modulo(self, request_cache):
        raise NotImplementedError()

    def create_text(self, text, friends):
        assert isinstance(text, unicode), type(text)
        assert all(isinstance(friend, str) for friend in friends), [type(friend) for friend in friends]

        meta = self.get_meta_message(u"text")
        message = meta.impl(authentication=(self._my_member,),
                            distribution=(self.claim_global_time(),),
                            payload=(text,))

        for friend in friends:
            self.create_encrypted(message.packet, friend)

        # self._dispersy.store_update_forward([message], True, True, False)

    def on_text(self, messages):
        for message in messages:
            if self.log_text:
                self.log_text("text-statistics", message.candidate.sock_addr, global_time=message._distribution.global_time + 1, created_by=message.authentication.member.mid.encode('hex'))
                
            self._text_db.add_message(message.authentication.member.mid, message.payload.text)

    def create_encrypted(self, message_str, dest_friend):
        assert isinstance(message_str, str)
        assert isinstance(dest_friend, str)

        # get key
        _,key, keyhash = self._friend_db.get_friend(dest_friend)

        if key:
            # encrypt message
            encrypted_message = self.dispersy.crypto.encrypt(key, message_str)

            # get overlapping connections
            overlapping_candidates = [tb.candidate for tb in self.filter_overlap(self.yield_taste_buddies(), [keyhash, ])]

            meta = self.get_meta_message(u"encrypted")
            message = meta.impl(authentication=(self._my_member,),
                                distribution=(self.claim_global_time(),),
                                destination=(tuple(overlapping_candidates)),
                                payload=(keyhash, encrypted_message))

            self._dispersy.store_update_forward([message], True, True, True)

    def on_encrypted(self, messages):
        if __debug__:
            key_hashes = [keyhash for _, keyhash in self._friend_db.get_my_keys()] + [keyhash for _, _, keyhash in self._friend_db.get_friend_keys()]
            assert all(message.payload.keyhash in key_hashes for message in messages)

        decrypted_messages = []
        for message in messages:
            self._friend_db.add_message(message.packet_id, message._distribution.global_time, message.payload.keyhash)

            could_decrypt = False
            for key, keyhash in self._friend_db.get_my_keys():
                if keyhash == message.payload.keyhash:
                    decrypted_messages.append((message.candidate, self.dispersy.crypto.decrypt(key, message.payload.encrypted_message)))
                    could_decrypt = True
                    break

            if self.log_text:
                # if no candidate -> message is created by me
                self.log_text("encrypted-statistics", message.candidate.sock_addr if message.candidate else None, global_time=message._distribution.global_time, created_by=message.authentication.member.mid.encode('hex'), created_by_me=(message.candidate == None), could_decrypt=could_decrypt)

        if decrypted_messages:
            self._dispersy.on_incoming_packets(decrypted_messages, cache=False)
            
    def add_friend(self, name, key):
        keyhash = long(sha1(self._crypto.key_to_bin(key)).hexdigest(), 16)
        self._mypref_db.addMyPreference(keyhash, {})
        self._friend_db.add_friend(name, key, keyhash)
        
        return keyhash
    
    def get_friends(self):
        my_friends = dict([(keyhash, [name, 0]) for name,_,keyhash in self._friend_db.get_friend_keys()])
        for tb in self.yield_taste_buddies():
            for keyhash, friend_tuple in my_friends:
                if tb.does_overlap(keyhash):
                    friend_tuple[1]+=1
        return my_friends.values()

    def get_tbs_from_peercache(self, nr, nr_standins):
        tbs = [TasteBuddy(overlap, (ip, port)) for overlap, ip, port in self._peercache.get_peers()]

        friends, foafs = self.determine_friends_foafs(tbs)
        my_key_hashes = [keyhash for _, keyhash in self._friend_db.get_my_keys()]

        if len(friends) > nr:
            friends = sample(list(friends), nr)

        peercache_candidates = []
        for friend in friends:
            peercache_friend = [friend] * 2

            standins = set()
            for overlapping_hash in friend.overlap:
                if overlapping_hash not in my_key_hashes:
                    standins.update(foafs.get(overlapping_hash, []))

            remaining_standins = nr_standins - len(peercache_friend)
            if len(standins) > remaining_standins:
                standins = sample(list(standins), remaining_standins)

            peercache_friend.extend(standins)
            peercache_candidates.append(peercache_friend)

        return peercache_candidates

    def filter_tb(self, tbs):
        tbs = list(tbs)

        to_maintain, foafs = self.determine_friends_foafs(tbs)

        # for each friend we maintain an additional connection to at least one foaf
        # this peer is chosen randomly to attempt to load balance these pings
        for keyhash, f_tbs in foafs.iteritems():
            to_maintain.add(choice(f_tbs))

        if DEBUG:
            print >> sys.stderr, long(time()), "SocialCommunity: Will maintain", len(to_maintain), "connections instead of", len(tbs)

        return to_maintain

    def determine_friends_foafs(self, tbs):
        my_key_hashes = [keyhash for _, keyhash in self._friend_db.get_my_keys()]

        friends = self.filter_overlap(tbs, my_key_hashes)
        foafs = defaultdict(list)
        for tb in tbs:
            if tb not in friends:
                for keyhash in tb.overlap:
                    foafs[keyhash].append(tb)

        return friends, foafs

    def filter_overlap(self, tbs, keys):
        to_maintain = set()
        for tb in tbs:
            # if a peer has overlap with any of my_key_hashes, its my friend -> maintain connection
            if any(map(tb.does_overlap, keys)):
                to_maintain.add(tb)

        return to_maintain

    def add_possible_taste_buddies(self):
        my_key_hashes = [keyhash for _, keyhash in self._friend_db.get_my_keys()]

        connections = defaultdict(int)
        for tb in self.yield_taste_buddies():
            for keyhash in tb.overlap:
                connections[keyhash] += 1

        def prefer_my_friends(a, b):
            if any(map(a.does_overlap, my_key_hashes)):
                return 1

            if any(map(b.does_overlap, my_key_hashes)):
                return -1

            if a.overlap and b.overlap:
                # neither are my friend, sort by a foaf which connects me to a least connected friend
                min_a = min(connections[overlapping] for overlapping in a.overlap)
                min_b = min(connections[overlapping] for overlapping in b.overlap)
                return cmp(min_a, min_b)

            if a.overlap:
                return 1
            if b.overlap:
                return -1
            return cmp(a, b)

        self.possible_taste_buddies.sort(cmp=prefer_my_friends, reverse=True)

        if DEBUG_VERBOSE:
            print >> sys.stderr, long(time()), "SocialCommunity: After sorting", [any(map(tb.does_overlap, my_key_hashes)) for tb in self.possible_taste_buddies], map(str, self.possible_taste_buddies),
        elif DEBUG:
            print >> sys.stderr, long(time()), "SocialCommunity: After sorting", [any(map(tb.does_overlap, my_key_hashes)) for tb in self.possible_taste_buddies]

class NoFSocialCommunity(HForwardCommunity, SocialCommunity):

    @classmethod
    def load_community(cls, dispersy, master, my_member, integrate_with_tribler=True, encryption=ENCRYPTION, max_prefs=None, max_fprefs=None, use_cardinality=True, log_text=None):
        dispersy_database = dispersy.database
        try:
            dispersy_database.execute(u"SELECT 1 FROM community WHERE master = ?", (master.database_id,)).next()
        except StopIteration:
            return cls.join_community(dispersy, master, my_member, my_member, integrate_with_tribler=integrate_with_tribler, encryption=encryption, max_prefs=max_prefs, max_fprefs=max_fprefs, log_text=log_text)
        else:
            return super(NoFSocialCommunity, cls).load_community(dispersy, master, integrate_with_tribler=integrate_with_tribler, encryption=encryption, max_prefs=max_prefs, max_fprefs=max_fprefs, log_text=log_text)

    def __init__(self, dispersy, master, integrate_with_tribler=True, encryption=ENCRYPTION, max_prefs=None, max_fprefs=None, use_cardinality=True, log_text=None):
        SocialCommunity.__init__(self, dispersy, master, integrate_with_tribler, encryption, log_text)
        HForwardCommunity.__init__(self, dispersy, master, integrate_with_tribler, encryption, 0, max_prefs, max_fprefs, max_taste_buddies=sys.maxint, send_simi_reveal=True)

    def initiate_conversions(self):
        return HForwardCommunity.initiate_conversions(self) + [SocialConversion(self)]

    def initiate_meta_messages(self):
        return HForwardCommunity.initiate_meta_messages(self) + SocialCommunity.initiate_meta_messages(self)

    def unload_community(self):
        HForwardCommunity.unload_community(self)
        SocialCommunity.unload_community(self)

    def add_possible_taste_buddies(self, possibles):
        HForwardCommunity.add_possible_taste_buddies(self, possibles)
        SocialCommunity.add_possible_taste_buddies(self)

    def new_taste_buddy(self, tb):
        HForwardCommunity.new_taste_buddy(self, tb)
        SocialCommunity.new_taste_buddy(self, tb)

    def filter_tb(self, tbs):
        return SocialCommunity.filter_tb(self, tbs)

    def get_tbs_from_peercache(self, nr, standins):
        return SocialCommunity.get_tbs_from_peercache(self, nr, standins)

    def _dispersy_claim_sync_bloom_filter_modulo(self):
        return SocialCommunity._dispersy_claim_sync_bloom_filter_modulo(self)

    def _select_and_fix(self, request_cache, syncable_messages, global_time, to_select, higher=True):
        return SocialCommunity._select_and_fix(self, request_cache, syncable_messages, global_time, to_select, higher)

class PSocialCommunity(PForwardCommunity, SocialCommunity):

    @classmethod
    def load_community(cls, dispersy, master, my_member, integrate_with_tribler=True, encryption=ENCRYPTION, max_prefs=None, max_fprefs=None, use_cardinality=True, log_text=None):
        dispersy_database = dispersy.database
        try:
            dispersy_database.execute(u"SELECT 1 FROM community WHERE master = ?", (master.database_id,)).next()
        except StopIteration:
            return cls.join_community(dispersy, master, my_member, my_member, integrate_with_tribler=integrate_with_tribler, encryption=encryption, max_prefs=max_prefs, max_fprefs=max_fprefs, log_text=log_text)
        else:
            return super(PSocialCommunity, cls).load_community(dispersy, master, integrate_with_tribler=integrate_with_tribler, encryption=encryption, max_prefs=max_prefs, max_fprefs=max_fprefs, log_text=log_text)

    def __init__(self, dispersy, master, integrate_with_tribler=True, encryption=ENCRYPTION, max_prefs=None, max_fprefs=None, use_cardinality=True, log_text=None):
        SocialCommunity.__init__(self, dispersy, master, integrate_with_tribler, encryption, log_text)
        PForwardCommunity.__init__(self, dispersy, master, integrate_with_tribler, encryption, 10, max_prefs, max_fprefs, max_taste_buddies=sys.maxint, send_simi_reveal=True)

    def initiate_conversions(self):
        return PForwardCommunity.initiate_conversions(self) + [SocialConversion(self)]

    def initiate_meta_messages(self):
        return PForwardCommunity.initiate_meta_messages(self) + SocialCommunity.initiate_meta_messages(self)

    def unload_community(self):
        PForwardCommunity.unload_community(self)
        SocialCommunity.unload_community(self)

    def add_possible_taste_buddies(self, possibles):
        PForwardCommunity.add_possible_taste_buddies(self, possibles)
        SocialCommunity.add_possible_taste_buddies(self)

    def new_taste_buddy(self, tb):
        PForwardCommunity.new_taste_buddy(self, tb)
        SocialCommunity.new_taste_buddy(self, tb)

    def filter_tb(self, tbs):
        return SocialCommunity.filter_tb(self, tbs)

    def get_tbs_from_peercache(self, nr, standins):
        return SocialCommunity.get_tbs_from_peercache(self, nr, standins)

    def _dispersy_claim_sync_bloom_filter_modulo(self):
        return SocialCommunity._dispersy_claim_sync_bloom_filter_modulo(self)

    def _select_and_fix(self, request_cache, syncable_messages, global_time, to_select, higher=True):
        return SocialCommunity._select_and_fix(self, request_cache, syncable_messages, global_time, to_select, higher)

class HSocialCommunity(HForwardCommunity, SocialCommunity):

    @classmethod
    def load_community(cls, dispersy, master, my_member, integrate_with_tribler=True, encryption=ENCRYPTION, max_prefs=None, max_fprefs=None, use_cardinality=True, log_text=None):
        dispersy_database = dispersy.database
        try:
            dispersy_database.execute(u"SELECT 1 FROM community WHERE master = ?", (master.database_id,)).next()
        except StopIteration:
            return cls.join_community(dispersy, master, my_member, my_member, integrate_with_tribler=integrate_with_tribler, encryption=encryption, max_prefs=max_prefs, max_fprefs=max_fprefs, log_text=log_text)
        else:
            return super(HSocialCommunity, cls).load_community(dispersy, master, integrate_with_tribler=integrate_with_tribler, encryption=encryption, max_prefs=max_prefs, max_fprefs=max_fprefs, log_text=log_text)

    def __init__(self, dispersy, master, integrate_with_tribler=True, encryption=ENCRYPTION, max_prefs=None, max_fprefs=None, use_cardinality=True, log_text=None):
        SocialCommunity.__init__(self, dispersy, master, integrate_with_tribler, encryption, log_text)
        HForwardCommunity.__init__(self, dispersy, master, integrate_with_tribler, encryption, 10, max_prefs, max_fprefs, max_taste_buddies=sys.maxint, send_simi_reveal=True)

    def initiate_conversions(self):
        return HForwardCommunity.initiate_conversions(self) + [SocialConversion(self)]

    def initiate_meta_messages(self):
        return HForwardCommunity.initiate_meta_messages(self) + SocialCommunity.initiate_meta_messages(self)

    def unload_community(self):
        HForwardCommunity.unload_community(self)
        SocialCommunity.unload_community(self)

    def add_possible_taste_buddies(self, possibles):
        HForwardCommunity.add_possible_taste_buddies(self, possibles)
        SocialCommunity.add_possible_taste_buddies(self)

    def new_taste_buddy(self, tb):
        HForwardCommunity.new_taste_buddy(self, tb)
        SocialCommunity.new_taste_buddy(self, tb)

    def filter_tb(self, tbs):
        return SocialCommunity.filter_tb(self, tbs)

    def get_tbs_from_peercache(self, nr, standins):
        return SocialCommunity.get_tbs_from_peercache(self, nr, standins)

    def _dispersy_claim_sync_bloom_filter_modulo(self):
        return SocialCommunity._dispersy_claim_sync_bloom_filter_modulo(self)

    def _select_and_fix(self, request_cache, syncable_messages, global_time, to_select, higher=True):
        return SocialCommunity._select_and_fix(self, request_cache, syncable_messages, global_time, to_select, higher)

class PoliSocialCommunity(PoliForwardCommunity, SocialCommunity):

    @classmethod
    def load_community(cls, dispersy, master, my_member, integrate_with_tribler=True, encryption=ENCRYPTION, max_prefs=None, max_fprefs=None, use_cardinality=True, log_text=None, send_simi_reveal=True):
        dispersy_database = dispersy.database
        try:
            dispersy_database.execute(u"SELECT 1 FROM community WHERE master = ?", (master.database_id,)).next()
        except StopIteration:
            return cls.join_community(dispersy, master, my_member, my_member, integrate_with_tribler=integrate_with_tribler, encryption=encryption, max_prefs=max_prefs, max_fprefs=max_fprefs, use_cardinality=use_cardinality, log_text=log_text, send_simi_reveal=send_simi_reveal)
        else:
            return super(PoliSocialCommunity, cls).load_community(dispersy, master, integrate_with_tribler=integrate_with_tribler, encryption=encryption, max_prefs=max_prefs, max_fprefs=max_fprefs, use_cardinality=use_cardinality, log_text=log_text, send_simi_reveal=send_simi_reveal)

    def __init__(self, dispersy, master, integrate_with_tribler=True, encryption=ENCRYPTION, max_prefs=None, max_fprefs=None, use_cardinality=True, log_text=None, send_simi_reveal=True):
        SocialCommunity.__init__(self, dispersy, master, integrate_with_tribler, encryption, log_text)
        PoliForwardCommunity.__init__(self, dispersy, master, integrate_with_tribler, encryption, 10, max_prefs, max_fprefs, max_taste_buddies=sys.maxint, use_cardinality=use_cardinality, send_simi_reveal=send_simi_reveal)

    def initiate_conversions(self):
        return PoliForwardCommunity.initiate_conversions(self) + [SocialConversion(self)]

    def initiate_meta_messages(self):
        return PoliForwardCommunity.initiate_meta_messages(self) + SocialCommunity.initiate_meta_messages(self)

    def unload_community(self):
        PoliForwardCommunity.unload_community(self)
        SocialCommunity.unload_community(self)

    def add_possible_taste_buddies(self, possibles):
        PoliForwardCommunity.add_possible_taste_buddies(self, possibles)
        SocialCommunity.add_possible_taste_buddies(self)

    def new_taste_buddy(self, tb):
        PoliForwardCommunity.new_taste_buddy(self, tb)
        SocialCommunity.new_taste_buddy(self, tb)

    def filter_tb(self, tbs):
        return SocialCommunity.filter_tb(self, tbs)

    def get_tbs_from_peercache(self, nr, standins):
        return SocialCommunity.get_tbs_from_peercache(self, nr, standins)

    def _dispersy_claim_sync_bloom_filter_modulo(self):
        return SocialCommunity._dispersy_claim_sync_bloom_filter_modulo(self)

    def _select_and_fix(self, request_cache, syncable_messages, global_time, to_select, higher=True):
        return SocialCommunity._select_and_fix(self, request_cache, syncable_messages, global_time, to_select, higher)
