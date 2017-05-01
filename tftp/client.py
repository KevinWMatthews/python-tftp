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
                received, (server_ip, tid) = self.socket.recvfrom(517)
            except timeout, msg:
                print 'Failed to receive from server: %s' % msg
                return False

            block_count += 1
            packet = tftp.PacketParser.parse(received)

            if not packet.OPCODE == tftp.DataPacket.OPCODE:
                print 'Received wrong opcode!'
                return False

            if not packet.block_number == block_count:
                print 'Received invalid block number!'
                return False

            # TFTP protocol imposes no restrictions on data (that I know of).

            # print 'Sending ack response to block number %d' % block_count
            ack_packet = tftp.AckPacket(packet.block_number)
            ack_string = ack_packet.network_string()
            self.socket.sendto(ack_string, (server_ip, tid))
            if packet.is_stop_condition():
                print 'Download successful!'
                return True
