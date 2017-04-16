import socket

class Client:
    def __init__(self, server_ip, client_directory, client_filename):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def get(self):
        pass
