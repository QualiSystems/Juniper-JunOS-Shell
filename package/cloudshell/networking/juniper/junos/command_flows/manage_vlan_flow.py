from cloudshell.networking.juniper.junos.command_modes.junipr_command_modes import ConfigCommandMode, DefaultCommandMode
from cloudshell.networking.juniper.junos.junos_cli import JunosCli
from cloudshell.cli.command_mode_helper import CommandModeHelper
from cloudshell.networking.juniper.junos.command_templates import add_remove_vlan


class AddVlanFlow(object):
    def __init__(self, junos_cli, context, logger):
        """
        :param junos_cli:
        :type junos_cli: JunosCli
        :param context:
        :param logger:
        :return:
        """
        self._junos_cli = junos_cli
        self._context = context
        self._logger = logger

        self._default_mode = None
        self._config_mode = None

    @property
    def default_mode(self):
        if not self._default_mode:
            self._default_mode = CommandModeHelper.create_command_mode(DefaultCommandMode, self._context)
        return self._default_mode

    @property
    def config_mode(self):
        if not self._config_mode:
            self._config_mode = CommandModeHelper.create_command_mode(ConfigCommandMode, self._context)
        return self._config_mode

    def create_qnq_vlan(self, vlan_name, vlan_id):
        """

        :param vlan_name:
        :param vlan_id:
        :return:
        """
        with self._junos_cli.get_session(self.config_mode) as config_session:
            config_session.send_command(add_remove_vlan.CREATE_VLAN.get_command(vlan_name, vlan_id))
            config_session.send_command(add_remove_vlan.CREATE_VLAN_QNQ.get_command(vlan_name))

    def create_vlan(self, vlan_name, vlan_id):
        """

        :param vlan_name:
        :param vlan_id:
        :return:
        """
        with self._junos_cli.get_session(self.config_mode) as config_session:
            config_session.send_command(add_remove_vlan.CREATE_VLAN.get_command(vlan_name, vlan_id))

    def set_vlan_to_interface(self, interface, mode, vlan_name):
        """

        :param interface:
        :param mode:
        :param vlan_name:
        :return:
        """
        with self._junos_cli.get_session(self.config_mode) as config_session:
            config_session.send_command(
                add_remove_vlan.SET_VLAN_TO_INTERFACE.get_command(interface, mode.lower(), vlan_name))
