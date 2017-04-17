from tftp import Client
import mock

def test_client_can_be_created():
    mock_socket = mock.Mock()
    assert Client(mock_socket)
