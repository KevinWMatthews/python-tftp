import struct

class Packet:
    OPCODE_NULL  = '\x00'
    OPCODE_READ  = '\x00\x01'
    OPCODE_WRITE = '\x00\x02'
    OPCODE_DATA  = '\x00\x03'
    OPCODE_ACK   = '\x00\x04'

    '''
     2 bytes     2 bytes
     ---------------------
    | Opcode |   Block #  |
     ---------------------
     '''
    @staticmethod
    def create_ack_packet(block_number):
        block_string = Packet.__pack_block_number(block_number)
        return Packet.__create_packet(Packet.OPCODE_ACK, block_string)

    '''
    2 bytes     string    1 byte     string   1 byte
    ------------------------------------------------
    | Opcode |  Filename  |   0  |    Mode    |   0  |
    ------------------------------------------------
    '''
    @staticmethod
    def create_read_packet(filename):
        return Packet.__create_packet(Packet.OPCODE_READ, filename, Packet.OPCODE_NULL, 'octet', Packet.OPCODE_NULL)

    '''
    server response packet structure:
     2 bytes     2 bytes      n bytes
     ----------------------------------
    | Opcode |   Block #  |   Data     |
     ----------------------------------
    '''
    @staticmethod
    def create_data_response(block_number, data):
        block_string = Packet.__pack_block_number(block_number)
        return Packet.__create_packet(Packet.OPCODE_DATA, block_string, data)

    @staticmethod
    def __pack_block_number(block_number):
        return struct.pack('!H', block_number)

    # Create a general packet from the fields given.
    # Fields are concatenated in sequential order.
    # All fields must be of the same type (assumed to be a string).
    @staticmethod
    def __create_packet(*fields):
        return ''.join(fields)
