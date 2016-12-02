from cloudshell.cli.command_template.command_template import CommandTemplate

SAVE = CommandTemplate('save {0}', [r'.+'], ['Incorrect path'])
RESTORE = CommandTemplate('load {0} {1}', [r'.+', r'.+'], ['Incorrect restore method', 'Incorrect source'])
