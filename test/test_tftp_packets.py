import pytest
import tftp

NULL_BYTE = '\x00'
OPCODE_READ = '\x00\x01'


def test_create_receive_packet():
    filename = 'a'

    packet_string = OPCODE_READ
    packet_string += filename
    packet_string += NULL_BYTE
    packet_string += 'octet'
    packet_string += NULL_BYTE

    assert tftp.create_packet(filename) == packet_string

def test_create_receive_packet_with_different_filename():
    filename = 'b'

    packet_string = OPCODE_READ
    packet_string += filename
    packet_string += NULL_BYTE
    packet_string += 'octet'
    packet_string += NULL_BYTE

    assert tftp.create_packet(filename) == packet_string

def test_create_receive_packet_with_longer_filename():
    filename = 'test.txt'

    packet_string = OPCODE_READ
    packet_string += filename
    packet_string += NULL_BYTE
    packet_string += 'octet'
    packet_string += NULL_BYTE

    assert tftp.create_packet(filename) == packet_string
