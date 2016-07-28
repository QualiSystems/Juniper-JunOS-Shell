import time

from cloudshell.cli.command_template import command_template_service
from cloudshell.configuration.cloudshell_cli_binding_keys import CLI_SERVICE
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER, CONTEXT, API
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

    def restore_configuration(self, source_file, config_type, restore_method='override', vrf=None):
        if restore_method is '':
            restore_method = 'override'

        if not source_file or source_file is '':
            raise Exception('JuniperJunosHandler', 'Config source cannot be empty')

        restore_method = restore_method.lower()
        if restore_method == 'append':
            restore_type = 'merge'
        elif restore_method == 'override':
            restore_type = restore_method
        else:
            raise Exception('JuniperJunosHandler', 'Incorrect restore type')

        self.execute_command_map({'restore': [restore_type, source_file]})
        self.cli_service.commit()
        return "Config file {0} has been restored with restore type {1}".format(source_file, restore_type)

    def save_configuration(self, destination_host, source_filename, vrf=None):
        system_name = self.context.resource.fullname
        system_name = re.sub(r'[\.\s]', '_', system_name)

        if not source_filename or source_filename.lower() != 'startup':
            source_filename = 'Running'

        file_name = "{0}-{1}-{2}".format(system_name, source_filename, time.strftime("%d%m%y-%H%M%S", time.localtime()))
        if not destination_host or destination_host is '':
            backup_location = self.api.GetAttributeValue(self.context.resource.fullname,
                                                         'Backup Location').Value
            if backup_location and backup_location is not '':
                destination_host = backup_location
            else:
                raise Exception('JuniperJunosHandler', "Backup location or path is empty")

        if destination_host.endswith('/'):
            destination_host = destination_host[:-1]
        full_path = "{0}/{1}".format(destination_host, file_name)
        self.logger.info("Save configuration to file {0}".format(full_path))
        self.execute_command_map({'save': full_path})
        return "Config file {0} has been saved".format(full_path)

    def update_firmware(self, remote_host, file_path, size_of_firmware=0):
        self.logger.info("Upgradeing firmware")
        if not remote_host or remote_host is '' or not file_path or file_path is '':
            raise Exception('JuniperJunosHandler', "Remote host or filepath cannot be empty")
        if remote_host.endswith('/'):
            remote_host = remote_host[:-1]
        if file_path.startswith('/'):
            file_path = file_path[1:]
        self.execute_command_map({'firmware_upgrade': '{0}/{1}'.format(remote_host, file_path)})
        self.execute_command_map({'reboot': []})
        return "Firmware has been upgraded"

    def send_command(self, command):
        if command is None or command == '':
            raise Exception('JuniperJunosHandler', "Command cannot be empty")
        self.cli_service.send_command(command)

    def send_config_command(self, command):
        if command is None or command == '':
            raise Exception('JuniperJunosHandler', "Command cannot be empty")
        self.cli_service.send_config_command(command)

    def shutdown(self):
        self.logger.info("shutting down")
        self.execute_command_map({'shutdown': []}, self.cli_service.send_command)
        return "Shutdown command completed"
