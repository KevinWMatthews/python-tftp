from tftp import Client
import pytest
import mock
from socket import timeout
from random import choice
from string import printable
from struct import pack

OPCODE_NULL = '\x00'
OPCODE_READ = '\x00\x01'
OPCODE_WRITE = '\x00\x02'
OPCODE_DATA = '\x00\x03'
OPCODE_ACK  = '\x00\x04'

MAX_DATA_SIZE = 512
MAX_BLOCK_NUMBER = 65535

# Create various TFTP packets
'''
2 bytes     string    1 byte     string   1 byte
------------------------------------------------
| Opcode |  Filename  |   0  |    Mode    |   0  |
------------------------------------------------
'''
def create_read_packet(filename):
    return create_packet(OPCODE_READ, filename, OPCODE_NULL, 'octet', OPCODE_NULL)

'''
 2 bytes     2 bytes
 ---------------------
| Opcode |   Block #  |
 ---------------------
 '''
def create_ack_packet(block_number):
    block_string = pack_block_number(block_number)
    return create_packet(OPCODE_ACK, block_string)


'''
server response packet structure:
 2 bytes     2 bytes      n bytes
 ----------------------------------
| Opcode |   Block #  |   Data     |
 ----------------------------------
'''
def create_data_response(block_number, data):
    block_string = pack_block_number(block_number)
    return create_packet(OPCODE_DATA, block_string, data)

# Create a general packet from the fields given.
# Fields are concatenated in sequential order.
# All fields must be of the same type (assumed to be a string).
def create_packet(*fields):
    return ''.join(fields)

# Python's sendto() and recvfrom() methods accept and return a tuple containing:
#   (data, (ip, port))
# They package the ip and port together - the socket address.
def create_socket_tuple(packet, ip, port):
    return (packet, (ip, port))

# Return the block number as a string of hex
def pack_block_number(block_number):
    return pack('!H', block_number)

def create_random_data_string(n_bytes):
    random_chars = (choice(printable) for i in range(n_bytes))
    return ''.join(random_chars)

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
        packet = create_read_packet(filename)
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
        packet = create_read_packet(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response
        block_number = 2                # Should be block number 1 but isn't
        data = create_random_data_string(1)
        packet = create_data_response(block_number, data)
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
                <--     Failure: opcode != OPCODE_DATA
    '''
    def test_server_returns_wrong_opcode_to_read_request(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        packet = create_read_packet(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response
        opcode = OPCODE_ACK                 # Should be OPCODE_DATA
        block_number = pack_block_number(1)
        data = create_random_data_string(1)
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
                <--     Data block 1 (1 byte of data)
    Ack block 1 -->
    '''
    def test_successfully_transfer_smallest_single_block(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        packet = create_read_packet(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(1)
        packet = create_data_response(block_number, data)
        server_response = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_packet(block_number)
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
                <--     Data block 1 (== 511 bytes of data)
    Ack block 1 -->
    '''
    def test_successfully_transfer_largest_single_block(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        packet = create_read_packet(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE-1)
        packet = create_data_response(block_number, data)
        server_response = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_packet(block_number)
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

                <--     Data block 1 (== 512 bytes of data)
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
        packet = create_read_packet(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        # Four bytes are taken up by the the opcode adn block number
        data = create_random_data_string(MAX_DATA_SIZE)
        packet = create_data_response(block_number, data)
        server_response_1 = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_packet(block_number)
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

                <--     Data block 1 (== 512 bytes of data)
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
        packet = create_read_packet(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        packet = create_data_response(block_number, data)
        server_response_1 = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_packet(block_number)
        ack_packet_args = create_socket_tuple(packet, server_ip, tid)

        # Server response - wrong block number
        block_number = 3                # Should be block number 2 but isn't
        data = create_random_data_string(1)
        packet = create_data_response(block_number, data)
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

                <--     Data block 1 (== 512 bytes of data)
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
        packet = create_read_packet(filename)
        read_request_args = create_socket_tuple(packet, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        packet = create_data_response(block_number, data)
        server_response_1 = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_packet(block_number)
        ack_packet_args = create_socket_tuple(packet, server_ip, tid)

        # Server response - wrong block number
        opcode = OPCODE_ACK                 # Should be OPCODE_DATA
        block_number = pack_block_number(2)
        data = create_random_data_string(1)
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

    '''
    Client              Server
    __________________________
    Read        -->

                <--     Data block 1 (512 bytes of data)
    Ack block 1 -->

                <--     Data block 2 (0 bytes of data)
    Ack block 2 -->
    '''
    def test_largest_single_block_requires_an_empty_block_to_end_transmission(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        packet = create_read_packet(filename)
        read_packet = create_socket_tuple(packet, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        packet = create_data_response(block_number, data)
        server_response_1 = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_packet(block_number)
        client_ack_1 = create_socket_tuple(packet, server_ip, tid)

        # Server response - data packet
        block_number = 2
        data = ''
        packet = create_data_response(block_number, data)
        server_response_2 = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_packet(block_number)
        client_ack_2 = create_socket_tuple(packet, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
                (read_packet,),
                (client_ack_1,),
                (client_ack_2,),
                ]
        # Set server response
        mock_socket.recvfrom.side_effect = [
                server_response_1,
                server_response_2
                ]

        ### Test
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 3 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    '''
    Client              Server
    __________________________
    Read        -->

                <--     Data block 1 (512 bytes of data)
    Ack block 1 -->

                <--     Data block 2 (1 byte of data)
    Ack block 2 -->
    '''
    def test_successfully_transfer_small_second_block(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        packet = create_read_packet(filename)
        read_packet = create_socket_tuple(packet, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        packet = create_data_response(block_number, data)
        server_response_1 = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_packet(block_number)
        client_ack_1 = create_socket_tuple(packet, server_ip, tid)

        # Server response - data packet
        block_number = 2
        data = create_random_data_string(1)
        packet = create_data_response(block_number, data)
        server_response_2 = create_socket_tuple(packet, server_ip, tid)

        # Cliet ack response
        packet = create_ack_packet(block_number)
        client_ack_2 = create_socket_tuple(packet, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
                (read_packet,),
                (client_ack_1,),
                (client_ack_2,),
                ]
        # Set server response
        mock_socket.recvfrom.side_effect = [
                server_response_1,
                server_response_2
                ]

        ### Test
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 3 == mock_socket.sendto.call_count
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
