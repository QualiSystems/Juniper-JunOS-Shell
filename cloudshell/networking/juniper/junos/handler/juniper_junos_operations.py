import time

from cloudshell.cli.command_template import command_template_service
from cloudshell.configuration.cloudshell_cli_binding_keys import CLI_SERVICE
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER, CONTEXT, API
from cloudshell.networking.juniper.junos.command_templates.firmware import FIRMWARE_UPGRADE
from cloudshell.networking.juniper.junos.command_templates.reboot import REBOOT
import cloudshell.networking.juniper.junos.command_templates.save_restore as save_restore
from cloudshell.networking.juniper.junos.command_templates.shutdown import SHUTDOWN
from cloudshell.shell.core.context_utils import get_attribute_by_name
import inject
import re
from cloudshell.networking.operations.interfaces.configuration_operations_interface import \
    ConfigurationOperationsInterface
from cloudshell.networking.operations.interfaces.firmware_operations_interface import FirmwareOperationsInterface
from cloudshell.networking.operations.interfaces.power_operations_interface import PowerOperationsInterface
from cloudshell.networking.operations.interfaces.send_command_interface import SendCommandInterface


class JuniperJunosOperations(ConfigurationOperationsInterface, FirmwareOperationsInterface,
                             PowerOperationsInterface, SendCommandInterface):
    def __init__(self, context=None, api=None, cli_service=None, logger=None):
        self._context = context
        self._api = api
        self._cli_service = cli_service
        self._logger = logger

    @property
    def logger(self):
        return self._logger or inject.instance(LOGGER)

    @property
    def cli_service(self):
        return self._cli_service or inject.instance(CLI_SERVICE)

    @property
    def context(self):
        return self._context or inject.instance(CONTEXT)

    @property
    def api(self):
        return self._api or inject.instance(API)

    def execute_command_map(self, command_map, send_command_func=None):
        if send_command_func:
            command_template_service.execute_command_map(command_map, send_command_func)
        else:
            command_template_service.execute_command_map(command_map, self.cli_service.send_config_command)

    def restore_configuration(self, source_file, config_type='running', restore_method='override', vrf=None):

        if not source_file:
            raise Exception(self.__class__.__name__, 'Config source cannot be empty')

        if config_type.lower() != 'running':
            raise Exception(self.__class__.__name__, 'Device does not support restoring in \"{}\" configuration type, '
                                                     '\"running\" is only supported'.format(config_type or 'None'))

        restore_method = restore_method.lower()
        if restore_method == 'append':
            restore_type = 'merge'
        elif restore_method == 'override':
            restore_type = restore_method
        else:
            raise Exception(self.__class__.__name__, 'Incorrect restore method')

        self.execute_command_map({save_restore.RESTORE: [restore_type, source_file]})
        self.cli_service.commit()

    def save_configuration(self, destination_host, source_filename='running', vrf=None):
        system_name = self.context.resource.fullname
        system_name = re.sub(r'[\.\s]', '_', system_name)

        if source_filename.lower() != 'running':
            raise Exception(self.__class__.__name__, 'Device does not support saving \"{}\" '
                                                     'configuration type, \"running\" is only supported'.format(
                source_filename or 'None'))

        file_name = "{0}-{1}-{2}".format(system_name, source_filename, time.strftime("%d%m%y-%H%M%S", time.localtime()))
        if not destination_host:
            backup_location = get_attribute_by_name('Backup Location', context=self.context)
            if backup_location:
                destination_host = backup_location
            else:
                raise Exception(self.__class__.__name__, "Backup location or path is empty")

        if destination_host.endswith('/'):
            destination_host = destination_host[:-1]
        full_path = "{0}/{1}".format(destination_host, file_name)
        self.logger.info("Save configuration to file {0}".format(full_path))
        self.execute_command_map({save_restore.SAVE: full_path})
        return full_path

    def update_firmware(self, remote_host, file_path, size_of_firmware=0):
        self.logger.info("Upgradeing firmware")
        if not remote_host or remote_host is '' or not file_path or file_path is '':
            raise Exception('JuniperJunosHandler', "Remote host or filepath cannot be empty")
        if remote_host.endswith('/'):
            remote_host = remote_host[:-1]
        if file_path.startswith('/'):
            file_path = file_path[1:]
        self.execute_command_map({FIRMWARE_UPGRADE: '{0}/{1}'.format(remote_host, file_path)})
        self.execute_command_map({REBOOT: []})

    def send_command(self, command):
        if not command:
            raise Exception(self.__class__.__name__, "Command cannot be empty")
        return self.cli_service.send_command(command)

    def send_config_command(self, command):
        if not command:
            raise Exception(self.__class__.__name__, "Command cannot be empty")
        return self.cli_service.send_config_command(command)

    def shutdown(self):
        self.logger.info("shutting down")
        self.execute_command_map({SHUTDOWN: []}, self.cli_service.send_command)
