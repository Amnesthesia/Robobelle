from twisted.application.service import Service
from twisted.internet.endpoints import clientFromString
from twisted.python import usage, log
from bot.factory import RobotFactory


class Options(usage.Options):
    # Using Twisted's usage Options
    optParameters = [
        ['config', 'c', 'settings.ini', 'Configuration file.'],
    ]


class RoboBelleService(Service):
    def __init__(self, endpoint, channels, nick, realname, user, modules,
                 command_prefix):
        self._endpoint = endpoint
        self._channels = channels
        self._nick = nick
        self._realname = realname
        self._user = user
        self._modules = modules
        self._command_prefix = command_prefix

    def startService(self):
        """Construct a client and connect to server"""
        from twisted.internet import reactor

        def connected(bot):
            self._bot = bot

        def failure(err):
            log.err(err, _why='Could not connect to specified server')
            reactor.stop()

        client = clientFromString(reactor, self._endpoint)
        factory = RobotFactory({"network": self._endpoint,
                                "channels": self._channels,
                                "user": self._user,
                                "nick": self._nick,
                                "modules": self._modules,
                                "realname": self._realname,
                                "command_prefix": self._command_prefix})

        return client.connect(factory).addCallbacks(connected, failure)

    def stopService(self):
        """Disconnect"""
        if self._bot and self._bot.transport.connected:
            self._bot.transport.loseConnection()
