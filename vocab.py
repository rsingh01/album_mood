#from bs4 import BeautifulSoup, SoupStrainer
import bs4
import requests
import string
import httplib2
import nltk
import pprint
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import sql
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

nltk.download('punkt')

class Artist: 
    def __init__(self, artist_name: str, albums: list):
        self.artist_name = artist_name
        self.albums = albums

    def print_attrs(self):
        print(self.artist_name)
        for album in self.albums:
            print(album)

class Album:
    def __init__(self, album_title: str, song_list: list):
        self.album_title = album_title
        self.song_list = song_list

class Song: 
    def __init__(self, song_title: str, lyrics: list):
        self.song_title = song_title
        self.lyrics = lyrics

def init_db():
    con = None
    #see if you can connect to the db directly, otherwise initialize it from scratch
    #cur is cursor -- used to execute SQL commands
    try:
        con = psycopg2.connect(dbname='music_db')
        print('connected to music db successfully')
        return con
    
    except psycopg2.DatabaseError as e:
        print('Error connecting to db: {}'.format(e))
        print('Creating db now...')
        con = psycopg2.connect(dbname='postgres')
        cur = con.cursor()
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) #because stackoverflow told me to
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier('music_db')))
        con.close()
        con = psycopg2.connect(dbname = 'music_db')
        return con


#have to get rid of hard coded credentials somehow
def access_control_db(con: psycopg2.connect) -> psycopg2.connect:
    #this function will create two users; an admin for us to populate the db, and another
    #user which can only query stuff (this will be what the front end users authenticate as)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    try:
        query = sql.SQL("select COUNT(*) from {table} where {pkey} = %s").format(
            table=sql.Identifier('pg_roles'),
            pkey=sql.Identifier('rolname'))
        cur.execute(query, ('music_man',))
        print(cur.fetchone()[0])
    except psycopg2.DatabaseError as e:
        print('Error in DB access control: {}'.format(e))
        #cur.execute("CREATE ROLE {} WITH LOGIN CREATEDB PASSWORD '{}'".format('music_man', 'music_man_rocks')))

def get_album_html() -> bs4.BeautifulSoup:
    http = httplib2.Http()
    artist_name = input("Please enter an artist name: ").capitalize()
    URL = 'https://genius.com/' + "artists/" + artist_name
    status, response = http.request(URL)
    return http, bs4.BeautifulSoup(response, "html.parser"), artist_name

def print_album_sentiments(album_sentiments: dict):
    for album, sentiments in album_sentiments.items():
        print('Album Name: {}'.format(album))
        pprint.pprint(sentiments)
        print()

def get_sentiment_by_album(artist: Artist) -> dict:
    analyzer = SentimentIntensityAnalyzer()
    album_sentiments = {}
    for album in artist.albums:
        sentiments = {'compound': 0.0, 'neg': 0.0, 'neu': 0.0, 'pos': 0.0}
        for song in album.song_list:
            for sentence in song.lyrics:
                vs = analyzer.polarity_scores(sentence)
                sentiments['compound'] += vs['compound']
                sentiments['neg'] += vs['neg']
                sentiments['neu'] += vs['neu']
                sentiments['pos'] += vs['pos']

            sentiments['compound'] /= len(song.lyrics)
            sentiments['neg'] /= len(song.lyrics)
            sentiments['neu'] /= len(song.lyrics)
            sentiments['pos'] /= len(song.lyrics)

        album_sentiments[album.album_title] = sentiments
    
    return album_sentiments


def populate_artist():

    #vertical album card for getting album urls
    #u-display_block for getting song urls per album

    http, artist_html, artist_name = get_album_html()
    #extract album related html from artist webpage
    album_names = artist_html.find_all("a", class_="vertical_album_card")
    x = 0
    #unique_words = {}
    album_urls = []
    album_titles = []

    for name in album_names:
        #get album urls and titles
        album_urls.append(name['href'])
        album_titles.append(name['title'])


    print(artist_name)
    print('Albums being analyzed: ' + ', '.join(album_titles))
    artist = Artist(artist_name, [])

    sentences = ""
    song_urls = []
    #for each album, collect all the songs
    #and perform unique word analysis on them
    for i in album_urls:
        #page = requests.get(i)
        status, response = http.request(i)
        #go to webpage of song listing in album
        html = bs4.BeautifulSoup(response, "html.parser")
        #find all song html
        song_html = html.find_all('a', class_="u-display_block")
        for name in song_html:
            #get song urls
            song_urls.append(name['href'])

        print("\nSongs in " + album_titles[x])
        album = Album(album_titles[x], [])
        
        #for each song
        for url in song_urls:
            #go to song lyrics web paage
            new_page = requests.get(url)
            new_html = bs4.BeautifulSoup(new_page.text, "html.parser")
            #get text version of song lyrics
            lyrics = new_html.find("div", class_ = "lyrics").get_text()
            song_name = new_html.find('h1', class_ = "header_with_cover_art-primary_info-title").get_text()
            print(song_name)
            split_lyrics = lyrics.split('\n')

            #remove extraneous lyrics like [verse] or [chorus]
            for i in split_lyrics:
                if '[' in i:
                    continue
                elif i == '':
                    continue
                else:
                    sentences = sentences + "\n" + i
                    sentences = sentences.replace('\u2005', '')
                    
            sentences = sentences.split('\n')
            song = Song(song_name, sentences)
            album.song_list.append(song)
            sentences = ""

        artist.albums.append(album)
        x = x + 1
        song_urls = []

    #album_sentiments = get_sentiments(album_dict)
    #print_album_sentiments(album_sentiments)
    #pprint.pprint(artist.__dict__)
    #for album in artist.albums:
    #    pprint.pprint(album.__dict__)
    return artist

def main():
    # artist = populate_artist()
    # album_sentiments = get_sentiment_by_album(artist)
    # print('printing sentiments by album')
    # pprint.pprint(album_sentiments)
    con = init_db()
    print(con)
    access_control_db(con)

if __name__ == "__main__":
    main()
