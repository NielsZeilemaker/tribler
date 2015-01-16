import os
import sys
import random

from Tribler.Core.SessionConfig import SessionStartupConfig
from Tribler.Core.Session import Session
from Tribler.Core.Utilities.twisted_thread import reactor

from Tribler.community.doubleentry.community import DoubleEntryCommunity
from Tribler.community.doubleentry.community import DoubleEntrySettings

from twisted.internet.threads import blockingCallFromThread
from twisted.internet.stdio import StandardIO
from twisted.protocols.basic import LineReceiver


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))


# Class that handles boot strapping the DoubleEntry Community.
class DoubleEntry(object):

    def __init__(self):
        self.community = None
        self._member = None
        self.settings = DoubleEntrySettings()
        # Change port so we can run multiple instances on local host.
        self.settings.socks_listen_ports = [random.randint(1000, 65535) for _ in range(5)]
        self.session = self.create_tribler_session()
        self.session.start()
        print >> sys.stderr, "Using port %d for swift tunnel" % self.session.get_swift_tunnel_listen_port()

        self.dispersy = self.session.lm.dispersy

    def create_tribler_session(self):
        # Setup the tribler session
        config = SessionStartupConfig()
        config.set_state_dir(os.path.join(BASE_DIR, ".Tribler-%d") % self.settings.socks_listen_ports[0])
        config.set_torrent_checking(False)
        config.set_torrent_collecting(False)
        config.set_multicast_local_peer_discovery(False)
        config.set_megacache(False)
        config.set_mainline_dht(False)
        config.set_libtorrent(False)
        config.set_dht_torrent_collecting(False)
        config.set_videoplayer(False)

        config.set_dispersy(True)
        config.set_swift_tunnel_listen_port(self.settings.swift_port)

        return Session(config)

    def run(self):
        # Start the community.
        def start_community():
            community = DoubleEntryCommunity
            self._member = self.dispersy.get_new_member(u"NID_secp160k1")
            self.community = self.dispersy.define_auto_load(community, self._member,
                                                            (None, self.settings), load=True)[0]
            self.community.set_ec(self._member.private_key)

        blockingCallFromThread(reactor, start_community)

    def signature_request(self):
        self.community.publish_signature_request_message()

# Reads cmdline input to operate the Double Entry community.
class CommandHandler(LineReceiver):
    from os import linesep
    delimiter = linesep

    def __init__(self, doubleentry):
        self.doubleentry = doubleentry

    def connectionMade(self):
        self.transport.write('>>> ')

    # Process a line received.
    def lineReceived(self, line):
        if line == 'r':
            self.doubleentry.signature_request()

        self.transport.write('>>> ')


def main(argv):
    doubleentry = DoubleEntry()
    StandardIO(CommandHandler(doubleentry))
    doubleentry.run()



if __name__ == "__main__":
    main(sys.argv[1:])
