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
