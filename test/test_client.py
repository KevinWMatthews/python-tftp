import pytest
import mock
from mock import MagicMock, patch
import tftp

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
