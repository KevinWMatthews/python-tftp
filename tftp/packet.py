import struct

class AckPacket:
    def __init__(self, opcode, block_number):
        self.opcode = opcode
        self.block_number = block_number

class DataPacket:
    def __init__(self, opcode, block_number, payload):
        self.opcode = opcode
        self.block_number = block_number
        self.data = payload

class PacketFactory:
    OPCODE_DATA  = 3
    OPCODE_ACK   = 4

    @staticmethod
    def parse(received):
        (opcode, block_number, payload) = PacketFactory.__split_packet(received)
        if opcode == PacketFactory.OPCODE_ACK:
            return AckPacket(opcode, block_number)
        elif opcode == PacketFactory.OPCODE_DATA:
            return DataPacket(opcode, block_number, payload)

    '''
     2 bytes     2 bytes
     ---------------------
    | Opcode |   Block #  |
     ---------------------
     '''
    @staticmethod
    def __split_packet(received):
        format_string = PacketFactory.__create_format_string()
        opcode_and_block = received[0:4]
        opcode, block_number = struct.unpack(format_string, opcode_and_block)
        payload = received[4:]
        return opcode, block_number, payload

    @staticmethod
    def __create_format_string():
        format_string = [
            '!',           # Network (big endian)
            'H',           # opcode - two-byte unsigned short
            'H',           # block number - two-byte unsigned short
        ]
        return ''.join(format_string)



class Packet:
    OPCODE_NULL  = 0
    OPCODE_READ  = 1
    OPCODE_WRITE = 2
    OPCODE_DATA  = 3
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
    read request packet
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
    data packet structure:
     2 bytes     2 bytes      n bytes
     ----------------------------------
    | Opcode |   Block #  |   Data     |
     ----------------------------------
    '''
    @staticmethod
    def create_data_packet(block_number, data):
        format_string = Packet.__create_data_format_string()
        opcode_and_block = struct.pack(format_string, Packet.OPCODE_DATA, block_number)
        return opcode_and_block + data

    @staticmethod
    def __create_data_format_string():
        format_string = [
            '!',           # Network (big endian)
            'H',           # opcode - two-byte unsigned short
            'H',           # block number - two-byte unsigned short
        ]
        # Rather than trying to pack a variable amount of data into the struct,
        # we'll just insist that the data is in string format and concatenate the strings.
        # Is this assumption valid?
        return ''.join(format_string)

    '''
     2 bytes     2 bytes
     ---------------------
    | Opcode |   Block #  |
     ---------------------
     '''
    @staticmethod
    def parse_ack_packet(packet):
        # struct.unpack() returns a tuple.
        # The number of elements in the tuple matches the number of elements
        # in unpack's format string.
        format_string = Packet.__create_data_format_string()
        return struct.unpack(format_string, packet)

    '''
    data packet structure:
     2 bytes     2 bytes      n bytes
     ----------------------------------
    | Opcode |   Block #  |   Data     |
     ----------------------------------
    '''
    @staticmethod
    def parse_data_packet(packet):
        # struct.unpack() returns a tuple.
        # The number of elements in the tuple matches the number of elements
        # in unpack's format string.
        format_string = Packet.__create_data_format_string()
        opcode_and_block = packet[0:4]
        opcode, block_number = struct.unpack(format_string, opcode_and_block)
        data = packet[4:]
        return opcode, block_number, data
