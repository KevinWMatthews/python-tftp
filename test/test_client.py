from tftp import Client
import mock

NULL_BYTE = '\x00'
OPCODE_READ = '\x00\x01'

def test_client_can_be_created():
    mock_socket = mock.Mock()
    assert Client(mock_socket)

def test_send_read_request():
    mock_socket = mock.Mock()

    filename = 'filename.ext'

    packet_string = OPCODE_READ
    packet_string += filename
    packet_string += NULL_BYTE
    packet_string += 'octet'
    packet_string += NULL_BYTE

    client = Client(mock_socket)

    assert packet_string == client.read(filename)
