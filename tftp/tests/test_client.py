from tftp import Client, ReadPacket, DataPacket, AckPacket
import pytest
import mock
import socket
from random import choice
from string import printable

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
    def test_read_request_client_fails_to_send(self, mock_socket):
        pass

    '''
    Client              Server
    __________________________
    Read        -->
                <--     Failure: socket timeout
    '''
    def test_read_request_server_times_out(self, mock_socket):
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

        # Server response
        mock_socket.recvfrom.side_effect = socket.timeout

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
    def test_read_request_server_returns_wrong_block_number(self, mock_socket):
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
                <--     Failure: block number != 1
    '''
    def test_read_request_server_can_not_return_previous_block_number(self, mock_socket):
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
        block_number = 0                # The 'previous block' is not valid for the first packet.
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
    def test_read_request_server_returns_wrong_opcode(self, mock_socket):
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
    def test_single_block_success_smallest_payload(self, mock_socket):
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

        # Client ack response
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
    def test_single_block_success_largest_payload(self, mock_socket):
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

        # Client ack response
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
                <--     Data block 1 (== 513 bytes of data)
    '''
    def test_single_block_fails_if_payload_is_too_large(self, mock_socket):
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

    '''
    Client              Server
    __________________________
    Read        -->

                <--     Data block 1 (== 512 bytes of data)
    Ack block 1 -->

                <--     Failure: socket timeout
    Ack block 1 -->

                <--     Failure: socket timeout
    Terminate
    '''
    def test_second_block_server_times_out(self, mock_socket):
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

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_1_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server response
        server_response_timeout = socket.timeout

        # Client resends ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_1_args  = create_socket_tuple(ack_string, server_ip, tid)

        # Server response
        server_response_timeout = socket.timeout

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
            (read_request_args,),
            (client_ack_1_args,),
            (client_ack_1_args,),
        ]
        # Set server response
        mock_socket.recvfrom.side_effect = [
            server_response_1,
            server_response_timeout,
            server_response_timeout,
        ]

        ### Test
        client = Client(mock_socket)
        assert False == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 3 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    '''
    Client              Server
    __________________________
    Read        -->

                <--     Data block 1 (== 512 bytes of data)
    Ack block 1 -->

                <--     Failure: block number != 2
    '''
    def test_second_block_server_returns_wrong_block_number(self, mock_socket):
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

        # Client ack response
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
    def test_second_block_server_returns_wrong_opcode(self, mock_socket):
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

        # Client ack response
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
    def test_second_block_success_empty_payload_ends_transmission(self, mock_socket):
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

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_1_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server response - data packet
        block_number = 2
        data = ''
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_2 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
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
    def test_second_block_success_smallest_payload(self, mock_socket):
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

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_1_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server response - data packet
        block_number = 2
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_2 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
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
    Ack block 1 -->     Server fails to receive ack

                <--     Resend data block 1 (512 byte of data)
    Ack block 1 -->

                <--     Data block 2 (1 byte of data)
    Ack block 2 -->
    '''
    def test_first_ack_fails_server_resends_first_block(self, mock_socket):
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

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_1_args = create_socket_tuple(ack_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_1_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server response - data packet
        block_number = 2
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_2 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_2_args = create_socket_tuple(ack_string, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
            (read_request_args,),
            (client_ack_1_args,),
            (client_ack_1_args,),
            (client_ack_2_args,),
        ]
        # Set server response
        mock_socket.recvfrom.side_effect = [
            server_response_1,
            server_response_1,
            server_response_2,
        ]

        ### Test
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 4 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    @pytest.mark.skip(reason='Fix test_server_does_not_send_next_block() first')
    def test_client_resends_ack_if_times_out_waiting_for_data_packet(self, mock_socket):
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

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_1_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server response - timeout
        server_response_timeout = socket.timeout

        # Client resends ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_2_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server response - data packet
        block_number = 2
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_2 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        client_ack_2_args = create_socket_tuple(ack_string, server_ip, tid)

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
            (read_request_args,),
            (client_ack_1_args,),
            (client_ack_1_args,),
            (client_ack_2_args,),
        ]
        # Set server response
        mock_socket.recvfrom.side_effect = [
            server_response_1,
            server_response_timeout,
            server_response_2,
        ]

        ### Test
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 3 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

        # Server response
        mock_socket.recvfrom.side_effect = socket.timeout


    @pytest.mark.skip('todo')
    def test_read_a_different_filename(self, mock_socket):
        pass

    @pytest.mark.skip('todo')
    def test_read_from_different_server_ip_address(self, mock_socket):
        pass

    @pytest.mark.skip('todo')
    def test_read_from_different_server_port(self, mock_socket):
        pass
