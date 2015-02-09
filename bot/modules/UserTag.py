from datetime import datetime
import random
import sqlite3 as sql

from BaseModule import BaseModule



class UserTag(BaseModule):

    matchers = {"^!tag\s+\w+": "set_tag", "!get": "get_tag", "!set": "set_tag", "!tags": "tag_list", "!taglist": "tag_list"}

    db = sql.connect('bot/modules/databases/usertags')
    db.row_factory = sql.Row

    def __init__(self, args):
        """
          Initialize the class as a subclass of BaseModule
          and call parent constructor with the defined matchers.
          These will be turned into regex-matchers that redirect to
          the provided function name
        """
        super(self.__class__,self).__init__(self)
        self.initialize_database()

    def get_tag(self, msg):
      """ Retrieve a previously stored tags content """
      cursor = self.db.cursor()
      split_message = msg.clean_contents.split()
      tag = split_message.pop(0)
      cursor.execute('SELECT contents FROM "tag" WHERE tag=? LIMIT 1',(tag,))

      contents = cursor.fetchone()
      if contents:
        msg.reply("\x02{tag}\x02: {content}".format(tag=tag.encode('utf-8'), content=contents["contents"].encode('utf-8')))
      else:
        msg.reply("I don't think that tag is set, {sender}".format(sender=msg.author))

    def set_tag(self, msg):
      """ Set a tag to remember things! I will print it again later if you ask with !get yourtag """
      split_message = msg.clean_contents.split()
      tag = split_message.pop(0)
      contents = " ".join(split_message)

      # Some different replies for new tags:
      tag_message= ["Sweet, a word!", "Wow, I love words!", "Words are like scooby-snacks for me <3", "THANKS MAN, THAT'S A COOL TAG. VERY COOL. NO, REALLY."]

      cursor = self.db.cursor()
      cursor.execute('INSERT OR REPLACE INTO "tag" (tag, contents) VALUES (?,?)', (tag, contents))
      self.db.commit()
      msg.reply(random.choice(tag_message))

    def tag_list(self,msg):
      """ Retrieves a list of tags """
      cursor = self.db.cursor()
      cursor.execute('SELECT GROUP_CONCAT(tag) as taglist FROM tag')
      contents = cursor.fetchone()
      if contents:
        msg.reply_handle.msg(msg.author, contents["taglist"])



    def initialize_database(self):
      cursor = self.db.cursor()
      cursor.execute('CREATE TABLE IF NOT EXISTS "tag" ("tag" TEXT PRIMARY KEY NOT NULL, "contents" TEXT NOT NULL);')
      self.db.commit()
