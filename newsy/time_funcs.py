import datetime
import newsy.settings as settings


def datetime_to_string(datetime_object):
    return datetime_object.strftime("%Y-%m-%d %H:%M:%S")


def string_to_datetime(datetime_string):
    return datetime.datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S")


def time_check(datetime_object):
    return item_age(datetime_object) / 3600 > settings.time_period_in_hours


def item_age(datetime_object):
    age = (datetime.datetime.now() - datetime_object).total_seconds()
    while age <= 0:
        age += 3600
    return age

def sort_by_time(item_dict, neighbors_list):
    unsorted_tuples = []
    for neighbor in neighbors_list:
        # if isinstance(item_dict[neighbor]["pub_date"], datetime.datetime):
        #     pub_date = datetime_to_string(item_dict[neighbor]["pub_date"])
        # else:
        #     pub_date = item_dict[neighbor]["pub_date"]
        unsorted_tuples.append([neighbor, item_age(item_dict[neighbor]["pub_date"])])
    sorted_tuples = sorted(unsorted_tuples, key=lambda x: x[1])
    return [x[0] for x in sorted_tuples]
