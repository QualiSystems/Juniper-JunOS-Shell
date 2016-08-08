from cloudshell.cli.service.cli_service import CliService
from cloudshell.configuration.cloudshell_cli_binding_keys import CLI_SERVICE
from cloudshell.configuration.cloudshell_snmp_binding_keys import SNMP_HANDLER
from cloudshell.shell.core.driver_bootstrap import DriverBootstrap
import inject


class JunosDriverBootstrap(DriverBootstrap):
    def bindings(self, binder):
        """Binding for CLI service"""
        try:
            binder.bind_to_provider(SNMP_HANDLER, self._config.SNMP_HANDLER_FACTORY)
        except inject.InjectorException:
            pass

        """Binding for CLI service"""
        try:
            binder.bind_to_constructor(CLI_SERVICE, CliService)
        except inject.InjectorException:
            pass
