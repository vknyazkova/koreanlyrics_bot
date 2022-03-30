import sqlite3


class DbHandler(object):
    conn = None
    cur = None

    def __init__(self):
        self.conn = sqlite3.connect('lyricsbot_database.db', check_same_thread=False)
        self.cur = self.conn.cursor()

    def __del__(self):
        self.conn.close()

    def add_user(self, user_id):
        self.cur.execute('''INSERT or IGNORE 
                            INTO users (id)
                            VALUES (?)''', (user_id,))
        self.conn.commit()

    def add_songs(self, title, artist):
        # self.cur.execute('TRUNCATE TABLE songs')
        # self.conn.commit()
        self.cur.execute('''INSERT INTO songs (name, artist_id)
                                SELECT ?, id
                                FROM artists
                                WHERE artists.genius_name = (?)''', (title, artist))
        self.conn.commit()

    def add_grammar(self, name, desc):
        print('add grammar')
        self.cur.execute('''INSERT INTO grammar (name, description)
                            VALUES (?, ?)''', (name, desc))
        self.conn.commit()

    def change_artist(self, user, new_artist_id):
        self.cur.execute('''UPDATE users
                            SET selected_artist = ?
                            WHERE id = ?''', (new_artist_id, user))
        self.conn.commit()

    def get_grammar_names(self):
        self.cur.execute('''SELECT (name)
                            FROM grammar''')
        grammar = self.cur.fetchall()
        return [g[0] for g in grammar]

    def get_grammar_descr(self, grammar_name):
        self.cur.execute('''SELECT (description)
                            FROM grammar
                            WHERE name = (?)''', (grammar_name,))
        return self.cur.fetchone()

    def get_songs(self, artist_id):
        self.cur.execute('''SELECT name
                            FROM songs
                            WHERE songs.artist_id = (?)''', (artist_id,))
        return [s[0] for s in self.cur.fetchall()]

    def get_selected_artists(self):
        self.cur.execute('''SELECT DISTINCT users.selected_artist, artists.genius_name
                            FROM users
                            INNER JOIN artists ON users.selected_artist=artists.id
                            ''')
        return self.cur.fetchall()

    def get_users(self):
        self.cur.execute('''SELECT users.id, users.selected_artist, artists.genius_name
                            FROM users
                            INNER JOIN artists ON users.selected_artist=artists.id''')
        return self.cur.fetchall()

    def get_user_info(self, user_id):
        self.cur.execute('''SELECT users.selected_artist, artists.genius_name
                            FROM users
                            INNER JOIN artists ON users.selected_artist=artists.id
                            WHERE users.id = (?)''', (user_id,))
        return self.cur.fetchone()

    def get_artists(self):
        self.cur.execute('''SELECT id, genius_name
                            FROM artists''')
        return self.cur.fetchall()

