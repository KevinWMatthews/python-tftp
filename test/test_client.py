from tftp import Client
import pytest
import mock
from socket import timeout

NULL_BYTE = '\x00'
OPCODE_READ = '\x00\x01'
OPCODE_DATA = '\x00\x03'
OPCODE_ACK  = '\x00\x04'

'''
Test list:
    Read request sendto() must handle failure.

    Server response to read packet:
        invalid
            no response
            wrong block number
            ?
        valid
            short data (end transmission)
'''

class TestClient:

    @pytest.fixture
    def mock_socket(self):
        mock_sock = mock.Mock()
        return mock_sock

    def test_client_can_be_created(self, mock_socket):
        assert Client(mock_socket)

    @pytest.mark.skip('Need to handle server response')
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

    @pytest.mark.skip('Need to handle server response')
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

    @pytest.mark.skip('Need to handle server response')
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

    '''
    Client          Server
    ______________________
    Read    -->
            <--     Data 1 (< 512 K)
    Ack     -->
    '''
    def test_parse_first_read_response(self, mock_socket):
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'

        read_request = OPCODE_READ
        read_request += filename
        read_request += NULL_BYTE
        read_request += 'octet'
        read_request += NULL_BYTE

        block_number = '\x00\x01'       # block number 1
        data = 'B\x0a'                  # data in our file: 'B' and LF
        server_packet = OPCODE_DATA
        server_packet += block_number
        server_packet += data

        ack_packet = OPCODE_ACK
        ack_packet += block_number

        tid = 12345                     # transmission id (port) is random?
        server_response = (server_packet, (server_ip, tid))
        mock_socket.recvfrom = mock.Mock(return_value = server_response)

        client = Client(mock_socket)
        client.read(filename, server_ip, server_port)
        # This works.
        #  calls = [
        #          mock.call(read_request, (server_ip, server_port)),
        #          mock.call(ack_packet, (server_ip, server_port))
        #          ]
        #  mock_socket.sendto.assert_has_calls(calls)

        # This also works:
        #  expected_args = [
        #                  mock.call( read_request, (server_ip, server_port) ),
        #                  mock.call( ack_packet,   (server_ip, server_port) )
        #                  ]

        # This is the recommended way.
        # Notice the insane commas:
        # (( ),) ,
        # (( ),) ,
        # (( ),)
        # This causes the tuples to be interpreted as calls?
        expected_args = [
                        (( read_request, (server_ip, server_port) ),),
                        (( ack_packet,   (server_ip, tid) ),)
                        ]
        assert expected_args == mock_socket.sendto.call_args_list
        assert 2 == mock_socket.sendto.call_count

    def test_server_does_not_respond(self, mock_socket):
        #TODO use socket.timeout
        # The docs say to use Exception(RuntimeError), but
        # I can't figure out how to test that.
        mock_socket.recvfrom.side_effect = timeout

        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'

        read_request = OPCODE_READ
        read_request += filename
        read_request += NULL_BYTE
        read_request += 'octet'
        read_request += NULL_BYTE

        client = Client(mock_socket)
        with pytest.raises(timeout):
            client.read(filename, server_ip, server_port)
