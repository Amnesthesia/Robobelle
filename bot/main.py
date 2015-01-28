import copy
import re

from twisted.internet import protocol
from twisted.python import log
from twisted.words.protocols import irc

from module_loader import ModuleLoader

class RoboBelle(irc.IRCClient):
    mods = []

    def connectionMade(self):
        """Called when a connection is made."""
        self.nickname = self.factory.nick
        self.realname = self.factory.realname
        irc.IRCClient.connectionMade(self)
        log.msg("Connection established")

    def connectionLost(self, reason):
        """Called when a connection is lost."""
        irc.IRCClient.connectionLost(self, reason)
        log.msg("connectionLost {!r}".format(reason))

    # Event callbacks
    def signedOn(self):
        """Called when bot has successfully signed on to server."""
        log.msg("Logged in")
        if self.nickname != self.factory.nick:
            log.msg('Nickname was taken, actual nickname is now '
                    '"{}"'.format(self.nickname))

        for channel in self.factory.channels:
            self.join(channel)

    def joined(self, channel):
        """Called when the bot joins the channel."""
        log.msg("[{nick} has joined {channel}]".format(nick=self.nickname,
                                                       channel=channel))

    def privmsg(self, user, channel, msg):
        """Called when the bot receives a message."""

        # If a message starts with the command_prefix (usually !)
        # then parse the command
        if msg.startswith(self.factory.command_prefix):
            sender = user.split('!', 1)[0]
            reply_to = ''

            # If it's a PM
            reply_to = sender if channel == self.nickname else channel

            # Iterate through all loaded modules and call the BaseModule
            # method 'run_if_matches' - if a module has any function
            # associated to the provided command, then it will be executed
            for module in self.factory.loader.modules["regex"]:
                if re.compile(module["regex"]).match(msg):
                    reply = getattr(module["module"],module["function"])(msg)
                    if reply:
                        log.msg("{match} matched a trigger in {cls} which returned: {reply}".format(match=msg, cls=module["module"].__class__.__name__,reply=reply))
                        log.msg("Sending reply to {}".format(reply_to))
                        self.msg(reply_to, reply)
                    else:
                        log.msg("{match} matched nothing in {cls}".format(match=msg, cls=module["module"].__class__.__name__))

        # It should also be possible to do "passive" things, like logging
        # or learning from messages.
        else:
            # If any module has a method "raw", it will be run on ANY message
            # but no reply can be sent
            for module in self.factory.loader.modules:
              if hasattr(module, 'raw'):
                getattr(module,'raw')(msg)
    
