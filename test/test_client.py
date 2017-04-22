from tftp import Client
import pytest
import mock
from socket import timeout

NULL_BYTE = '\x00'
OPCODE_READ = '\x00\x01'
OPCODE_DATA = '\x00\x03'
OPCODE_ACK  = '\x00\x04'

'''
TFTP protocol for reading N blocks:
    Client              Server
    __________________________
    Read        -->

                <--     Data block 1 (== 512 K)
    Ack block 1 -->

                <--     Data block 2 (== 512 K)
    Ack block 2 -->

                ...

                <--     Data block n (== 512 K)
    Ack block n -->

                <--     Data N (< 512 K)
    Ack block N -->

Test list:
    Read request failure.
        --> Failure

    Server response failure, block 1.
        --> Read
        <-- Failure:
                no response (timeout)
                wrong block number
                wrong opcode

    Ack failure, block 1.
        --> Read
        <-- Data block 1
        --> Failure
                ?

    Valid transmission, 1 block:
        --> Read
        <-- Data block 1
        --> Ack block 1

    Server response failure, block n.
        --> Read
        <-- Data block 1
        --> Ack block 1
        <-- Failure
                no response
                wrong block number
                ?
        Does the client send an ack? I think not.
        Does the server retry?

    Ack failure, block n.
        --> Read
        <-- Data block 1
        --> Ack block 1
        <-- Data block n
        --> Failure
                ?

    Server response failure, block N.
        --> Read
        <-- Data block 1
        --> Ack block 1
        <-- Data block n
        --> Ack block n
        <-- Failure
                no response
                wrong block number

    Ack failure, block N.
        --> Read
        <-- Data block 1
        --> Ack block 1
        <-- Data block n
        --> Ack block n
        <-- Data block N
        --> Failure
                ?

    Valid transmission, N blocks.
        --> Read
        <-- Data block 1
        --> Ack block 1
        <-- Data block n
        --> Ack block n
        <-- Data block N
        --> Ack block N

    Different filenames.
        input sanitization
    Different server IP.
        input sanitization
    Different server port.
        69 by default?
        Other ports?
    Different Transmission ID:
        1
        65535
        65536   fail
        Are there any theoreticall invalid ports?
    Different data packets:
        minimum
        512 K
        513 K
    Different number of blocks:
        1
        2
        65535   (original TFTP size limit was 512K * 65535 = 32 M)
        65536?  this works with some tftp server implementations; the block number just rolls over.

TODO
    Do we want to convert read()'s ip and port arguments into a tuple? I think so.
'''

# A list of arguments from all client communication.
# Use this to identify what the client sent and in what order.
# Each list element is a tuple taken from each method invocation:
#   (<ordered_arguments>, <keywork_arguments>)
sendto_args = []

from mock import call
def expect_read_request(filename, server_ip, server_port):
    read_request = create_read_request(filename)
    read_request_args = read_request, (server_ip, server_port)
    # We have no keyword arguments
    sendto_args.extend( call(1,1) )

def expect_ack(block_number, server_ip, tid):
    ack_packet = create_ack_packet(block_number)
    ack_packet_args = ack_packet, (server_ip, tid)
    sendto_args.append( (ack_packet_args,) )

def create_read_request(filename):
    read_request = OPCODE_READ
    read_request += filename
    read_request += NULL_BYTE
    read_request += 'octet'
    read_request += NULL_BYTE
    return read_request

def create_data_packet(block_number, data):
    data_packet = OPCODE_DATA
    data_packet += block_number
    data_packet += data
    return data_packet

def create_ack_packet(block_number):
    ack_packet = OPCODE_ACK
    ack_packet += block_number
    return ack_packet

def create_server_response(block_number, data, server_ip, transmission_id):
    data_packet = create_data_packet(block_number, data)
    return (data_packet, (server_ip, transmission_id))

class TestClient:

    @pytest.fixture
    def mock_socket(self):
        mock_sock = mock.Mock()
        return mock_sock

    def test_client_can_be_created(self, mock_socket):
        assert Client(mock_socket)

    '''
    Client              Server
    __________________________
    Failure     -->
    '''
    @pytest.mark.skip(reason='Not yet sure how to test this')
    def test_client_fails_to_send_read_request(self, mock_socket):
        pass

    '''
    Client              Server
    __________________________
    Read        -->
                <--     Timeout
    '''
    def test_server_does_not_respond_to_read_request(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'

        ### Set expectations
        mock_socket.recvfrom.side_effect = timeout  # socket.timeout
        read_request = create_read_request(filename)

        ### Test
        client = Client(mock_socket)
        assert False == client.read(filename, server_ip, server_port)

    '''
    Client              Server
    __________________________
    Read        -->
                <--     Block number != 1
    '''
    def test_server_returns_wrong_block_number_to_read_request(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations

        block_number = '\x00\x02'       # Should be block number 1 but isn't
        data = 'B\x0a'                  # data in our file: 'B' and LF
        server_response = create_server_response(block_number, data, server_ip, tid)
        mock_socket.recvfrom = mock.Mock(return_value = server_response)

        expect_read_request(filename, server_ip, server_port)

        # Actual call
        client = Client(mock_socket)
        assert False == client.read(filename, server_ip, server_port)
        assert sendto_args == mock_socket.sendto.call_args_list
        assert 1 == mock_socket.sendto.call_count

    '''
    Client              Server
    __________________________
    Read        -->
                <--     Data block 1 (== 512 K)
    Ack block 1 -->
    '''
    def test_parse_first_read_response(self, mock_socket):
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        # Client read request
        read_request = create_read_request(filename)
        sendto_args = []

        # Server response - data packet
        block_number = '\x00\x01'       # block number 1
        data = 'B\x0a'                  # data in our file: 'B' and LF
        server_response = create_server_response(block_number, data, server_ip, tid)
        mock_socket.recvfrom = mock.Mock(return_value = server_response)

        # Client ack
        ack_packet = create_ack_packet(block_number)

        # Mock expectations
        read_request_args = read_request, (server_ip, server_port)
        ack_packet_args = ack_packet, (server_ip, tid)
        expect_read_request(filename, server_ip, server_port)
        expect_ack(block_number, server_ip, tid)
        expected_args = [
                        # A list of: (<ordered arguments>, <empty_dictionary>)
                        (read_request_args,),
                        (ack_packet_args,)
                        ]

        # Actual call
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        # Check expectations
        assert expected_args == mock_socket.sendto.call_args_list
        assert 2 == mock_socket.sendto.call_count

    @pytest.mark.skip('todo')
    def test_read_a_different_filename(self, mock_socket):
        pass

    @pytest.mark.skip('todo')
    def test_read_from_different_server_ip_address(self, mock_socket):
        pass

    @pytest.mark.skip('todo')
    def test_read_from_different_server_port(self, mock_socket):
        pass
