from tftp import Client
import pytest
import mock
from socket import timeout
from random import choice
from string import printable

OPCODE_NULL = '\x00'
OPCODE_READ = '\x00\x01'
OPCODE_WRITE = '\x00\x02'
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
                no response (timeout)
                wrong block number
                wrong opcode
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
                no response (timeout)
                wrong block number
                wrong opcode

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
    Different modes:
        octed
        mail
        netascii

TODO
    Do we want to convert read()'s ip and port arguments into a tuple? I think so.
    If input sanitation fails, do we send a response to the server?
'''

# Create various TFTP packets
def create_read_request(filename):
    return create_packet(OPCODE_READ, filename, OPCODE_NULL, 'octet', OPCODE_NULL)

def create_ack_response(block_number):
    return create_packet(OPCODE_ACK, block_number)
    
def create_data_packet(block_number, data):
    return create_packet(OPCODE_DATA, block_number, data)

# Create a general packet from the fields given.
# Fields are concatenated in sequential order.
def create_packet(*fields):
    packet = ''
    for f in fields:
        packet += f
    return packet

# Python's sendto() and recvfrom() methods accept and return a tuple containing:
#   (data, (ip, port))
# They package the ip and port together - the socket address.
def create_socket_tuple(packet, ip, port):
    return (packet, (ip, port))


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
    Failure: ?  -->
    '''
    @pytest.mark.skip(reason='Not yet sure how to test this')
    def test_client_fails_to_send_read_request(self, mock_socket):
        pass

    '''
    Client              Server
    __________________________
    Read        -->
                <--     Failure: timeout
    '''
    def test_server_does_not_respond_to_read_request(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'

        ### Set expectations
        # Client read request
        packet = create_read_request(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
                        (read_request_args,),
                        ]

        # Server response - socket.timeout
        mock_socket.recvfrom.side_effect = timeout

        ### Test
        client = Client(mock_socket)
        assert False == client.read(filename, server_ip, server_port)

    '''
    Client              Server
    __________________________
    Read        -->
                <--     Failure: block number != 1
    '''
    def test_server_returns_wrong_block_number_to_read_request(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        packet = create_read_request(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response
        block_number = '\x00\x02'       # Should be block number 1 but isn't
        data = 'B\x0a'                  # data in our file: 'B' and LF
        packet = create_data_packet(block_number, data)
        server_response = create_socket_tuple(packet, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
                        (read_request_args,),
                        ]
        # Set server response
        mock_socket.recvfrom.side_effect = [server_response]

        ### Test
        client = Client(mock_socket)
        assert False == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 1 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    '''
    Client              Server
    __________________________
    Read        -->
                <--     Fialure: opcode != OPCODE_DATA
    '''
    def test_server_returns_wrong_opcode_to_read_request(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        packet = create_read_request(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response
        opcode = OPCODE_NULL            # Should be OPCODE_DATA
        block_number = '\x00\x01'       # Block number 1
        data = 'B\x0a'                  # data in our file: 'B' and LF
        data_packet = OPCODE_WRITE + block_number + data
        packet = create_packet(opcode, block_number, data)
        server_response = create_socket_tuple(packet, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
                        (read_request_args,),
                        ]
        # Set server response
        mock_socket.recvfrom = mock.Mock(return_value = server_response)

        ### Test
        client = Client(mock_socket)
        assert False == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 1 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    '''
    Client              Server
    __________________________
    Read        -->
                <--     Data block 1 (== 512 K)
    Ack block 1 -->
    '''
    def test_transfer_a_single_block_successfully(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        packet = create_read_request(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response - data packet
        block_number = '\x00\x01'       # block number 1
        data = 'B\x0a'                  # data in our file: 'B' and LF
        packet = create_data_packet(block_number, data)
        server_response = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_response(block_number)
        ack_packet_args = create_socket_tuple(packet, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
                        (read_request_args,),
                        (ack_packet_args,),
                        ]
        # Set server response
        mock_socket.recvfrom.side_effect = [server_response]

        ### Test
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 2 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    '''
    Client              Server
    __________________________
    Read        -->

                <--     Data block 1 (== 512 K)
    Ack block 1 -->

                <--     Failure: timeout
    '''
    def test_server_does_not_send_next_block(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        packet = create_read_request(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response - data packet
        block_number = '\x00\x01'       # block number 1
        data = ''.join(choice(printable) for i in range(512))
        packet = create_data_packet(block_number, data)
        server_response_1 = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_response(block_number)
        ack_packet_args = create_socket_tuple(packet, server_ip, tid)

        # Server response - socket.timeout
        server_response_2 = timeout

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
                        (read_request_args,),
                        (ack_packet_args,),
                        ]
        # Set server response
        mock_socket.recvfrom.side_effect = [server_response_1, server_response_2]

        ### Test
        client = Client(mock_socket)
        assert False == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 2 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    '''
    Client              Server
    __________________________
    Read        -->

                <--     Data block 1 (== 512 K)
    Ack block 1 -->

                <--     Failure: block number != 2
    '''
    def test_server_returns_wrong_block_number_on_next_block(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        packet = create_read_request(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response - data packet
        block_number = '\x00\x01'       # block number 1
        data = ''.join(choice(printable) for i in range(512))
        packet = create_data_packet(block_number, data)
        server_response_1 = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_response(block_number)
        ack_packet_args = create_socket_tuple(packet, server_ip, tid)

        # Server response - wrong block number
        block_number = '\x00\x03'       # Should be block number 2 but isn't
        data = 'B\x0a'                  # data in our file: 'B' and LF
        packet = create_data_packet(block_number, data)
        server_response_2 = create_socket_tuple(packet, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
                        (read_request_args,),
                        (ack_packet_args,),
                        ]
        # Set server response
        mock_socket.recvfrom.side_effect = [server_response_1, server_response_2]

        ### Test
        client = Client(mock_socket)
        assert False == client.read(filename, server_ip, server_port)

        assert 2 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    '''
    Client              Server
    __________________________
    Read        -->

                <--     Data block 1 (== 512 K)
    Ack block 1 -->

                <--     Failure: wrong opcode
    '''
    def test_server_returns_wrong_opcode_on_next_block(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        packet = create_read_request(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response - data packet
        block_number = '\x00\x01'       # block number 1
        data = ''.join(choice(printable) for i in range(512))
        packet = create_data_packet(block_number, data)
        server_response_1 = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_response(block_number)
        ack_packet_args = create_socket_tuple(packet, server_ip, tid)

        # Server response - wrong block number
        opcode = OPCODE_NULL            # Should be OPCODE_DATA
        block_number = '\x00\x02'
        data = 'B\x0a'                  # data in our file: 'B' and LF
        packet = create_packet(opcode, block_number, data)
        server_response_2 = create_socket_tuple(packet, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
                        (read_request_args,),
                        (ack_packet_args,),
                        ]
        # Set server response
        mock_socket.recvfrom.side_effect = [server_response_1, server_response_2]

        ### Test
        client = Client(mock_socket)
        assert False == client.read(filename, server_ip, server_port)

        assert 2 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    @pytest.mark.skip('todo')
    def test_read_a_different_filename(self, mock_socket):
        pass

    @pytest.mark.skip('todo')
    def test_read_from_different_server_ip_address(self, mock_socket):
        pass

    @pytest.mark.skip('todo')
    def test_read_from_different_server_port(self, mock_socket):
        pass
