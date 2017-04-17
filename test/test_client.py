import pytest
import mock
from mock import MagicMock


class ProductionClass():
    def __init__(self):
        pass

    def method(self):
        pass


def test_1(mocker):
    thing = ProductionClass()
    thing.method = MagicMock(return_value = 66) # This also works with Mock
    assert thing.method(42) == 66
    thing.method.assert_called_with(42)
