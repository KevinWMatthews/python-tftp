import tftp
from socket import timeout
import struct

class Client:
    def __init__(self, socket):
        self.socket = socket
        self.block_size = 512

    def read(self, filename, ip, port):
        mode = 'octet'
        self.__initiate_read_from_server(filename, mode, ip, port)

        buffer_size = self.__get_buffer_size(self.block_size)
        block_count = 0
        (packet, server_ip, tid) = self.__get_server_response(buffer_size)

        while True:
            if not packet.OPCODE == tftp.DataPacket.OPCODE:
                print 'Received wrong opcode!'
                print 'Aborting transfer!'
                return False
            if not packet.is_payload_valid():
                print 'Packet payload is invalid!'
                print 'Aborting transfer!'
                return False

            block_count += 1

            if self.__is_packet_retry(packet, block_count):
                print 'Server resending packet!'
                block_count -= 1

            if not self.__is_valid_block_number(packet, block_count):
                print 'Received invalid block number!'
                return False

            # print 'Sending ack response to block number %d' % block_count
            self.__send_ack_response(packet.block_number, server_ip, tid)

            if packet.is_stop_condition():
                print 'Stop condition received.'
                print 'Ending transfer!'
                return True

            (packet, ip, port) = self.__get_server_response(buffer_size)

    def __initiate_read_from_server(self, filename, mode, ip, port):
        read_packet = tftp.ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        self.socket.sendto(read_string, (ip, port))

    def __get_server_response(self, buffer_size):
        try:
            # This returns two tuples, nested:
            #   (packet, (ip, port))
            # The Transmission ID is the response port that the server chooses.
            received, (server_ip, tid) = self.socket.recvfrom(buffer_size)
        except timeout, msg:
            print 'Failed to receive from server: %s' % msg
            return (tftp.InvalidPacket(), '', 0)

        packet = tftp.PacketParser.parse(received)

        return (packet, server_ip, tid)

    def __is_valid_data_packet(self, packet):
        pass

    def __is_valid_block_number(self, packet, block_count):
        if packet.block_number == block_count:
            return True
        return False

    def __is_packet_retry(self, packet, block_count):
        if packet.block_number == block_count - 1:
            return True
        return False

    def __send_ack_response(self, block_number, server_ip, tid):
        ack_packet = tftp.AckPacket(block_number)
        ack_string = ack_packet.network_string()
        self.socket.sendto(ack_string, (server_ip, tid))

    def __get_buffer_size(self, block_size):
        opcode_length = 2
        block_number_length = 2
        return opcode_length + block_number_length + block_size
