import struct

def create_packet(filename):
    return struct.pack("!HcB5sB", 1, filename, 0, 'octet', 0)
