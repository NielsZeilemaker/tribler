"""
Functionality to draw graphs for the double entry chain.
"""
import networkx as nx
import matplotlib.pyplot as plot

from Tribler.community.doubleentry.database import GENESIS_ID


class GraphDrawer:

    def __init__(self, persistence):
        self._persistence = persistence
        # Create Directed Graph
        self.graph = nx.DiGraph()
        self.setup_graph()

    def setup_graph(self):
        # Get all keys
        keys = self._persistence.get_ids()
        # Every key is a node and iterate over each node
        for key in keys:
            self.graph.add_node(key)
            # Add the edges
            block = self._persistence.get(key)
            self._add_edge(key, block.previous_hash_requester, block.public_key_requester)
            self._add_edge(key, block.previous_hash_responder, block.public_key_responder)

    def _add_edge(self, head, tail, unique_identifier):
        """
        Add an edge between the head and tail. If the tail is the genesis block,
        then add a unique identifier to distinguish different genesis blocks.
        :param head: Head of the directed edge.
        :param tail: Tail of the directed edge.
        :param unique_identifier: Unique identifier to be added to hash.
        :return:
        """
        if tail == GENESIS_ID:
            self.graph.add_edge(head, tail + unique_identifier)
        else:
            self.graph.add_edge(head, tail)

    def draw_graph(self):
        nx.draw(self.graph)
        plot.show(self.graph)
