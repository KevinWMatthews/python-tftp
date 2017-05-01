import struct
from socket import timeout
import tftp

BYTE_OPCODE_NULL  = '\x00'
BYTE_OPCODE_READ  = '\x00\x01'
BYTE_OPCODE_WRITE = '\x00\x02'
BYTE_OPCODE_DATA  = '\x00\x03'
BYTE_OPCODE_ACK   = '\x00\x04'

OPCODE_NULL  = 0
OPCODE_READ  = 1
OPCODE_WRITE = 2
OPCODE_DATA  = 3

class Client:
    def __init__(self, socket):
        self.socket = socket

    def read(self, filename, ip, port):
        read_packet = tftp.ReadPacket(filename, 'octet')
        read_string = read_packet.network_string()
        self.socket.sendto(read_string, (ip, port))

        block_count = 0
        while True:
            try:
                # This returns two tuples, nested:
                #   (packet, (ip, port))
                # The Transmission ID is the response port that the server chooses.
                receive_packet, (server_ip, tid) = self.socket.recvfrom(517)
            except timeout, msg:
                print 'Failed to receive from server: %s' % msg
                return False

            block_count += 1
            opcode, block_number, data = self.__parse_receive_packet(receive_packet)

            if not opcode == BYTE_OPCODE_DATA:
                print 'Received wrong opcode!'
                return False

            if not block_number == block_count:
                print 'Received invalid block number!'
                return False

            # print 'Sending ack response to block number %d' % block_count
            ack_packet = tftp.AckPacket(block_number)
            ack_string = ack_packet.network_string()
            self.socket.sendto(ack_string, (server_ip, tid))
            if self.__received_stop_condition(data):
                print 'Download successful!'
                return True

    def __parse_receive_packet(self, packet):
        '''
        server response packet structure:
         2 bytes     2 bytes      n bytes
         ----------------------------------
        | Opcode |   Block #  |   Data     |
         ----------------------------------
        '''
        opcode = packet[0] + packet[1]
        block_bytes = packet[2] + packet[3]
        block_number = self.__unpack_block_number(block_bytes)
        data = packet[4:]
        return opcode, block_number, data

    def __received_stop_condition(self, data):
        length = len(data)
        # print 'Length of packet received: ' + str(length)
        if length > 512:
            print 'Received data packet larger than the 512 byte limit!'
            return True
        elif length < 512:
            return True
        elif length == 512:
            return False

    def __unpack_block_number(self, string):
        # unpack() returns a tuple.
        # The number of elements in the tuple matches the number of elements
        # in unpack's format string.
        format_string = '!'             # Network (big endian)
        format_string += 'H'            # block number - two-byte unsigned short
        block_tuple = struct.unpack(format_string, string)
        return block_tuple[0]
