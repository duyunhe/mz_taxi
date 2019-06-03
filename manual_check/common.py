# -*- coding: utf-8 -*-
# @Time    : 2019/5/31 16:40
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : common.py


from math import radians, cos, sin, asin, sqrt
from time import clock


def geo_distance(lng1, lat1, lng2, lat2):
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    dlon = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    dist = 2 * asin(sqrt(a)) * 6371 * 1000
    return dist


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "__.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper
