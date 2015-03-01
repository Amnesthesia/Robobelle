import urllib
import re
from pyshorteners.shorteners import Shortener
from bs4 import BeautifulSoup
import random
import pyimgur
from ConfigParser import ConfigParser
from BaseModule import BaseModule

class UrbanDictionary(BaseModule):

    matchers = { "!ud": "lookup", "!search": "search_ed", "!ed": "search_ed", "!un": "search_uncyclopedia", "!quote": "get_quote", "!smart": "get_quote", "!wise": "get_quote", "!verysmart": "get_quote"}
    timer = {"15000": "get_quote"}

    RANDOM_TIMER = 15000

    def __init__(self, args):
        """
          Initialize the class as a subclass of BaseModule
          and call parent constructor with the defined matchers.
          These will be turned into regex-matchers that redirect to
          the provided function name
        """
        super(self.__class__,self).__init__(self)
        config = ConfigParser()
        config.read(["settings.ini"])
        self.imgur_handle = pyimgur.Imgur(config.get('belle', 'imgur_app_id'))
        self.QUOTE_CHANNEL = config.get('belle', 'quotes')


    def get_quote(self, msg=None):
        """
        Gets a quote from a cool dude of history times
        """
        import urllib2
        # Reschedule next quote fetch
        if self.RANDOM_TIMER and hasattr(self, 'timer_get_quote'):

            time = [key for key, value in self.timer.items() if value == 'get_quote']
            if time:
                t = int(time.pop())
                t += random.randrange(1, self.RANDOM_TIMER)
                print("Setting new timer for Quote: "+str(t)+" seconds")
                self.timer_get_quote.interval = t
                self.timer_get_quote._reschedule()

        quote = urllib2.Request("http://www.quotedb.com/quote/quote.php?action=random_quote&c[69]=69&c[44]=44&c[40]=40&c[121]=121&c[80]=80&c[48]=48&c[13]=13&c[6]=6&c[45]=45&c[91]=91&c[115]=115&c[74]=74&c[101]=101&c[43]=43&c[5]=5&c[11]=11&c[62]=62&c[20]=20&c[109]=109&c[84]=84&c[71]=71&c[15]=15&c[73]=73&c[51]=51&c[33]=33&c[64]=64&c[32]=32", headers={'User-Agent': 'Magic Browser'})
        quote = urllib2.urlopen(quote)
        soup = BeautifulSoup(quote)
        print(soup)

        quote = soup.find('p').text.encode('utf-8').strip()
        quote = quote.replace('\n','')
        quote = quote.replace("document.write('", "")
        quote = quote.replace("More quotes from", "")
        quote = quote.replace("');", ";")

        if len(quote) > 1:
            quote = filter(None, quote.split(';'))

            author = quote.pop().strip()
            quote = " - ".join(quote).strip()

            assembled = "{quote} ~ \x02{author}\x02".format(quote=quote, author=author)
            if not msg:
                ModuleLoader().reply_handle(self.QUOTE_CHANNEL, assembled)
            else:
                msg.reply(assembled)
            return assembled

    def search_uncyclopedia(self, msg):
        """
        Searches uncyclopedia
        """
        ed_page = self.get_ed_page(urllib.urlencode({"search": msg.clean_contents}), where="uncyclopedia")
        if not ed_page:
            ed_page = self.get_ed_page(urllib.urlencode({"search": msg.clean_contents}))
        if ed_page:
            print(ed_page)
            message = ""
            if ed_page["title"].capitalize() in ed_page["summary"][0]:
                ed_page["summary"][0] = ed_page["summary"][0].replace(ed_page["title"].capitalize(), "\x02"+ed_page["title"].capitalize()+"\x02")
            elif ed_page["title"] in ed_page["summary"][0]:
                ed_page["summary"][0] = ed_page["summary"][0].replace(ed_page["title"], "\x02"+ed_page["title"]+"\x02")
            else:
                msg.reply("\x02{title}\x02".format(title=ed_page["title"]))

            for paragraph in ed_page["summary"]:
                msg.reply("{summary}".format(summary=paragraph))

            if "pic_url" in ed_page:
                message += "\x02[Pic: {pic} ]".format(pic=ed_page["pic_url"])

            if "gallery" in ed_page:
                message += "\x02[Gallery: {gallery}]\x02".format(gallery=ed_page["gallery"])

            message += " \x02[Read more: {url}]\x02".format(url=ed_page["url"])
            msg.reply(message)
        else:
            print(ed_page)
            msg.reply("Nothing on the internet about that. I SWAER.")

    def search_ed(self, msg):
        """
        Searches the encyclopedia of the internet for information
        """
        ed_page = self.get_ed_page(urllib.urlencode({"search": msg.clean_contents}))
        if not ed_page:
            ed_page = self.get_ed_page(urllib.urlencode({"search": msg.clean_contents}), where="uncyclopedia")
        if ed_page:
            print(ed_page)
            message = ""
            if ed_page["title"].capitalize() in ed_page["summary"][0]:
                ed_page["summary"][0] = ed_page["summary"][0].replace(ed_page["title"].capitalize(), "\x02"+ed_page["title"].capitalize()+"\x02")
            elif ed_page["title"] in ed_page["summary"][0]:
                ed_page["summary"][0] = ed_page["summary"][0].replace(ed_page["title"], "\x02"+ed_page["title"]+"\x02")
            else:
                msg.reply("\x02{title}\x02".format(title=ed_page["title"]))

            for paragraph in ed_page["summary"]:
                msg.reply("{summary}".format(summary=paragraph))

            if "pic_url" in ed_page:
                message += "\x02[Pic: {pic} ]".format(pic=ed_page["pic_url"])

            if "gallery" in ed_page:
                message += "\x02[Gallery: {gallery}]\x02".format(gallery=ed_page["gallery"])

            message += " \x02[Read more: {url}]\x02".format(url=ed_page["url"])
            msg.reply(message)
        else:
            print(ed_page)
            msg.reply("Nothing on the internet about that. I SWAER.")

    def get_ed_page(self, search="", where="ed"):
        if search == "":
            return False
        if where == "ed":
            search_url = "https://encyclopediadramatica.se/index.php?{search}".format(search=search)
        else:
            search_url = "http://uncyclopedia.wikia.com/index.php?title=Special%3ASearch&{search}&go=Go".format(search=search)
        page = urllib.urlopen(search_url)



        soup = BeautifulSoup(page.read())
        print("https://encyclopediadramatica.se/index.php?{search}".format(search=search))
        p = re.compile('<title>(.+) \- (Encyclopedia Dramatica|Uncyclopedia, the content\-free encyclopedia)<\/title>')

        paragraph = soup.find('div', {'id': 'bodyContent'}).findChildren('p')
        print(paragraph)

        if 'There is currently no text' in paragraph[0].text.encode('utf-8').strip() \
        or "Create the page" in paragraph[0].text.encode('utf-8').strip()  \
        or not soup:
            print("Nope")
            return False
        else:
            title = ""
            title = p.findall(str(soup.title))
            if isinstance(title, list) and len(title):
                title = title[0]
                if isinstance(title, tuple):
                    title = title[0]


            url = ""

            scanning_paragraphs = 1
            words = 0
            paragraphs = []
            for t in paragraph:
                print(t)
                if scanning_paragraphs > 380 or words > 55:
                    if words > 80:
                        paragraphs[-1] += "..."
                    break
                if t.text.strip() != u'':
                    paragraphs.append(t.text.encode('utf-8').strip())
                    words += len(t.text.encode('utf-8').strip().split())
                    scanning_paragraphs += len(t.text.encode('utf-8').strip())

            short_url_handle = Shortener('GoogleShortener')
            summary = paragraphs

            print(page.url)
            try:
                link = short_url_handle.short(page.url).encode('utf-8')
            except:
                link = page.url


            if where == "ed":
                base_url = "/".join(page.url.split('/')[:-1])
            else:
                base_url = "/".join(page.url.split('/')[:-2])
            return_dict = {"title": title, "summary": summary, "url": link}

            all_pics = soup.find('div', {'id': 'bodyContent'}).findChild('div', {'class': 'floatright'})

            if all_pics:
                all_pics = all_pics.findAll('a', {'class': 'image'})
                picture = None
                for picture in all_pics:
                    if "Main_Page" not in picture['href']:
                        picture = picture["href"]
                        break

                if picture:
                    picture = base_url+picture
                    picture_page = urllib.urlopen(picture)
                    print(picture)


                    picture_soup = BeautifulSoup(picture_page.read())

                    large_pic = picture_soup.find('div', {'id': 'file'}).findChild('a')['href']
                    print(large_pic)

                    if not large_pic:
                        pic_link = short_url_handle.short(picture).encode('utf-8')
                    else:
                        image = self.imgur_handle.upload_image(url=large_pic, title="from {url}".format(url=link))
                        pic_link = image.link if image and image.link else short_url_handle.short(picture).encode('utf-8')


                    return_dict["pic_url"] = pic_link

            gallery = soup.find('table', {'class': 'gallery'})

            if gallery:
                gallery = gallery.findAll('a', {'class': 'image'})



            return return_dict



    def lookup(self,msg):
        """ Looks up a term on UrbanDictionary """
        page = urllib.urlopen("http://www.urbandictionary.com/define.php?term=%s" % msg.clean_contents)

        try:
          soup = BeautifulSoup(page.read())
          title = "\x02" + soup.find('div', {'id': 'content'}).findChild('div', {'class': 'def-header'}).findChild('a', {'class': 'word'}).text.encode('utf-8').strip() + "\x02"
          meaning = soup.find('div', {'id': 'content'}).findChild('div', {'class': 'meaning'}).text.encode('utf-8').strip()
          example = "\x03" + soup.find('div', {'id': 'content'}).findChild('div', {'class': 'example'}).text.encode('utf-8').strip('\t\n\r') + "\x03"

          response = title + ": " + meaning + "\n\x02Example:\x02 " + example
          msg.reply(response)
        except Exception, e:
          raise Exception(e)

        return msg
