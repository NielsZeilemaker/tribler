from Tribler.dispersy.crypto import ECCrypto
# imports graph experiment
import networkx as nx
import matplotlib.pyplot as plot

__author__ = 'norberhuis'
"""
File containing experiments
"""


class NumericalExample:

    def __init__(self, double_entry_community):
        self._community = double_entry_community

    def perform_experiment(self):
        self.save_key_to_file(self._community.get_key())

        message = self._community.create_signature_request_message()

        self.save_payload_to_file(message.payload.timestamp)
        self.save_signature_to_file(message.payload.signature_requester)

    @staticmethod
    def save_key_to_file(ec):
        pem = ECCrypto().key_to_pem(ec)
        f = open("key.pem", 'w')
        f.write(pem)
        f.close()

    @staticmethod
    def save_payload_to_file(payload):
        f = open("payload", 'w')
        f.write(payload)
        f.close()

    @staticmethod
    def save_signature_to_file(signature):
        f = open("signature", 'w')
        f.write(signature)
        f.close()


class GraphDrawer:

    def __init__(self, persistence):
        self._persistence = persistence
        # Create Directed Graph
        self.graph = nx.DiGraph()
        self.setup_graph()

    def setup_graph(self):
        # Get all keys
        keys = self._persistence.get_keys()
        # Every key is a node and iterate over each node
        for key in keys:
            self.graph.add_node(key)
            # Add the edges
            block = self._persistence.get(key).payload
            requester_edge_tail = block.previous_hash_requester
            responder_edge_tail = block.previous_hash_responder
            self.graph.add_edge(key, requester_edge_tail)
            self.graph.add_edge(key, responder_edge_tail)

    def draw_graph(self):
        nx.draw(self.graph)
        plot.show(self.graph)



