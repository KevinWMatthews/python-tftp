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
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'a'

        packet_string = OPCODE_READ
        packet_string += filename
        packet_string += NULL_BYTE
        packet_string += 'octet'
        packet_string += NULL_BYTE

        client = Client(mock_socket)

        client.read(filename, server_ip, server_port)
        mock_socket.sendto.assert_called_with(packet_string, (server_ip, server_port))

    def test_read_a_different_filename(self, mock_socket):
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'b'

        packet_string = OPCODE_READ
        packet_string += filename
        packet_string += NULL_BYTE
        packet_string += 'octet'
        packet_string += NULL_BYTE

        client = Client(mock_socket)

        client.read(filename, server_ip, server_port)
        mock_socket.sendto.assert_called_with(packet_string, (server_ip, server_port))

    def test_read_a_longer_filename(self, mock_socket):
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'

        packet_string = OPCODE_READ
        packet_string += filename
        packet_string += NULL_BYTE
        packet_string += 'octet'
        packet_string += NULL_BYTE

        client = Client(mock_socket)

        client.read(filename, server_ip, server_port)
        mock_socket.sendto.assert_called_with(packet_string, (server_ip, server_port))

    @pytest.mark.skip('todo')
    def test_read_from_different_server_ip_address(self, mock_socket):
        pass

    @pytest.mark.skip('todo')
    def test_read_from_different_server_port(self, mock_socket):
        pass
