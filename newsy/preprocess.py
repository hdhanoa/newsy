import nltk
from nltk.stem import WordNetLemmatizer

stemmer = WordNetLemmatizer()


def stem_words(words_list, stemmer):
    return [stemmer.lemmatize(word) for word in words_list]


def tokenize(text):
    tokens = nltk.word_tokenize(text)
    stems = stem_words(tokens, stemmer)
    return stems
