# Originally written by Fivesheep:
# http://code.google.com/p/gtranslatecmd/downloads/detail?name=translator.py
# modified by sbte:
# https://github.com/Sbte/xchat-translate

__module_name__ = "Translator"
__module_version__ = '0.2'
__module_description__ = 'Translate the messages of a given user to a specified language'

import xchat
import urllib
import urllib2
import re
from threading import Thread
import Queue
import traceback
import os

try:
    import json
except:
    import simplejson as json

LAST_ERROR = ''
if os.path.isfile('./translator_users'):
    autouser_file_name = './translator_users'
    f = open(autouser_file_name, 'r')
    AUTOUSER = json.load(f)
    print AUTOUSER
    f.close()
elif os.path.isfile(os.path.expanduser('.xchat2/translator_users')):
    autouser_file_name = os.path.expanduser('.xchat2/translator_users')
    f = open(autouser_file_name, 'r')
    AUTOUSER = json.load(f)
    print AUTOUSER
    f.close()
else:
    AUTOUSER = {}

class TranslateException(Exception):
    pass

class GoogleTranslator:

    LANGUAGES = {
        'AFRIKAANS' : 'af',
        'ALBANIAN' : 'sq',
        'AMHARIC' : 'am',
        'ARABIC' : 'ar',
        'ARMENIAN' : 'hy',
        'AZERBAIJANI' : 'az',
        'BASQUE' : 'eu',
        'BELARUSIAN' : 'be',
        'BENGALI' : 'bn',
        'BIHARI' : 'bh',
        'BULGARIAN' : 'bg',
        'BURMESE' : 'my',
        'CATALAN' : 'ca',
        'CHEROKEE' : 'chr',
        'CHINESE' : 'zh',
        'CHINESE_SIMPLIFIED' : 'zh-CN',
        'CHINESE_TRADITIONAL' : 'zh-TW',
        'CROATIAN' : 'hr',
        'CZECH' : 'cs',
        'DANISH' : 'da',
        'DHIVEHI' : 'dv',
        'DUTCH': 'nl',
        'ENGLISH' : 'en',
        'ESPERANTO' : 'eo',
        'ESTONIAN' : 'et',
        'FILIPINO' : 'tl',
        'FINNISH' : 'fi',
        'FRENCH' : 'fr',
        'GALICIAN' : 'gl',
        'GEORGIAN' : 'ka',
        'GERMAN' : 'de',
        'GREEK' : 'el',
        'GUARANI' : 'gn',
        'GUJARATI' : 'gu',
        'HEBREW' : 'iw',
        'HINDI' : 'hi',
        'HUNGARIAN' : 'hu',
        'ICELANDIC' : 'is',
        'INDONESIAN' : 'id',
        'INUKTITUT' : 'iu',
        'IRISH' : 'ga',
        'ITALIAN' : 'it',
        'JAPANESE' : 'ja',
        'KANNADA' : 'kn',
        'KAZAKH' : 'kk',
        'KHMER' : 'km',
        'KOREAN' : 'ko',
        'KURDISH': 'ku',
        'KYRGYZ': 'ky',
        'LAOTHIAN': 'lo',
        'LATVIAN' : 'lv',
        'LITHUANIAN' : 'lt',
        'MACEDONIAN' : 'mk',
        'MALAY' : 'ms',
        'MALAYALAM' : 'ml',
        'MALTESE' : 'mt',
        'MARATHI' : 'mr',
        'MONGOLIAN' : 'mn',
        'NEPALI' : 'ne',
        'NORWEGIAN' : 'no',
        'ORIYA' : 'or',
        'PASHTO' : 'ps',
        'PERSIAN' : 'fa',
        'POLISH' : 'pl',
        'PORTUGUESE' : 'pt',
        'PUNJABI' : 'pa',
        'ROMANIAN' : 'ro',
        'RUSSIAN' : 'ru',
        'SANSKRIT' : 'sa',
        'SERBIAN' : 'sr',
        'SINDHI' : 'sd',
        'SINHALESE' : 'si',
        'SLOVAK' : 'sk',
        'SLOVENIAN' : 'sl',
        'SPANISH' : 'es',
        'SWAHILI' : 'sw',
        'SWEDISH' : 'sv',
        'TAJIK' : 'tg',
        'TAMIL' : 'ta',
        'TAGALOG' : 'tl',
        'TELUGU' : 'te',
        'THAI' : 'th',
        'TIBETAN' : 'bo',
        'TURKISH' : 'tr',
        'UKRAINIAN' : 'uk',
        'URDU' : 'ur',
        'UZBEK' : 'uz',
        'UIGHUR' : 'ug',
        'VIETNAMESE' : 'vi',
        'WELSH' : 'cy',
        'YIDDISH' : 'yi'}

    CODES_SET = set(LANGUAGES.values())

    BASEURL = r'http://ajax.googleapis.com/ajax/services/language/translate?'

    @classmethod
    def _translate(cls, text, src, langpair):
        params = urllib.urlencode({'v':1.0, 'q':text, 'langpair':langpair,
                                    'format':'text'})
        url = cls.BASEURL + params
        data = json.loads(urllib2.urlopen(url).read())

        if data['responseStatus'] !=  200:
            raise TranslateException(data['responseDetails'])

        translated_text = data['responseData']['translatedText'].encode('utf-8')
        detected_lang = src
        if data['responseData'].has_key('detectedSourceLanguage'):
            detected_lang = data['responseData']['detectedSourceLanguage']
        return (detected_lang, translated_text)

    @classmethod
    def translate(cls, text, dest='en', src=None):
        """Translate the given text into the targetLang.

        Arguments:
        - `text`: the text to be translated
        - `dest`: the code of the destination language
        - `src`: the code of the source language, if not given, auto-detect feature will be used.
        """

        langpair = ''

        if dest not in cls.CODES_SET:
            raise TranslateException('Destination language not supported.')

        langpair = '|'+dest
        try:
            detected_lang, translated_text = cls._translate(text, src, langpair)
        except TranslateException, e:
            raise TranslateException(e)

        if translated_text.strip().lower() ==  text.strip().lower():
            return (detected_lang, text)

        if src in cls.CODES_SET:
            langpair = src+'|'+dest
        elif src is not None:
            raise TranslateException('Source language not supported.')

        try:
            detected_lang, translated_text = cls._translate(text, src, langpair)
        except TranslateException, e:
            raise TranslateException(e)

        return (detected_lang, translated_text)

def timeout(func, args=(), timeout_duration=1, default=None):
    class InterruptableThread(Thread):
        def __init__(self):
            Thread.__init__(self)
            self.result = None

        def run(self):
            try:
                self.result = func(*args)
            except:
                traceback.print_exc()
                self.result = default

    it = InterruptableThread()
    it.start()
    it.join(float(timeout_duration))
    if it.isAlive():
        return default
    else:
        return it.result

class TranslateThread(Thread):
    def __init__(self, queue):
        Thread.__init__(self, target = self.doTranslate)
        self.queue = queue
        self.keepalive = True

    def doTranslate(self):

        global LAST_ERROR
        while True:
            task = self.queue.get()
            if not self.keepalive or task == None:
                break

            try:
                context, user, src, dest, text = task
                lang, translation = timeout(GoogleTranslator.translate,
                        (text, dest, src), timeout_duration=5,
                        default=(None, text))
                if translation.strip().lower() !=  text.strip().lower():
                    nick = "[%s|%s]"%(user, lang)
                    context.emit_print("Channel Message", nick, translation)
            except TranslateException, e:
                LAST_ERROR = "[TE: %s] <%s> %s"%(e, user, text)
            except urllib2.URLError, e:
                LAST_ERROR = "[URL] %s"%e
            except UnicodeError, e:
                LAST_ERROR = "[Encode: %s] <%s> %s"%(e, user, text)

class TranslateMachine:
    tasks = Queue.Queue()
    workThread = TranslateThread(tasks)
    workThread.setDaemon(True)
    workThread.start()

    @classmethod
    def addTask(cls, task):
        cls.tasks.put(task)

def _write_to_file(AUTOUSER):
    ''' write the users to translate to a file'''
    f = open(os.path.expanduser('.xchat2/translator_users'), 'w')
    json.dump(AUTOUSER, f)
    f.close()

def translate(word, word_eol, userdata):
    """Translate the given sentence."""
    text = None
    lang = None
    if re.match(r'[a-z]+\|[a-z]+', word[1]):
        src, dest = word[1].split('|')
        lang, text = GoogleTranslator.translate(word_eol[2], dest, src)
    else:
        lang, text = GoogleTranslator.translate(word_eol[1])

    xchat.prnt("|%s| %s"%(lang, text))
    return xchat.EAT_NONE

xchat.hook_command("tr", translate)

def auto_translate(word, word_eol, userdata):
    """Translate a given user's msgs automaticially.
       Nick [dest] [src]
    """
    global AUTOUSER
    #print word
    channel = xchat.get_info('channel')
    user = word[1]
    dest = 'en'
    src = None
    if len(word) > 2:
        dest = word[2]
    if len(word) > 3:
        src = word[3]

    AUTOUSER[channel+' '+user.lower()] = (dest, src)
    _write_to_file(AUTOUSER)
    xchat.prnt("user '%s' has been added to auto-translate list"%user)
    return xchat.EAT_ALL

xchat.hook_command("a2tr", auto_translate)

def remove_auto_translate(word, word_eol, userdata):
    """Remove a user from the a2tr list
    """
    global AUTOUSER
    channel = xchat.get_info('channel')
    user = word[1]
    cu = channel+' '+user
    if AUTOUSER.pop(cu, None) !=  None:
        _write_to_file(AUTOUSER)
        xchat.prnt("User %s has been removed from the list"%user)
    return xchat.EAT_ALL

xchat.hook_command("rma2tr", remove_auto_translate)

def read_error(word, word_eol, userdata):
    """Read last error
    """
    global LAST_ERROR
    xchat.prnt(LAST_ERROR)

xchat.hook_command("last_err", read_error)

def add_translate_task(word, word_eol, userdata):
    """add tasks
    """
    global AUTOUSER
    user = word[0]
    text = word[1]
    channel = xchat.get_info('channel')
    cu = channel+' '+user.lower()
    if AUTOUSER.has_key(cu):
        #xchat.prnt('Add a TasK: %s'%text)
        dest, src = AUTOUSER[cu]
        TranslateMachine.addTask((xchat.get_context(), user, src, dest, text))

    return xchat.EAT_NONE

xchat.hook_print("Channel Message", add_translate_task)

def _print_watching_users():
    '''actually print what users are being translated'''
    global AUTOUSER
    channel = xchat.get_info('channel')
    users = [user for user in AUTOUSER.keys() if user.split(' ')[0] == channel]
    print_users = []
    for user in users:
        print_users.append(user.split(' ')[1] + ' (' \
            + (AUTOUSER[user][1] if AUTOUSER[user][1] is not None else 'None') \
            + '=>' \
            + (AUTOUSER[user][0] if AUTOUSER[user][0] is not None else 'None') \
            + ')')
    xchat.prnt('Translated are: %s'%(', '.join(print_users)))

def print_watching_users(word, word_eol, userdata):
    '''print what users are being translated'''
    _print_watching_users()
    xchat.EAT_ALL

xchat.hook_command("lsa2tr", print_watching_users)

def channel_joined(word, word_eol, userdata):
    '''print what users are being translated upon joining'''
    _print_watching_users()
    xchat.EAT_NONE

xchat.hook_print("You Join", channel_joined)

def c2l(word, word_eol, userdata):
    """langcode to language
    """
    code = word[1].lower()
    for lang, c in GoogleTranslator.LANGUAGES.items():
        if code == c:
            xchat.prnt("%s <=> %s"%(lang, c))
            return xchat.EAT_ALL
    xchat.prnt("No Language for %s"%code)
    xchat.EAT_ALL

xchat.hook_command("code2lang", c2l)

def l2c(word, word_eol, userdata):
    """language to langcode
    """
    lang = word[1].upper()
    if GoogleTranslator.LANGUAGES.has_key(lang):
        code = GoogleTranslator.LANGUAGES[lang]
        xchat.prnt("%s <=> %s"%(code, word[1]))
    else:
        xchat.prnt("No langcode for %s"%word[1])
    xchat.EAT_ALL

xchat.hook_command("lang2code", l2c)

def unload_translator(userdata):
    TranslateMachine.workThread.keepalive = False
    TranslateMachine.addTask(None)
    print "Translator is unloaded."

xchat.hook_unload(unload_translator)

print 'Translator plugin loaded.'
