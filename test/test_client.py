from tftp import Client
import mock

NULL_BYTE = '\x00'
OPCODE_READ = '\x00\x01'

class TestClient:

    def test_client_can_be_created(self):
        mock_socket = mock.Mock()
        assert Client(mock_socket)

    def test_send_read_request(self):
        mock_socket = mock.Mock()

        filename = 'a'

        packet_string = OPCODE_READ
        packet_string += filename
        packet_string += NULL_BYTE
        packet_string += 'octet'
        packet_string += NULL_BYTE

        client = Client(mock_socket)

        assert packet_string == client.read(filename)

    def test_read_request_with_different_filename(self):
        mock_socket = mock.Mock()

        filename = 'b'

        packet_string = OPCODE_READ
        packet_string += filename
        packet_string += NULL_BYTE
        packet_string += 'octet'
        packet_string += NULL_BYTE

        client = Client(mock_socket)

        assert packet_string == client.read(filename)

    def test_create_receive_packet_with_longer_filename(self):
        mock_socket = mock.Mock()

        filename = 'test.txt'

        packet_string = OPCODE_READ
        packet_string += filename
        packet_string += NULL_BYTE
        packet_string += 'octet'
        packet_string += NULL_BYTE

        client = Client(mock_socket)

        assert packet_string == client.read(filename)
