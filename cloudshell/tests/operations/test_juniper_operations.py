from unittest import TestCase, main

from cloudshell.cli.session.session_creator import SessionCreator
from cloudshell.cli.session.session_proxy import ReturnToPoolProxy
from cloudshell.configuration.cloudshell_cli_configuration import CONNECTION_TYPE_SSH
from cloudshell.networking.juniper.junos.junos_resource_driver import JunosResourceDriver
from cloudshell.shell.core.context import ResourceCommandContext, ResourceContextDetails, ReservationContextDetails
import types
import inject
from mock import MagicMock as Mock

from cloudshell.networking.juniper.junos.handler.juniper_junos_operations import JuniperJunosOperations


class TestJuniperOperations(TestCase):
    def setUp(self):
        self._cli_service = Mock()
        self._logger = Mock()
        self._operations_instance = JuniperJunosOperations(cli_service=self._cli_service, logger=self._logger)

    def test_call_send_custom_command(self):
        command = 'test command'
        self._operations_instance.send_command(command)
        self._cli_service.send_command.assert_called_once_with(command)

    def test_call_send_custom_command_empty_command(self):
        command = ''
        self.assertRaises(Exception, self._operations_instance.send_command, command)

    def test_call_send_custom_config_command(self):
        command = 'test command'
        self._operations_instance.send_config_command(command)
        self._cli_service.send_config_command.assert_called_once_with(command)

    def test_call_send_custom_config_command_empty_command(self):
        command = ''
        self.assertRaises(Exception, self._operations_instance.send_config_command, command)

    def test_shutdown(self):
        self._operations_instance.shutdown()
        self._cli_service.send_command.assert_called_once_with('request system power-off', expected_map=None, error_map=None)


if __name__ =='__main__':
    main()