from collections import OrderedDict
import time

from cloudshell.cli.command_template import command_template_service
from cloudshell.configuration.cloudshell_cli_binding_keys import CLI_SERVICE, SESSION
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER, CONTEXT, API, CONFIG
from cloudshell.networking.juniper.junos.command_templates.firmware import FIRMWARE_UPGRADE
from cloudshell.networking.juniper.junos.command_templates.reboot import REBOOT
import cloudshell.networking.juniper.junos.command_templates.save_restore as save_restore
from cloudshell.networking.juniper.junos.command_templates.shutdown import SHUTDOWN
from cloudshell.shell.core.config_utils import override_attributes_from_config
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
    SESSION_WAIT_TIMEOUT = 600
    DEFAULT_PROMPT = '[%>#]\s*$|[%>#]\s*\n'
    ERROR_MAP = {}

    def __init__(self, context=None, api=None, cli_service=None, logger=None, config=None, session=None):
        self._context = context
        self._api = api
        self._cli_service = cli_service
        self._logger = logger
        self._config = config
        self._session = session
        overridden_config = override_attributes_from_config(JuniperJunosOperations, config=self.config)
        self._session_wait_timeout = overridden_config.SESSION_WAIT_TIMEOUT
        self._default_prompt = overridden_config.DEFAULT_PROMPT
        self._error_map = overridden_config.ERROR_MAP

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

    @property
    def config(self):
        return self._config or inject.instance(CONFIG)

    @property
    def session(self):
        return self._session or inject.instance(SESSION)

    def execute_command_map(self, command_map, send_command_func=None, **kwargs):
        if send_command_func:
            command_template_service.execute_command_map(command_map, send_command_func=send_command_func, **kwargs)
        else:
            command_template_service.execute_command_map(command_map,
                                                         send_command_func=self.cli_service.send_config_command,
                                                         **kwargs)

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

    def update_firmware(self, remote_host, file_path=None, size_of_firmware=0):
        self.logger.info("Upgradeing firmware")
        if not remote_host:
            raise Exception(self.__class__.__name__, "Firmware file path cannot be empty")
        expected_map = {r'\[[Yy]es,[Nn]o\]': lambda session: session.send_line('yes')}
        flow = OrderedDict()
        flow[FIRMWARE_UPGRADE] = [remote_host]
        flow[REBOOT] = []
        self.execute_command_map(flow, send_command_func=self.cli_service.send_command, expected_map=expected_map,
                                 error_map=self._error_map)
        session = self.session
        if session.session_type.lower() != 'console':
            self._wait_session_up(self.session)

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

    def _wait_session_up(self, session):
        self.logger.debug('Waiting session up')
        waiting_reboot_time = time.time()
        while True:
            try:
                if time.time() - waiting_reboot_time > self._session_wait_timeout:
                    raise Exception(self.__class__.__name__,
                                    'Session cannot start reboot after {} sec.'.format(self._session_wait_timeout))
                session.send_line('')
                time.sleep(1)
            except:
                self.logger.debug('Session disconnected')
                break
        reboot_time = time.time()
        while True:
            if time.time() - reboot_time > self._session_wait_timeout:
                self.cli_service.destroy_threaded_session(session=session)
                raise Exception(self.__class__.__name__,
                                'Session cannot connect after {} sec.'.format(self._session_wait_timeout))
            try:
                self.logger.debug('Reconnect retry')
                session.connect(re_string=self._default_prompt)
                self.logger.debug('Session connected')
                break
            except:
                time.sleep(5)
