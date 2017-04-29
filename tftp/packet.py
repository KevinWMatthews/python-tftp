import struct

class Packet:
    OPCODE_ACK  = '\x00\x04'

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

    @staticmethod
    def __pack_block_number(block_number):
        return struct.pack('!H', block_number)

    # Create a general packet from the fields given.
    # Fields are concatenated in sequential order.
    # All fields must be of the same type (assumed to be a string).
    @staticmethod
    def __create_packet(*fields):
        return ''.join(fields)
