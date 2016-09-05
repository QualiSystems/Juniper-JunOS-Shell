import inject

from cloudshell.configuration.cloudshell_cli_binding_keys import CLI_SERVICE
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER, API, CONTEXT, CONFIG
from cloudshell.networking.operations.state_operations import StateOperations
from cloudshell.shell.core.context_utils import get_resource_context_attribute


class JuniperJunosConnectivityOperations(StateOperations):

    def __init__(self, cli_service=None, logger=None, api=None, context=None, config=None, resource_name=None):
        self._cli_service = cli_service
        self._logger = logger
        self._api = api
        self._context = context
        self._config = config
        self._resource_name = resource_name

    @property
    def logger(self):
        if self._logger is None:
            self._logger = inject.instance(LOGGER)

        return self._logger

    @property
    def cli(self):
        if self._cli_service is None:
            self._cli_service = inject.instance(CLI_SERVICE)

        return self._cli_service

    @property
    def api(self):
        if self._api is None:
            self._api = inject.instance(API)

        return self._api

    @property
    def context(self):
        if self._context is None:
            self._context = inject.instance(CONTEXT)

        return self._context

    @property
    def config(self):
        if self._config is None:
            self._config = inject.instance(CONFIG)

        return self._config

    @property
    def resource_name(self):
        if self._resource_name is None:
            self._resource_name = get_resource_context_attribute('name', self.context)

        return self._resource_name

    def shutdown(self):
        pass
