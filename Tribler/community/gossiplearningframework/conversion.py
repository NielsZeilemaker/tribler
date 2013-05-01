from struct import pack, unpack_from
import copy
import json
import numpy

from Tribler.dispersy.dprint import dprint
from Tribler.dispersy.message import DropPacket
from Tribler.dispersy.conversion import BinaryConversion
from Tribler.community.gossiplearningframework.payload import *
# TODO: autoload
from Tribler.community.gossiplearningframework.models.logisticregression import LogisticRegressionModel
from Tribler.community.gossiplearningframework.models.adalineperceptron import AdalinePerceptronModel
from Tribler.community.gossiplearningframework.models.p2pegasos import P2PegasosModel

if __debug__:
    from Tribler.dispersy.dprint import dprint

class StructConversion(BinaryConversion):
    _model_map = {LogisticRegressionModel:"l", AdalinePerceptronModel:"a", P2PegasosModel:"p"}
    _rev_model_map = dict((value, key) for key, value in _model_map.iteritems())

    def __init__(self, community):
        super(StructConversion, self).__init__(community, "\x02") # Community version 2
        # Message type ID 1
        self.define_meta_message(chr(1), community.get_meta_message(u"modeldata"), self._encode_modeldata, self._decode_modeldata)

    def _encode_modeldata(self, message):
        assert isinstance(message.payload.message, GossipMessage)
        assert message.payload.message.__class__ in self._model_map
        model = message.payload.message
        if __debug__: dprint(len(model.w), " floats: ~", len(model.w) * 4 / 1024, "KB", box=1)
        return (self._model_map[model.__class__],
                pack(">LL", model.age, len(model.w)),
                "".join(pack(">f", f) for f in model.w))

    def _decode_modeldata(self, meta_message, offset, data):
        if len(data) < offset + 9:
            raise DropPacket("Insufficient packet size")

        model_cls = self._rev_model_map.get(data[offset])
        offset += 1
        if not model_cls:
            raise DropPacket("Unknown model")
        model = model_cls()

        model.age, w_length = unpack_from(">LL", data, offset)
        offset += 8

        if len(data) < offset + w_length * 4:
            raise DropPacket("Insufficient packet size")

        model.w = list(unpack_from(">%df" % w_length, data, offset))
        offset += w_length * 4

        if __debug__: dprint(len(model.w), " floats: ~", len(model.w) * 4 / 1024, "KB", box=1)
        return offset, meta_message.meta.payload.implement(model)

class JSONConversion(BinaryConversion):
    def __init__(self, community):
        super(JSONConversion, self).__init__(community, "\x01")  # Community version 1
        # Message type ID 1
        self.define_meta_message(chr(1), community.get_meta_message(u"modeldata"), self._encode_json, self._decode_json)

    def _encode_json(self, message):
        if __debug__:
            dprint(type(message.payload.message))
            dprint(message.payload.message)
        assert isinstance(message.payload.message, GossipMessage)
        wiredata = json.dumps(message.payload.message, cls=ClassCoder).encode("UTF-8")

        assert len(wiredata) < 2 ** 16

        if __debug__: dprint(wiredata)

        # Encode the length on 4 bytes, network byte order. The wire data follows.
        return pack("!I", len(wiredata)), wiredata

    def _decode_json(self, meta_message, offset, data):
        if len(data) < offset + 4:
            raise DropPacket("Insufficient packet size")

        data_length, = unpack_from("!I", data, offset)
        offset += 4

        try:
            wiredata = json.loads(data[offset:offset + data_length].decode("UTF-8"),
                                  object_hook=ClassCoder.decode_class)
            offset += data_length
        except UnicodeError:
            raise DropPacket("Unable to decode UTF-8")

        return offset, meta_message.meta.payload.implement(wiredata)

class ClassCoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, GossipMessage):
            # Get a copy of class variables.
            result = copy.deepcopy(obj.__dict__)

            # Add the class name.
            result[u'__class__'] = obj.__class__.__name__
            return result

        elif isinstance(obj, numpy.ndarray):
            return {'__class__':'ndarray', 'value': obj.tolist()}

        else:
            return json.JSONEncoder.default(self, obj)

    @classmethod
    def decode_class(cls, d):
        if isinstance(d, dict) and '__class__' in d:
            if d['__class__'] in ['GossipMessage', 'AdalinePerceptronModel', 'LogisticRegressionModel', 'P2PegasosModel', ]:
                # Get the class, create object.
                res = globals()[str(d['__class__'])]()

                # Update class variables recursively.
                for k, v in d.items():
                    if k != '__class__':
                        res.__dict__[k] = cls.decode_class(v)

                return res
            elif d['__class__'] == 'ndarray':
                return numpy.array(d['value'])
        return d

