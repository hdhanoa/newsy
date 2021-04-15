from newsy.cache import Cache

import newsy.settings as settings


cache = Cache()
# cache.build_from_feeds(settings.data_dir + settings.feeds_filename)
cache.build_from_file(settings.data_dir + settings.cache_filename)
cache.update(settings.data_dir + settings.feeds_filename)
cache.save_to_file(settings.data_dir + settings.cache_filename)
cache.get_all_neighbors()

