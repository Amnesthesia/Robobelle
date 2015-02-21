from ConfigParser import ConfigParser
from twisted.application.service import IServiceMaker
from twisted.plugin import IPlugin
from zope.interface import implementer
from robobelle_service import *


@implementer(IServiceMaker, IPlugin)
class RoboBelleServiceMaker(object):
    tapname = "belle"
    description = "A modular IRC bot"
    options = Options

    def makeService(self, options):
        """Creates the service"""
        config = ConfigParser()
        config.read([options['config']])
        modules = filter(None, list(module.strip() for module in config.get('belle', 'modules').split('\n')))
        channels = filter(None, list(channel.strip() for channel in config.get('irc','channels').split('\n')))

        return RoboBelleService(
            endpoint = config.get('irc','endpoint'),
            channels = channels,
            nick = config.get('irc', 'nick'),
            realname = config.get('irc', 'realname'),
            user = config.get('irc', 'user'),
            modules = modules,
            command_prefix = config.get('belle', 'command_prefix')
        )


serviceMaker = RoboBelleServiceMaker()
