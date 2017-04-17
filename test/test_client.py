import pytest
import mock
from mock import MagicMock, patch
import tftp
import socket

def test_1(mocker):
    thing = tftp.ProductionClass()
    thing.method = MagicMock(return_value = 66) # This also works with Mock
    assert thing.method(42) == 66
    thing.method.assert_called_with(42)

@patch('tftp.ProductionClass')
def test_2(mock_pc):
    tftp.ProductionClass()
    assert mock_pc is tftp.ProductionClass
    assert mock_pc.called

@patch('tftp.ProductionClass.method')
def test_3(mock_pc_method):
    tftp.ProductionClass.method()
    assert mock_pc_method is tftp.ProductionClass.method
    assert mock_pc_method.called

@patch('tftp.ProductionClass.method')
@patch('tftp.ProductionClass')
def test_4(mock_pc, mock_pc_method):
    assert mock_pc is tftp.ProductionClass
    assert mock_pc_method is tftp.ProductionClass.method
    tftp.ProductionClass()
    tftp.ProductionClass.method()
    assert mock_pc.called
    assert mock_pc_method.called

@patch('tftp.ProductionClass.method')
@patch('tftp.ProductionClass')
def test_5(mock_pc, mock_pc_method):
    assert mock_pc is tftp.ProductionClass
    assert mock_pc_method is tftp.ProductionClass.method
    tftp.ProductionClass()
    tftp.ProductionClass.method()
    assert mock_pc.called
    mock_pc_method.assert_called()

@patch.object(tftp.ProductionClass, 'method')
def test_6(mock_method):
    tftp.ProductionClass.method()
    mock_method.assert_called()

@patch.object(tftp.ProductionClass, 'method')
def test_7(mock_method):
    t = tftp.ProductionClass()
    t.method()
    mock_method.assert_called()

@patch.object(tftp.ProductionClass, 'method')
@patch('tftp.ProductionClass')
def test_8(mock_pc, mock_method):
    assert mock_pc is tftp.ProductionClass
    tftp.ProductionClass()
    assert mock_pc.called

    # This fails
    #  assert mock_method is tftp.ProductionClass.method

    # This fails
    #  tftp.ProductionClass.method()
    #  mock_method.assert_called()

    # And this fails
    #  t = tftp.ProductionClass()
    #  t.method()
    #  mock_method.assert_called()

# This fails: '_socketobject' object attribute 'sendto' is read-only
# I wonder if it's true that sendto is implemented in C so it can't be mocked.
#  @patch.object(socket.socket, 'sendto')
#  def test_sendto(mock_sendto):
    #  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #  assert mock_sendto.called

def test_pass_mock():
    m = mock.Mock()
    pc = tftp.PC(m)
    pc.call_socket()
    assert m.called

def test_send_to_socket():
    mock_socket = mock.Mock()
    tftp_client = tftp.Client2(mock_socket)
    tftp_client.send_to_socket()
    mock_socket.sendto.assert_called()
