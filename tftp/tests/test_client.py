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

def expect_sendto_call(args_list, args):
    # Mock objects keep a list of call arguments.
    # This list is of the form: (<ordered arguments>, <keyword arguments>)
    args_list.append( (args,) )     # Assume no keyword arguments

def expect_recvfrom_call(side_effects_list, side_effect):
    side_effects_list.append(side_effect)

class TestClient:

    @pytest.fixture
    def mock_socket(self):
        mock_sock = mock.Mock()
        return mock_sock

    def test_client_can_be_created(self, mock_socket):
        assert Client(mock_socket)

    '''
    Client                  Server
    ______________________________
    Failure: ?          -->
    '''
    @pytest.mark.skip(reason='Not yet sure how to test this')
    def test_read_request_client_fails_to_send(self, mock_socket):
        pass

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Timeout
    Abort
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
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data packet, block number > 1
    Abort
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
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data packet, block number == 0
    Abort
    '''
    def test_read_request_server_can_not_return_block_number_zero(self, mock_socket):
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
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Not data packet: opcode != 3
    Abort
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
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (1 byte of data)
    Write: Ack block 1  --> Received

    Read:               <-- Timeout
    '''
    def test_one_block_success_smallest_payload(self, mock_socket):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        sendto_args_list = []
        # Return value/server response
        recvfrom_side_effects = []

        # Expect Client read request
        read_packet = ReadPacket(filename, mode)
        read_request = read_packet.network_string()
        read_request_args = create_socket_tuple(read_request, server_ip, server_port)
        expect_sendto_call(sendto_args_list, read_request_args)

        # Expect Server response - data packet
        block_number = 1
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        server_response_1 = create_socket_tuple(data_string, server_ip, tid)
        expect_recvfrom_call(recvfrom_side_effects, server_response_1)

        # Expect Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_packet_args = create_socket_tuple(ack_string, server_ip, tid)
        expect_sendto_call(sendto_args_list, ack_packet_args)

        # Expect Server times out/does not retransmit last packet
        server_response_2 = socket.timeout
        expect_recvfrom_call(recvfrom_side_effects, server_response_2)

        # Set side effects
        mock_socket.recvfrom.side_effect = recvfrom_side_effects

        ### Test
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        ### Check expectations
        # sendto
        assert 2 == mock_socket.sendto.call_count
        assert sendto_args_list == mock_socket.sendto.call_args_list

        # recvfrom
        assert 2 == mock_socket.recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (== 511 bytes of data)
    Write: Ack block 1  --> Received

    Read:               <-- Timeout
    '''
    def test_one_block_success_largest_payload(self, mock_socket):
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
        server_response_1 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_packet_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server does not retransmit last packet
        server_response_2 = socket.timeout

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
            (read_request_args,),
            (ack_packet_args,),
        ]

        # Set server response
        mock_socket.recvfrom.side_effect = [
            server_response_1,
            server_response_2,
        ]

        ### Test
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 2 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list
        assert 2 == mock_socket.recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (< 512 bytes of data)
    Write: Ack block 1  --> Not received

    Read:               <-- Data block 1 (< 512 bytes of data)
    Write: Ack block 1  --> Does not matter
    '''
    def test_one_block_success_server_retransmits_packet(self, mock_socket):
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
        server_response_1 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_packet_args = create_socket_tuple(ack_string, server_ip, tid)

        # Server does not retransmit last packet
        server_response_2 = socket.timeout

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
            (read_request_args,),
            (ack_packet_args,),
            (ack_packet_args,),
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
        assert 3 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list
        assert 2 == mock_socket.recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (== 513 bytes of data)
    Abort
    '''
    def test_one_block_fails_if_payload_is_too_large(self, mock_socket):
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
    Client                  Server
    ______________________________
    Write: Read Request --> Received

    Read:               <-- Data block 1 (== 512 bytes of data)
    Write: Ack block 1  -->

    Read:               <-- Failure: socket timeout
    Write: Ack block 1  -->

    Read:               <-- Failure: socket timeout
    Abort
    '''
    def test_two_blocks_server_times_out(self, mock_socket):
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
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (== 512 bytes of data)
    Write: Ack block 1  --> Received

    Read:               <-- Data packet, block number != 2
    Abort
    '''
    def test_two_blocks_server_returns_wrong_block_number(self, mock_socket):
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
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (== 512 bytes of data)
    Write: Ack block 1  --> Received

    Read:               <-- Not a data packet: wrong opcode
    Abort
    '''
    def test_two_blocks_server_returns_wrong_opcode(self, mock_socket):
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
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (512 bytes of data)
    Write: Ack block 1  --> Received

    Read:               <-- Data block 2 (0 bytes of data)
    Ack block 2         --> Received

    Read:               <-- Timeout
    '''
    def test_two_blocks_success_empty_payload_ends_transmission(self, mock_socket):
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

        # Server does not retransmit last packet
        server_response_3 = socket.timeout

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
            server_response_2,
            server_response_3,
        ]

        ### Test
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 3 == mock_socket.sendto.call_count
        assert 3 == mock_socket.recvfrom.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (512 bytes of data)
    Write: Ack block 1  --> Received

    Read:               <-- Data block 2 (1 byte of data)
    Write:Ack block 2   --> Received

    Read:               --> Timeout
    '''
    def test_two_blocks_success_smallest_payload(self, mock_socket):
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

        # Server does not retransmit last packet
        server_response_3 = socket.timeout

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
            server_response_2,
            server_response_3,
        ]

        ### Test
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 3 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (512 bytes of data)
    Write: Ack block 1  --> Not received

    Read:               <-- Data block 1 (512 byte of data)
    Write: Ack block 1  --> Received

    Read:               <-- Data block 2 (1 byte of data)
    Write: Ack block 2  --> Received

    Read:               <-- Timeout
    '''
    def test_two_blocks_success_server_resends_first_block(self, mock_socket):
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

        # Server does not retransmit last packet
        server_response_3 = socket.timeout

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
            server_response_3,
        ]

        ### Test
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 4 == mock_socket.sendto.call_count
        assert expected_args == mock_socket.sendto.call_args_list

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (512 bytes of data)
    Write: Ack block 1  --> Not received

    Read:               <-- Resend data block 1 (512 byte of data)
    Write: Ack block 1  --> Received

    Read:               <-- Data block 2 (1 byte of data)
    Write: Ack block 2  --> Not received

    Read:               <-- Data block 2 (1 byte of data)
    Write: Ack block 2  --> Does not matter

    Terminate
    '''
    def test_two_blocks_success_server_resends_first_and_final_blocks(self, mock_socket):
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

        # Server does not retransmit last packet
        server_response_3 = socket.timeout

        # Set client expectations
        # A list of: (<ordered arguments>, <empty_dictionary>)
        expected_args = [
            (read_request_args,),
            (client_ack_1_args,),
            (client_ack_1_args,),
            (client_ack_2_args,),
            (client_ack_2_args,),
        ]
        # Set server response
        mock_socket.recvfrom.side_effect = [
            server_response_1,
            server_response_1,
            server_response_2,
            server_response_2,
            server_response_3,
        ]

        ### Test
        client = Client(mock_socket)
        assert True == client.read(filename, server_ip, server_port)

        ### Check expectations
        assert 5 == mock_socket.sendto.call_count
        assert 4 == mock_socket.recvfrom.call_count
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
