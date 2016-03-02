from cloudshell.networking.parameters_service.command_template import CommandTemplate

SAVE_RESTORE = {'save': CommandTemplate('save {0}', [r'.+'], ['Incorrect path']),
                'restore': CommandTemplate('load {0} {1}', [r'.+', r'.+'],
                                           ['Incorrect restore method', 'Incorrect source'])}
