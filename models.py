import re
import random
import time

import lyricsgenius
from config import GENIUS_TOKEN
from database import DbHandler
from requests.exceptions import ConnectionError, Timeout


def escape_symb(string):
    markdown = r'[_*\[\]\(\)~`>#\+-=\|{}\.!]'
    line = string.translate({ord(i): '\\' + i for i in markdown})
    return line


def html2tgmarkdown(html_str):
    html_str = re.sub('<ul>', '\n', html_str)
    html_str = re.sub(r'<\/?ul>', '', html_str)
    html_str = re.sub('<li>','\u2022 ', html_str)
    html_str = re.sub('<\/li>', '\n', html_str)
    html_str = re.sub(r'<\/?p.*?>', '', html_str)
    html_str = re.sub('<br>', '\n\n', html_str)
    html_str = re.sub(r'<\/?strong>', '**', html_str)
    html_str = re.sub('&nbsp;', '', html_str)
    markdown = r'[_\[\]\(\)~`>#\+-=\|{}\.!]'
    html_str = html_str.translate({ord(i): '\\' + i for i in markdown})
    return html_str


def lyrics2markdown(kor_lyrics, translation):
    message = escape_symb(kor_lyrics) + '\n' + '_' + escape_symb(translation) + '_'
    return message


def random_song(artist, songs_list):
    rand_song = random.randint(0, len(songs_list) - 1)
    genius = lyricsgenius.Genius(GENIUS_TOKEN, remove_section_headers=True)
    while True:
        try:
            random_lyrics = genius.search_song(title=songs_list[rand_song], artist=artist).lyrics
        except ConnectionError or Timeout as e:
            print('there is an exception ', e)
            time.sleep(5)
            continue
        break
    if len(random_lyrics) != 0:
        random_lyrics = random_lyrics.split('Lyrics')
        return random_lyrics[0], random_lyrics[1]
    else:
        print(rand_song, 'lyrics not found')
        return random_song(artist, songs_list)





def clean_lyrics(lyrics):
    parts = lyrics.split('\n\n')
    text_only = []
    for part in parts:
        if len(part) > 1:
            text_only.append(part.split('\n'))
            text_only[-1][-1] = text_only[-1][-1].strip('Embed')
    return text_only


def random_lines(artist, song_list, line_n=2):
    clean_text = clean_lyrics(random_song(artist, song_list)[1])
    rand_part = random.randint(0, len(clean_text) - 1)
    if len(clean_text[rand_part]) > line_n:
        rand_idx = random.randint(0, len(clean_text[rand_part]) - 1 - line_n)
        rand_lyr = ' '.join(clean_text[rand_part][rand_idx: rand_idx + line_n]).lower()
    elif len(clean_text[rand_part]) == line_n:
        rand_lyr = ' '.join(clean_text[rand_part])
    else:
        rand_lyr = random_lines(artist, song_list, line_n)

    if re.search(r'^[A-z ()\',\"\"?!.]*$', rand_lyr):
        return random_lines(artist, song_list, line_n)
    else:
        return rand_lyr


def grammar_to_db(gram_def):
    db = DbHandler()
    db_grammar = db.get_grammar_names()
    if db_grammar:
        for grammar in gram_def:
            if grammar not in db_grammar:
                db.add_grammar(grammar, gram_def[grammar])
    else:
        for grammar in gram_def:
            db.add_grammar(grammar, gram_def[grammar])
    return None
