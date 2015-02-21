import random
import urllib
from datetime import datetime
from bs4 import BeautifulSoup
import sqlite3 as sql


from BaseModule import BaseModule

class MarkovSpeech(BaseModule):

    matchers = {"^!speak": "generate_sentence", "!topic": "force_random_topic"}
    events = {"joined": "random_topic", "parted": "random_topic", "nick": "random_topic", "action": "random_topic", "mode": "random_topic"}
    db = sql.connect('bot/modules/databases/markovspeechnew')
    db.row_factory = sql.Row

    last_message_time = datetime.now()

    def __init__(self, args):
        """
          Initialize the class as a subclass of BaseModule
          and call parent constructor with the defined matchers.
          These will be turned into regex-matchers that redirect to
          the provided function name
        """
        super(self.__class__,self).__init__(self)
        self.initialize_database()


    def random_topic(self, msg):
      """
      I'll come up with a random topic to get the conversation going
      """
      prefixes = ["I've been wondering ...",
                  "So I was thinking, ",
                  "Don't ask me why I came to think of it but ...",
                  "So ...", "Uhm, guys? ",
                  "HEY, GUYS! I GOT A QUESTION FOR YOU, KINDA ...",
                  "Yeah, right, so ... ",
                  "Such lively mood in here... anyways, ",
                  "ok so, ",
                  "ok so I've been doing some thinking and ..."
                  ]
      if (datetime.now() - self.last_message_time).seconds > (7*60):
        self.last_message_time = datetime.now()
        msg.reply(random.choice(prefixes)+BeautifulSoup(urllib.urlopen("http://conversationstarters.com/generator.php")).find("div", { 'id': 'random'}).text.encode('utf-8'))

    def force_random_topic(self, msg):
      """
      I'll come up with a random topic to get the conversation going
      """
      msg.reply(BeautifulSoup(urllib.urlopen("http://conversationstarters.com/generator.php")).find("div", { 'id': 'random'}).text.encode('utf-8'))

    def generate_sentence(self,msg):
        """
        Generates a sentence by fetching a word based on the provided word,
        or picking one at random if none is provided
        """
        i = 0
        sentence = msg.clean_contents.strip().split()
        print(sentence)
        while len(sentence)<100:

          # This is not pythonic but I had a brainfreeze about boolean operations
          if (len(sentence.join(" "))>150 and random.randint(1,12)<5):
            break

          if i == 0 and not len(sentence):
            word = self.get_word(None,1)
          elif(i == 0) and len(sentence) > 0:
            word = self.get_word(sentence[-1],1)
          elif(i > 0):
            word = self.get_word(sentence[-1])

          if not word or (type(word) is str and word.strip().endswith(('.', '!', '?'))) or (type(word) is list and word[-1].strip().endswith(('.','!','?'))):
            break
          elif type(word) is list:
            sentence.extend(word)
          else:
            sentence.append(word)
          i += 1
        msg.reply(" ".join(sentence))
        return sentence

    def get_word(self,wrd, first=0):
      """
      Retrieve a word from the database. If parameter wrd is not supplied,
      and parameter first is False or 0, this function returns None.
      If wrd is supplied but first is 1 or True, wrd is discarded and a new
      word will be picked from the database based on its weight.
      """
      if not wrd and not first:
        return None

      cursor = self.db.cursor()
      if first or not wrd:
        cursor.execute('select RANDOM()*occurance as choice,w1.word as first_word,w2.word as second_word,occurance from sequence join word as w1 on w1.id=first join word as w2 on w2.id=second WHERE first_word=1 ORDER BY choice DESC LIMIT 1;')
        result = cursor.fetchone()
        return [result["first_word"].encode('utf-8'),result["second_word"].encode('utf-8')]
      elif wrd and not first:
        cursor.execute("select RANDOM()*occurance as choice,w1.word,w2.word as wrd,occurance from sequence join word as w1 on w1.id=first join word as w2 on w2.id=second WHERE w1.word=? ORDER BY choice DESC LIMIT 1;",(wrd,))
      else:
        cursor.execute("select RANDOM()*occurance as choice,w1.word,w2.word as wrd,occurance from sequence join word as w1 on w1.id=first join word as w2 on w2.id=second WHERE w1.word=? ORDER BY choice DESC LIMIT 1;",(wrd,))

      result = cursor.fetchone()
      if result:
        print(result["wrd"])
        return result["wrd"].encode('utf-8')
      else:
        return None


    def initialize_database(self):
      cursor = self.db.cursor()
      cursor.execute('CREATE TABLE IF NOT EXISTS "sequence" ("first" INTEGER NOT NULL, "second" INTEGER NOT NULL, "occurance" INTEGER DEFAULT(1));')
      cursor.execute('CREATE TABLE IF NOT EXISTS "word" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "word" TEXT NOT NULL UNIQUE);')

      self.db.commit()

    def insert_word_pair(self, first,second,first_pair=False):
      cursor = self.db.cursor()


      cursor.execute("SELECT occurance FROM sequence WHERE first=(SELECT id FROM word WHERE word=? LIMIT 1) AND second=(SELECT id FROM word WHERE word=? LIMIT 1) and first_word = ?", (first, second, first_pair))
      if not cursor.fetchone():
        cursor.execute("INSERT INTO sequence (first,second,first_word) VALUES ((SELECT id FROM word WHERE word=? LIMIT 1), (SELECT id FROM word WHERE word=? LIMIT 1),?)",(first,second,first_pair))
      else:
        cursor.execute("UPDATE sequence SET occurance=occurance+1 WHERE first=(SELECT id FROM word WHERE word=? LIMIT 1) AND second=(SELECT id FROM word WHERE word=? LIMIT 1) AND first_word=?", (first,second,first_pair))
      self.db.commit()

    def raw(self, msg):
        """ Process messages and learn """
        self.last_message_time = datetime.now()
        cursor = self.db.cursor()
        words = [(single,) for single in msg.contents.split()]
        # Add the words if it doesnt exist
        cursor.executemany("INSERT OR IGNORE INTO word (word) VALUES (?)",words)

        for index,word in enumerate(words):
          if index == 0:
            continue
          if index == 1:
            self.insert_word_pair(words[index-1][0],words[index][0],1)
          else:
            self.insert_word_pair(words[index-1][0],words[index][0],0)
