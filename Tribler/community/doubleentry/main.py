"""
Python file to bootstrap a single DoubleEntry Community.
"""
import os
import sys
import random
import time
import logging.config

from Tribler.Core.SessionConfig import SessionStartupConfig
from Tribler.Core.Session import Session
from Tribler.Core.Utilities.twisted_thread import reactor

from Tribler.community.doubleentry.community import DoubleEntryCommunity
from Tribler.community.doubleentry.community import DoubleEntrySettings

from Tribler.community.doubleentry.experiments import NumericalExample
from Tribler.community.doubleentry.experiments import GraphDrawer

from twisted.internet.threads import blockingCallFromThread
from twisted.internet.stdio import StandardIO
from twisted.protocols.basic import LineReceiver


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))


# Class that handles boot strapping the DoubleEntry Community.
class DoubleEntry(object):
    """
    Class that handles boot strapping the DoubleEntry Community
    when running a single community instance without Tribler.
    """

    def __init__(self):
        """
        Setup this class to be able to run the community with the run method.
        """
        self.community = None
        self._member = None
        self.settings = DoubleEntrySettings()
        # Change port so we can run multiple instances on local host.
        self.settings.socks_listen_ports = [random.randint(1000, 65535) for _ in range(5)]
        self.session = self.create_tribler_session()
        self.session.start()
        print >> sys.stderr, "Using port %d" % self.session.get_dispersy_port()

        self.dispersy = self.session.lm.dispersy

    def create_tribler_session(self):
        """
        Create a tribler session usable to create a DoubleEntry Community.
        :return: Tribler.Core.Session
        """
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
        config.set_dispersy_port(self.settings.dispersy_port)

        return Session(config)

    def run(self):
        """
        Starts the Double Entry community with a new EC key as ID.
        :return:
        """
        def start_community():
            community = DoubleEntryCommunity
            self._member = self.dispersy.get_new_member(u"NID_secp160k1")
            self.community = self.dispersy.define_auto_load(community, self._member,
                                                            (None, self.settings), load=True)[0]
        blockingCallFromThread(reactor, start_community)

    def get_community(self):
        return self.community

    def signature_request(self):
        """
        Instruct the community to send out a signature request.
        """
        self.community.publish_signature_request_message()

    def print_community(self):
        """
        Instruct the community to print out information.
        """
        print(self.community.to_string())

    def draw_community(self):
        """
        Instruct the community to draw the blockchain.
        """
        graph_drawer = GraphDrawer(self.community.persistence)
        graph_drawer.draw_graph()


class CommandHandler(LineReceiver):
    """
    Reads cmdline input to operate the Double Entry community.
    """
    from os import linesep
    delimiter = linesep

    def __init__(self, double_entry):
        self.double_entry = double_entry

    def connectionMade(self):
        self.transport.write('>>> ')

    def lineReceived(self, line):
        if line == 'r':
            self.double_entry.signature_request()
        elif line == 'n':
            experiment = NumericalExample(self.double_entry.get_community())
            experiment.perform_experiment()
        elif line == 'p':
            self.double_entry.print_community()
        elif line == 'g':
            self.double_entry.draw_community()

        self.transport.write('>>> ')


def main():
    """
    Main method to start a Double Entry community that listens to commandline input.
    """
    logging.config.fileConfig("logger.conf")

    doubleentry = DoubleEntry()
    StandardIO(CommandHandler(doubleentry))
    doubleentry.run()

    # Keep the program running.
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
