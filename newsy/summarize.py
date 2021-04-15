import datetime as dt
import re
from transformers import BartTokenizer, BartForConditionalGeneration

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from nltk.tokenize import sent_tokenize

import newsy.debugger as debug

PRETRAINED_MODEL = 'facebook/bart-large-cnn'

# debug.log('*' * debug.rem_len(settings.TW_wrapping_width))
# debug.log("")
debug.header(f"Initializing '{PRETRAINED_MODEL}' summarization model...")

runtime_start = dt.datetime.now()

model = BartForConditionalGeneration.from_pretrained(PRETRAINED_MODEL)
tokenizer = BartTokenizer.from_pretrained(PRETRAINED_MODEL)

run_time = (dt.datetime.now() - runtime_start).seconds

debug.footer(f"Initialization complete in {run_time} seconds!")


def field_from_neighbors(items_dict, neighbors_list, field, remove_punc=False):
    text_to_summarize = ""
    for i in range(len(neighbors_list)):
        item_id = neighbors_list[i]
        text = items_dict[item_id][field]
        if remove_punc:
            regex = r"(?<!\w)(\D)\.|(\D)(\.)(\D| |$)"
            sub_string = "\\1\\2\\4"
            text = re.sub(regex, sub_string, text)
            # text = text.replace(".", "") + "."
        if text[-1] != ".":
            text += "."
        text_to_summarize += text + " "
    output = " ".join(text_to_summarize.split())
    return output


def abstractive_summarizer(text):

    inputs = tokenizer([text], truncation=True, max_length=1024, return_tensors="pt")
    summary_ids = model.generate(inputs['input_ids'], num_beams=4, min_length=30, max_length=100,
                                 early_stopping=True)
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)


def extractive_summarizer(items_dict, neighbors_list, field):

    text = field_from_neighbors(items_dict, neighbors_list, field)

    parser = PlaintextParser.from_string(text, Tokenizer("english"))

    lsa_summary = ""
    summarizer = LsaSummarizer()
    for sentence in summarizer(parser.document, 100):
        lsa_summary += str(sentence) + " "

    return " ".join(lsa_summary.split())


def content(items_dict, neighbors_list):
    extractive_summary = extractive_summarizer(items_dict, neighbors_list, "content")
    return abstractive_summarizer(extractive_summary)


def topic(items_dict, neighbors_list):
    topic_summary = field_from_neighbors(items_dict, neighbors_list, "title", True)
    # print(topic_summary)
    topic_summary = abstractive_summarizer(topic_summary)
    return sent_tokenize(topic_summary)[0]