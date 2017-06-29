from tftp import Client, Client2, ReadPacket, DataPacket, AckPacket
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
def create_socket_tuple_from_packet(packet, ip, port):
    network_string = packet.network_string()
    return create_socket_tuple(network_string, ip, port)

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
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_read_request_server_times_out(self, mock_sendto, mock_recvfrom):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        mode = 'octet'

        ### Set expectations
        # Client read request
        read_packet = ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server does not transmit packet
        server_timeout = socket.timeout

        # Set sendto expectations
        sendto_calls = [
            read_request,
        ]

        # Server response
        mock_recvfrom.side_effect = [
            server_timeout,
        ]

        ### Test
        client = Client2()
        assert False == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 1 == mock_recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data packet, block number > 1
    Abort
    '''
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_read_request_server_returns_wrong_block_number(self, mock_sendto, mock_recvfrom):
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
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server response
        block_number = 2                # Should be block number 1 but isn't
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Set sendto expectations
        sendto_calls = [
            read_request,
        ]

        # Set server response
        mock_recvfrom.side_effect = [
            data_block_1,
        ]

        ### Test
        client = Client2()
        assert False == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 1 == mock_recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data packet, block number == 0
    Abort
    '''
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_read_request_server_can_not_return_block_number_zero(self, mock_sendto, mock_recvfrom):
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
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server response
        block_number = 0                # The 'previous block' is not valid for the first packet.
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Set sendto expectations
        sendto_calls = [
            read_request,
        ]

        # Set server response
        mock_recvfrom.side_effect = [
            data_block_1,
        ]

        ### Test
        client = Client2()
        assert False == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 1 == mock_recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Not data packet: opcode != 3
    Abort
    '''
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_read_request_server_returns_wrong_opcode(self, mock_sendto, mock_recvfrom):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Send to TFTP Server: read request
        read_packet = ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Receive from TFTP Server: packet with wrong opcode
        opcode = AckPacket.OPCODE       # Will set the wrong opcode
        block_number = 1
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_packet.OPCODE = opcode
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Set sendto expectations
        sendto_calls = [
            read_request,
        ]

        # Set recvfrom responses/side effects
        mock_recvfrom.side_effect = [
            data_block_1,
        ]

        ### Test
        client = Client2()
        assert False == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 1 == mock_recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (1 byte of data)
    Write: Ack block 1  --> Received

    Read:               <-- Timeout
    '''
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_one_block_success_smallest_payload(self, mock_sendto, mock_recvfrom):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Send to TFTP Server: read request
        read_packet = ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Receive from TFTP Server: data packet
        block_number = 1
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_block_1 = create_socket_tuple_from_packet(data_packet, server_ip, tid)

        # Send to TFTP Server: ack
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_1 = mock.call( ack_string, (server_ip, tid) )

        # Receive from server: timeout/server does not retransmit last packet
        server_timeout = socket.timeout

        # Set sendto expectations
        sendto_calls = [
            read_request,
            ack_block_1,
        ]

        # Set recvfrom responses/side effects
        mock_recvfrom.side_effect = [
            data_block_1,
            server_timeout,
        ]

        ### Test
        client = Client2()
        assert True == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 2 == mock_recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (== 511 bytes of data)
    Write: Ack block 1  --> Received

    Read:               <-- Timeout
    '''
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_one_block_success_largest_payload(self, mock_sendto, mock_recvfrom):
        ### Setup
        server_ip = '127.0.0.1'
        server_port = 69
        filename = 'test.txt'
        mode = 'octet'
        tid = 12345                     # transmission id (port) is random?

        ### Set expectations
        # Send to server: read request
        read_packet = ReadPacket(filename, mode)
        read_string = read_packet.network_string()
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Receive from server: data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE-1)
        data_packet = DataPacket(block_number, data)
        data_block_1 = create_socket_tuple_from_packet(data_packet, server_ip, tid)

        # Send to server: ack
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_1 = mock.call( ack_string, (server_ip, tid) )

        # Receive from server: timeout/server does not retransmit last packet
        server_timeout = socket.timeout

        # Set sendto expectations
        sendto_calls = [
            read_request,
            ack_block_1,
        ]

        # Set server response/side effects
        mock_recvfrom.side_effect = [
            data_block_1,
            server_timeout,
        ]

        ### Test
        client = Client2()
        assert True == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 2 == mock_recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (< 512 bytes of data)
    Write: Ack block 1  --> Not received

    Read:               <-- Data block 1 (< 512 bytes of data)
    Write: Ack block 1  --> Does not matter
    '''
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_one_block_success_server_retransmits_packet(self, mock_sendto, mock_recvfrom):
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
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_1 = mock.call( ack_string, (server_ip, tid) )

        # Server does not retransmit last packet
        server_timeout = socket.timeout

        # Set sendto expectations
        sendto_calls = [
            read_request,
            ack_block_1,
            ack_block_1,
        ]

        # Set recvfrom responses/side effects
        mock_recvfrom.side_effect = [
            data_block_1,
            data_block_1,
            server_timeout          # This would be returned but the Client will not wait and read again
        ]

        ### Test
        client = Client2()
        assert True == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 2 == mock_recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (== 513 bytes of data)
    Abort
    '''
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_one_block_fails_if_payload_is_too_large(self, mock_sendto, mock_recvfrom):
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
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE+1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Set sendto expectations
        sendto_calls = [
            read_request,
        ]

        # Set server response
        mock_recvfrom.side_effect = [
            data_block_1,
        ]

        ### Test
        client = Client2()
        assert False == client.read(filename, server_ip, server_port)
        assert 1 == mock_recvfrom.call_count

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
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_two_blocks_server_times_out(self, mock_sendto, mock_recvfrom):
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
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_1 = mock.call( ack_string, (server_ip, tid) )

        # Server response
        server_response_timeout = socket.timeout

        # Client resends ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_1 = mock.call( ack_string, (server_ip, tid) )

        # Server response
        server_timeout = socket.timeout

        # Set sendto expectations
        sendto_calls = [
            read_request,
            ack_block_1,
            ack_block_1,
        ]

        # Set recvfrom responses/side effects
        mock_recvfrom.side_effect = [
            data_block_1,
            server_timeout,
            server_timeout,
        ]

        ### Test
        client = Client2()
        assert False == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 3 == mock_recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (== 512 bytes of data)
    Write: Ack block 1  --> Received

    Read:               <-- Data packet, block number != 2
    Abort
    '''
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_two_blocks_server_returns_wrong_block_number(self, mock_sendto, mock_recvfrom):
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
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_1 = mock.call( ack_string, (server_ip, tid) )

        # Server response - wrong block number
        block_number = 3                # Should be block number 2 but isn't
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_2 = create_socket_tuple(data_string, server_ip, tid)

        # Set sendto expectations
        sendto_calls = [
            read_request,
            ack_block_1,
        ]

        # Set recvfrom responses/side effects
        mock_recvfrom.side_effect = [
            data_block_1,
            data_block_2,
        ]

        ### Test
        client = Client2()
        assert False == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 2 == mock_recvfrom.call_count

    '''
    Client                  Server
    ______________________________
    Write: Read request --> Received

    Read:               <-- Data block 1 (== 512 bytes of data)
    Write: Ack block 1  --> Received

    Read:               <-- Not a data packet: wrong opcode
    Abort
    '''
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_two_blocks_server_returns_wrong_opcode(self, mock_sendto, mock_recvfrom):
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
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_1 = mock.call( ack_string, (server_ip, tid) )

        # Server response - wrong block number
        opcode = AckPacket.OPCODE       # Will set wrong opcode
        block_number = 2
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_packet.OPCODE = opcode
        data_string = data_packet.network_string()
        data_block_2 = create_socket_tuple(data_string, server_ip, tid)

        # Set sendto expectations
        sendto_calls = [
            read_request,
            ack_block_1,
        ]

        # Set recvfrom responses/side effects
        mock_recvfrom.side_effect = [
            data_block_1,
            data_block_2,
        ]

        ### Test
        client = Client2()
        assert False == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 2 == mock_recvfrom.call_count

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
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_two_blocks_success_empty_payload_ends_transmission(self, mock_sendto, mock_recvfrom):
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
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_1 = mock.call( ack_string, (server_ip, tid) )

        # Server response - data packet
        block_number = 2
        data = ''
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_2 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_2 = mock.call( ack_string, (server_ip, tid) )

        # Server does not retransmit last packet
        server_timeout = socket.timeout

        # Set sendto expectations
        sendto_calls = [
            read_request,
            ack_block_1,
            ack_block_2,
        ]

        # Set recvfrom responses/side effects
        mock_recvfrom.side_effect = [
            data_block_1,
            data_block_2,
            server_timeout,
        ]

        ### Test
        client = Client2()
        assert True == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 3 == mock_recvfrom.call_count

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
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_two_blocks_success_smallest_payload(self, mock_sendto, mock_recvfrom):
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
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_1 = mock.call( ack_string, (server_ip, tid) )

        # Server response - data packet
        block_number = 2
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_2 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_2 = mock.call( ack_string, (server_ip, tid) )

        # Server does not retransmit last packet
        server_timeout = socket.timeout

        # Set sendto expectations
        sendto_calls = [
            read_request,
            ack_block_1,
            ack_block_2,
        ]

        # Set recvfrom responses/side effects
        mock_recvfrom.side_effect = [
            data_block_1,
            data_block_2,
            server_timeout,
        ]

        ### Test
        client = Client2()
        assert True == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.call_args_list
        assert 3 == mock_recvfrom.call_count

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
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_two_blocks_success_server_resends_first_block(self, mock_sendto, mock_recvfrom):
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
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_1 = mock.call( ack_string, (server_ip, tid) )

        # Server response - data packet
        block_number = 2
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_2 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_2 = mock.call( ack_string, (server_ip, tid) )

        # Server does not retransmit last packet
        server_timeout = socket.timeout

        # Set sendto expectations
        sendto_calls = [
            read_request,
            ack_block_1,
            ack_block_1,
            ack_block_2,
        ]

        # Set recvfrom responses/side effects
        mock_recvfrom.side_effect = [
            data_block_1,
            data_block_1,
            data_block_2,
            server_timeout,
        ]

        ### Test
        client = Client2()
        assert True == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 4 == mock_recvfrom.call_count

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
    @mock.patch('socket.socket.recvfrom')
    @mock.patch('socket.socket.sendto')
    def test_two_blocks_success_server_resends_first_and_final_blocks(self, mock_sendto, mock_recvfrom):
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
        read_request = mock.call( read_string, (server_ip, server_port) )

        # Server response - data packet
        block_number = 1
        data = create_random_data_string(MAX_DATA_SIZE)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_1 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_1 = mock.call( ack_string, (server_ip, tid) )

        # Server response - data packet
        block_number = 2
        data = create_random_data_string(1)
        data_packet = DataPacket(block_number, data)
        data_string = data_packet.network_string()
        data_block_2 = create_socket_tuple(data_string, server_ip, tid)

        # Client ack response
        ack_packet = AckPacket(block_number)
        ack_string = ack_packet.network_string()
        ack_block_2 = mock.call( ack_string, (server_ip, tid) )

        # Server does not retransmit last packet
        server_timeout = socket.timeout

        # Set sendto expectations
        sendto_calls = [
            read_request,
            ack_block_1,
            ack_block_1,
            ack_block_2,
            ack_block_2,
        ]

        # Set recvfrom responses/side effects
        mock_recvfrom.side_effect = [
            data_block_1,
            data_block_1,
            data_block_2,
            data_block_2,
            server_timeout,
        ]

        ### Test
        client = Client2()
        assert True == client.read(filename, server_ip, server_port)
        assert sendto_calls == mock_sendto.mock_calls
        assert 4 == mock_recvfrom.call_count

    @pytest.mark.skip('todo')
    def test_read_a_different_filename(self, mock_socket):
        pass

    @pytest.mark.skip('todo')
    def test_read_from_different_server_ip_address(self, mock_socket):
        pass

    @pytest.mark.skip('todo')
    def test_read_from_different_server_port(self, mock_socket):
        pass
