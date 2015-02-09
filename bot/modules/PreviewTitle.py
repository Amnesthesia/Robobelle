import urllib
import re

from BaseModule import BaseModule
from markdown import markdown
from bs4 import BeautifulSoup
import praw


class PreviewTitle(BaseModule):

    matchers = {"!sub": "sub_new", "!hot": "sub_hot", "!top\s+.": "sub_top"}
    r = praw.Reddit(user_agent = "Mirabelle")

    def __init__(self, args):
        """
          Initialize the class as a subclass of BaseModule
          and call parent constructor with the defined matchers.
          These will be turned into regex-matchers that redirect to
          the provided function name
        """
        super(self.__class__,self).__init__(self)

    def sub_new(self, msg):
      """
      Retrieves current top 5 new links for a subreddit
      """
      subreddit = self.r.get_subreddit(msg.clean_contents.strip())
      if subreddit:
        for submission in subreddit.get_new(limit=5):
          msg.reply("[{score}] {title} ({url})".format(score=submission.score, title=submission.title, url=submission.short_link).encode("utf-8"))
      return None

    def sub_hot(self, msg):
      """
      Retrieves current top 3 hot links for a subreddit
      """
      subreddit = self.r.get_subreddit(msg.clean_contents.strip())
      if subreddit:
        for submission in subreddit.get_hot(limit=5):
          msg.reply("[{score}] {title} ({url})".format(score=submission.score, title=submission.title, url=submission.short_link))
      return None

    def sub_top(self, msg):
      """
      Retrieves current top 3 links for a subreddit
      """
      subreddit = self.r.get_subreddit(msg.clean_contents.strip())
      if subreddit:
        for submission in subreddit.get_top(limit=5):
          msg.reply("[{score}] {title} ({url})".format(score=submission.score, title=submission.title, url=submission.short_link))
      return None

    def get_reddit_preview(self, url):
      submission = self.r.get_submission(url)
      html = markdown(submission.selftext)
      text = ''.join(BeautifulSoup(html).findAll(text=True))
      amount_lines = 2

      summary = " ".join(text.split('\n'))
      summary = (summary[:amount_lines*348] + '...') if len(summary) > 348 else summary
      return summary.encode('utf-8')


    def raw(self, msg):
        """ If msg contains a URL, fetch the title and return it as a fancy string """
        print("Scanning {}".format(msg.contents))
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', msg.contents)
        if len(urls):
          soup = BeautifulSoup(urllib.urlopen(urls[0]))
          print("Scanned for URLs. Match: {}".format(urls[0]))
          msg.reply("\x02Title: \x02" + soup.title.string.encode('utf-8'))
          if re.match('http[s]?://[w]{0,3}\.?reddit\.com/\w+/.*', urls[0]):
            msg.reply(self.get_reddit_preview(urls[0]))
          return
        return None
        print("Scanned for URLs. No match.")
