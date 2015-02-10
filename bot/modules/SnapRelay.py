import os
from threading import Thread
import sqlite3 as sql
from snapchat.snapchat import Snapchat
import pyimgur
from pyshorteners.shorteners import Shortener
from ConfigParser import ConfigParser
from datetime import datetime
from bot.module_loader import ModuleLoader

from BaseModule import BaseModule

class SnapRelay(BaseModule):

    IMGUR_APP_ID  =  ""
    SNAPCHAT_USERNAME = ""
    SNAPCHAT_PASSWORD = ""
    SNAP_CHANNEL = ""

    matchers = {"!snap": "check_for_snaps", "!gallery": "gallery_link", "!friend": "add_friend", "!irl": "gallery_link"}
    timer = {"90": "download_snaps"}
    imgur_handle = None
    snapchat_handle = Snapchat()
    short_url_handle = Shortener('GoogleShortener')
    album_id = None
    db = sql.connect('bot/modules/databases/snap')
    last_check = None
    PATH = './snaps/'
    EXTENSIONS = [
        'jpeg',
        'jpg',
        'png'
    ]

    def __init__(self, args):
      super(self.__class__,self).__init__(self)
      self.initialize_database()
      config = ConfigParser()
      config.read(["settings.ini"])
      self.imgur_handle = pyimgur.Imgur(config.get('belle', 'imgur_app_id'))
      self.IMGUR_APP_ID = config.get('belle', 'imgur_app_id')
      self.SNAPCHAT_USERNAME = config.get('belle', 'snapchat_username')
      self.SNAPCHAT_PASSWORD = config.get('belle', 'snapchat_password')
      self.SNAP_CHANNEL = config.get('belle', 'snap_channel')
      self.snapchat_handle.login(self.SNAPCHAT_USERNAME,self.SNAPCHAT_PASSWORD)


    def check_for_snaps(self,msg=None):
      """
      Checks for snaps sent to mirabellezzz and posts a link
      """
      msg.reply("Ok give me a second!")
      if not self.download_snaps(self.snapchat_handle, msg):
        msg.reply("I don't have any new snaps :(")


    def add_friend(self,msg):
      """
      Adds a friend on snapchat - add yourself with !friend username to send snaps to mirabellezzz
      """
      self.snapchat_handle.add_friend(msg.clean_contents)
      msg.reply("Added!")

    def gallery_link(self,msg):
      """
      Gets the link to all snaps
      """
      link = self.generate_gallery_link()
      msg.reply(link)


    def generate_gallery_link(self):
      """
      Post a link to the imgur gallery
      """
      cursor = self.db.cursor()
      cursor.execute("SELECT COALESCE(GROUP_CONCAT(imgur_id),1) as img FROM snap ORDER BY id DESC")
      result = cursor.fetchone()[0]
      result = result.split(",")
      result.reverse()
      result = ",".join(result)
      url = "http://imgur.com/"+result.encode("utf-8")
      link = self.short_url_handle.short(url).encode('utf-8') if len(url)>75 else url
      return link



    def get_downloaded_snaps(self):
        """Gets the snapchat IDs that have already been downloaded and returns them in a set."""

        result = set()

        for name in os.listdir(self.PATH):
            print(name)
            split_name = name.split('.')
            ext = split_name.pop()
            filename = ".".join(split_name)

            if ext not in self.EXTENSIONS:
                continue

            ts, username, id = filename.split('+')
            result.add(id)
        return result

    def download_single_snap(self, s, snap):
        """Download a specific snap, given output from s.get_snaps()."""

        id = snap['id']
        name = snap['sender']
        s.add_friend(name)
        ts = str(snap['sent']).replace(':', '-')

        result = s.get_media(id)

        if not result:
            print "Result was ", result
            return False

        ext = s.is_media(result)

        if ext not in self.EXTENSIONS:
          print("Skipping {} snap".format(ext))
          return False

        filename = '{}+{}+{}.{}'.format(ts, name, id, ext)
        print "Writing to ", filename
        path = self.PATH + filename
        with open(path, 'wb') as fout:
            fout.write(result)


        image = self.imgur_handle.upload_image(path, title="via {user} ({date})".format(user=name, date=datetime.now()), album=self.album_id)
        return image.link or True

    def download_snaps(self, s=None, msg=None):
        """Download all snaps that haven't already been downloaded."""
        if not s:
          s = self.snapchat_handle
        existing = self.get_downloaded_snaps()
        cursor = self.db.cursor()
        loader = ModuleLoader()

        snaps = s.get_snaps()
        snaps_to_imgur = []
        for snap in snaps:
            id = snap['id']
            if id[-1] == 's' or id in existing:
                print 'Skipping:', id
                continue

            result = self.download_single_snap(s, snap)

            if not result:
                print 'FAILED:', id
                print result
            else:
                if not msg:
                  loader.reply_handle.msg(self.SNAP_CHANNEL, "{user} just sent me a snap! {url}".format(user=snap['sender'].capitalize(), url=result))
                else:
                  msg.reply("{user} just sent me a snap! {url}".format(user=snap['sender'].capitalize(), url=result))
                imgur_id = result.split("/").pop().split(".").pop(0)
                snaps_to_imgur.append((imgur_id,snap['sender'],snap['time']))
                print 'Downloaded:', id
                print 'Uploading to imgur...'
        if snaps_to_imgur:
          cursor.executemany("INSERT INTO snap (imgur_id, author, time) VALUES (?,?,?)",snaps_to_imgur)
          self.db.commit()
          s.clear_feed()
          return True
        else:
          return False

    def initialize_database(self):
      """
      Sets up the database
      """
      cursor = self.db.cursor()
      cursor.execute('CREATE TABLE IF NOT EXISTS "snap" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "author" text NOT NULL, "imgur_id" TEXT NOT NULL, "time" INTEGER);')
      self.db.commit()
