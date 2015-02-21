from bot.main import RoboBelle
from main import *


class RobotFactory(protocol.ClientFactory):
    """ This class inherits IRC protocol stuff
    from Twisted and sets up the basics """

    # Instantiate IRC protocol
    protocol = RoboBelle

    def __init__(self, settings):
        self.modules = []                   # Array containing modules

        """ Initialize the bot factory with provided settings """
        self.network = settings["network"]
        self.channels = settings["channels"]
        self.realname = settings["realname"]
        self.user = settings["user"]
        self.nick = settings["nick"]
        self.command_prefix = settings["command_prefix"]
        self.modules = settings["modules"]
        self.loader = copy.copy(ModuleLoader())
