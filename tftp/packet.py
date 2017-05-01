import struct

'''
 2 bytes     2 bytes
 ---------------------
| Opcode |   Block #  |
 ---------------------
Opcode = 4
 '''
class AckPacket:
    def __init__(self, block_number):
        self.opcode = 4
        self.block_number = block_number

    def to_string(self):
        format_string = self.__create_ack_format_string()
        return struct.pack(format_string, self.opcode, self.block_number)

    def __create_ack_format_string(self):
        format_string = [
            '!',           # Network (big endian)
            'H',           # opcode - two-byte unsigned short
            'H',           # block number - two-byte unsigned short
        ]
        return ''.join(format_string)

'''
 2 bytes     2 bytes      n bytes
 ----------------------------------
| Opcode |   Block #  |   Data     |
 ----------------------------------
Opcode = 3
'''
class DataPacket:
    def __init__(self, block_number, payload):
        self.opcode = 3
        self.block_number = block_number
        self.data = payload

'''
read request packet
2 bytes     string    1 byte     string   1 byte
 ------------------------------------------------
| Opcode |  Filename  |   0  |    Mode    |   0  |
 ------------------------------------------------
opcode = 1
'''
class ReadPacket:
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def to_string(self):
        format_string = self.__create_format_string()
        return struct.pack(format_string, 1, self.filename, 0, self.mode, 0)

    def __create_format_string(self):
        format_string = [
            '!',           # Network (big endian)
            'H',           # opcode - two-byte unsigned short
            str(len(self.filename)),
            's',           # filename - string
            'B',           # null byte - one-byte unsigned char
            '5s',          # mode - 'octet'
            'B',           # null byte - one-byte unsigned char
        ]
        return ''.join(format_string)

class PacketFactory:
    OPCODE_DATA  = 3
    OPCODE_ACK   = 4

    @staticmethod
    def parse(received):
        (opcode, block_number, payload) = PacketFactory.__split_packet(received)
        if opcode == PacketFactory.OPCODE_ACK:
            return AckPacket(block_number)
        elif opcode == PacketFactory.OPCODE_DATA:
            return DataPacket(block_number, payload)

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
