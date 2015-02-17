import urllib2
import sqlite3 as sql
from ConfigParser import ConfigParser
from bot.module_loader import ModuleLoader
from bot.message import Message
from BaseModule import BaseModule


class RadioAmnesthesia(BaseModule):

    RADIO_STREAM = "http://radio.amnesthesia.com/stream"
    db = sql.connect('bot/modules/databases/radio')
    db.row_factory = sql.Row
    matchers = {"!song": "print_information",
                "!upvote": "upvote_song",
                "!downvote": "downvote_song",
                "!radio": "print_information",
                "!track": "print_track_info"
                }
    timer = {"100": "get_metadata"}
    current_artist = ""
    current_song = ""
    auto_printed = False

    def __init__(self, args):
        """
          Initialize the class as a subclass of BaseModule
          and call parent constructor with the defined matchers.
          These will be turned into regex-matchers that redirect to
          the provided function name
        """
        super(self.__class__, self).__init__(self)
        self.initialize_database()
        config = ConfigParser()
        config.read(["settings.ini"])
        self.CHANNEL = config.get('radio', 'channel')

    def print_information(self, msg):
        """
        Display currently playing track and a link to the radio
        """
        r = self.get_metadata()
        print(r)
        if r != 0 and not self.auto_printed:
            msg.reply("Now playing: \x02{track}\x02 by \x02{artist}\x02 [{url}]".format(track=self.current_song, artist=self.current_artist, url=self.RADIO_STREAM))
        elif not self.auto_printed:
            msg.reply("Nothing currently playing :(")


    def get_metadata(self, msg=None):
        """
        Retrieve metadata from the radiostream

        :returns: Title of the song / artist playing
        """
        print("Trying to get metadata ....")
        request = urllib2.Request(self.RADIO_STREAM)
        try:
            request.add_header('Icy-MetaData', 1)
            response = urllib2.urlopen(request)
            icy_metaint_header = response.headers.get('icy-metaint')
            print("So far so good, but ...")
            if icy_metaint_header is not None:
                metaint = int(icy_metaint_header)
                read_buffer = metaint+255
                content = response.read(read_buffer)
                title = content[metaint:].split("'")[1]
                split_title = title.split('-')
                artist = split_title[0].strip()
                track = split_title[1].strip()
                print("Alright, got "+title+" aka "+artist+" / "+track)
                # If the track has changed, write it in the channel
                if track != self.current_song:
                    ModuleLoader().reply_handle.msg(self.CHANNEL, "Now playing: \x02{artist}\x02 - \x02{track}\x02".format(artist=artist, track=track))
                    self.auto_printed = True
                else:
                    self.auto_printed = False
                print("Updating current artist")
                self.current_artist = artist
                self.current_song = track

                if artist and track:
                    cursor = self.db.cursor()
                    print("Trying to insert {artist} and {track}".format(artist=artist, track=track))
                    cursor.execute('INSERT OR IGNORE INTO song (artist, track) VALUES (?, ?)', (artist, track))
                    self.db.commit()
                    print("Insert didnt throw exception")
                print(title)
                return title
            else:
                return 0
        except:
            return 0

    def upvote_song(self, msg):
        """
        Upvote the currently playing song
        """
        cursor = self.db.cursor()
        user = msg.author
        title = self.get_metadata()

        if title:
            cursor.execute('INSERT OR IGNORE INTO votes(user, song_id, point) VALUES (?, (SELECT id FROM song WHERE artist = ? AND track = ?), 1);', (user, self.current_artist, self.current_song))
            self.db.commit()
            msg.reply("Thank you for sharing your opinion on {title} by {artist}".format(title=self.current_song, artist=self.current_artist))

    def downvote_song(self, msg):
        """
        Downvote the currently playing song
        """
        cursor = self.db.cursor()
        user = msg.author
        title = self.get_metadata()

        if title:
            cursor.execute('INSERT OR IGNORE INTO votes(user, song_id, point) VALUES (?, (SELECT id FROM song WHERE artist = ? AND track = ?), 0);', (user, self.current_artist, self.current_song))
            self.db.commit()
            msg.reply("Thank you for sharing your opinion on {title} by {artist}".format(title=self.current_song, artist=self.current_artist))

    def print_track_info(self, msg, optional=None):
        """
        Display information about a track (or the current track)
        """
        if len(msg.clean_contents) > 4:
            title = msg.clean_contents.split('-')
            if len(title)>1:
                artist = title[0].strip()
                song = title[1].strip()
        elif optional:
            artist = msg
            song = optional
        else:
            artist = self.current_artist
            song = self.current_song

        if artist and song:
            cursor = self.db.cursor()

            cursor.execute('SELECT SUM(point) as sum, COUNT(*) as total FROM votes WHERE song_id = (SELECT id FROM song WHERE artist = ? AND track = ?)', (artist, song))
            results = cursor.fetchone()

            up = results["sum"] if results["sum"] else 0
            down = results["total"]-up if results["sum"] else 0

            if isinstance(msg, Message):
                msg.reply("\x02{artist} - {song}\x02 ({up}/{down})".format(artist=artist, song=song, up=str(up), down=str(down)))
            else:
                return "{artist} - {song} ({up}/{down})".format(artist=artist, song=song, up=str(up), down=str(down))

    def initialize_database(self):
        """
        Sets up the song database
        """
        cursor = self.db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS song ("id" INTEGER PRIMARY KEY AUTOINCREMENT, "artist" TEXT NOT NULL, "track" TEXT NOT NULL, CONSTRAINT unq UNIQUE (artist, track));')
        cursor.execute('CREATE TABLE IF NOT EXISTS votes ("id" INTEGER PRIMARY KEY AUTOINCREMENT, "user" TEXT NOT NULL, "song_id" INTEGER, "point" INTEGER NOT NULL, FOREIGN KEY(song_id) REFERENCES song(id), CONSTRAINT unq UNIQUE(user, song_id))')
        self.db.commit()
