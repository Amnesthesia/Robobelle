import copy

from twisted.internet import protocol
from twisted.python import log
from twisted.words.protocols import irc

from module_loader import ModuleLoader
from event import Event
from message import Message

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

    #
    # Existing events are:
    #     - action [A user performs an action, i.e /me dances]
    #     - kicked [A user is kicked]
    #     - joined [A user has joined]
    #     - mode   [Channel mode is changed]
    #     - parted [A user has left the channel]
    #     - quit   [A user has quit the network]
    #     - renamed[A user changed nick]
    #     - topic  [Channel topic is changed]

    # Action Event(contents, source, target, channel, reply_handle)
    def action(self, user, channel, emote):
        ev = Event('action',emote, user, None, channel, self)
        ev.dispatch()
    # Kicked
    def userKicked(self, kickee, channel, kicker, message):
        ev = Event('kick', message, kicker, kickee, channel, self)
        ev.dispatch()
    # Joined
    def userJoined(self, user, channel):
        ev = Event('joined', None, user, channel, channel, self)
        ev.dispatch()
    # Mode
    #def modeChanged(self, user, channel, set, modes, args):
    #    with Event('mode', modes, user, channel, channel, self) as response:
    #        response.dispatch()
    # Parted
    def userLeft(self, user, channel):
        ev = Event('parted', None, user, channel, channel, self)
        ev.dispatch()
    # Quit
    def userQuit(self, user, quitMessage):
        ev = Event('quit', quitMessage, user, None, None, self)
        ev.dispatch()
    # Renamed
    def userRenamed(self, oldname, newname):
        ev = Event('nick', None, oldname, newname, None, self)
        ev.dispatch()
    # Topic
    def topicUpdated(self, user, channel, newTopic):
        ev = Event('topic', newTopic, user, channel, channel, self)
        ev.dispatch()





    def privmsg(self, user, channel, msg):
        """Called when the bot receives a message."""

        # If a message starts with the command_prefix (usually !)
        # then parse the command
        if msg.startswith(self.factory.command_prefix):
            sender = user.split('!', 1)[0]
            reply_to = ''

            # If it's a PM
            reply_to = sender

            # Create an important Message object. It will dispatch the
            # wanted functions in each module.
            m = Message(msg, reply_to, channel, self)
            m.dispatch()


        # It should also be possible to do "passive" things, like logging
        # or learning from messages.
        else:
            # If any module has a method "raw", it will be run on ANY message
            # but no reply can be sent
            for module in self.factory.loader.modules["regex"]:
              if hasattr(module["module"], 'raw'):
                getattr(module["module"],'raw')(msg)
