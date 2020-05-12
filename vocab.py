from bs4 import BeautifulSoup, SoupStrainer
import requests
import string
import httplib2
import nltk
nltk.download('punkt')

#vertical album card for getting album urls
#u-display_block for getting song urls per album

#the following block of code gets all of the popular albums of the
#artist that is entered.

http = httplib2.Http()
artist_name = input("Please enter an artist name: ").capitalize()
print(artist_name)
URL = 'https://genius.com/' + "artists/" + artist_name
status, response = http.request(URL)
artist_html = BeautifulSoup(response, "html.parser")

#extract album related html from artist webpage
album_names = artist_html.find_all("a", class_="vertical_album_card")
x = 0
unique_words = dict()
album_urls = []
album_titles = []

for name in album_names:
    #get album urls and titles
    album_urls.append(name['href'])
    album_titles.append(name['title'])


print('Albums being analyzed: ' + ', '.join(album_titles))

temp_str = ""
song_urls = []
#for each album, collect all the songs
#and perform unique word analysis on them
for i in album_urls:
    #page = requests.get(i)
    status, response = http.request(i)
    #go to webpage of song listing in album
    html = BeautifulSoup(response, "html.parser")
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
        new_html = BeautifulSoup(new_page.text, "html.parser")
        #get text version of song lyrics
        lyrics = new_html.find("div", class_ = "lyrics").get_text()
        split_lyrics = lyrics.split('\n')
        #print(split_lyrics)
        #remove extraneous lyrics like [verse] or [chorus]
        for i in split_lyrics:
            if '[' in i:
                continue
            elif i == '':
                continue
            else:
                temp_str = temp_str + " " + i


        temp_str = nltk.word_tokenize(temp_str)
        #print(temp_str)

        #unique word analysis
        for word in temp_str:
            if word in unique_words.keys():
                continue
            else:
                unique_words[word] = ''

        temp_str = ""

    print("\n" + artist_name + " used " + str(len(unique_words.keys())) + " unique words in " + album_titles[x] + '\n')
    x = x + 1
    unique_words = {}
    song_urls = []
