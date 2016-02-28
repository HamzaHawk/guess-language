Attempts to determine the natural language of a selection of Unicode (utf-8) text.

Based on [guesslanguage.cpp](http://websvn.kde.org/branches/work/sonnet-refactoring/common/nlp/guesslanguage.cpp?view=markup) by Jacob R Rideout for KDE which itself is based on [Language::Guess](http://languid.cantbedone.org/) by Maciej Ceglowski.

Detects over 60 languages; Greek (el), Korean (ko), Japanese (ja), Chinese (zh) and all the languages listed in the [trigrams](http://code.google.com/p/guess-language/source/browse/trunk/guess_language/trigrams/) directory.

Code is available from [svn](http://code.google.com/p/guess-language/source/checkout).

Note: I (Kent Johnson) am no longer using or maintaining this code. Phi-Long DO maintains a Python 3 version (with support for lib3to2) at https://bitbucket.org/spirit/guess_language.