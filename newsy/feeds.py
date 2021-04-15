import json
import os
import time

import requests
from bs4 import BeautifulSoup

import newsy.settings as settings

# Constants

HTML5_TAGS_TO_REMOVE = ["header", "figure", "aside", "footer", "nav", "audio", "video", "footer",
                        "figcaption"]

OLD_HTML_TAGS_TO_REMOVE = ["head", "script", "noscript", "button", "style", "img", "code", "label"]

FILTERED_STRINGS = ["/#", "?source", "?utm_source", "?edition", "?il"]


def import_feeds(feeds_filepath):

    if os.path.isfile(feeds_filepath):
        with open(feeds_filepath, "r") as f:
            return json.load(f)
    else:
        # TO DO: Build tool to collect feeds from user.
        pass


def pull_text_by_tag(soup, tag):

    content = ""
    for item in soup.find_all(tag):
        content_to_add = item.get_text()
        if content_to_add[-1] != " ":
            content_to_add += " "
        if content_to_add not in content:
            content += content_to_add
    return content


def extract_content(html):

    soup = BeautifulSoup(html, 'html.parser')

    tags_to_remove = HTML5_TAGS_TO_REMOVE + OLD_HTML_TAGS_TO_REMOVE
    for tag_to_remove in tags_to_remove:
        for s in soup(tag_to_remove):
            s.extract()

    for x in soup.find_all("span", {"class": "rollover-people-block"}):
        x.extract()

    for x in soup.find_all():
        if len(x.get_text(strip=True)) == 0:
            x.extract()

    for unwrap_tag in ["a", "em", "span"]:
        for tag in soup(unwrap_tag):
            tag.unwrap()

    for li_tag in soup("li"):
        li_tag.wrap(soup.new_tag("p"))
        li_tag.unwrap()

    for x in soup.find_all():
        if len(x.get_text(strip=True).split(".")) < 2:
            x.extract()

    if len(soup.find_all("article")) == 1:
        article = soup.find("article")
    else:
        article = soup

    if len(article.find_all("p")) > 1:
        tag = "p"
    else:
        tag = "div"

    content = pull_text_by_tag(article, tag)

    return " ".join(content.split())


def is_forbidden(url):

    with open(settings.data_dir + settings.forbidden_url_dirs_filename) as f:
        forbidden_url_dirs = json.load(f)

    for forbidden_url_dir in forbidden_url_dirs:
        if f"/{forbidden_url_dir}/" in url:
            return True

    return False


def clean_url(url):

    for tag in FILTERED_STRINGS:
        if tag in url:
            return url.split(tag)[0]

    return url


def clean_title(title_string_from_feed):

    divider = " - "
    title = title_string_from_feed[:title_string_from_feed.rfind(divider) + 1]
    title = title[:title.rfind("| ")]
    title = " ".join(title.split())
    source = title_string_from_feed[title_string_from_feed.rfind(divider) + len(divider):]
    source = source.replace("The ", "")
    return title, source


def lex_url(lexology_url):
    time.sleep(1)
    r = requests.get(lexology_url)
    soup = BeautifulSoup(r.content, "html.parser")
    stem = soup.find("a", {"title": "View the original document this article came from"})["href"]
    print(stem)
    return "www.lexology.com" + stem
