from tftp import Client
import pytest
import mock

NULL_BYTE = '\x00'
OPCODE_READ = '\x00\x01'

class TestClient:

    @pytest.fixture
    def mock_socket(self):
        mock_sock = mock.Mock()
        return mock_sock

    def test_client_can_be_created(self, mock_socket):
        assert Client(mock_socket)

    def test_send_read_request(self, mock_socket):
        filename = 'a'

        packet_string = OPCODE_READ
        packet_string += filename
        packet_string += NULL_BYTE
        packet_string += 'octet'
        packet_string += NULL_BYTE

        client = Client(mock_socket)

        assert packet_string == client.read(filename)

    def test_read_request_with_different_filename(self, mock_socket):
        filename = 'b'

        packet_string = OPCODE_READ
        packet_string += filename
        packet_string += NULL_BYTE
        packet_string += 'octet'
        packet_string += NULL_BYTE

        client = Client(mock_socket)

        assert packet_string == client.read(filename)

    def test_create_receive_packet_with_longer_filename(self, mock_socket):
        filename = 'test.txt'

        packet_string = OPCODE_READ
        packet_string += filename
        packet_string += NULL_BYTE
        packet_string += 'octet'
        packet_string += NULL_BYTE

        client = Client(mock_socket)

        assert packet_string == client.read(filename)
