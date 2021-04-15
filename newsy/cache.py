import datetime as dt
import json
import re

import feedparser
import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from fuzzywuzzy import fuzz
import warnings

import newsy.debugger as debug
import newsy.settings as settings
import newsy.output as output2
import newsy.feeds as feeds
from newsy.preprocess import tokenize
from newsy.time_funcs import string_to_datetime, datetime_to_string, time_check, sort_by_time


class Cache:

    def __init__(self):
        self.items = {}
        self.n_items = 0
        self.url_hashes = set()
        self.title_hashes = set()
        self.content_hashes = set()
        self.content_dict = {}
        self.tfidf = TfidfVectorizer(tokenizer=tokenize, stop_words="english")
        self.tfs = None
        self.model_tf_idf = NearestNeighbors(metric="cosine", algorithm="auto")
        self.sorted_neighbors_lists = []
        self.neighbors_list_by_dist = []

    def add_item(self, item_id, item_dict, increment_item_count=True):
        debug.add_item(item_dict)
        self.url_hashes.add(hash(item_dict["link"]))
        self.title_hashes.add(hash(item_dict["title"]))
        self.content_hashes.add(hash(item_dict["content"]))
        self.items[item_id] = item_dict
        if increment_item_count:
            self.n_items += 1

    def build_from_feeds(self, feed_filepath):
        """Builds a cache based on a given dictionary of RSS feeds"""
        debug.header("Building cache from feeds...")

        runtime_start = dt.datetime.now()
        added_items_count = 0
        items_skipped_count = 0
        feed_count = 0
        feed_dict = feeds.import_feeds(feeds_filepath=feed_filepath)
        num_feeds = len(feed_dict)

        for feed in feed_dict:
            feed_count += 1
            debug.feed_label(feed, feed_count, num_feeds)
            rss_url = f"https://news.google.com/rss/search?q=when:" \
                      f"{settings.time_period_in_hours}h" \
                      f"+allinurl:{feed_dict[feed]}&ceid=US:en&hl=en-US&gl=US"
            d = feedparser.parse(rss_url)

            for entry in d.entries:

                # Get title
                title, source = feeds.clean_title(entry.title)

                # Get link
                url = feeds.clean_url(entry.link)

                if feeds.is_forbidden(url) or hash(url) in self.url_hashes or hash(title) in self.title_hashes:
                    debug.skip_item(title, source, url)
                    items_skipped_count += 1
                    continue

                # Get publication date
                pub_date = dt.datetime(*entry.published_parsed[:6])

                # Get content
                headers = {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
                                  "like Gecko) Chrome/51.0.2704.103 Safari/537.36"
                }
                try:
                    r = requests.get(url, headers=headers)
                except:
                    debug.skip_item(title, source, url)
                    items_skipped_count += 1
                    continue
                content = feeds.extract_content(r.content)
                content = content.encode("ascii", "ignore")
                content = content.decode()

                if hash(content) in self.content_hashes:
                    debug.skip_item(title, source, url)
                    items_skipped_count += 1
                    continue

                # Get keywords
                # keywords = preprocess(content)

                # Add entry to cache.
                item_dict = {"title": title,
                             "source": source,
                             "link": url,
                             "pub_date": pub_date,
                             "content": content
                             }
                self.add_item(item_id=self.n_items, item_dict=item_dict)
                added_items_count += 1
        run_time = (dt.datetime.now() - runtime_start).seconds
        debug.footer(f"Build complete in {run_time} seconds!",
                     f"{added_items_count} items added — {items_skipped_count} items skipped")

    def build_from_single_rss(self, rss_url):
        """Builds a cache based on a given RSS feed"""
        debug.header("Building cache from single RSS feed...")

        runtime_start = dt.datetime.now()
        added_items_count = 0
        items_skipped_count = 0

        d = feedparser.parse(rss_url)

        for entry in d.entries:
            # Get title
            title = entry.title
            source = entry.author

            # Get link
            url = feeds.lex_url(entry.link)

            if feeds.is_forbidden(url) or hash(url) in self.url_hashes or hash(
                    title) in self.title_hashes:
                debug.skip_item(title, source, url)
                items_skipped_count += 1
                continue

            # Get publication date
            pub_date = dt.datetime(*entry.published_parsed[:6])

            # Get content
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
                              "like Gecko) Chrome/51.0.2704.103 Safari/537.36"
            }
            try:
                r = requests.get(url, headers=headers, )
            except:
                debug.skip_item(title, source, url + " (unable to connect)")
                items_skipped_count += 1
                continue
            content = feeds.extract_content(r.content)
            content = content.encode("ascii", "ignore")
            content = content.decode()

            if hash(content) in self.content_hashes:
                debug.skip_item(title, source, url)
                items_skipped_count += 1
                continue

            # Get keywords
            # keywords = preprocess(content)

            # Add entry to cache.
            item_dict = {"title": title,
                         "source": source,
                         "link": url,
                         "pub_date": pub_date,
                         "content": content
                         }
            self.add_item(item_id=self.n_items, item_dict=item_dict)
            added_items_count += 1
        run_time = (dt.datetime.now() - runtime_start).seconds
        debug.footer(f"Build complete in {run_time} seconds!",
                     f"{added_items_count} items added — {items_skipped_count} items skipped")

    def build_from_file(self, cache_filepath):
        debug.header("Building cache from file...")

        runtime_start = dt.datetime.now()
        with open(cache_filepath, "r") as f:
            import_dict = json.load(f)
        self.n_items = import_dict["information"]["n_items"]
        cache_dict = import_dict["cache"]
        imported_items_count = 0
        skipped_items_count = 0
        for key in cache_dict:
            pub_date = string_to_datetime(cache_dict[key]["pub_date"])
            if time_check(pub_date):
                debug.skip_item(cache_dict[key]['title'], cache_dict[key]['source'],
                                cache_dict[key]['pub_date'])
                skipped_items_count += 1
            else:
                item_dict = {"title": cache_dict[key]["title"],
                             "source": cache_dict[key]["source"],
                             "link": cache_dict[key]["link"],
                             "pub_date": pub_date,
                             "content": cache_dict[key]["content"]
                             }
                self.add_item(item_id=int(key), item_dict=item_dict, increment_item_count=False)
                imported_items_count += 1
        run_time = (dt.datetime.now() - runtime_start).seconds
        debug.footer(f"Build complete in {run_time} seconds!",
                     f"{imported_items_count} items added — {skipped_items_count} items skipped")

    def update(self, feeds_filepath):
        self.clean()
        self.build_from_feeds(feed_filepath=feeds_filepath)

    def clean(self):
        debug.header("Cleaning cache...")

        runtime_start = dt.datetime.now()
        count_items_removed = 0
        for key in self.items:
            item_dict = self.items[key]
            if time_check(item_dict["pub_date"]):
                if settings.DIV_show_all_items or settings.DIV_show_removed_items:
                    debug.log(f"Removing '{item_dict['title']}' [{item_dict['source']}]...",
                              indents=1)
                del self.items[key]
                count_items_removed += 1
        run_time = (dt.datetime.now() - runtime_start).seconds
        debug.footer(f"Cleaning complete in {run_time} seconds!",
                     f"{count_items_removed} items removed")

    def save_to_file(self, filepath):
        debug.header(f"Exporting cache to '{filepath}'...")

        runtime_start = dt.datetime.now()

        # Build JSON-compatible dict for cache items
        cache_dict = {}
        for key in self.items:
            item_dict = self.items[key]
            # if isinstance(item_dict["pub_date"], dt.datetime):
            #     pub_date = datetime_to_string(item_dict["pub_date"])
            # else:
            #     pub_date = item_dict["pub_date"]

            cache_dict[key] = {"title": item_dict["title"],
                               "source": item_dict["source"],
                               "link": item_dict["link"],
                               "pub_date": datetime_to_string(item_dict["pub_date"]),
                               "content": item_dict["content"]
                               }

        # Store cache info (e.g., n_items)
        export_dict = {"information": {"n_items": self.n_items},
                       "cache": cache_dict
                       }

        # Export cache.
        with open(filepath, "w") as f:
            json.dump(export_dict, f, indent=4)
        run_time = (dt.datetime.now() - runtime_start).seconds
        debug.footer(f"Export complete in {run_time} seconds!")

    def build_cluster_dict(self):
        for key in self.items:
            letters_only = re.sub('[^a-zA-Z]', ' ', self.items[key]["content"])
            words = letters_only.lower().split()
            self.content_dict[key] = ' '.join(words)
        return self.content_dict

    def vectorize(self):
        debug.header("Vectorizing cache contents...")

        runtime_start = dt.datetime.now()
        if not self.content_dict:
            self.build_cluster_dict()
        warnings.filterwarnings("ignore", category=UserWarning,
                                module='sklearn.feature_extraction.text')
        self.tfs = self.tfidf.fit_transform(self.content_dict.values())
        self.model_tf_idf.fit(self.tfs)
        run_time = (dt.datetime.now() - runtime_start).seconds
        debug.footer(f"Vectorization complete in {run_time} seconds!")

    def get_neighbors(self, query_item_id):

        if self.tfs is None:
            self.vectorize()
        indices = self.model_tf_idf.radius_neighbors(self.tfs[query_item_id],
                                                     settings.max_item_dist, sort_results=True)[1]
        return {list(self.content_dict.keys())[x] for x in np.asarray(indices[0])}

    def get_all_neighbors(self):
        self.vectorize()

        debug.header("Identifying similar items...")

        runtime_start = dt.datetime.now()
        for i in range(len(self.items)):
            neighbors = self.get_neighbors(i)
            self.sorted_neighbors_lists.append(neighbors)
            self.neighbors_list_by_dist.append(neighbors)
        self.sorted_neighbors_lists.sort(key=len)
        non_duplicate_neighbors = []
        for i in range(len(self.sorted_neighbors_lists)):
            query = self.sorted_neighbors_lists.pop(0)
            if any([fuzz.partial_token_set_ratio(query, x) > settings.max_item_similarity for x in
                    self.sorted_neighbors_lists]):
                continue
            non_duplicate_neighbors.append(query)
        run_time = (dt.datetime.now() - runtime_start).seconds
        debug.footer(f"Identification complete in {run_time} seconds!")
        debug.divider()

        for neighbor in sorted(non_duplicate_neighbors, key=len, reverse=True):
            if len(neighbor) > 3:
                # items_dict.summarize_neighbor_titles(list(neighbor))
                # neighbor = list(neighbor)
                neighbor = sort_by_time(self.items, neighbor)
                output2.topic(self.items, neighbor)
                output2.summary(self.items, neighbor)
                output2.neighbors(self.items, neighbor)
                print()
                output2.divider()

        # print(items_dict.neighbors_list_by_dist)
