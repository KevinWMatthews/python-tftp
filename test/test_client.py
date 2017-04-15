import pytest
from tftp import Client

def test_client_can_be_created():
    server_ip = '127.0.0.1'
    client_directory = '.'
    client_filename = 'tst.txt'
    assert Client(server_ip, client_directory, client_filename)

#TODO do we need to verify that we create a socket?
# Let's go with no. If it sends to the socket, we're fine.


@pytest.mark.skip(reason="Need to add parameters to Client initilization")
def test_send_read_request():
    server_ip = '127.0.0.1'
    client_directory = '.'
    client_filename = 'tst.txt'
    assert Client(server_ip, client_directory, client_filename)
