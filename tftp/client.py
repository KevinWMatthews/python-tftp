import struct
from socket import timeout

class Client:
    def __init__(self, socket):
        self.socket = socket

    def read(self, filename, ip, port):
        format_string = '!'             # Network (big endian)
        format_string += 'H'            # opcode - two-byte unsigned short
        format_string += str(len(filename))
        format_string += 's'            # filename - string
        format_string += 'B'            # null byte - one-byte unsigned char
        format_string += '5s'           # mode - 'octet'
        format_string += 'B'            # null byte - one-byte unsigned char
        packet = struct.pack(format_string, 1, filename, 0, 'octet', 0)
        self.socket.sendto(packet, (ip, port))

        # This returns two tuples, nested:
        #   (packet, socket_address)
        try:
            server_response = self.socket.recvfrom(512)
        except timeout, msg:
            print 'Failed to receive from server: %s' % msg
            return False

        packet = server_response[0]
        server_socket_addr = server_response[1]

        '''
        server response packet structure:
         2 bytes     2 bytes      n bytes
         ----------------------------------
        | Opcode |   Block #  |   Data     |
         ----------------------------------
        '''
        block_number = packet[2] + packet[3]
        if not block_number == '\x00\x01':
            return False

        # socket_address = (ip, port/tid)
        tid = server_socket_addr[1]

        format_string = '!'             # Network (big endian)
        # can do 2H
        format_string += 'H'            # opcode - two-byte unsigned short
        format_string += 'H'            # block number - two-byte unsigned short
        packet = struct.pack(format_string, 4, 1)
        self.socket.sendto(packet, (ip, tid))
        return True
