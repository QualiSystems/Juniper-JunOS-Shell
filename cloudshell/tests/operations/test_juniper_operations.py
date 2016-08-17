from unittest import TestCase

from mock import MagicMock as Mock
from cloudshell.networking.juniper.junos.handler.juniper_junos_operations import JuniperJunosOperations
import cloudshell.networking.juniper.junos.command_templates.save_restore as save_restore
from cloudshell.networking.juniper.junos.command_templates.shutdown import SHUTDOWN


class TestJuniperOperations(TestCase):
    def setUp(self):
        self._cli_service = Mock()
        self._logger = Mock()
        self._context = Mock()
        self._operations_instance = JuniperJunosOperations(cli_service=self._cli_service, logger=self._logger,
                                                           context=self._context)

    # send_custom_command
    def test_call_send_custom_command(self):
        command = 'test command'
        self._operations_instance.send_command(command)
        self._cli_service.send_command.assert_called_once_with(command)

    def test_call_send_custom_command_empty_command(self):
        command = ''
        self.assertRaises(Exception, self._operations_instance.send_command, command)

    # send_custom_config_command
    def test_call_send_custom_config_command(self):
        command = 'test command'
        self._operations_instance.send_config_command(command)
        self._cli_service.send_config_command.assert_called_once_with(command)

    def test_call_send_custom_config_command_empty_command(self):
        command = ''
        self.assertRaises(Exception, self._operations_instance.send_config_command, command)

    # shutdown
    def test_shutdown(self):
        self._operations_instance.shutdown()
        self._cli_service.send_command.assert_called_once_with(SHUTDOWN.get_command(), expected_map=None,
                                                               error_map=None)

    # save_configuration

    def test_save_configuration_convert_resource_name(self):
        destination_host = 'ftp://testhost.com'
        config_type = 'running'
        self._context.resource.fullname = 'test.resource name'
        file_name = self._operations_instance.save_configuration(destination_host, config_type)
        self.assertTrue('test_resource_name' in file_name)

    def test_save_configuration_support_only_running(self):
        destination_host = 'ftp://testhost.com'
        config_type = 'startup'
        self._context.resource.fullname = 'test.resource name'
        self.assertRaises(Exception, self._operations_instance.save_configuration, destination_host, config_type)

    def test_save_configuration_use_backup_location_attribute(self):
        destination_host = 'ftp://testhost.com'
        self._context.resource.attributes = {'Backup Location': destination_host}
        self._context.resource.fullname = 'test.resource name'
        config_type = 'running'
        file_name = self._operations_instance.save_configuration(None, config_type)
        self.assertTrue(destination_host in file_name)

    def test_save_configuration_backup_location_none(self):
        destination_host = ''
        self._context.resource.attributes = {'Backup Location': destination_host}
        self._context.resource.fullname = 'test.resource name'
        config_type = 'running'
        self.assertRaises(self._operations_instance.save_configuration, None, config_type)

    def test_save_configuration_backup_location_remove_slash(self):
        destination_host = 'ftp://testhost.com/test/'
        self._context.resource.fullname = 'test.resource name'
        config_type = 'running'
        file_name = self._operations_instance.save_configuration(destination_host, config_type)
        self.assertTrue('ftp://testhost.com/test/test_resource_name-running' in file_name)

    def test_save_configuration_call_command(self):
        destination_host = 'ftp://testhost.com/test/'
        self._context.resource.fullname = 'test.resource name'
        config_type = 'running'
        file_name = self._operations_instance.save_configuration(destination_host, config_type)
        self._cli_service.send_config_command.assert_called_once_with(save_restore.SAVE.get_command(file_name),
                                                                      error_map=None, expected_map=None)

    # restore_configuration
    def test_restore_configuration_source_file_none(self):
        self.assertRaises(Exception, self._operations_instance.restore_configuration, None)

    def test_restore_configuration_only_running(self):
        self.assertRaises(Exception, self._operations_instance.restore_configuration, 'test', 'startup')

    def test_restore_configuration_incorrect_method(self):
        self.assertRaises(Exception, self._operations_instance.restore_configuration, 'test', 'running',
                          restore_method='test')

    def test_restore_configuration_call_command(self):
        url = 'ftp://testhost.com/test/'
        config_type = 'running'
        restore_method = 'override'
        self._operations_instance.restore_configuration(url, config_type, restore_method=restore_method)
        self._cli_service.send_config_command.assert_called_once_with(
            save_restore.RESTORE.get_command(restore_method, url), error_map=None, expected_map=None)
