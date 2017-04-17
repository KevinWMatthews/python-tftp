import socket

class ProductionClass():
    def __init__(self):
        pass

    def method(self):
        pass

class PC():
    def __init__(self, socket):
        self.s = socket

    def call_socket(self):
        self.s()

class Client:
    def __init__(self, server_ip, client_directory, client_filename):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def get(self):
        pass

class Client2:
    def __init__(self, socket):
        self.socket = socket

    def send_to_socket(self):
        self.socket.sendto()
