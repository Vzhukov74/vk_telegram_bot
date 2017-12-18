import requests
from BeautifulSoup import BeautifulSoup
import urllib
import sqlite3
import telegram
import time
import sys

telegramBotUrl = "https://api.telegram.org/bot509579116:AAGcXZp79nxlWvmTj8pqyXnrsbowzFwnq-c/"

class DataObj(object):
    def __init__(self, url, id, hashtag):
        self.url = url
        self.id = id
        self.hashtag = hashtag

class ImgObj(object):
    def __init__(self, url, name, id, hashtag):
        self.url = url
        self.name = name
        self.id = id
        self.hashtag = hashtag

class ImageDBObj(object):
    def __init__(self, name, hashtag):
        self.name = name
        self.hashtag = hashtag

def getHtml(url):
  response = requests.get(url)
  return response.text

def fetchHashtag(item):
    hashtag = ''

    body = item.find('div', {'class': 'wi_body'})
    if body != None:
        hashtagDiv = body.find('div', {'class': 'pi_text'})
        if hashtagDiv != None:
            hashtagHtamlData = hashtagDiv.find('a')
            if hashtagHtamlData != None:
                hashtag = ''#hashtagHtamlData.string

    return hashtag

def parsePosts(html):
    soup = BeautifulSoup(''.join(html))
    items = soup.findAll('div', {'class': 'wall_item'})

    dataObjs = []
    for item in items:


        footer = item.find('div', {'class': 'doc_preview_rows doc_preview_rows_1'})
        if footer != None:
            hashtag = fetchHashtag(item)

            aTegWithLink = footer.find('a', {'class': 'medias_thumb doc_preview'})
            halfUrl = aTegWithLink['href']
            url = 'https://vk.com' + halfUrl

            idForPostData = item.find('a', {'class': 'post__anchor anchor'})
            print '######'

            if idForPostData != None:
                 idForPost = idForPostData['name']
                 print idForPost
                 print url
                 dataObj = DataObj(url, idForPost, hashtag)
                 dataObjs.append(dataObj)
        #print '========='
    return dataObjs

def parseImages(dataObjs):
    for dataObj in dataObjs:
        response = requests.get(dataObj.url)
        soup = BeautifulSoup(''.join(response.text))
        image = soup.find('img')
        link = image['src']
        dataObj.url = link
        print link
        print '===='
    return dataObjs

def downloadImages(dataObjs):
    index = 0
    imageObjs = []
    names = []
    for dataObj in dataObjs:
        name = str(index) + '.jpg'
        urllib.urlretrieve(dataObj.url, name)
        index += 1
        names.append(name)
        imageObj = ImgObj(dataObj.url, name, dataObj.id, dataObj.hashtag)
        imageObjs.append(imageObj)
    return imageObjs

def readImage(filename):
    try:
        fin = open(filename, "rb")
        img = fin.read()
        return img

    except IOError, e:
        print "Error %d: %s" % (e.args[0],e.args[1])
        sys.exit(1)

    finally:
        if fin:
            fin.close()

def saveInDB(imageObjs):
    try:
        conn = sqlite3.connect("wallpaper.db")
        cursor = conn.cursor()

        cursor.execute("""create table if not exists Images
                      (Id INTEGER PRIMARY KEY AUTOINCREMENT, Data BLOB, url text, urlId text, published text, hashtag text)
                      """)

        for imageObj in imageObjs:
            cursor.execute("SELECT * FROM Images WHERE urlId=?", (imageObj.id,))
            result = cursor.fetchall()
            print len(result)
            if len(result) == 0:
                data = readImage(imageObj.name)
                binary = sqlite3.Binary(data)
                print "######"
                print(imageObj.url)
                print(imageObj.name)
                cursor.execute("INSERT INTO Images VALUES (?, ?, ?, ?, ?, ?)", (None, binary, imageObj.url, imageObj.id, "0", imageObj.hashtag))
                conn.commit()
            else:
                print 'this image is alredy download'

    except sqlite3.Error, e:
        if conn:
            conn.rollback()
        print "Error %s:" % e.args[0]
            #sys.exit(1)

    finally:
        if conn:
            conn.close()

def writeImage(data, name):
    try:
        fout = open(name,'wb')
        fout.write(data)

    except IOError, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        #sys.exit(1)

    finally:
        if fout:
            fout.close()

def fethImagesFromDB():
    try:
        conn = sqlite3.connect('wallpaper.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Images Where published = 0")
        datas = cursor.fetchall()
        names = []
        for data in datas:
            #print data
            imgId = data[0]
            name = str(imgId) + '.jpg'
            writeImage(data[1], name)
            hashtag = data[5]

            print hashtag
            imgData = ImageDBObj(name, hashtag)

            names.append(imgData)

            url = data[2]
            sql = """UPDATE Images
            SET published = '1'
            WHERE url = '%s'
            """ % (url)

            cursor.execute(sql)
            conn.commit()

        return names

    except sqlite3.Error, e:
        print "Error %s:" % e.args[0]
        #sys.exit(1)
        return []

    finally:
        if conn:
            conn.close()

def main():
   bot = telegram.Bot('509579116:AAGcXZp79nxlWvmTj8pqyXnrsbowzFwnq-c')

   while True:
       html = getHtml('https://vk.com/lux_oboi')
       dataObjs = parsePosts(html)
       dataObjs = parseImages(dataObjs)
       imageObjs = downloadImages(dataObjs)
       saveInDB(imageObjs)
       names = fethImagesFromDB()
       for name in names:
           caption = name.hashtag + ' @wallpapersForMobile'
           bot.send_photo(chat_id="@wallpapersForMobile", photo=open(name.name, 'rb'), caption = caption)
       time.sleep(60 * 5)

if __name__ == '__main__':
  main()
