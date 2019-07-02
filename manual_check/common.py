# -*- coding: utf-8 -*-
# @Time    : 2019/5/31 16:40
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : common.py


from math import radians, cos, sin, asin, sqrt
from time import clock
import numpy as np


def calc_dist(pt0, pt1):
    """
    计算两点距离
    :param pt0: [x0, y0]
    :param pt1: [x1, y1]
    :return: 
    """
    v0 = np.array(pt0)
    v1 = np.array(pt1)
    dist = np.linalg.norm(v0 - v1)
    return dist


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "__.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper
