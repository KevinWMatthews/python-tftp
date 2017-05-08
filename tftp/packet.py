import struct

'''
 2 bytes     2 bytes
 ---------------------
| Opcode |   Block #  |
 ---------------------
Opcode = 4
 '''
class AckPacket:
    OPCODE = 4

    def __init__(self, block_number):
        self.block_number = block_number

    def network_string(self):
        format_string = self.__create_ack_format_string()
        return struct.pack(format_string, self.OPCODE, self.block_number)

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
Data may be from 0 to 512 bytes.
Data != 512 bytes signals a stop condition.
'''
class DataPacket:
    OPCODE = 3

    def __init__(self, block_number, payload):
        self.block_number = block_number
        self.data = payload
        self.block_size = 512

    def network_string(self):
        format_string = self.__create_format_string()
        opcode_and_block = struct.pack(format_string, self.OPCODE, self.block_number)
        return opcode_and_block + self.data

    def is_payload_valid(self):
        return len(self.data) <= self.block_size

    def is_stop_condition(self):
        if len(self.data) == self.block_size:
            return False
        return True

    @staticmethod
    def __create_format_string():
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
read request packet
2 bytes     string    1 byte     string   1 byte
 ------------------------------------------------
| Opcode |  Filename  |   0  |    Mode    |   0  |
 ------------------------------------------------
opcode = 1
mode may be octet, netascii, or mail
'''
class ReadPacket:
    OPCODE = 1

    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def network_string(self):
        format_string = self.__create_format_string()
        return struct.pack(format_string, self.OPCODE, self.filename, 0, self.mode, 0)

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

'''
Not in the TFTP RFC.
Implemented so the PacketParser can return an object that
behaves like a packet but signals that it is not a valid packet.
OPCODE = 0
'''
class InvalidPacket:
    OPCODE = 0

    def __init__(self, error_msg=''):
        self.error_msg = error_msg

class PacketParser:
    @staticmethod
    def parse(received):
        (opcode, block_number, payload) = PacketParser.__split_packet(received)
        if opcode == AckPacket.OPCODE:
            return AckPacket(block_number)
        elif opcode == DataPacket.OPCODE:
            return DataPacket(block_number, payload)
        else:
            return InvalidPacket()

    '''
     2 bytes     2 bytes
     ---------------------
    | Opcode |   Block #  |
     ---------------------
     '''
    @staticmethod
    def __split_packet(received):
        format_string = PacketParser.__create_format_string()
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
