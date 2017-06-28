import tftp
from socket import timeout
import struct

class Client:
    def __init__(self, socket):
        self.socket = socket
        self.block_size = 512
        self.buffer_size = self.__get_buffer_size(self.block_size)

    def read(self, filename, ip, port):
        mode = 'octet'
        resent_packet = 0

        self.__initiate_read_from_server(filename, mode, ip, port)

        # The first packet is special only in that we save the TID
        # for the rest of the transmission.
        (packet, tid) = self.__get_server_response(self.buffer_size)
        if not self.__is_valid_data_packet(packet):
            print 'Invalid server response! Aborting transfer.'
            return False
        if not packet.block_number == 1:
            print 'Received invalid block number!'
            print 'Aborting transfer!'
            return False

        # print 'Sending ack response to block number %d' % packet.block_number
        self.__send_ack_response(packet.block_number, ip, tid)
        last_packet_received = packet

        if packet.is_stop_condition():
            print 'Stop condition received. Checking for retransmission...'
            self.__check_for_retransmission(ip, tid)
            return True

        while True:
            (packet, port) = self.__get_server_response(self.buffer_size)
            if packet.OPCODE == tftp.TimeoutPacket.OPCODE:
                if last_packet_received == resent_packet:
                    print 'Server timed out twice.'
                    print 'Aborting transfer!'
                    return False
                resent_packet = last_packet_received
                packet = last_packet_received
            elif not self.__is_valid_data_packet(packet):
                print 'Invalid server response! Aborting transfer.'
                return False
            elif packet.block_number == last_packet_received.block_number:
                print 'Server resent last packet'
            elif not packet.block_number == last_packet_received.block_number+1:
                print 'Received invalid block number!'
                print 'Aborting transfer!'
                return False

            # print 'Sending ack response to block number %d' % packet.block_number
            self.__send_ack_response(packet.block_number, ip, tid)
            last_packet_received = packet

            if packet.is_stop_condition():
                print 'Stop condition received. Checking for retransmission...'
                self.__check_for_retransmission(ip, tid)
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
            return (tftp.TimeoutPacket(), 0)

        packet = tftp.PacketParser.parse(received)
        return (packet, tid)

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

    def __check_for_retransmission(self, server_ip, tid):
        (packet, port) = self.__get_server_response(self.buffer_size)
        if packet.OPCODE == tftp.TimeoutPacket.OPCODE:
            print 'Transfer success!'
        else:
            print 'Server timed out! Resending final ack'
            self.__send_ack_response(packet.block_number, server_ip, tid)
            print 'Not dallying for another retransmission'

class Client2:
    def __init__(self, socket):
        self.socket = socket
        self.block_size = 512
        self.buffer_size = self.__get_buffer_size(self.block_size)

    def read(self, filename, ip, port):
        mode = 'octet'
        resent_packet = 0

        self.__initiate_read_from_server(filename, mode, ip, port)

        # The first packet is special only in that we save the TID
        # for the rest of the transmission.
        (packet, tid) = self.__get_server_response(self.buffer_size)
        if not self.__is_valid_data_packet(packet):
            print 'Invalid server response! Aborting transfer.'
            return False
        if not packet.block_number == 1:
            print 'Received invalid block number!'
            print 'Aborting transfer!'
            return False

        # print 'Sending ack response to block number %d' % packet.block_number
        self.__send_ack_response(packet.block_number, ip, tid)
        last_packet_received = packet

        if packet.is_stop_condition():
            print 'Stop condition received. Checking for retransmission...'
            self.__check_for_retransmission(ip, tid)
            return True

        while True:
            (packet, port) = self.__get_server_response(self.buffer_size)
            if packet.OPCODE == tftp.TimeoutPacket.OPCODE:
                if last_packet_received == resent_packet:
                    print 'Server timed out twice.'
                    print 'Aborting transfer!'
                    return False
                resent_packet = last_packet_received
                packet = last_packet_received
            elif not self.__is_valid_data_packet(packet):
                print 'Invalid server response! Aborting transfer.'
                return False
            elif packet.block_number == last_packet_received.block_number:
                print 'Server resent last packet'
            elif not packet.block_number == last_packet_received.block_number+1:
                print 'Received invalid block number!'
                print 'Aborting transfer!'
                return False

            # print 'Sending ack response to block number %d' % packet.block_number
            self.__send_ack_response(packet.block_number, ip, tid)
            last_packet_received = packet

            if packet.is_stop_condition():
                print 'Stop condition received. Checking for retransmission...'
                self.__check_for_retransmission(ip, tid)
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
            return (tftp.TimeoutPacket(), 0)

        packet = tftp.PacketParser.parse(received)
        return (packet, tid)

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

    def __check_for_retransmission(self, server_ip, tid):
        (packet, port) = self.__get_server_response(self.buffer_size)
        if packet.OPCODE == tftp.TimeoutPacket.OPCODE:
            print 'Transfer success!'
        else:
            print 'Server timed out! Resending final ack'
            self.__send_ack_response(packet.block_number, server_ip, tid)
            print 'Not dallying for another retransmission'
