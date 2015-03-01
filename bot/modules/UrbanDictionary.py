import urllib
import re
from pyshorteners.shorteners import Shortener
from bs4 import BeautifulSoup
import pyimgur
from ConfigParser import ConfigParser
from BaseModule import BaseModule

class UrbanDictionary(BaseModule):

    matchers = { "!ud": "lookup", "!search": "search_ed"}

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

    def search_ed(self, msg):
        """
        Searches the encyclopedia of the internet for information
        """
        ed_page = self.get_ed_page(urllib.urlencode({"search": msg.clean_contents}))

        if ed_page:
            print(ed_page)

            if ed_page["title"].capitalize() in ed_page["summary"][0]:
                ed_page["summary"][0] = ed_page["summary"][0].replace(ed_page["title"].capitalize(), "\x02"+ed_page["title"].capitalize()+"\x02")
            elif ed_page["title"] in ed_page["summary"][0]:
                ed_page["summary"][0] = ed_page["summary"][0].replace(ed_page["title"], "\x02"+ed_page["title"]+"\x02")
            else:
                msg.reply("\x02{title}\x02".format(title=ed_page["title"]))

            for paragraph in ed_page["summary"]:
                msg.reply("{summary}".format(summary=paragraph))

            if "pic_url" in ed_page:
                msg.reply("\x02[Pic: {pic} ] [Read more: {url}]\x02".format(url=ed_page["url"], pic=ed_page["pic_url"]))
            else:
                msg.reply("\x02[Read more:\x02 {url}]".format(url=ed_page["url"]))
        else:
            print(ed_page)
            msg.reply("Nothing on the internet about that. I SWAER.")

    def get_ed_page(self, search=""):
        if search == "":
            return False
        page = urllib.urlopen("https://encyclopediadramatica.se/index.php?{search}".format(search=search))



        soup = BeautifulSoup(page.read())
        print("https://encyclopediadramatica.se/index.php?{search}".format(search=search))
        p = re.compile('<title>(.+) \- Encyclopedia Dramatica<\/title>')
        paragraph = soup.find('div', {'id': 'bodyContent'}).findChildren('p')

        if 'There is currently no text' in paragraph[0].text.encode('utf-8').strip():
            print("Nope")
            return False
        else:
            title = ""
            title = p.findall(str(soup.title))
            if isinstance(title, list):
              title = title[0]
            url = ""

            scanning_paragraphs = 1
            paragraphs = []
            for t in paragraph:
                if t.text.strip() != u'':
                    paragraphs.append(t.text.encode('utf-8').strip())

                    scanning_paragraphs += len(t.text.encode('utf-8').strip())

                    if scanning_paragraphs > 300:
                        break

            short_url_handle = Shortener('GoogleShortener')
            summary = paragraphs
            print(page.url)
            try:
                link = short_url_handle.short(page.url).encode('utf-8')
            except:
                link = page.url
                
            all_pics = soup.find('div', {'id': 'bodyContent'}).findChild('div', {'class': 'floatright'}).findAll('a', {'class': 'image'})

            picture = None
            for picture in all_pics:
                if "Main_Page" not in picture['href']:
                    picture = picture["href"]
                    break

            if picture:
                picture = "/".join(page.url.split('/')[:-1])+picture
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


                return {"title": title, "summary": summary, "url": link, "pic_url": pic_link}

            return {"title": title, "summary": summary, "url": link}



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
