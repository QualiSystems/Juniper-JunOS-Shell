from pkgutil import extend_path
from cloudshell.shell.core.handler_factory import HandlerFactory
from cloudshell.networking.juniper.junos.handler.juniper_junos_handler import JuniperJunosHandler

__path__ = extend_path(__path__, __name__)
HandlerFactory.handler_classes['JUNOS'] = JuniperJunosHandler