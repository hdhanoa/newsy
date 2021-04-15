import datetime

import newsy.settings as settings


def log(msg, indents=0):

    if settings.debug:

        output = ""

        if settings.DSE_show_timestamp:
            output += f"[{datetime.datetime.now()}] "

        if settings.DSE_show_debug_label:
            output += "DEBUG: "

        output += "\t" * indents + msg

        print(output)

        return output

    return ""


def rem_debug_len(string_length):

    return string_length - len(log(""))


def header(msg):
    header_lines = ["*" * rem_debug_len(settings.TW_wrapping_width),
                    "",
                    msg]

    for line in header_lines:
        log(line)


def footer(msg, secondary_info=""):
    log(msg, indents=1)
    if secondary_info:
        log(secondary_info, indents=1)


def divider():
    divider_lines = ['*' * rem_debug_len(settings.TW_wrapping_width),
                     ""]
    for line in divider_lines:
        log(line)


def feed_label(feed, feed_count, num_feeds):
    if settings.DIV_show_all_items or settings.DIV_show_feeds:
        label_lines = ['*' * rem_debug_len(80),
                       f"Adding articles from {feed} (feed {feed_count} of {num_feeds})..."]
        for line in label_lines:
            log(line)


def skip_item(title, source, secondary_info):
    if settings.DIV_show_all_items or settings.DIV_show_skipped_items:
        log(f"Skipping '{title}' [{source}]...", indents=1)
        log(f"{secondary_info}", indents=2)


def add_item(item_dict):
    if settings.DIV_show_all_items or settings.DIV_show_added_items:
        debug_msg = f"Adding '{item_dict['title']}' [{item_dict['source']}] to cache..."
        log(debug_msg, indents=1)
