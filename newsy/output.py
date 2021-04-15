import datetime
import textwrap

import newsy.settings as settings
import newsy.summarize as summarize
from newsy.time_funcs import item_age


def timestamp():

    if settings.OSE_show_timestamp:
        return f"[{datetime.datetime.now()}] "
    return ""


def rem_output_len():

    return settings.TW_wrapping_width - len(timestamp())


def divider():
    divider_lines = [timestamp() + "*" * rem_output_len(),
                     ""
                     ]
    for line in divider_lines:
        print(line)


def wrap(text, width, initial_indents=0, subsequent_indents=0):

    lines = textwrap.wrap(text, width - 4 * (initial_indents + subsequent_indents),
                          initial_indent="\t" * initial_indents,
                          subsequent_indent="\t" * subsequent_indents)

    for line in lines:
        print(timestamp() + line)


def neighbors(items_dict, neighbors_list):

    for i in range(len(neighbors_list)):

        item_id = neighbors_list[i]

        title = items_dict[item_id]["title"]
        if settings.OSE_show_source_in_title:
            title += f" [{items_dict[item_id]['source']}]"

        if settings.OSE_show_item_age_in_title:
            age = item_age(items_dict[item_id]['pub_date'])
            if age >= 3600:
                age_string = f"{round(age / 3600, 2)} hours ago"
            else:
                age_string = f"{round(age / 60, 2)} minutes ago"
            title += f" [{age_string}]"

        url = items_dict[item_id]["link"]

        if settings.OIV_show_item_titles:

            title_string = f"{i + 1}:\t{title}"

            if settings.TW_wrap_item_titles or settings.TW_wrap_all_output:
                wrap(title_string, rem_output_len(), initial_indents=1,
                     subsequent_indents=2)
            else:
                print(timestamp() + "\t" + title_string)

        if settings.OIV_show_urls:

            if settings.TW_wrap_urls or settings.TW_wrap_all_output:
                wrap(url, rem_output_len(), initial_indents=3, subsequent_indents=3)
            else:
                print(timestamp() + "\t" * 4 + url)


def summary(items_dict, neighbors_list):

    if settings.OIV_show_summary:

        runtime_start = datetime.datetime.now()
        summary_string = summarize.content(items_dict, neighbors_list)

        if summary_string[-1] != " ":
            summary_string += " "

        if settings.DIV_show_all_items or settings.DIV_show_summary_generation_time:
            runtime = (datetime.datetime.now() - runtime_start).seconds
            summary_string += f"(Generated in {runtime} seconds)"

        if settings.TW_wrap_summary or settings.TW_wrap_all_output:
            wrap(summary_string, rem_output_len())
        else:
            print(timestamp() + summary_string)

    print(timestamp())


def topic(items_dict, neighbors_list):

    if settings.OIV_show_topic:

        # topic_summary = summarize.multistage_summarizer(items_dict, neighbors_list, "title")
        # topic_summary = summarize.field_from_neighbors(items_dict, neighbors_list, "title")
        # topic_summary = summarize.abstractive_summarizer(topic_summary)
        topic_string = summarize.topic(items_dict, neighbors_list).upper()

        if settings.TW_wrap_topic or settings.TW_wrap_all_output:
            wrap(topic_string, rem_output_len())
        else:
            print(timestamp() + topic_string)

    print(timestamp())
