import struct

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
        #   (data, (ip, port))
        server_response = self.socket.recvfrom(512)

        server_socket_addr = server_response[1]
        tid = server_socket_addr[1]
        format_string = '!'             # Network (big endian)
        # can do 2H
        format_string += 'H'            # opcode - two-byte unsigned short
        format_string += 'H'            # byte number - two-byte unsigned short
        packet = struct.pack(format_string, 4, 1)
        self.socket.sendto(packet, (ip, tid))
