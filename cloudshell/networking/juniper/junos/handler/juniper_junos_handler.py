import time

from cloudshell.cli.command_template import command_template_service
from cloudshell.configuration.cloudshell_cli_binding_keys import CLI_SERVICE
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER
import inject
import re
from cloudshell.networking.juniper.autoload.juniper_snmp_autoload import JuniperSnmpAutoload
from cloudshell.networking.operations.interfaces.autoload_operations_interface import AutoloadOperationsInterface


# from cloudshell.networking.operations.interfaces.configuration_operations_interface import save



class JuniperJunosHandler(AutoloadOperationsInterface):
    def __init__(self):
        pass

    @property
    def logger(self):
        return inject.instance(LOGGER)

    @property
    def cli_service(self):
        return inject.instance(CLI_SERVICE)

    def execute_command_map(self, command_map):
        command_template_service.execute_command_map(command_map, self.cli_service.send_config_command)

    def restore_configuration(self, source_file, config_type, clear_config='override'):
        if clear_config is '':
            clear_config = 'override'

        if not source_file or source_file is '':
            raise Exception('JuniperJunosHandler', 'Config source cannot be empty')

        clear_config = clear_config.lower()
        if clear_config == 'append':
            restore_type = 'merge'
        elif clear_config == 'override':
            restore_type = clear_config
        else:
            raise Exception('JuniperJunosHandler', 'Incorrect restore type')

        self.execute_command_map({'restore': [restore_type, source_file]})
        self.commit()
        return "Config file {0} has been restored with restore type {1}".format(source_file, restore_type)

    def update_firmware(self, remote_host, file_path):
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

    def backup_configuration(self, destination_host, source_filename):
        system_name = self.attributes_dict['ResourceFullName']
        system_name = re.sub(r'[\.\s]', '_', system_name)

        if not source_filename or source_filename.lower() != 'startup':
            source_filename = 'Running'

        file_name = "{0}-{1}-{2}".format(system_name, source_filename, time.strftime("%d%m%y-%H%M%S", time.localtime()))
        if not destination_host or destination_host is '':
            backup_location = self.cloud_shell_api.GetAttributeValue(self.attributes_dict['ResourceFullName'],
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

    def send_command(self, cmd, expected_str=None, timeout=30):
        if cmd is None or cmd == '':
            raise Exception('JuniperJunosHandler', "Command cannot be empty")
        if expected_str is None or expected_str == '':
            expected_str = self._prompt
        self._exit_configuration_mode()
        return self._check_output_for_errors(self._send_command(cmd, expected_str=expected_str,
                                                                timeout=timeout, is_need_default_prompt=False,
                                                                retry_count=20))

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

    def normalize_output(self, output):
        if output:
            return output.replace(' ', self.SPACE).replace('\r\n', self.NEWLINE).replace('\n', self.NEWLINE).replace(
                '\r', self.NEWLINE)
        return None

    def shutdown(self):
        self.logger.info("shutting down")
        self.execute_command_map({'shutdown': []}, self._send_command)
        return "Shutdown command completed"
