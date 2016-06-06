import time

from cloudshell.cli.command_template import command_template_service
from cloudshell.configuration.cloudshell_cli_binding_keys import CLI_SERVICE
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER, CONTEXT, API
from cloudshell.configuration.cloudshell_snmp_binding_keys import SNMP_HANDLER
import inject
import re
from cloudshell.networking.juniper.autoload.juniper_snmp_autoload import JuniperSnmpAutoload
from cloudshell.networking.operations.interfaces.autoload_operations_interface import AutoloadOperationsInterface
from cloudshell.networking.operations.interfaces.configuration_operations_interface import \
    ConfigurationOperationsInterface
from cloudshell.networking.operations.interfaces.firmware_operations_interface import FirmwareOperationsInterface
from cloudshell.networking.operations.interfaces.power_operations_interface import PowerOperationsInterface
from cloudshell.networking.operations.interfaces.send_command_interface import SendCommandInterface


class JuniperJunosHandler(AutoloadOperationsInterface, ConfigurationOperationsInterface, FirmwareOperationsInterface,
                          PowerOperationsInterface, SendCommandInterface):
    def __init__(self):
        pass

    @property
    def logger(self):
        return inject.instance(LOGGER)

    @property
    def cli_service(self):
        return inject.instance(CLI_SERVICE)

    @property
    def snmp_handler(self):
        return inject.instance(SNMP_HANDLER)

    @property
    def context(self):
        return inject.instance(CONTEXT)

    @property
    def api(self):
        return inject.instance(API)

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

    def update_firmware(self, remote_host, file_path, size_of_firmware):
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

    def discover(self):
        """Load device structure, and all required Attribute according to Networking Elements Standardization design
        :return: Attributes and Resources matrix,
        currently in string format (matrix separated by '$', lines by '|', columns by ',')
        """
        # ToDo add voperation system validation
        # if not self.is_valid_device_os():
        # error_message = 'Incompatible driver! Please use correct resource driver for {0} operation system(s)'. \
        #    format(str(tuple(self.supported_os)))
        # self.logger.error(error_message)
        # raise Exception(error_message)

        self.logger.info('************************************************************************')
        self.logger.info('Start SNMP discovery process .....')
        generic_autoload = JuniperSnmpAutoload(self.snmp_handler, self.logger)
        result = generic_autoload.discover_snmp()
        self.logger.info('Start SNMP discovery Completed')
        return result

    # def normalize_output(self, output):
    #     if output:
    #         return output.replace(' ', self.SPACE).replace('\r\n', self.NEWLINE).replace('\n', self.NEWLINE).replace(
    #             '\r', self.NEWLINE)
    #     return None

    def shutdown(self):
        self.logger.info("shutting down")
        self.execute_command_map({'shutdown': []}, self.cli_service.send_command)
        return "Shutdown command completed"
