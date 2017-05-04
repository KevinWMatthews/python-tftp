from tftp import Client, ReadPacket, DataPacket, AckPacket
import pytest
import mock
from socket import timeout
from random import choice
from string import printable
from struct import pack

MAX_DATA_SIZE = 512
MAX_BLOCK_NUMBER = 65535


# Python's sendto() and recvfrom() methods accept and return a tuple containing:
#   (data, (ip, port))
# They package the ip and port together - the socket address.
def create_socket_tuple(string, ip, port):
    return (string, (ip, port))

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
        mode = 'octet'

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        read_request_args = create_socket_tuple(read_string, server_ip, server_port)

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

        ### Check expectations
        assert 1 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

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
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_request = read_packet.network_string()
        read_request_args = create_socket_tuple(read_request, server_ip, server_port)

        # Server response
        block_number = 2                # Should be block number 1 but isn't
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response = create_socket_tuple(data_string, server_ip, tid)

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
                <--     Failure: opcode != 3
    '''
    def test_server_returns_wrong_opcode_to_read_request(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_request = read_packet.network_string()
        read_request_args = create_socket_tuple(read_request, server_ip, server_port)

        # Server response
        opcode = AckPacket.OPCODE       # Will set the wrong opcode
        block_number = 1
        data = create_random_data_string(1)

        data_packet = DataPacket(block_number, data)
        data_packet.OPCODE = opcode
        data_string = data_packet.network_string()
        server_response = create_socket_tuple(data_string, server_ip, tid)

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
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_request = read_packet.network_string()
        read_request_args = create_socket_tuple(read_request, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response = create_socket_tuple(data_string, server_ip, tid)

        # Cliet ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_packet_args = create_socket_tuple(ack_string, server_ip, tid)

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
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        read_request_args = create_socket_tuple(read_string, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE-1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response = create_socket_tuple(data_string, server_ip, tid)

        # Cliet ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_packet_args = create_socket_tuple(ack_string, server_ip, tid)

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
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        read_request_args = create_socket_tuple(read_string, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        # Four bytes are taken up by the the opcode adn block number
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_1 = create_socket_tuple(data_string, server_ip, tid)

        # Cliet ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_packet_args = create_socket_tuple(ack_string, server_ip, tid)

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
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        read_request_args = create_socket_tuple(read_string, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_1 = create_socket_tuple(data_string, server_ip, tid)

        # Cliet ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_packet_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server response - wrong block number
        block_number = 3                # Should be block number 2 but isn't
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_2 = create_socket_tuple(data_string, server_ip, tid)

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
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        read_request_args = create_socket_tuple(read_string, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_1 = create_socket_tuple(data_string, server_ip, tid)

        # Cliet ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_packet_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server response - wrong block number
        opcode = AckPacket.OPCODE       # Will set wrong opcode
        block_number = 2
        data = create_random_data_string(1)

        data_packet = DataPacket(block_number, data)
        data_packet.OPCODE = opcode
        data_string = data_packet.network_string()
        server_response_2 = create_socket_tuple(data_string, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
            (read_request_args,),
            (ack_packet_args,),
        ]
        # Set server response
        mock_socket.recvfrom.side_effect = [
            server_response_1,
            server_response_2
        ]

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
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        read_request_args = create_socket_tuple(read_string, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_1 = create_socket_tuple(data_string, server_ip, tid)

        # Cliet ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_1_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server response - data packet
        block_number = 2
        data = ''
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_2 = create_socket_tuple(data_string, server_ip, tid)

        # Cliet ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_2_args = create_socket_tuple(ack_string, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
            (read_request_args,),
            (client_ack_1_args,),
            (client_ack_2_args,),
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
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_request = read_packet.network_string()
        read_request_args = create_socket_tuple(read_request, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_1 = create_socket_tuple(data_string, server_ip, tid)

        # Cliet ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_1_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server response - data packet
        block_number = 2
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_2 = create_socket_tuple(data_string, server_ip, tid)

        # Cliet ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_2_args = create_socket_tuple(ack_string, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
            (read_request_args,),
            (client_ack_1_args,),
            (client_ack_2_args,),
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
                <--     Data block 1 (== 513 bytes of data)
    '''
    def test_client_fails_if_data_is_too_large(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        read_request_args = create_socket_tuple(read_string, server_ip, server_port)

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE+1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response = create_socket_tuple(data_string, server_ip, tid)

        # Set server response
        mock_socket.recvfrom.side_effect = [server_response]

        ### Test
        client = Client(mock_socket)
        assert False == client.read(filename, server_ip, server_port)

    @pytest.mark.skip('todo')
    def test_read_a_different_filename(self, mock_socket):
        pass

    @pytest.mark.skip('todo')
    def test_read_from_different_server_ip_address(self, mock_socket):
        pass

    @pytest.mark.skip('todo')
    def test_read_from_different_server_port(self, mock_socket):
        pass
