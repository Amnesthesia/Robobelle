import re
import sqlite3 as sql
from BaseModule import BaseModule

class Democracy(BaseModule):

    matchers = {"^!poll\s+\d": "results",
                "^!newpoll\s+\w+.*": "create_poll",
                "^!vote\s+\d": "vote",
                "^!polls": "last_polls",
                "^!ballot": "add_option",
                "^!option": "add_option",
                "^!answer": "add_option"}

    db = sql.connect('bot/modules/databases/democracynew')
    db.row_factory = sql.Row
    current_poll = 0

    def __init__(self, args):
        """
          Initialize the class as a subclass of BaseModule
          and call parent constructor with the defined matchers.
          These will be turned into regex-matchers that redirect to
          the provided function name
        """
        super(self.__class__,self).__init__(self)
        self.initialize_database()

    def create_poll(self, msg):
      """Creates a new poll (either !poll title;answer1;answer2, or !poll title followed by !answer First option)"""
      cursor = self.db.cursor()

      if ";" in msg.clean_contents:
        poll_and_options = msg.clean_contents.split(";")
        cursor.execute("INSERT INTO poll(title, user) VALUES (?, ?)", (poll_and_options.pop(0), msg.author))

        # Commit this transaction, or else all options will be linked to the previous poll
        self.db.commit()

        options = []

        # Add options as well
        for option in poll_and_options:
          options.append((int(self.current_poll), int(self.current_poll), option))


        print(options)
        cursor.executemany("INSERT INTO option (poll_id, list_order, description) VALUES (?, coalesce((SELECT list_order FROM option WHERE poll_id = ? ORDER BY list_order DESC LIMIT 1)+1, 1), ?);", options)
      else:
        cursor.execute("INSERT INTO poll(title, user) VALUES (?, ?)", (msg.clean_contents, msg.author))
        # Add options as well

      self.db.commit()

      # Set current poll_id to the newly created poll
      cursor.execute("SELECT id FROM poll ORDER BY id DESC LIMIT 1")
      self.current_poll = cursor.fetchone()[0]

      return None

    def last_polls(self, msg):
      """Returns a list of the most recent polls and their IDs"""
      cursor = self.db.cursor()

      cursor.execute("SELECT DISTINCT id, title FROM results ORDER BY date DESC LIMIT 5")

      results = cursor.fetchall()
      for row in results:
        msg.reply(str(row["id"]) + ": "+row["title"].encode('utf-8'))
      return None

    def vote(self, msg):
      """Vote for option with provided number in current poll"""
      option_number = re.search(r'(\d+)',msg.contents)

      if option_number:
        option_number = option_number.group(1)
        try:
          cursor = self.db.cursor()

          # Vote if no vote is cast
          cursor.execute("SELECT count(*) FROM vote WHERE user=? AND poll_id=?", (msg.author, self.current_poll))
          has_voted = cursor.fetchone()

          if not has_voted:
            cursor.execute("INSERT INTO vote (poll_id, option_id, user) VALUES (?,(SELECT id FROM option WHERE poll_id=? AND list_order=?),?)", (self.current_poll, self.current_poll, option_number, msg.author))
            msg.reply(msg.author+" voted for option #"+option_number)
          else:
            # Revote if vote was already cast
            cursor.execute("UPDATE vote SET option_id = (SELECT id FROM option WHERE list_order=? AND poll_id=?) WHERE poll_id=? AND user=?", (option_number, self.current_poll, self.current_poll, msg.author))
            msg.reply(msg.author+" can't decide and changed their vote to option #"+option_number)
          self.db.commit()
        except Exception, e:
          print(e)
      return None

    def results(self, msg):
      """Shows the current statistics for a specific poll"""
      poll_id = re.search(r'(\d+)',msg.contents)

      if poll_id:
        poll_id = poll_id.group(1)
      else:
        poll_id = self.current_poll

      print("Looking for poll with ID {}".format(poll_id))
      cursor = self.db.cursor()



      results = cursor.execute("SELECT * FROM results WHERE id=? ORDER BY opt_id", (poll_id,))
      results = cursor.fetchall()


      if len(results):

        print(results)
        response = "\x02"+results[0]["title"]+"\x02"

        # Set the current poll_id
        self.current_poll = results[0]["id"]

        # If no options exists, just continue
        if len(results)>1:
          for row in results:
            response += "\n\x02 [" + str(row["nVotes"]-1) + "]\x02\t" + str(row["list_order"]) + ". " + row["description"]
        elif len(results) is 1:
          order = str(results[0]["list_order"]) if str(results[0]["list_order"]) else "0"
          desc = results[0]["description"] if results[0]["description"]  else "No description"
          nvotes = str(results[0]["nVotes"]-1)  if str(results[0]["nVotes"]-1) else "0"

          response += "\n\x02 [" + nvotes + "]\x02\t" + order+ ". " + desc
      else:
        response = "Poll not found :("

      msg.reply(response.encode('utf-8'))
      return response

    def add_option(self, msg):
      """Adds an option to the current poll"""

      try:
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO option (poll_id, list_order, description) VALUES (?, coalesce((SELECT list_order FROM option WHERE poll_id = ? ORDER BY list_order DESC LIMIT 1)+1, 1), ?);", (self.current_poll, self.current_poll, msg.clean_contents))
        self.db.commit()
      except Exception, e:
        print(e)
      return None


    # Database set up
    def initialize_database(self):
      cursor = self.db.cursor()

      try:
        # Create a table for polls
        cursor.execute('CREATE TABLE IF NOT EXISTS "poll" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "title" TEXT NOT NULL, "user" TEXT NOT NULL, "timestamp" INTEGER NOT NULL DEFAULT (CURRENT_TIMESTAMP));')

        # Create a table for options linked to each poll
        cursor.execute('CREATE TABLE IF NOT EXISTS "option" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "poll_id" INTEGER NOT NULL, "list_order" INTEGER NOT NULL DEFAULT 0, "description" TEXT NOT NULL, FOREIGN KEY (poll_id) REFERENCES poll(id));')

        # Create a table for votes on each option
        cursor.execute('CREATE TABLE IF NOT EXISTS "vote" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "poll_id" INTEGER NOT NULL, "option_id" INTEGER NOT NULL, "user" TEXT NOT NULL, FOREIGN KEY (poll_id) REFERENCES poll(id), FOREIGN KEY (option_id) REFERENCES option(id))')

        # Create a view to retrieve all polls, with options, and votes (counted)
        cursor.execute('CREATE VIEW IF NOT EXISTS "results" AS SELECT COUNT(*) as nVotes, p.id, p.title, p.user as author, p.timestamp as date, o.id as opt_id, o.list_order, o.description,  v.user, v.option_id FROM poll as p LEFT JOIN option as o ON (o.poll_id=p.id) LEFT JOIN vote as v ON (v.option_id = o.id) GROUP BY p.id, opt_id;')

        self.db.commit()
        cursor.execute('SELECT id FROM poll ORDER BY id DESC LIMIT 1')
        self.current_poll = cursor.fetchone()[0]
      except Exception, e:
        print str(e)
