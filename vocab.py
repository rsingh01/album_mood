#from bs4 import BeautifulSoup, SoupStrainer
import bs4
import requests
import string
import httplib2
import nltk
import pprint
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

nltk.download('punkt')

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

def get_sentiments(album_dict: dict) -> dict:
    analyzer = SentimentIntensityAnalyzer()
    album_sentiments = {}
    for album, lyrics in album_dict.items():
        sentiments = {'compound': 0.0, 'neg': 0.0, 'neu': 0.0, 'pos': 0.0}
        for sentence in lyrics:
            vs = analyzer.polarity_scores(sentence)
            sentiments['compound'] += vs['compound']
            sentiments['neg'] += vs['neg']
            sentiments['neu'] += vs['neu']
            sentiments['pos'] += vs['pos']

        sentiments['compound'] /= len(lyrics)
        sentiments['neg'] /= len(lyrics)
        sentiments['neu'] /= len(lyrics)
        sentiments['pos'] /= len(lyrics)
        album_sentiments[album] = sentiments

    return album_sentiments


def main():

    #vertical album card for getting album urls
    #u-display_block for getting song urls per album

    http, artist_html, artist_name = get_album_html()
    #extract album related html from artist webpage
    album_names = artist_html.find_all("a", class_="vertical_album_card")
    x = 0
    #unique_words = {}
    album_urls = []
    album_titles = []
    album_sentiments = {}
    album_dict = {}
    for name in album_names:
        #get album urls and titles
        album_urls.append(name['href'])
        album_titles.append(name['title'])


    print(artist_name)
    print('Albums being analyzed: ' + ', '.join(album_titles))

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

        print("Songs in " + album_titles[x])
        #for each song
        for url in song_urls:
            print(url)
            #go to song lyrics web paage
            new_page = requests.get(url)
            new_html = bs4.BeautifulSoup(new_page.text, "html.parser")
            #get text version of song lyrics
            lyrics = new_html.find("div", class_ = "lyrics").get_text()
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
            album_dict[album_titles[x]] = sentences
            sentences = ""

        x = x + 1
        song_urls = []
    
    album_sentiments = get_sentiments(album_dict)
    print_album_sentiments(album_sentiments)

if __name__ == "__main__":
    main()