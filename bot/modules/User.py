from __future__ import division
from datetime import datetime

import sqlite3 as sql
import re

from BaseModule import BaseModule



class User(BaseModule):

    matchers = {"!seen": "last_seen", "!greet": "force_greet_user", "!addgreeting": "add_greeting", "!dropgreeting": "remove_greeting", "!stats": "get_statistics"}
    events = { "joined": "update_last_seen_and_greet", "parted": "update_last_seen_and_greet" }
    db = sql.connect('bot/modules/databases/user')
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


    def force_greet_user(self, msg):
      """ Force me to say hi to someone """
      greeting = self.get_greeting(msg.clean_contents, msg.channel)
      if not greeting:
        greeting = self.get_greeting('new', msg.channel)
        message = re.sub("new", msg.clean_contents, greeting)
        msg.reply(message)
      else:
        msg.reply(greeting)

    def greet_user(self, event):
      greeting = self.get_greeting(event.author, event.channel)
      if self.first_seen(event.author):
        greeting = self.get_greeting('new', event.channel)
        greeting = re.sub("new", event.author, greeting)
        event.reply(greeting)
      elif greeting:
        event.reply(greeting)

    def get_greeting(self, user, channel):
      """ Retrieves greeting for a user """
      cursor = self.db.cursor()
      cursor.execute('SELECT id, message FROM greeting WHERE user = ? AND channel = ? ORDER BY RANDOM() LIMIT 1',(user,channel))
      user_greeting = cursor.fetchone()
      if user_greeting:
        message = "\x02[" + str(user_greeting["id"]) + "]\x02 " + user_greeting["message"].encode('utf-8').strip("'")
        message = re.sub("USER", user, message)
        message = re.sub("''", "'", message)

        return message
      else:
        return None

    def add_greeting(self, msg):
      """ Add a new greeting. I'll replace USER with username in the message. Arguments are: user message """
      split_message = msg.clean_contents.split()
      user = split_message.pop(0)
      greeting = " ".join(split_message)

      cursor = self.db.cursor()
      cursor.execute('INSERT INTO "greeting" (user, message, channel) VALUES (?,?,?)', (user, unicode(greeting.decode('utf-8')), msg.channel))
      self.db.commit()
      cursor.execute('SELECT id FROM "greeting" WHERE user=? ORDER BY id DESC LIMIT 1',(user,))
      last_id = cursor.fetchone()
      last_id = last_id["id"]

      if user == "new":
        user = "a new face around here"

      if last_id:
        msg.reply("Hey, {sender}, I'll remember this the next time I see {user} (#{id})".format(sender=msg.author,user=user, id=last_id))
      else:
        msg.reply("Oops, crap, I already forgot what you said ...")


    def remove_greeting(self, msg):
      """ Removes a greeting identified by its ID. IDs are shown when greetings are added or posted """
      greeting_id = re.search(r'(\d+)',msg.contents)

      if greeting_id:
        greeting_id = greeting_id.group(1)
      else:
        msg.reply("I'm so sorry, but I don't think I even remember that one! :(")
        return

      cursor = self.db.cursor()
      cursor.execute("DELETE FROM greeting WHERE id=?",(greeting_id,))
      if self.db.commit():
        msg.reply("Okay, okay, fine! I get it ... I won't say that again, alright?")

    def first_seen(self, user):
      """
      Checks if the user has ever been seen before the last 10 sec
      """
      cursor = self.db.cursor()
      cursor.execute("SELECT first_seen FROM user WHERE user = ?",(user.lower(),))
      results = cursor.fetchone()
      if results:
        if results["first_seen"]:
          diff = datetime.now() - datetime.strptime(results["first_seen"], "%Y-%m-%d %H:%M:%S")
          if diff.seconds < 10 and diff.days < 1:
            return True
      return False

    ##
    ## Last seen and user timestamps
    ##
    def last_seen(self,message):
      """
      Checks when a user was last seen
      """
      cursor = self.db.cursor()

      cursor.execute("SELECT * FROM user WHERE user = ?",(message.clean_contents.lower(),))
      cursor.execute("SELECT * FROM user WHERE user = ?",(message.clean_contents.lower(),))
      results = cursor.fetchone()
      if results:
        message.reply("{user} was last seen {time}".format(user=results["user"],time=self.how_long_ago(results["timestamp"])).capitalize())
      else:
        print(results)
      return message


    def update_last_seen_and_greet(self,event):
      """
      Updates last seen time for a user when (s)he joined or parted
      """
      cursor = self.db.cursor()
      cursor.execute("INSERT OR REPLACE INTO user (user, first_seen, timestamp) VALUES(?, coalesce((SELECT first_seen FROM user WHERE user = ? AND first_seen IS NOT NULL),CURRENT_TIMESTAMP), CURRENT_TIMESTAMP)", (event.author.lower(),event.author.lower()))
      self.db.commit()
      if event.event == "joined":
        self.greet_user(event)
      else:
        print(event.contents)
      return None

    def get_statistics(self, msg):
      """ Who talks the most in here? And how efficiently? See the top 5 (or give a number like !stats 10 for top whatever!) """
      cursor = self.db.cursor()

      limit = re.search(r'(\d+)',msg.contents)

      if limit:
        limit = limit.group(1)
        results = cursor.execute("SELECT user, lines, words FROM statistics WHERE channel = ? ORDER BY words DESC LIMIT ?", (msg.channel,limit))
      else:
        results = cursor.execute("SELECT user, lines, words FROM statistics WHERE channel = ? ORDER BY words DESC LIMIT 5", (msg.channel,))
      results = cursor.fetchall()

      response = "\x02Statistics for {channel}\x02".format(channel=msg.channel)
      count = 0
      for row in results:
        count += 1
        wpl = row["words"] / row["lines"]
        response += "\n\x02{rank}.\x02 {user} with {words} words over {lines} lines (average {wpl} words/line)".format(rank=count,user=row["user"], words=row["words"], lines=row["lines"], wpl="{0:.2f}".format(wpl))
      msg.reply(response)


    def update_statistics(self, msg):
      cursor = self.db.cursor()
      words = msg.contents.split()

      cursor.execute("SELECT count(*) FROM statistics WHERE user = ? and channel = ?",(msg.author,msg.channel))

      results = cursor.fetchone()[0]
      if results == 0  :
        print("No results found, adding {u} of {c} to statistics".format(u=msg.author,c=msg.channel))
        cursor.execute("INSERT INTO statistics (user, lines, words, channel) VALUES (?,?,?,?)", (msg.author, 1, len(words), msg.channel))
      else:
        print("Results found, attempting update of {u} from {c} to statistics".format(u=msg.author,c=msg.channel))
        cursor.execute("UPDATE statistics SET lines=lines+1, words=words+? WHERE user = ? and channel = ?", (len(words), msg.author, msg.channel))
      self.db.commit()

    def raw(self, msg):
      self.update_statistics(msg)

    def how_long_ago(self, date):
      """
      Turn a past date into how long ago it was, i.e 2 hours ago, 1 hour ago, yesterday.
      Provide either a timestamp or a past date
      """

      now = datetime.now()

      if type(date) is int:
        difference = now - datetime.fromtimestamp(date)
      elif isinstance(date,datetime):
        difference = now - date
      elif not date:
        difference = 0
      else:
        difference = now - datetime.strptime(date, "%Y-%m-%d %H:%M:%S")


      if difference.days < 0:
        return '... I dont even know who I am anymore'

      if difference.days == 0:
        if difference.seconds < 10:
          return "just now"
        elif difference.seconds < 60:
          return str(difference.seconds) + " seconds ago"
        elif difference.seconds < 120:
          return "a minute ago"
        elif difference.seconds < 3600:
          return "{0:.2f}".format(difference.seconds/60) + " minutes ago"
        elif difference.seconds < 7200:
          return "an hour or so ago"
        elif difference.seconds < 86400:
          return str(difference.seconds/3600) + " hours ago"
      if difference.days == 1:
        return "yesterday"
      if difference.days < 7:
        return str(difference.days) + " days ago"
      if difference.days < 31:
        return str(difference.days/7) + " weeks, " + str(difference.days % 7) + " days ago"
      if difference.days < 365:
        return str(difference.days/30) + " months, " + str(difference.days % 30) + " days ago"
      return str(difference.days/365) + " years ago"

    def initialize_database(self):
      cursor = self.db.cursor()
      cursor.execute('CREATE TABLE IF NOT EXISTS "user" ("user" TEXT PRIMARY KEY NOT NULL, "first_seen" INTEGER NOT NULL DEFAULT (date("now", "localtime")), "timestamp" INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP);')
      cursor.execute('CREATE TABLE IF NOT EXISTS "greeting" ("id" INTEGER PRIMARY KEY AUTOINCREMENT, "user" TEXT NOT NULL, "message" TEXT NOT NULL, "channel" TEXT NOT NULL);')
      cursor.execute('CREATE TABLE IF NOT EXISTS "statistics" ("id" INTEGER PRIMARY KEY, "user" VARCHAR(15), "lines" INTEGER DEFAULT 1, "words" INTEGER DEFAULT 0, "channel" TEXT NOT NULL)')
      self.db.commit()
