import tftp
from socket import timeout
import struct

class Client:
    def __init__(self, socket):
        self.socket = socket
        self.block_size = 512

    def read(self, filename, ip, port):
        mode = 'octet'
        buffer_size = self.__get_buffer_size(self.block_size)

        self.__initiate_read_from_server(filename, mode, ip, port)

        # The first packet is special only in that we save the TID
        # for the rest of the transmission.
        (packet, server_ip, tid) = self.__get_server_response(buffer_size)
        if not self.__is_valid_data_packet(packet):
            print 'Invalid server response! Aborting transfer.'
            return False
        if not packet.block_number == 1:
            print 'Received invalid block number!'
            print 'Aborting transfer!'
            return False

        # print 'Sending ack response to block number %d' % packet.block_number
        last_block_number = 1
        self.__send_ack_response(packet.block_number, server_ip, tid)

        #TODO is this tested?
        if packet.is_stop_condition():
            print 'Stop condition received.'
            print 'Ending transfer!'
            return True

        while True:
            (packet, ip, port) = self.__get_server_response(buffer_size)

            if not self.__is_valid_data_packet(packet):
                print 'Invalid server response! Aborting transfer.'
                return False

            if packet.block_number == last_block_number+1:
                last_block_number += 1
            elif packet.block_number == last_block_number:
                print 'Server resent last packet'
            else:
                print 'Received invalid block number!'
                print 'Aborting transfer!'
                return False

            # print 'Sending ack response to block number %d' % packet.block_number
            self.__send_ack_response(packet.block_number, server_ip, tid)

            if packet.is_stop_condition():
                print 'Stop condition received.'
                print 'Ending transfer!'
                return True


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

    def __send_ack_response(self, block_number, server_ip, tid):
        ack_packet = tftp.AckPacket(block_number)
        ack_string = ack_packet.network_string()
        self.socket.sendto(ack_string, (server_ip, tid))

    def __get_buffer_size(self, block_size):
        opcode_length = 2
        block_number_length = 2
        return opcode_length + block_number_length + block_size

    def __is_valid_data_packet(self, packet):
        #TODO it seems bad that different packet types have different interfaces
        if not packet.OPCODE == tftp.DataPacket.OPCODE:
            print 'Received wrong opcode!'
            return False
        if not packet.is_payload_valid():
            print 'Packet payload is invalid!'
            return False
        return True
