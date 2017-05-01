from tftp import AckPacket, ReadPacket, DataPacket, PacketParser
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

class TestAckPacket:
    def test_ack_packet_smallest_block_number(self):
        block_number = 0
        packet = AckPacket(block_number)
        assert '\x00\x04\x00\x00' == packet.network_string()

    def test_ack_packet_largest_block_number(self):
        block_number = MAX_BLOCK_NUMBER
        packet = AckPacket(block_number)
        assert '\x00\x04\xff\xff' == packet.network_string()

class TestReadPacket:
    def test_read_packet_shortest_filename(self):
        filename = 'a'
        mode = 'octet'
        packet = ReadPacket(filename, mode)
        assert '\x00\x01a\x00octet\x00' == packet.network_string()

    def test_read_packet_longer_filename(self):
        filename = 'abcdefg'
        mode = 'octet'
        packet = ReadPacket(filename, mode)
        assert '\x00\x01abcdefg\x00octet\x00' == packet.network_string()

class TestDataPacket:
    def test_empty_data_packet_smallest_block(self):
        block_number = 0
        string = create_random_data_string(0)
        packet = DataPacket(block_number, string)
        assert '\x00\x03\x00\x00' + string == packet.network_string()

    def test_empty_data_packet_largest_block(self):
        block_number = MAX_BLOCK_NUMBER
        string = create_random_data_string(0)
        packet = DataPacket(block_number, string)
        assert '\x00\x03\xff\xff' == packet.network_string()

    def test_shortest_data_packet_smallest_block(self):
        block_number = 0
        string = create_random_data_string(1)
        packet = DataPacket(block_number, string)
        assert '\x00\x03\x00\x00' + string == packet.network_string()

    def test_shortest_data_packet_largest_block(self):
        block_number = MAX_BLOCK_NUMBER
        string = create_random_data_string(1)
        packet = DataPacket(block_number, string)
        assert '\x00\x03\xff\xff' + string == packet.network_string()

    def test_largest_data_packet_smallest_block(self):
        block_number = 0
        string = create_random_data_string(MAX_DATA_SIZE)
        packet = DataPacket(block_number, string)
        assert '\x00\x03\x00\x00' + string == packet.network_string()

    def test_largest_data_packet_largest_block(self):
        block_number = MAX_BLOCK_NUMBER
        string = create_random_data_string(MAX_DATA_SIZE)
        packet = DataPacket(block_number, string)
        assert '\x00\x03\xff\xff' + string == packet.network_string()

class TestPacketParse:
    def test_parse_ack_packet_with_smallest_block_number(self):
        received = '\x00\x04\x00\x00'
        packet = PacketParser.parse(received)
        assert OPCODE_ACK == packet.OPCODE
        assert 0 == packet.block_number

    def test_parse_ack_packet_with_largest_block_number(self):
        received = '\x00\x04\xff\xff'
        packet = PacketParser.parse(received)
        assert OPCODE_ACK == packet.OPCODE
        assert MAX_BLOCK_NUMBER == packet.block_number

    def test_parse_empty_data_packet_smallest_block_number(self):
        string = ''
        received = '\x00\x03\x00\x00' + string
        packet = PacketParser.parse(received)
        assert OPCODE_DATA == packet.OPCODE
        assert 0 == packet.block_number
        assert string == packet.data

    def test_parse_empty_data_packet_largest_block_number(self):
        string = ''
        received = '\x00\x03\xff\xff' + string
        packet = PacketParser.parse(received)
        assert OPCODE_DATA == packet.OPCODE
        assert MAX_BLOCK_NUMBER == packet.block_number
        assert string == packet.data

    def test_shortest_data_packet_smallest_block(self):
        string = create_random_data_string(1)
        received = '\x00\x03\x00\x00' + string
        packet = PacketParser.parse(received)
        assert OPCODE_DATA == packet.OPCODE
        assert 0 == packet.block_number
        assert string == packet.data

    def test_shortest_data_packet_largest_block(self):
        string = create_random_data_string(1)
        received = '\x00\x03\xff\xff' + string
        packet = PacketParser.parse(received)
        assert OPCODE_DATA == packet.OPCODE
        assert MAX_BLOCK_NUMBER == packet.block_number
        assert string == packet.data

    def test_largest_data_packet_smallest_block(self):
        string = create_random_data_string(MAX_DATA_SIZE)
        received = '\x00\x03\x00\x00' + string
        packet = PacketParser.parse(received)
        assert OPCODE_DATA == packet.OPCODE
        assert 0 == packet.block_number
        assert string == packet.data

    def test_largest_data_packet_largest_block(self):
        string = create_random_data_string(MAX_DATA_SIZE)
        received = '\x00\x03\xff\xff' + string
        packet = PacketParser.parse(received)
        assert OPCODE_DATA == packet.OPCODE
        assert MAX_BLOCK_NUMBER == packet.block_number
        assert string == packet.data
