from imdbpie import Imdb
from pyshorteners.shorteners import Shortener
from BaseModule import BaseModule

class ImdbLookup(BaseModule):

    matchers = {"!imdb": "find_movie", "!i\s+": "find_movie"}
    short_url_handle = Shortener('GoogleShortener')
    imdb_handle = Imdb({'anonymize': True})

    def __init__(self, args):
        """
          Initialize the class as a subclass of BaseModule
          and call parent constructor with the defined matchers.
          These will be turned into regex-matchers that redirect to
          the provided function name
        """
        super(self.__class__,self).__init__(self)

    def find_movie(self,msg):
        """
        Search for a movie title and get a summary
        """
        movie = self.get_movie(msg.clean_contents)
        if movie:
          title = movie.title.encode('utf-8')
          plot = movie.plot["outline"].encode('utf-8')
          rating = movie.rating
          trailer = movie.trailers[movie.trailers.keys()[0]]
          trailer = self.short_url_handle.short(trailer).encode('utf-8') if len(trailer)>75 else trailer
          msg.reply("\x02{title}\x02 ({rating}/10): {plot}".format(title=title, plot=plot, rating=rating))
          msg.reply("\x02Read more: \x02http://www.imdb.com/title/{movie_id}/ or \x02Watch the trailer:\x02 {trailer}".format(movie_id=movie.imdb_id, trailer=trailer))
        else:
          msg.reply("I couldn't find that movie :(")
        return msg


    def get_movie(self, title):
      results = self.imdb_handle.find_by_title(title)
      return False if not results else self.imdb_handle.find_movie_by_id(results.pop(0)["imdb_id"])
