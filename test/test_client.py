import pytest
from tftp import Client
from mock import patch
import socket

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

#  @patch('socket.socket.sendto')
#  @patch('socket.socket')
#  def test_get_sends_read_request(mock_socket, mock_method):
#      server_ip = '127.0.0.1'
#      client_directory = '.'
#      client_filename = 'tst.txt'
#      client = Client(server_ip, client_directory, client_filename)
#      #TODO Redo with socket defined here.
#      #  client.get()
#      
#      assert mock_socket.called
#      #  assert mock_method.called
#      mock_method.assert_called()

#  def test_get_sends_read_request2():
#      server_ip = '127.0.0.1'
#      client_directory = '.'
#      client_filename = 'tst.txt'
#      client = Client(server_ip, client_directory, client_filename)
#      with patch.object(socket.socket, 'send', return_value=None) as mm:
#          sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#          sock.send('data')#, ('localhost, 69'))
#      mm.assert_called()
#      #  assert mock_socket.called
#      #  mock_socket.sendto.assert_called()
