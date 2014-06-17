from struct import pack, unpack_from

from Tribler.Core.Utilities.encoding import encode, decode
from Tribler.dispersy.conversion import BinaryConversion
from Tribler.dispersy.message import DropPacket


class TunnelConversion(BinaryConversion):
    def __init__(self, community):
        super(TunnelConversion, self).__init__(community, "\x02")

        self.define_meta_message(chr(1), community.get_meta_message(u"create"), lambda message: self._encode_decode(self._encode_create, self._decode_create, message), self._decode_create)
        self.define_meta_message(chr(2), community.get_meta_message(u"created"), lambda message: self._encode_decode(self._encode_created, self._decode_created, message), self._decode_created)
        self.define_meta_message(chr(3), community.get_meta_message(u"extend"), lambda message: self._encode_decode(self._encode_extend, self._decode_extend, message), self._decode_extend)
        self.define_meta_message(chr(4), community.get_meta_message(u"extended"), lambda message: self._encode_decode(self._encode_extended, self._decode_extended, message), self._decode_extended)
        self.define_meta_message(chr(5), community.get_meta_message(u"ping"), lambda message: self._encode_decode(self._encode_ping, self._decode_ping, message), self._decode_ping)
        self.define_meta_message(chr(6), community.get_meta_message(u"pong"), lambda message: self._encode_decode(self._encode_pong, self._decode_pong, message), self._decode_pong)
        # self.define_meta_message(chr(7), community.get_meta_message(u"stats"), lambda message: self._encode_decode(self._encode_stats, self._decode_stats, message), self._decode_stats)

    def _encode_create(self, message):
        payload = message.payload
        packet = pack("!IHH", payload.circuit_id, len(payload.key), len(payload.public_key)) + payload.key + payload.public_key
        return packet,

    def _decode_create(self, placeholder, offset, data):
        circuit_id, = unpack_from('!I', data, offset)
        offset += 4

        len_key, len_pub_key = unpack_from("!HH", data, offset)
        offset += 4

        key = data[offset:offset + len_key]
        offset += len_key

        public_key = data[offset:offset + len_pub_key]
        offset += len_pub_key

        return offset, placeholder.meta.payload.implement(circuit_id, key, public_key)

    def _encode_created(self, message):
        payload = message.payload
        packet = pack("!IH", payload.circuit_id, len(payload.key)) + payload.key + encode(payload.candidate_list)
        return packet,

    def _decode_created(self, placeholder, offset, data):
        circuit_id, = unpack_from('!I', data, offset)
        offset += 4

        len_key, = unpack_from("!H", data, offset)
        offset += 2

        key = data[offset:offset + len_key]
        offset += len_key

        encoded_candidate_list = data[offset:]
        offset += len(encoded_candidate_list)
        _, candidate_list = decode(encoded_candidate_list)

        return offset, placeholder.meta.payload.implement(circuit_id, key, candidate_list)

    def _encode_extend(self, message):
        payload = message.payload
        packet = pack("!IHH", payload.circuit_id, len(payload.extend_with), len(payload.key)) + payload.extend_with + payload.key
        return packet,

    def _decode_extend(self, placeholder, offset, data):
        circuit_id, = unpack_from('!I', data, offset)
        offset += 4

        len_extend_with, len_key = unpack_from("!HH", data, offset)
        offset += 4

        extend_with = data[offset:offset + len_extend_with]
        offset += len_extend_with

        key = data[offset:offset + len_key]
        offset += len_key

        return offset, placeholder.meta.payload.implement(circuit_id, key, extend_with)

    def _encode_extended(self, message):
        payload = message.payload
        return pack("!IH", payload.circuit_id, len(payload.key)) + payload.key + encode(payload.candidate_list),

    def _decode_extended(self, placeholder, offset, data):
        circuit_id, = unpack_from('!I', data, offset)
        offset += 4

        key_length, = unpack_from("!H", data, offset)
        offset += 2

        key = data[offset:offset + key_length]
        offset += key_length

        encoded_candidate_list = data[offset:]
        offset += len(encoded_candidate_list)
        _, candidate_list = decode(encoded_candidate_list)

        return offset, placeholder.meta.payload.implement(circuit_id, key, candidate_list)

    def _encode_data(self, message):
        host, port = ("0.0.0.0", 0) if message.destination is None else message.destination
        origin = ("0.0.0.0", 0) if message.origin is None else message.origin
        packet = pack("!IHHHHL", message.payload.circuit_id, len(host), port, len(origin[0]), origin[1], len(message.data)) + \
                 host + origin[0] + message.data
        return packet,

    def _decode_data(self, placeholder, offset, data):
        circuit_id, host_length, port, origin_host_length, origin_port, payload_length = unpack_from("!IHHHHL", data, offset)
        offset += 16

        if len(data) < offset + host_length:
            raise ValueError("Cannot unpack Host, insufficient packet size")
        host = data[offset:offset + host_length]
        offset += host_length

        destination = (host, port)

        if len(data) < offset + origin_host_length:
            raise ValueError("Cannot unpack Origin Host, insufficient packet size")
        origin_host = data[offset:offset + origin_host_length]
        offset += origin_host_length

        origin = (origin_host, origin_port)

        if origin == ("0.0.0.0", 0):
            origin = None

        if destination == ("0.0.0.0", 0):
            destination = None

        if payload_length == 0:
            payload = None
        else:
            if len(data) < offset + payload_length:
                raise ValueError("Cannot unpack Data, insufficient packet size")
            payload = data[offset:offset + payload_length]

        return offset, placeholder.meta.payload.implement(circuit_id, destination, payload, origin)

    def _encode_ping(self, message):
        return pack('!I', message.payload.circuit_id),

    def _decode_ping(self, placeholder, offset, data):
        if len(data) < offset + 2:
            raise DropPacket("Insufficient packet size")

        circuit_id, = unpack_from('!I', data, offset)
        offset += 4

        return offset, placeholder.meta.payload.implement(circuit_id)

    def _encode_pong(self, message):
        return self._encode_ping(message)

    def _decode_pong(self, placeholder, offset, data):
        return self._decode_ping(placeholder, offset, data)

    def _encode_stats(self, message):
        return encode(message.payload.stats),

    def _decode_stats(self, placeholder, offset, data):
        offset, stats = decode(data, offset)
        return offset, placeholder.meta.payload.implement(stats)

    def _encode_decode(self, encode, decode, message):
        result = encode(message)
        try:
            decode(None, 0, result[0])

        except DropPacket:
            from traceback import print_exc
            print_exc()
            raise
        except:
            pass
        return result

    @staticmethod
    def swap_circuit_id(packet, old_circuit_id, new_circuit_id):
        circuit_id_pos = 31
        circuit_id, = unpack_from('!I', packet, circuit_id_pos)
        assert circuit_id == old_circuit_id, circuit_id
        packet = packet[:circuit_id_pos] + pack('!I', new_circuit_id) + packet[circuit_id_pos + 4:]
        return packet
