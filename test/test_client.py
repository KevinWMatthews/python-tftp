import pytest
from tftp import Client
from mock import patch

def test_client_can_be_created():
    server_ip = '127.0.0.1'
    client_directory = '.'
    client_filename = 'tst.txt'
    assert Client(server_ip, client_directory, client_filename)

#TODO do we need to verify that we create a socket?
# Probably not If it sends to the socket, we're fine.
# Having said that, here's an example of how to test this.
@patch('socket.socket')
def test_client_creates_socket(mock_socket):
    server_ip = '127.0.0.1'
    client_directory = '.'
    client_filename = 'tst.txt'
    Client(server_ip, client_directory, client_filename)
    assert mock_socket.called
