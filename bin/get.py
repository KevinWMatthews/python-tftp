#!/usr/bin/env python

from tftp import Client
import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#TODO do we need to set the socket timeout? If so, whose responsibility is this?
client = Client(client_socket)
client.read('tst.txt')
