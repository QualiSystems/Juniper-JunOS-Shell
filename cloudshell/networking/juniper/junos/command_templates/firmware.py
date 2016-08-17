from cloudshell.cli.command_template.command_template import CommandTemplate

FIRMWARE_UPGRADE = CommandTemplate('request system software add {0}', [r'.+'], ['Incorrect package path'])
