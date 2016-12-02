from cloudshell.cli.command_template.command_template import CommandTemplate


class AddRemoveVlan(CommandTemplate):
    ADD_VLAN=''
    REMOVE_VLAN=''

    def __init__(self, command):
        CommandTemplate.__init__(self, command)