''' Guess the language of text.

    Based on guesslanguage.cpp by Jacob R Rideout for KDE
    http://websvn.kde.org/branches/work/sonnet-refactoring/common/nlp/guesslanguage.cpp?view=markup
    which itself is based on Language::Guess by Maciej Ceglowski
    http://languid.cantbedone.org/

    Copyright (c) 2008, Kent S Johnson

    C++ version is Copyright (c) 2006 Jacob R Rideout <kde@jacobrideout.net>
    Perl version is (c) 2004-6 Maciej Ceglowski
    
    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
    
    Note: Language::Guess is GPL-licensed. KDE developers received permission
    from the author to distribute their port under LGPL:
    http://lists.kde.org/?l=kde-sonnet&m=116910092228811&w=2
    
'''

import codecs, os, re, sys, unicodedata
from collections import defaultdict
from pprint import pprint
from blocks import unicodeBlock

# I'ts possible to enforce proper handling of UTF-8 characters when using print
#class LangEnvironmentNotSetError(Exception): pass
#try:
#    if os.environ['LANG'] == 'LANG=en_US.UTF-8':
#        raise LangEnvironmentNotSetError, "need to set environment variable: LANG=en_US.UTF-8"
#except KeyError,msg:
#    raise LangEnvironmentNotSetError, "need to set environment variable: LANG=en_US.UTF-8"

MIN_LENGTH = 20

BASIC_LATIN = "en ceb ha so tlh id haw la sw eu nr nso zu xh ss st tn ts".split()
EXTENDED_LATIN = "cs af pl hr ro sk sl tr hu az et sq ca es fr de nl it da is no sv fi lv pt ve lt tl cy".split()
ALL_LATIN = BASIC_LATIN + EXTENDED_LATIN
CYRILLIC = "ru uk kk uz mn sr mk bg ky".split()
ARABIC = "ar fa ps ur".split()
DEVANAGARI = "hi ne".split()

# We are interested in normalizing to 'zh', 'ja' and 'ko'
SPECIAL_BLOCKS = { "Bopomofo": "CJK Unified Ideographs",
                   "Bopomofo Extended": "CJK Unified Ideographs",
                   "KangXi Radicals": "CJK Unified Ideographs",
                   "Arabic Presentation Forms-A": "CJK Unified Ideographs",

                   "Hangul Syllables": "Hangul",
                   "Hangul Jamo": "Hangul",
                   "Hangul Compatibility Jamo": "Hangul",

                   "Katakana": "Hiragana",
                   "Katakana Phonetic Extensions": "Hiragana",

                   }


# NOTE mn appears twice, once for mongolian script and once for CYRILLIC
SINGLETONS = [
    ('Armenian', 'hy'),
    ('Hebrew', 'he'),
    ('Bengali', 'bn'),
    ('Gurmukhi', 'pa'),
    ('Greek', 'el'),
    ('Gujarati', 'gu'),
    ('Oriya', 'or'),
    ('Tamil', 'ta'),
    ('Telugu', 'te'),
    ('Kannada', 'kn'),
    ('Malayalam', 'ml'),
    ('Sinhala', 'si'),
    ('Thai', 'th'),
    ('Lao', 'lo'),
    ('Tibetan', 'bo'),
    ('Burmese', 'my'),
    ('Georgian', 'ka'),
    ('Mongolian', 'mn-Mong'),
    ('Khmer', 'km'),
]

PT = "pt_BR pt_PT".split()

UNKNOWN = 'UNKNOWN'

models = {}

NAME_MAP = {
    "it" : "italian",
    "no" : "norwegian",
    "sv" : "swedish",
    "fy" : "Frisian",
    "pa" : "Punjabi",
    "he" : "hebrew",
    "tr" : "turkish",
    "sk" : "slovak",
    "ms" : "Malay",
    "hy" : "armenian",
    "id" : "indonesian",
    "mk" : "macedonian",
    "uk" : "ukranian",
    "km" : "Cambodian",
    "tw" : "Twi",
    "mg" : "Malagasy",
    "el" : "greek",
    "vi" : "vietnamese",
    "et" : "estonian",
    "bg" : "bulgarian",
    "bo" : "tibetan",
    "mn" : "mongolian",
    "lv" : "latvian",
    "ky" : "kyrgyz",
    "ne" : "nepali",
    "ml" : "malayalam",
    "en" : "english",
    "fr" : "french",
    "bn" : "bengali",
    "pt" : "portuguese",
    "tl" : "tagalog",
    "eu" : "Basque",
    "tn" : "Setswana",
    "sr" : "serbian",
    "ha" : "hausa",
    "ceb" : "cebuano",
    "be" : "Byelorussian",
    "ro" : "romanian",
    "uz" : "uzbek",
    "so" : "somali",
    "ja" : "japanese",
    "hu" : "hungarian",
    "gd" : "Scots Gaelic",
    "tlh" : "klingon",
    "fo" : "Faroese",
    "nn" : "Nynorsk",
    "pl" : "polish",
    "gu" : "gujarati",
    "la" : "latin",
    "ur" : "urdu",
    "zh" : "chinese",
    "eo" : "Esperanto",
    "sl" : "slovene",
    "ru" : "russian",
    "br" : "Breton",
    "is" : "icelandic",
    "th" : "thai",
    "sa" : "Sanskrit",
    "fi" : "finnish",
    "ko" : "korean",
    "ab" : "Abkhazian",
    "cs" : "czech",
    "te" : "telugu",
    "sh" : "Serbo-Croatian",
    "az" : "azeri",
    "af" : "Afrikaans",
    "es" : "spanish",
    "haw" : "hawaiian",
    "uk" : "ukrainian",
    "ca" : "Catalan",
    "fa" : "farsi",
    "da" : "danish",
    "nl" : "dutch",
    "de" : "german",
    "mr" : "Marathi",
    "lt" : "lithuanian",
    "zh-tw" : "Traditional Chinese (Taiwan)",
    "cy" : "welsh",
    "kk" : "kazakh",
    "ta" : "tamil",
    "ps" : "pashto",
    "sq" : "albanian",
    "hr" : "croatian",
    "ka" : "georgian",
    "sw" : "swahili",
    "ar" : "arabic",
    "ku" : "Kurdish",
    "hi" : "hindi",
    "gl" : "Galician",
}

IANA_MAP = {
    "it" : 26230,
    "no" : 26340,
    "sv" : 26480,
    "fy" : 1353,
    "pa" : 65550,
    "he" : 26592,
    "tr" : 26500,
    "sk" : 26430,
    "ms" : 1147,
    "hy" : 26597,
    "id" : 26220,
    "mk" : 26310,
    "uk" : 26520,
    "km" : 1222,
    "tw" : 1499,
    "mg" : 1362,
    "el" : 26165,
    "vi" : 26550,
    "et" : 26120,
    "bg" : 26050,
    "bo" : 26601,
    "mn" : 26320,
    "lv" : 26290,
    "ky" : 26260,
    "ne" : 26330,
    "ml" : 26598,
    "en" : 26110,
    "fr" : 26150,
    "bn" : 26040,
    "pt" : 26390,
    "tl" : 26490,
    "eu" : 1232,
    "tn" : 65578,
    "sr" : 26420,
    "ha" : 26170,
    "ceb" : 26060,
    "be" : 11890,
    "ro" : 26400,
    "uz" : 26540,
    "so" : 26450,
    "ja" : 26235,
    "hu" : 26200,
    "gd" : 65555,
    "tlh" : 26250,
    "fo" : 11817,
    "nn" : 172,
    "pl" : 26380,
    "gu" : 26599,
    "la" : 26280,
    "ur" : 26530,
    "zh" : 26065,
    "eo" : 11933,
    "sl" : 26440,
    "ru" : 26410,
    "br" : 1361,
    "is" : 26210,
    "th" : 26594,
    "sa" : 1500,
    "fi" : 26140,
    "ko" : 26255,
    "ab" : 12026,
    "cs" : 26080,
    "te" : 26596,
    "sh" : 1399,
    "az" : 26030,
    "af" : 40,
    "es" : 26460,
    "haw" : 26180,
    "uk" : 26510,
    "ca" : 3,
    "fa" : 26130,
    "da" : 26090,
    "nl" : 26100,
    "de" : 26160,
    "mr" : 1201,
    "lt" : 26300,
    "zh-tw" : 22,
    "cy" : 26560,
    "kk" : 26240,
    "ta" : 26595,
    "ps" : 26350,
    "sq" : 26010,
    "hr" : 26070,
    "ka" : 26600,
    "sw" : 26470,
    "ar" : 26020,
    "ku" : 11815,
    "hi" : 26190,
    "gl" : 1252,
}

def _load_models():
    modelsDir = os.path.join(os.path.dirname(__file__), 'trigrams')
    modelsList = os.listdir(modelsDir)
    
    lineRe = re.compile(r"(.{3})\s+(.*)")
    for modelFile in modelsList:
        modelPath = os.path.join(modelsDir, modelFile)
        if os.path.isdir(modelPath):
            continue
        f = codecs.open(modelPath, 'r', 'utf-8')
        model = {}  # QHash<QString,int> model
        for line in f:
            m = lineRe.search(line)
            if m:
                model[m.group(1)] = int(m.group(2))

        models[modelFile.lower()] = model

_load_models()

"""
    Returns the language tag.  i.e. 'en'
"""
def guessLanguage(text):
    if not text:
        return UNKNOWN
    
    if isinstance(text, str):
        text = unicode(text, 'utf-8')
    
    text = normalize(text)

    tag = _identify(text, find_runs(text))
    return tag  
"""
    Returns (tag, id, name)  i.e. ('en', 26110, 'english')
"""
def guessLanguageInfo(text):
    if not text:
        return UNKNOWN
    
    if isinstance(text, str):
        text = unicode(text, 'utf-8')
    
    text = normalize(text)

    tag = _identify(text, find_runs(text))
    if tag == UNKNOWN:
        return UNKNOWN,UNKNOWN,UNKNOWN

    id = _getId(tag)
    name = _getName(tag)
    return tag,id,name

"""
    Returns the same as guessLanguage()
"""
def guessLanguageTag(text):
    return guessLanguage(text)

"""
    Returns the language id.  i.e. 26110
"""
def guessLanguageId(text):
    if not text:
        return UNKNOWN

    lang = guessLanguage(text)
    return _getId(lang)
   
"""
    Returns the language name.  i.e. 'english'
"""
def guessLanguageName(text):
    if not text:
        return UNKNOWN

    lang = guessLanguage(text)
    return _getName(lang) 


def _getId(iana):
    if iana in IANA_MAP:
        return IANA_MAP[iana]
    return UNKNOWN

def _getName(iana):
    if iana in NAME_MAP:
        return NAME_MAP[iana]
    return UNKNOWN

def find_runs(text):
    ''' Count the number of characters in each character block '''
    run_types = defaultdict(int)

    totalCount = 0

    for c in text:
        if c.isalpha():
            block = unicodeBlock(c)
            run_types[block] += 1
            totalCount += 1

    special_count = 0
    types = run_types.keys()
    # We normalize chinese, japanese and korean characters 
    for block in types:
        if block in SPECIAL_BLOCKS:
            run_types[SPECIAL_BLOCKS[block]] += run_types[block]
            del run_types[block]

    # We default CJK Unified Ideographs to chinese in _identify(), but the characters could be japanese or korean just as easily.
    # Boost japanese
    if "Hiragana" in run_types and "CJK Unified Ideographs" in run_types:
        run_types["Hiragana"] += run_types["CJK Unified Ideographs"]
    # Boost korean
    if "Hangul" in run_types and "CJK Unified Ideographs" in run_types:
        run_types["Hangul"] += run_types["CJK Unified Ideographs"]
 
    # Let's just sort by count and return
    alist = sorted(run_types.iteritems(), key=lambda (k,v): (v,k), reverse=True)
    return [key for key,val in alist]

def _identify(sample, scripts):
    if len(sample) < 3:
        return UNKNOWN

    for target_lang in scripts:
        if "Basic Latin" == target_lang or "Extended Latin" == target_lang:
            if "Basic Latin" == target_lang:
                latinLang = check( sample, ALL_LATIN )
            elif "Extended Latin" == target_lang:
                latinLang = check( sample, EXTENDED_LATIN )
            if latinLang == "pt":
                ret = check(sample, PT)
                if ret == "pt_PT" or ret == "pt_BR":
                    return "pt"
                return ret
            else:
                return latinLang
 
        if "Hangul" == target_lang or "Hangul Syllables" == target_lang or "Hangul Jamo" == target_lang \
                or "Hangul Compatibility Jamo" == target_lang: 
            return "ko"

        if "Greek and Coptic" == target_lang:
            return "el"

        if "Hiragana" == target_lang or "Katakana" == target_lang or "Katakana Phonetic Extensions" == target_lang:
            return "ja"

        if "CJK Unified Ideographs" == target_lang or "Bopomofo" == target_lang \
                or "Bopomofo Extended" == target_lang or "KangXi Radicals" == target_lang:
            return "zh"

        if "Cyrillic" == target_lang:
            return check( sample, CYRILLIC )

        if "Arabic" == target_lang or "Arabic Presentation Forms-A" == target_lang or "Arabic Presentation Forms-B" == target_lang:
            return check( sample, ARABIC )

        if "Devanagari" == target_lang:
            return check( sample, DEVANAGARI )


        # Try languages with unique scripts
        for blockName, langName in SINGLETONS:
            if blockName == target_lang:
                return langName

        if "Latin Extended Additional" == target_lang:
            return "vi"

           
    return UNKNOWN


def check(sample, langs):
    if len(sample) < MIN_LENGTH:
        return UNKNOWN

    scores = []
    model = createOrderedModel(sample)  # QMap<int,QString>

    for key in langs:
        lkey = key.lower()

        if lkey in models:
            scores.append( (distance(model, models[lkey]), key) )
    if not scores:
        return UNKNOWN

    # we want the lowest score, less distance = greater chance of match
    return min(scores)[1]


def createOrderedModel(content):
    ''' Create a list of trigrams in content sorted by frequency '''
    trigrams = defaultdict(int) # QHash<QString,int> 
    content = content.lower()
    
    for i in xrange(0, len(content)-2):
        trigrams[content[i:i+3]]+=1

    return sorted(trigrams.keys(), key=lambda k: (-trigrams[k], k))


spRe = re.compile(r"\s\s", re.UNICODE)
MAXGRAMS = 300

def distance(model, knownModel):
    dist = 0

    for i, value in enumerate(model[:MAXGRAMS]):
        if not spRe.search(value):
            if value in knownModel:
                dist += abs(i - knownModel[value])
            else:
                dist += MAXGRAMS

    return dist


def _makeNonAlphaRe():
    nonAlpha = [u'[^']
    for i in range(sys.maxunicode):
      c = unichr(i)
      if c.isalpha(): nonAlpha.append(c)
    nonAlpha.append(u']')
    nonAlpha = u"".join(nonAlpha)
    return re.compile(nonAlpha)


nonAlphaRe = _makeNonAlphaRe()
spaceRe = re.compile('\s+', re.UNICODE)
    
def normalize(u):
    ''' Convert to normalized unicode.
        Remove non-alpha chars and compress runs of spaces.
    '''
    u = unicodedata.normalize('NFC', u)
    u = nonAlphaRe.sub(' ', u)
    u = spaceRe.sub(' ', u)
    return u
