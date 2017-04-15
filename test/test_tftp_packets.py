import tftp

OPCODE_READ = '\x01'


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

    packet_string = OPCODE_READ.encode('hex')
    packet_string += filename.encode('hex')
    packet_string += '\x00'.encode('hex')
    packet_string += 'octet'.encode('hex')
    packet_string += '\x00'.encode('hex')

    assert tftp.create_packet(filename) == packet_string
