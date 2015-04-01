import unittest


from Tribler.community.doubleentry.experiments import GraphDrawer


class TestGraphDrawer(unittest.TestCase):

    def test_setup_graph(self):
        # Arrange
        persistence = TestPersistence()
        # Act
        graph_drawer = GraphDrawer(persistence)
        # Assert
        for key in persistence.get_keys():
            assert(set(graph_drawer.graph.neighbors(key)) == set(persistence.get(key).get_test_data()))


class TestBlock:

    def __init__(self, prev_req, prev_res):
        self.payload = TestPayload(prev_req, prev_res)

    def get_test_data(self):
        # get the neighbors and reverse these to comply to nx standard.
        return [self.payload.previous_hash_requester, self.payload.previous_hash_responder]


class TestPayload:

    def __init__(self, prev_req, prev_res):
        self.previous_hash_requester = prev_req
        self.previous_hash_responder = prev_res


class TestPersistence:

    def __init__(self):
        self.keys = [1, 2, 3, 4, 5, 6]
        self.dict = dict()
        self.dict[1] = TestBlock("G1", "G2")
        self.dict[2] = TestBlock("G3", "G4")
        self.dict[3] = TestBlock(1, 2)
        self.dict[4] = TestBlock(3, "G5")
        self.dict[5] = TestBlock(4, 6)
        self.dict[6] = TestBlock("G6", "G7")

    def get_keys(self):
        return self.keys

    def get(self, key):
        return self.dict[key]

# persistence = TestPersistence()
# gd = GraphDrawer(persistence)
# gd.draw_graph()