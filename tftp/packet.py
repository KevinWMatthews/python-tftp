import struct

class Packet:
    OPCODE_NULL  = 0
    OPCODE_READ  = 1
    OPCODE_WRITE = '\x00\x02'
    OPCODE_DATA  = '\x00\x03'
    OPCODE_ACK   = 4

    '''
     2 bytes     2 bytes
     ---------------------
    | Opcode |   Block #  |
     ---------------------
     '''
    @staticmethod
    def create_ack_packet(block_number):
        format_string = Packet.__create_ack_format_string()
        return struct.pack(format_string, Packet.OPCODE_ACK, block_number)

    @staticmethod
    def __create_ack_format_string():
        format_string = [
            '!',           # Network (big endian)
            'H',           # opcode - two-byte unsigned short
            'H',           # block number - two-byte unsigned short
        ]
        return ''.join(format_string)

    '''
    2 bytes     string    1 byte     string   1 byte
    ------------------------------------------------
    | Opcode |  Filename  |   0  |    Mode    |   0  |
    ------------------------------------------------
    '''
    @staticmethod
    def create_read_packet(filename):
        format_string = Packet.__create_read_format_string(filename)
        return struct.pack(format_string, Packet.OPCODE_READ, filename, Packet.OPCODE_NULL, 'octet', Packet.OPCODE_NULL)

    @staticmethod
    def __create_read_format_string(filename):
        format_string = [
            '!',           # Network (big endian)
            'H',           # opcode - two-byte unsigned short
            str(len(filename)),
            's',           # filename - string
            'B',           # null byte - one-byte unsigned char
            '5s',          # mode - 'octet'
            'B',           # null byte - one-byte unsigned char
        ]
        return ''.join(format_string)

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

    # Return the block number as a string of hex
    @staticmethod
    def __pack_block_number(block_number):
        return struct.pack('!H', block_number)

    # Create a general packet from the fields given.
    # Fields are concatenated in sequential order.
    # All fields must be of the same type (assumed to be a string).
    @staticmethod
    def __create_packet(*fields):
        return ''.join(fields)
