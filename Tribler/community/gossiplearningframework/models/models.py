from Tribler.community.gossiplearningframework.payload import GossipMessage

if __debug__:
    from Tribler.dispersy.dprint import dprint

class GossipLearningModel(GossipMessage):

    def __init__(self):
        pass

    def update(self):
        raise NotImplementedError('update')

    def predict(self):
        raise NotImplementedError('predict')

    def merge(self):
        raise NotImplementedError('predict')