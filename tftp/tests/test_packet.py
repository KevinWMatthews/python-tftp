from tftp import Packet

from random import choice
from string import printable
from struct import pack

OPCODE_NULL = '\x00'
OPCODE_READ = '\x00\x01'
OPCODE_WRITE = '\x00\x02'
OPCODE_DATA = '\x00\x03'
OPCODE_ACK  = '\x00\x04'

MAX_DATA_SIZE = 512
MAX_BLOCK_NUMBER = 65535

# Create various TFTP packets
'''
server response packet structure:
 2 bytes     2 bytes      n bytes
 ----------------------------------
| Opcode |   Block #  |   Data     |
 ----------------------------------
'''
def create_data_response(block_number, data):
    block_string = pack_block_number(block_number)
    return create_packet(OPCODE_DATA, block_string, data)

# Create a general packet from the fields given.
# Fields are concatenated in sequential order.
# All fields must be of the same type (assumed to be a string).
def create_packet(*fields):
    return ''.join(fields)

# Python's sendto() and recvfrom() methods accept and return a tuple containing:
#   (data, (ip, port))
# They package the ip and port together - the socket address.
def create_socket_tuple(packet, ip, port):
    return (packet, (ip, port))

# Return the block number as a string of hex
def pack_block_number(block_number):
    return pack('!H', block_number)

def create_random_data_string(n_bytes):
    random_chars = (choice(printable) for i in range(n_bytes))
    return ''.join(random_chars)

class TestPacket:
    def test_ack_packet_smallest_block_number(self):
        assert '\x00\x04\x00\x00' == Packet.create_ack_packet(0)

    def test_ack_packet_largest_block_number(self):
        assert '\x00\x04\xff\xff' == Packet.create_ack_packet(MAX_BLOCK_NUMBER)

    def test_read_packet_shortest_filename(self):
        assert '\x00\x01a\x00octet\x00' == Packet.create_read_packet('a')

    def test_empty_data_packet_smallest_block(self):
        string = create_random_data_string(0)
        assert 0 == len(string)
        assert '\x00\x03\x00\x00' + string == create_data_response(0, string)

    def test_empty_data_packet_largest_block(self):
        string = create_random_data_string(0)
        assert 0 == len(string)
        assert '\x00\x03\xff\xff' == create_data_response(MAX_BLOCK_NUMBER, string)

    def test_shortest_data_packet_smallest_block(self):
        string = create_random_data_string(1)
        assert 1 == len(string)
        assert '\x00\x03\x00\x00' + string == create_data_response(0, string)

    def test_shortest_data_packet_largest_block(self):
        string = create_random_data_string(1)
        assert 1 == len(string)
        assert '\x00\x03\xff\xff' + string == create_data_response(MAX_BLOCK_NUMBER, string)

    def test_largest_data_packet_smallest_block(self):
        string = create_random_data_string(MAX_DATA_SIZE)
        assert MAX_DATA_SIZE == len(string)
        assert '\x00\x03\x00\x00' + string == create_data_response(0, string)

    def test_largest_data_packet_largest_block(self):
        string = create_random_data_string(MAX_DATA_SIZE)
        assert MAX_DATA_SIZE == len(string)
        assert '\x00\x03\xff\xff' + string == create_data_response(MAX_BLOCK_NUMBER, string)
