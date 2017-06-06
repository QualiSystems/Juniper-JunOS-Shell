from unittest import TestCase

from mock import patch, Mock

from juniper_junos_resource_driver import JuniperJunOSResourceDriver


class TestJuniperJunOSResourceDriver(TestCase):
    def setUp(self):
        self._instance = JuniperJunOSResourceDriver()
        self._context = Mock()

    @patch('juniper_junos_resource_driver.get_attribute_by_name')
    @patch('juniper_junos_resource_driver.get_cli')
    def test_initialize(self, get_cli_func, get_attribute_by_name_func):
        session_pool = 5
        get_attribute_by_name_func.return_value = session_pool
        cli_inst = Mock()
        get_cli_func.return_value = cli_inst
        self._instance.initialize(self._context)
        get_attribute_by_name_func.assert_called_once_with(context=self._context,
                                                           attribute_name='Sessions Concurrency Limit')
        get_cli_func.assert_called_once_with(session_pool)
