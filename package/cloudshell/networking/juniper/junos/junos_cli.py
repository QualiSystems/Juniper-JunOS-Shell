from cloudshell.cli.cli import CLI


class JunosCli():
    def __init__(self, cli, context, logger):
        """
        :param cli:
        :type cli: CLI
        :param context:
        :param logger:
        :return:
        """
        self._cli = cli
        self._context = context
        self._logger = logger

    def _ssh_params(self):
        pass

    def _telnet_params(self):
        pass

    def _new_sessions(self):
        pass

    def get_session(self, command_mode):
        """
        :param command_mode:
        :return:
        :rtype:
        """
        return self._cli.get_session(self._new_sessions(), command_mode, self._logger)
