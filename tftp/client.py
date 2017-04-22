import struct
from socket import timeout

BYTE_OPCODE_NULL  = '\x00'
BYTE_OPCODE_READ  = '\x00\x01'
BYTE_OPCODE_WRITE = '\x00\x02'
BYTE_OPCODE_DATA  = '\x00\x03'
BYTE_OPCODE_ACK   = '\x00\x04'

OPCODE_NULL  = 0
OPCODE_READ  = 1
OPCODE_WRITE = 2
OPCODE_DATA  = 3
OPCODE_ACK   = 4

class Client:
    def __init__(self, socket):
        self.socket = socket

    def read(self, filename, ip, port):
        packet = self.__create_read_packet(filename)
        self.socket.sendto(packet, (ip, port))

        while True:
            try:
                # This returns two tuples, nested:
                #   (packet, (ip, port))
                # The Transmission ID is the response port that the server chooses.
                packet, (server_ip, tid) = self.socket.recvfrom(512)
            except timeout, msg:
                print 'Failed to receive from server: %s' % msg
                return False

            opcode, block_number, data = self.__parse_response_packet(packet)

            if not opcode == BYTE_OPCODE_DATA:
                print 'Received wrong opcode!'
                return False

            if not block_number == '\x00\x01':
                print 'Received invalid block number!'
                return False

            packet = self.__create_ack_packet(block_number)
            self.socket.sendto(packet, (server_ip, tid))
            if self.__received_stop_condition(data):
                return True

    def __create_read_packet(self, filename):
        format_string = self.__create_read_format_string(filename)
        return struct.pack(format_string, OPCODE_READ, filename, 0, 'octet', 0)

    def __create_ack_packet(self, block_number):
        format_string = self.__create_ack_format_string()
        return struct.pack(format_string, 4, 1)

    def __create_read_format_string(self, filename):
        format_string = '!'             # Network (big endian)
        format_string += 'H'            # opcode - two-byte unsigned short
        format_string += str(len(filename))
        format_string += 's'            # filename - string
        format_string += 'B'            # null byte - one-byte unsigned char
        format_string += '5s'           # mode - 'octet'
        format_string += 'B'            # null byte - one-byte unsigned char
        return format_string

    def __create_ack_format_string(self):
        format_string = '!'             # Network (big endian)
        format_string += 'H'            # opcode - two-byte unsigned short
        format_string += 'H'            # block number - two-byte unsigned short
        return format_string

    def __parse_response_packet(self, packet):
        '''
        server response packet structure:
         2 bytes     2 bytes      n bytes
         ----------------------------------
        | Opcode |   Block #  |   Data     |
         ----------------------------------
        '''
        opcode = packet[0] + packet[1]
        block_number = packet[2] + packet[3]
        data = packet[4:]
        return opcode, block_number, data

    def __received_stop_condition(self, data):
        return not len(data) == 512
