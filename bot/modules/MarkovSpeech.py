import random
import urllib
from datetime import datetime
from bs4 import BeautifulSoup
import sqlite3 as sql

from bot.module_loader import ModuleLoader


from BaseModule import BaseModule

class MarkovSpeech(BaseModule):

    matchers = {"^!speak": "generate_sentence", "!topic": "force_random_topic", "!talk(\s+.*|$)": "sane_speech", "!talktous": "set_auto_speak"}
    events = {"joined": "random_topic", "parted": "random_topic", "nick": "random_topic", "action": "random_topic", "mode": "random_topic"}
    timer = {"60": "auto_speak"}
    db = sql.connect('bot/modules/databases/markovspeechnew')
    db.row_factory = sql.Row

    last_message_time = datetime.now()
    auto_talk = False
    interval = [30*60,90*60]

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

    def sane_speech(self,msg):
        """
        Generate a SANE sentence
        """
        sentence = self.generate_sane_sentence(msg)
        if sentence:
            msg.reply(sentence)
        elif random.randrange(1,2) == 1:
            return self.sane_speech(msg)
        else:
            msg.reply("eh... idk what to say")

    def set_auto_speak(self, msg):
        """
        Enable auto-talk. Arguments: minute-minute (like 60-90) for random interval, or 0 to turn off
        """
        time = msg.clean_contents

        if time == '0':
            self.auto_talk = False
            msg.reply("Okay, I'll shut up :(")
            return
        else:
            t = time.split('-')
            if len(t) < 2 or not isinstance(t, list):
                msg.reply("You gotta give me a time interval! Like 10-50 ... Yes, I'm THIS bad at social interaction.. At least I'm in the right place")
                return
            else:
                self.interval[0] = int(t[0].strip())*60
                self.interval[1] = int(t[1].strip())*60
                self.auto_talk = msg.channel
                self.auto_speak()
                msg.reply("Deal! :)")

    def auto_speak(self, msg=None):
        """
        Automatically talks every 60-180 minutes
        """
        if self.auto_talk:
            what_to_say = self.generate_sane_sentence()
            if what_to_say:
                ModuleLoader().reply_handle.msg(self.auto_talk, self.generate_sane_sentence())
            elif random.randrange(1, 2) == 1:
                return self.auto_speak(msg)

        if self.auto_talk and hasattr(self, 'timer_auto_speak'):
            t = random.randrange(int(self.interval[0]), int(self.interval[1]))
            print("Setting new timer for MarkovSpeech.auto_speak: "+str(t)+" seconds")
            self.timer_auto_speak.interval = t
            self.timer_auto_speak._reschedule()


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
          if (len(" ".join(sentence))>150 and random.randint(1,12)<5):
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

    def get_word(self, wrd, first=0):
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
        cursor.execute('select (ABS(RANDOM()%10000)*occurance) as choice,w1.word as first_word,w2.word as second_word,occurance from sequence join word as w1 on w1.id=first join word as w2 on w2.id=second WHERE first_word=1 ORDER BY choice DESC LIMIT 1;')
        result = cursor.fetchone()
        return [result["first_word"].encode('utf-8'),result["second_word"].encode('utf-8')]
      elif wrd and not first:
        cursor.execute("select (ABS(RANDOM()%10000)*occurance) as choice,w1.word,w2.word as wrd,occurance from sequence join word as w1 on w1.id=first join word as w2 on w2.id=second WHERE w1.word=? ORDER BY choice DESC LIMIT 1;",(wrd,))
      else:
        cursor.execute("select (ABS(RANDOM()%10000)*occurance) as choice,w1.word,w2.word as wrd,occurance from sequence join word as w1 on w1.id=first join word as w2 on w2.id=second WHERE w1.word=? ORDER BY choice DESC LIMIT 1;",(wrd,))

      result = cursor.fetchone()
      if result:
        print(result["wrd"])
        return result["wrd"].encode('utf-8')
      else:
        return None


    def initialize_database(self):
      cursor = self.db.cursor()
      cursor.execute('CREATE TABLE IF NOT EXISTS "sequence" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "first" INTEGER NOT NULL, "second" INTEGER NOT NULL, "occurance" INTEGER DEFAULT(1), "first_word" INTEGER DEFAULT(0));')
      cursor.execute('CREATE TABLE IF NOT EXISTS "word" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "word" TEXT NOT NULL UNIQUE);')
      cursor.execute('CREATE TABLE IF NOT EXISTS "pair" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "first_pair" TEXT NOT NULL, "second_pair" TEXT NOT NULL, "occurance" DEFAULT(1), "occured_first" INTEGER DEFAULT(0), "occured_last" INTEGER DEFAULT(0));')
      self.db.commit()

    def insert_word_pair(self, first,second,first_pair=0):
      cursor = self.db.cursor()


      cursor.execute("SELECT occurance FROM sequence WHERE first=(SELECT id FROM word WHERE word=? LIMIT 1) AND second=(SELECT id FROM word WHERE word=? LIMIT 1) and first_word = ?", (first, second, first_pair))
      if not cursor.fetchone():
        cursor.execute("INSERT INTO sequence (first,second,first_word) VALUES ((SELECT id FROM word WHERE word=? LIMIT 1), (SELECT id FROM word WHERE word=? LIMIT 1),?)",(first,second,first_pair))
      else:
        cursor.execute("UPDATE sequence SET occurance=occurance+1 WHERE first=(SELECT id FROM word WHERE word=? LIMIT 1) AND second=(SELECT id FROM word WHERE word=? LIMIT 1) AND first_word=?", (first,second,first_pair))
      self.db.commit()

      cursor.execute("SELECT id FROM sequence WHERE first=(SELECT id FROM word WHERE word=? LIMIT 1) AND second=(SELECT id FROM word WHERE word=? LIMIT 1) and first_word = ?", (first, second, first_pair))
      result = cursor.fetchone()
      return result["id"]

    def pair_the_pairs(self, first_pair, second_pair, is_first=0, is_last=0):
        cursor = self.db.cursor()
        cursor.execute("SELECT occurance FROM pair WHERE first_pair=? AND second_pair=?",(first_pair, second_pair))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO pair (first_pair, second_pair, occured_first, occured_last, occurance) VALUES (?, ?, ?, ?, ?)", (first_pair, second_pair, is_first, is_last, 1))
        else:
            cursor.execute("UPDATE pair SET occurance=occurance+1, occured_first=occured_first+?, occured_last=occured_last+? WHERE first_pair = ? and second_pair = ?",(is_first, is_last, first_pair, second_pair))
        self.db.commit()

    def generate_sane_sentence(self, msg=""):
        """
        Generate a sane sentence
        """
        contents = msg.clean_contents.split() if msg is not "" else ""
        cursor = self.db.cursor()

        first_word = None
        second_word = None

        if len(contents) > 1:
            first_word = contents[-2]
            second_word = contents[-1]
        elif len(contents):
            first_word = contents[-1]
        else:
            word_pair = self.get_word('', first=1)
            first_word = word_pair[0]
            second_word = word_pair[1]

        print("Generating sentence based on: "+str(first_word))
        if first_word and second_word:
            cursor.execute("SELECT first_pair, second_pair, (occured_first+ABS(RANDOM()%10000)) as choice FROM pair WHERE first_pair=(SELECT id FROM (SELECT id FROM sequence WHERE first=(SELECT id FROM word WHERE word=?) AND second=(SELECT id FROM word WHERE word=?)) LIMIT 1) ORDER BY choice DESC LIMIT 1;", (first_word, second_word))
            print("Starting with both a first and second word")
        else:
            print("Starting with a first word")
            cursor.execute("SELECT first_pair, second_pair,(occured_first+ABS(RANDOM()%10000)) as choice FROM pair WHERE first_pair=(SELECT id FROM (SELECT id,(occurance*ABS(RANDOM()%10000)) as choice FROM sequence WHERE first=(SELECT id FROM word WHERE word=?)) ORDER BY choice DESC LIMIT 1) ORDER BY choice DESC LIMIT 1;", (first_word,))

        sequence_list = []
        pair_id = cursor.fetchone()
        if not pair_id:
            return "I don't know where to start :x"

        if pair_id:
            sequence_list.append(pair_id["first_pair"])
            sequence_list.append(pair_id["second_pair"])

            pair_id = pair_id["second_pair"]
            print("Here we go! Collecting word pairs")
            while len(sequence_list) < 100:
                cursor.execute("SELECT second_pair, (occurance+ABS(RANDOM()%10000)) as choice, occurance, occured_last FROM pair WHERE first_pair = ? ORDER BY choice DESC LIMIT 1", (pair_id,))
                p = cursor.fetchone()
                if p:
                    pair_id = p["second_pair"]
                    sequence_list.append(pair_id)
                    break_chance = (float(p["occured_last"])/float(p["occurance"]))*100

                    # Break if the number is less than break_chance.
                    # If break_chance is low, chances are it wont break
                    if break_chance > random.randrange(1,100):
                        break
                else:
                    break

            # Build query to pick out words
            queries = []
            word_order = 0
            for word_pair in sequence_list:
                word_order += 1
                queries.append("SELECT word, {order} as ordr FROM word WHERE id=(SELECT first FROM sequence WHERE id={id})".format(id=word_pair, order=word_order))
                word_order += 1
                queries.append("SELECT word, {order} as ordr FROM word WHERE id=(SELECT second FROM sequence WHERE id={id})".format(id=word_pair, order=word_order))


            query = " UNION ".join(queries)

            query = "SELECT word, ordr FROM ({q}) ORDER BY ordr ASC".format(q=query)
            cursor.execute(query)

            rows = cursor.fetchall()

            sentence = []

            for row in rows:
                sentence.append(row["word"].encode('utf-8'))

            sentence = " ".join(sentence)
            if " ." in sentence:
                sentence = sentence.replace(" .", ".")

    def raw(self, msg):
        """ Process messages and learn """
        self.last_message_time = datetime.now()
        cursor = self.db.cursor()
        words = [(unicode(single),) for single in msg.contents.split()]
        # Add the words if it doesnt exist
        cursor.executemany("INSERT OR IGNORE INTO word (word) VALUES (?)",words)

        for index, word in enumerate(words):
          if index == 0:
            continue
          if index == 1:
            last_pair_id = self.insert_word_pair(words[index-1][0],words[index][0],1)
          elif index % 2 != 0:

            this_pair_id = self.insert_word_pair(words[index-1][0],words[index][0],0)
            print("Uneven pair index, pairing: "+str(last_pair_id)+" with "+str(this_pair_id))

            if index == 3:
                self.pair_the_pairs(last_pair_id, this_pair_id, 1, 0)
            elif index == len(words)-1:
                self.pair_the_pairs(last_pair_id, this_pair_id, 0, 1)
            else:
                self.pair_the_pairs(last_pair_id, this_pair_id, 0, 0)
            last_pair_id = this_pair_id
          elif index == len(words)-1:
            this_pair_id = self.insert_word_pair(words[index][0],".",0)
            self.pair_the_pairs(last_pair_id, this_pair_id, 0, 1)
          else:
            last_paid_id = self.insert_word_pair(words[index-1][0],words[index][0],0)
