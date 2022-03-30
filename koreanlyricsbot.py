import telebot
import schedule
import time
import lyricsgenius
from keyboa import Keyboa
from requests.exceptions import ConnectionError, Timeout

from config import BOT_TOKEN, GENIUS_TOKEN
from database import DbHandler
from mirinae import MirinaeScrapping
from models import html2tgmarkdown, lyrics2markdown, random_lines, grammar_to_db, escape_symb

bot = telebot.TeleBot(BOT_TOKEN)
genius = lyricsgenius.Genius(GENIUS_TOKEN, remove_section_headers=True)


def init():  # добавление названий песен в бд, если их нет
    db = DbHandler()
    selected_artists = db.get_selected_artists()

    for artist_id, name in selected_artists:
        db_songs = db.get_songs(artist_id)
        gns_songs = genius.search_artist(name).songs
        gns_songs_titles = [s.title for s in gns_songs]
        diff = set(gns_songs_titles) - set(db_songs)
        if diff:
            for song in diff:
                db.add_songs(song, name)


def send_lyrics():  # отправка рандомной строчки из песни
    db = DbHandler()
    randoms = {}  # словарь вида {исполнитель: {рандомная строчка: перевод}}
    for art_id, gns_name in db.get_selected_artists():
        songs = db.get_songs(art_id)
        rand_lines = random_lines(gns_name, songs)

        mrn = MirinaeScrapping()
        mrn.analyze(rand_lines)
        grammar_to_db(mrn.get_patterns_def())  # добавляем грамматику в бд, если ее нет

        randoms[art_id] = {'lines': rand_lines,
                           'translation': mrn.translation}

    # каждому пользователю отправляем рандомную строчку выбранного исполнителя
    for user, user_art_id, art_name in db.get_users():
        user_rand_lines = randoms[user_art_id]['lines']
        to_send = lyrics2markdown(user_rand_lines, randoms[user_art_id]['translation'])
        gram_vocab = Keyboa(items=['grammar', 'vocabulary', 'songname'],
                            copy_text_to_callback=True,
                            back_marker='_choice',
                            items_in_row=3).keyboard
        bot.send_message(user, to_send, reply_markup=gram_vocab, parse_mode='MarkdownV2')


# Функции, которые запускаются по времени: поиск песен на genius и отправка рандомной строчки из песни
def scheduled_funcs():
    schedule.every(3).week.do(init)
    schedule.every().day.at('10:10').do(send_lyrics)
    # schedule.every().day.at('19:06').do(init)

    while True:
        schedule.run_pending()
        time.sleep(1)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    start_message = '''
    Using this bot you can:
    * get some random korean lyrics everyday
    * explore grammar of current lyrics excerpt
    * get translation of it
    * get the title of the song

    NB: For sentence structure analysis and for translation this bot uses mirinae.io and papago.naver.com (respectively), so both translation and parsed grammar can be inaccurate
    P.S. I am very slow 🐢🐢🐢 please be patient
    '''
    bot.send_message(message.chat.id, start_message)
    db = DbHandler()
    db.add_user(message.chat.id)


# изменяет выбранного исполнителя
@bot.message_handler(commands=['select_artist'])
def change_artist(message):
    print(message.text)
    db = DbHandler()
    artists = db.get_artists()
    art_kb = Keyboa(items=[{a[1]: a[0]} for a in artists],
                    back_marker='_artist',
                    items_in_row=3,
                    copy_text_to_callback=True).keyboard
    to_send = 'Please select artist'
    bot.send_message(message.chat.id, text=to_send, reply_markup=art_kb)


# отправка сообщений по команде
@bot.message_handler(commands=['sendlyrics'])
def send_extra_lyrics(message):
    db = DbHandler()
    selected_artist = db.get_user_info(message.chat.id)

    songs = db.get_songs(selected_artist[0])
    rand_lines = random_lines(selected_artist[1], songs)

    mrn = MirinaeScrapping()
    mrn.analyze(rand_lines)
    grammar_to_db(mrn.get_patterns_def())
    tr = mrn.translation
    if tr:
        to_send = lyrics2markdown(rand_lines, tr)
    else:
        to_send = lyrics2markdown(rand_lines, ' ')
    gram_vocab = Keyboa(items=['grammar', 'vocabulary', 'songname'],
                        copy_text_to_callback=True,
                        back_marker='_choice',
                        items_in_row=3).keyboard
    bot.send_message(message.chat.id, to_send, reply_markup=gram_vocab, parse_mode='MarkdownV2')


@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    db = DbHandler()
    db.get_grammar_names()
    #print('call.data=', call.data)
    if call.data.split('_')[1] == 'choice':

        mrn = MirinaeScrapping()
        kor_lyrics = call.message.text.split('\n')[0]
        mrn.analyze(kor_lyrics)
        text = lyrics2markdown(kor_lyrics, mrn.translation)

        if call.data.split('_')[0] == 'grammar':  # нажатие на кнопку grmmar
            lyr_gram = list(mrn.get_patterns_def().keys())
            if lyr_gram:
                grammar_buttons = Keyboa(items=lyr_gram,
                                         back_marker='_grammar',
                                         items_in_row=3,
                                         copy_text_to_callback=True,
                                         alignment=True).keyboard
                back_button = Keyboa(items=['back'],
                                     back_marker='_back').keyboard
                grammar_section = Keyboa.combine(keyboards=(grammar_buttons, back_button))
            else:
                grammar_section = Keyboa(items={'there is no grammar. go back': '_back'}).keyboard
            bot.edit_message_text(text=text,
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=grammar_section,
                                  parse_mode='MarkdownV2')

        elif call.data.split('_')[0] == 'vocabulary':  # нажатие на кнопку vocabulary

            words = mrn.get_words()
            if words:
                vocab_buttons = Keyboa(items=[{w[0]: str(i) + '@' + w[1]} for i, w in enumerate(words)],
                                       back_marker='_vocab',
                                       items_in_row=3,
                                       alignment=True).keyboard
                back_button = Keyboa(items=['back'],
                                     back_marker='_back').keyboard
                vocab_section = Keyboa.combine(keyboards=(vocab_buttons, back_button))
            else:
                vocab_section = Keyboa(items={'there is no vocabulary. go back': '_back'}).keyboard
            bot.edit_message_text(text=text,
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=vocab_section,
                                  parse_mode='MarkdownV2')

        elif call.data.split('_')[0] == 'songname':  # нажатие на кнопку songname
            kor_lyrics = call.message.text.split('\n')[0]
            while True:
                try:
                    search_result = genius.search(kor_lyrics)
                except Timeout or ConnectionError as e:
                    print(e)
                    time.sleep(5)
                    continue
                break

            title = search_result['hits'][0]['result']['full_title']
            bot.send_message(call.message.chat.id, text=title)

    elif call.data.split('_')[1] == 'grammar':  # нажатие на кнопку с какой-то грамматикой
        if call.data.split('_')[0] in db.get_grammar_names():
            descr = html2tgmarkdown(db.get_grammar_descr(call.data.split('_')[0])[0])
            bot.send_message(call.message.chat.id, descr, parse_mode='MarkdownV2')

    elif call.data.split('_')[1] == 'vocab':  # нажатие на кнопку с каким-нибудь словом
        tr = call.data.split('_')[0].split('@')[1]
        ind = call.data.split('@')[0]
        mrn = MirinaeScrapping()
        kor_lyrics = call.message.text.split('\n')[0]
        mrn.analyze(kor_lyrics)
        text = lyrics2markdown(kor_lyrics, mrn.translation)
        words = mrn.get_words()
        kb_items = []
        for i, w in enumerate(words):
            if i != int(ind):
                kb_items.append({w[0]: str(i) + '@' + w[1]})
            else:
                kb_items.append({tr: 'IGNORE'})
        transl_buttons = Keyboa(items=kb_items,
                                back_marker='_vocab',
                                items_in_row=3,
                                alignment=True).keyboard
        back_button = Keyboa(items=['back'],
                             back_marker='_back').keyboard
        transl_section = Keyboa.combine(keyboards=(transl_buttons, back_button))
        bot.edit_message_text(text=text,
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=transl_section,
                              parse_mode='MarkdownV2')

    elif call.data.split('_')[1] == 'back':  # нажатие на кнопку назад
        text = call.message.text.split('\n')
        text = lyrics2markdown(text[0], text[1])
        gram_vocab = Keyboa(items=['grammar', 'vocabulary', 'songname'],
                            copy_text_to_callback=True,
                            back_marker='_choice',
                            items_in_row=3).keyboard
        bot.edit_message_text(text=text,
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=gram_vocab,
                              parse_mode='MarkdownV2')

    elif call.data.split('_')[1] == 'artist':  # нажатие на кнопку с именем исполнителя
        db.change_artist(call.message.chat.id, call.data.split('_')[0])
        bot.send_message(call.message.chat.id, 'successfully changed')

