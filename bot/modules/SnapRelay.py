import os
import imghdr
from PIL import Image
from itertools import repeat
from moviepy.editor import *
import urllib
import re
import sqlite3 as sql
import random

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
    last_check = datetime.now()

    # Randomizes timer to timer value + 0..180
    RANDOM_TIMER = 180

    matchers = {"!snap": "send_snap", "!checksnaps": "check_for_snaps", "!gallery": "gallery_link", "!friend": "add_friend", "!irl": "gallery_link"}
    timer = {"120": "download_snaps"}
    imgur_handle = None
    snapchat_handle = Snapchat()
    short_url_handle = Shortener('GoogleShortener')
    album_id = None
    db = sql.connect('bot/modules/databases/snap')
    last_check = None
    ignore_snap_ids = []
    PATH = './snaps/'
    EXTENSIONS = [
        'jpeg',
        'jpg',
        'png'
    ]

    def __init__(self, args):
        super(self.__class__, self).__init__(self)
        self.last_check = datetime.now()
        self.initialize_database()
        config = ConfigParser()
        config.read(["settings.ini"])
        self.imgur_handle = pyimgur.Imgur(config.get('belle', 'imgur_app_id'))
        self.IMGUR_APP_ID = config.get('belle', 'imgur_app_id')
        self.SNAPCHAT_USERNAME = config.get('belle', 'snapchat_username')
        self.SNAPCHAT_PASSWORD = config.get('belle', 'snapchat_password')
        self.SNAP_CHANNEL = config.get('belle', 'snap_channel')
        self.snapchat_handle.login(self.SNAPCHAT_USERNAME,self.SNAPCHAT_PASSWORD)

    def check_for_snaps(self, msg=None):
      """
      Checks for snaps sent to mirabellezzz and posts a link
      """
      msg.reply("Ok give me a second!")
      if not self.download_snaps(self.snapchat_handle, msg):
        msg.reply("I don't have any new snaps :(")


    def add_friend(self, msg):
      """
      Adds a friend on snapchat - add yourself with !friend username to send snaps to mirabellezzz
      """
      self.snapchat_handle.add_friend(msg.clean_contents)
      msg.reply("Added!")

    def gallery_link(self, msg):
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

        now = datetime.now()
        if self.last_check and (self.last_check - now).seconds < self.RANDOM_TIMER:
            if msg:
                msg.reply("Just wait a little bit, I don't want to get banned from SnapChat again")
            return False
        else:
            self.last_check = now

        if self.RANDOM_TIMER and hasattr(self, 'timer_download_snaps'):

            time = [key for key, value in self.timer.items() if value == 'download_snaps']
            if time:
                t = int(time.pop())
                t += random.randrange(1, self.RANDOM_TIMER)
                print("Setting new timer for SnapRelay: "+str(t)+" seconds")
                self.timer_download_snaps.interval = t
                self.timer_download_snaps._reschedule()

        existing = self.get_downloaded_snaps()
        cursor = self.db.cursor()
        loader = ModuleLoader()

        snaps = s.get_snaps()
        snaps_to_imgur = []
        for snap in snaps:
            id = snap['id']
            if id[-1] == 's' or id in existing or id in self.ignore_snap_ids:
                print 'Skipping:', id
                continue

            result = self.download_single_snap(s, snap)

            if not result:
                print 'FAILED:', id
                self.ignore_snap_ids.append(id)
                print result
            else:
                if not msg:
                    loader.reply_handle.msg(self.SNAP_CHANNEL, "{user} just sent me a snap! {url}".format(user=snap['sender'].capitalize(), url=result))
                else:
                    msg.reply("{user} just sent me a snap! {url}".format(user=snap['sender'].capitalize(), url=result))
                imgur_id = result.split("/").pop().split(".").pop(0)
                snaps_to_imgur.append((imgur_id, snap['sender'], snap['time']))
                print 'Downloaded:', id
                print 'Uploading to imgur...'
        if snaps_to_imgur:
            cursor.executemany("INSERT INTO snap (imgur_id, author, time) VALUES (?,?,?)", snaps_to_imgur)
            loader.reply_handle.msg(self.SNAP_CHANNEL, ".. into the gallery with all the others :)")
            self.db.commit()
            s.clear_feed()

            return True
        else:
            return False

    def is_jpeg(self, image_path):
      """Checks if a file is ACTUALLY a jpeg"""
      if imghdr.what(image_path) not in ["jpg", "jpeg", "JPG", "JPEG"]:
        i = Image.open(image_path)
        if i.format in ["jpg", "jpeg", "JPG", "JPEG"]:
          return True
        else:
          return False
      else:
        return True

    def send_snap(self, msg):
      """ Sends a snap to a user, arguments being: !send username imgur-link """
      message = msg.clean_contents.split()

      image_url = message.pop()
      users = message
      if not isinstance(users, list):
        users = [users]


      if re.compile('https?://[a-zA-Z0-9\./\-_]+\.(jpg|jpeg)').match(image_url):
        image = urllib.urlretrieve(image_url, self.PATH+"sending/tmp.jpg")
        if not self.is_jpeg(self.PATH+"sending/tmp.jpg"):
          msg.reply("I'm sorry, {user}. I cant let you do that. Only JPEGs supported on Snapchat!".format(user=msg.author))
        else:
          snap_img_id = self.snapchat_handle.upload(Snapchat.MEDIA_IMAGE, self.PATH+"sending/tmp.jpg")
          msg.reply("Alright, sending that picture to {user}".format(user=", ".join(users)))
          self.snapchat_handle.send(snap_img_id, users)
      elif re.compile('https?://[a-zA-Z0-9\./\-_]+\.(mp4|gif|MP4|GIF)').match(image_url):
        extension = image_url.split(".").pop()
        image_or_video = urllib.urlretrieve(image_url, self.PATH+"sending/tmp."+extension)

        if extension in ["gif", "GIF"] and imghdr.what(self.PATH+"sending/tmp."+extension) in ["gif", "GIF"]:
          original_clip = VideoFileClip(self.PATH+"sending/tmp."+extension)

          if original_clip:
            if original_clip.duration > 10:
              clip = original_clip.subclip(0,10)
            else:
              clip = concatenate_videoclips(list(repeat(original_clip, int(10/original_clip.duration))))

            # Rotate mp4 if width > height
            if original_clip.w > original_clip.h:
              clip.write_videofile(self.PATH+"sending/send.mp4", fps=original_clip.fps, audio=False, codec="mpeg4", ffmpeg_params=["-vf", "transpose=1"])
              msg.reply("Sorry for the delay, I rotated your {x}x{y} gif and sent it as an mp4!".format(x=clip.w, y=clip.h))
            else:
              clip.write_videofile(self.PATH+"sending/send.mp4", fps=original_clip.fps, audio=False, codec="mpeg4")
              msg.reply("Sent {x}x{y} gif as mp4!".format(x=clip.w, y=clip.h))


            snap_vid_id = self.snapchat_handle.upload(Snapchat.MEDIA_VIDEO, self.PATH+"sending/send.mp4")
            print("Sending {}".format(snap_vid_id))
            self.snapchat_handle.send(snap_vid_id, users)
          else:
            msg.reply("Shit, sorry! Something went wrong when I tried to convert your gif to mp4")
        # MP4
      elif extension in ["MP4", "mp4"]:
          snap_vid_id = self.snapchat_handle.upload(Snapchat.MEDIA_VIDEO, self.PATH+"sending/tmp."+extension)
          self.snapchat_handle.send(snap_vid_id, users)
          msg.reply("Sent video to "+",".join(users))
      else:
        msg.reply("I don't think {url} is actually a direct link to a jpg/jpeg image :/ I need username, then image-link".format(url=url))




    def initialize_database(self):
      """
      Sets up the database
      """
      cursor = self.db.cursor()
      cursor.execute('CREATE TABLE IF NOT EXISTS "snap" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "author" text NOT NULL, "imgur_id" TEXT NOT NULL, "time" INTEGER);')
      self.db.commit()
