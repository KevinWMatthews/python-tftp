import pytest
import tftp

NULL_BYTE = '\x00'
OPCODE_READ = '\x00\x01'


def test_create_receive_packet():
    filename = 'a'

    """
    Field       Hex
    Opcode      01
    Filename    61 <-> 'a'
    Null        00
    Mode        6f 63 74 65 74 <-> octet
    Null        00
    """

    packet_string = OPCODE_READ
    packet_string += filename
    packet_string += NULL_BYTE
    packet_string += 'octet'
    packet_string += NULL_BYTE

    assert tftp.create_packet(filename) == packet_string

def test_create_receive_packet_with_different_filename():
    filename = 'b'

    """
    Field       Hex
    Opcode      01
    Filename    62 <-> 'b'
    Null        00
    Mode        6f 63 74 65 74 <-> octet
    Null        00
    """

    packet_string = OPCODE_READ
    packet_string += filename
    packet_string += NULL_BYTE
    packet_string += 'octet'
    packet_string += NULL_BYTE

    assert tftp.create_packet(filename) == packet_string
