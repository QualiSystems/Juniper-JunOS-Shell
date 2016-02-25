from cloudshell.networking.parameters_service.command_template import CommandTemplate

FIRMWARE_UPGRADE = {'firmware_upgrade': CommandTemplate('request system software add {0}', [r'.+'], ['Incorrect package path']),
            'reboot': CommandTemplate('request system reboot', [], [])}
