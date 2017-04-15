import socket

class Client:
    def __init__(self, server_ip, client_directory, client_filename):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)
