from Tribler.community.anontunnel.ConnectionHandlers.CommandHandler import CommandHandler

__author__ = 'chris'

import logging.config

logger = logging.getLogger(__name__)

from Tribler.community.anontunnel.DispersyTunnelProxy import DispersyTunnelProxy
from Tribler.community.anontunnel.ProxyCommunity import ProxyCommunity
from Tribler.community.anontunnel.Socks5AnonTunnelServer import Socks5AnonTunnelServer
from Tribler.dispersy.callback import Callback
from Tribler.dispersy.dispersy import Dispersy
from Tribler.dispersy.endpoint import RawserverEndpoint


class AnonTunnel:
    def __init__(self, socks5_port, cmd_port):
        self.callback = Callback()
        self.socket_server = Socks5AnonTunnelServer(socks5_port)

        self.endpoint = RawserverEndpoint(self.socket_server.raw_server, port=10000)
        self.dispersy = Dispersy(self.callback, self.endpoint, u".", u":memory:")

        self.command_handler = CommandHandler(self)
        self.command_handler.attach_to(self.socket_server, cmd_port)

        self.community = None
        self.tunnel = None

    def start(self):
        self.dispersy.start()
        logger.info("Dispersy is listening on port %d" % self.dispersy.lan_address[1])

        def join_overlay(dispersy):
            master_member = dispersy.get_temporary_member_from_id("-PROXY-OVERLAY-HASH-")
            my_member = dispersy.get_new_member()
            return ProxyCommunity.join_community(dispersy, master_member, my_member)

        self.community = self.dispersy.callback.call(join_overlay, (self.dispersy,))

        self.tunnel = DispersyTunnelProxy(self.community)

        self.socket_server.tunnel = self.tunnel
        self.socket_server.start()

    def stop(self):
        if self.community:
            pass

        if self.socket_server:
            self.socket_server.shutdown()

        if self.dispersy:
            self.dispersy.stop()
