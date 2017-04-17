import struct

class Client:
    def __init__(self, socket):
        pass

    def read(self, filename):
        format_string = '!'             # Network (big endian)
        format_string += 'H'            # opcode - two-byte unsigned short
        format_string += str(len(filename))
        format_string += 's'            # filename - string
        format_string += 'B'            # null byte - one-byte unsigned char
        format_string += '5s'           # mode - 'octet'
        format_string += 'B'            # null byte - one-byte unsigned char
        return struct.pack(format_string, 1, filename, 0, 'octet', 0)
