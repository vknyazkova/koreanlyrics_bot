import requests
import json


class MirinaeScrapping(object):

    def __init__(self):

        self.words_translation = None
        self.patterns_def = None
        self.translation = None
        self.analysis = None

        self.payload = {'options': {
            'enableTranslation': True,
            'disableCorrections': False,
            'forceReanalyze': True,
            'allParseTreeLevels': False,
            'enableCompactParseTree': True,
            'enabledTranslation': True,
            'zoomedPatterns': [],
            'enableAutoScaleToFit': True,
            'enableDebugging': False,
            'enablePartialParseOnError': False,
            'ignoreSpacingErrors': False,
            'language': 'en',
        },
            'user': '62432f307f425955bebae558'
        }
        self.url = 'https://mirinae.io/api/nlp/analyze'
        self.headers = {
            'authority': 'mirinae.io',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            'accept': 'application/json, text/plain, */*',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'origin': 'https://mirinae.io',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://mirinae.io/',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,ko;q=0.6',
        }
        self.cookies = {
            '_ga': 'GA1.2.1478315438.1644400734',
            'G_ENABLED_IDPS': 'google',
            'agreed': 'true',
            'ber': 'false',
            'visited': 'true',
            'koa.sess': 'eyJwYXNzcG9ydCI6eyJ1c2VyIjoiNjI0MzJmMzA3ZjQyNTk1NWJlYmFlNTU4In0sIl9leHBpcmUiOjE2NDkxNzQ5NjA0NjgsIl9tYXhBZ2UiOjYwNDgwMDAwMH0=',
            'koa.sess.sig': '00OS8uhPo3ImQG0rl9Oy4im_0lU',
            '_gid': 'GA1.2.833791374.1648570158',
            'G_AUTHUSER_H': '0',
            'useVirtualKeyboard': 'false',
            '_gat': '1',
            'ec': '44',
            'sur': 'false',
        }

    def analyze(self, text):
        self.payload['text'] = text
        response = requests.post(self.url,
                                 headers=self.headers,
                                 cookies=self.cookies,
                                 json=self.payload)
        res = json.loads(response.text)
        self.analysis = res['response']['analysis'][0]['subparts'][0]['sentence']
        self.translation = self.analysis['translation']

        self.grammar()
        self.vocabulary()

    def grammar(self):
        self.patterns_def = {}
        for pattern in self.analysis['patterns']:
            gr = self.analysis['patterns'][pattern]['gr']
            self.patterns_def[gr['referenceDefStr']] = gr['defHTML']

    def vocabulary(self):
        self.words_translation = []
        forms_lemmas = {}
        for word in self.analysis['displayDefs']:
            lemma = self.analysis['displayDefs'][word]['word']
            forms_lemmas[word.split(':')[0]] = lemma
        for el in self.analysis['mappedPosList']:
            if el['phoneme'] in forms_lemmas:
                if 'translation' in el.keys():
                    self.words_translation.append((forms_lemmas[el['phoneme']], el['translation']))

    def get_patterns_def(self):
        return self.patterns_def

    def get_translation(self):
        return self.translation

    def get_words(self):
        return self.words_translation
