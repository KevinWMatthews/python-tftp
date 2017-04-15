import struct

def create_packet(filename):
    return struct.pack("!HcB5sB", 1, 'a', 0, 'octet', 0)
