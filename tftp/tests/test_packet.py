from tftp import Packet, PacketFactory
import pytest

from random import choice
from string import printable

MAX_DATA_SIZE = 512
MAX_BLOCK_NUMBER = 65535

OPCODE_DATA  = 3
OPCODE_ACK   = 4

def create_random_data_string(n_bytes):
    random_chars = (choice(printable) for i in range(n_bytes))
    return ''.join(random_chars)

class TestPacketCreate:
    def test_ack_packet_smallest_block_number(self):
        block_number = 0
        packet = PacketFactory.factory(OPCODE_ACK, block_number)
        assert '\x00\x04\x00\x00' == packet.to_string()

    def test_ack_packet_largest_block_number(self):
        assert '\x00\x04\xff\xff' == Packet.create_ack_packet(MAX_BLOCK_NUMBER)

    def test_read_packet_shortest_filename(self):
        assert '\x00\x01a\x00octet\x00' == Packet.create_read_packet('a')

    def test_empty_data_packet_smallest_block(self):
        string = create_random_data_string(0)
        assert 0 == len(string)
        assert '\x00\x03\x00\x00' + string == Packet.create_data_packet(0, string)

    def test_empty_data_packet_largest_block(self):
        string = create_random_data_string(0)
        assert 0 == len(string)
        assert '\x00\x03\xff\xff' == Packet.create_data_packet(MAX_BLOCK_NUMBER, string)

    def test_shortest_data_packet_smallest_block(self):
        string = create_random_data_string(1)
        assert 1 == len(string)
        assert '\x00\x03\x00\x00' + string == Packet.create_data_packet(0, string)

    def test_shortest_data_packet_largest_block(self):
        string = create_random_data_string(1)
        assert 1 == len(string)
        assert '\x00\x03\xff\xff' + string == Packet.create_data_packet(MAX_BLOCK_NUMBER, string)

    def test_largest_data_packet_smallest_block(self):
        string = create_random_data_string(MAX_DATA_SIZE)
        assert MAX_DATA_SIZE == len(string)
        assert '\x00\x03\x00\x00' + string == Packet.create_data_packet(0, string)

    def test_largest_data_packet_largest_block(self):
        string = create_random_data_string(MAX_DATA_SIZE)
        assert MAX_DATA_SIZE == len(string)
        assert '\x00\x03\xff\xff' + string == Packet.create_data_packet(MAX_BLOCK_NUMBER, string)

class TestPacketParse:
    def test_parse_ack_packet_with_smallest_block_number(self):
        received = '\x00\x04\x00\x00'
        packet = PacketFactory.parse(received)
        assert OPCODE_ACK == packet.opcode
        assert 0 == packet.block_number

    def test_parse_ack_packet_with_largest_block_number(self):
        received = '\x00\x04\xff\xff'
        packet = PacketFactory.parse(received)
        assert OPCODE_ACK == packet.opcode
        assert MAX_BLOCK_NUMBER == packet.block_number

        #  assert (Packet.OPCODE_ACK, MAX_BLOCK_NUMBER) == Packet.parse_ack_packet(packet)

    def test_parse_empty_data_packet_smallest_block_number(self):
        string = ''
        received = '\x00\x03\x00\x00' + string
        packet = PacketFactory.parse(received)
        assert OPCODE_DATA == packet.opcode
        assert 0 == packet.block_number
        assert string == packet.data

    def test_parse_empty_data_packet_largest_block_number(self):
        string = ''
        received = '\x00\x03\xff\xff' + string
        packet = PacketFactory.parse(received)
        assert OPCODE_DATA == packet.opcode
        assert MAX_BLOCK_NUMBER == packet.block_number
        assert string == packet.data

    def test_shortest_data_packet_smallest_block(self):
        string = create_random_data_string(1)
        received = '\x00\x03\x00\x00' + string
        packet = PacketFactory.parse(received)
        assert OPCODE_DATA == packet.opcode
        assert 0 == packet.block_number
        assert string == packet.data

    def test_shortest_data_packet_largest_block(self):
        string = create_random_data_string(1)
        received = '\x00\x03\xff\xff' + string
        packet = PacketFactory.parse(received)
        assert OPCODE_DATA == packet.opcode
        assert MAX_BLOCK_NUMBER == packet.block_number
        assert string == packet.data

    def test_largest_data_packet_smallest_block(self):
        string = create_random_data_string(MAX_DATA_SIZE)
        received = '\x00\x03\x00\x00' + string
        packet = PacketFactory.parse(received)
        assert OPCODE_DATA == packet.opcode
        assert 0 == packet.block_number
        assert string == packet.data

    def test_largest_data_packet_largest_block(self):
        string = create_random_data_string(MAX_DATA_SIZE)
        received = '\x00\x03\xff\xff' + string
        packet = PacketFactory.parse(received)
        assert OPCODE_DATA == packet.opcode
        assert MAX_BLOCK_NUMBER == packet.block_number
        assert string == packet.data
