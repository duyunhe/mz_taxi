# -*- coding: utf-8 -*-
# @Time    : 2019/5/31 16:34
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : check.py


from getData import get_data, get_jq_points, get_jq_path
from datetime import datetime, timedelta
from common import geo_distance, debug_time
import numpy as np
from collections import defaultdict
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
# from read_map import show_map
from geo import xy2bl, bl2xy, calc_dist
from matplotlib.path import Path


NAME = 2
NEAR_DIST = 100
STAY_DURING = 600
EMG_CNT = 5


class StayPoint(object):
    def __init__(self, arv_time, dpt_time, coord):
        self.arv_time, self.dpt_time, self.coord = arv_time, dpt_time, coord


class StayRecord(object):
    """
    停留10分钟以上的记录[时间，点id]
    """
    def __init__(self):
        self.rec_list = []

    def add_rec(self, rec):
        self.rec_list.append(rec)


class EmergeRecord(object):
    """
    出现5次以上的记录
    """
    def __init__(self):
        self.rec_list = []

    def add_rec(self, rec):
        self.rec_list.append(rec)


def check_pt(trace, pt_list):
    # print len(trace)
    rec_list = []
    for data in trace:
        min_dist, sel_pt = 1e10, None
        for i, pt in enumerate(pt_list):
            dist = calc_dist([data.px, data.py], [pt[0], pt[1]])
            if dist < min_dist:
                min_dist, sel_pt = dist, i
        if min_dist < 100:
            print min_dist, sel_pt
        if min_dist < 50:
            rec_list.append([sel_pt, data.stime])
    return rec_list


# @debug_time
def check_5p(trace, pt_list):
    rec_dict = defaultdict(list)
    last_pt = None
    bt, et = None, None
    emerge_rec = EmergeRecord()
    emerge_set = set()
    for data in trace:
        min_dist, sel_pt = 1e10, None
        for i, pt in enumerate(pt_list):
            dist = calc_dist([data.px, data.py], [pt[0], pt[1]])
            if dist < NEAR_DIST and dist < min_dist:
                min_dist, sel_pt = dist, i
        if sel_pt is not None:
            if last_pt is None:
                last_pt = sel_pt
                bt = data.stime
        else:
            if last_pt is not None:
                et = data.stime
                rec_dict[last_pt].append([bt, et])
                last_pt = None
    print "emerge"
    for idx, rec_list in rec_dict.items():
        name = pt_list[idx][NAME]
        if len(rec_list) >= EMG_CNT:
            # print name
            for rec in rec_list:
                tup = [name, rec[0], rec[1]]
                print name, rec[0], rec[1]
                emerge_rec.add_rec(tup)
        emerge_set.add(name)
    return emerge_rec, emerge_set


# @debug_time
def check_10m(trace, pt_list):
    stay_pt = None
    bt, et = None, None
    rec_dict = defaultdict(list)
    stay_rec = StayRecord()
    for data in trace:
        min_dist, sel_pt = 1e10, None
        for i, pt in enumerate(pt_list):
            dist = calc_dist([data.px, data.py], [pt[0], pt[1]])
            if dist < NEAR_DIST and dist < min_dist:
                min_dist, sel_pt = dist, i
        if sel_pt is not None:
            if stay_pt is None:
                stay_pt = sel_pt
                bt = data.stime
        else:
            if stay_pt is not None:
                et = data.stime
                during = int((et - bt).total_seconds())
                if during > STAY_DURING:
                    rec_dict[stay_pt].append(during)
                stay_pt = None
    print "stay"
    for idx, rec_list in rec_dict.items():
        name = pt_list[idx][NAME]
        print name
        tup = [name, round(sum(rec_list) / 60, 1), len(rec_list)]
        stay_rec.add_rec(tup)
    return stay_rec


def check_ratio(trace):
    path = get_jq_path("../data/jq.txt")
    pt_list = []
    for data in trace:
        pt = [data.px, data.py]
        pt_list.append(pt)
    res = path.contains_points(pt_list)
    all_cnt = len(res)
    cnt = 0
    a = res[175]
    for r in res:
        if r:
            cnt += 1
    # print cnt, all_cnt
    try:
        ratio = 1.0 * cnt / all_cnt
    except ZeroDivisionError:
        ratio = 0
    print ratio, all_cnt


def cluster(trace):
    trs = []
    for data in trace:
        trs.append([data.px, data.py])
    X = np.array(trs)
    db = DBSCAN(eps=50, min_samples=10).fit(X)

    x_dict = {}
    y_dict = {}
    labels = db.labels_
    for t in labels:
        x_dict[t] = []
        y_dict[t] = []
    for i in range(len(labels)):
        x_dict[labels[i]].append(X[:, 0][i])
        y_dict[labels[i]].append(X[:, 1][i])
    # x, y = x_dict[7][50], y_dict[7][50]
    # lat, lng = xy2bl(x, y)
    # print lng, lat
    flag = 0


def draw_data(trace):
    xy_list = []
    stop_list = []
    for data in trace:
        if data.speed < 5:
            stop_list.append([data.px, data.py])
            # plt.text(data.px, data.py, '{0}'.format(data.direction))
        xy_list.append([data.px, data.py])
    x, y = zip(*xy_list)
    plt.plot(x, y, linestyle='', marker='+', alpha=0.1)


def draw_stay_points(stay_pts, pt_list):
    xy_list = []
    for sp in stay_pts:
        xy_list.append([sp.coord[0], sp.coord[1]])
        min_dist, sel_pt = 1e10, None
        for i, pt in enumerate(pt_list):
            dist = calc_dist(sp.coord, [pt[0], pt[1]])
            if dist < min_dist:
                min_dist, sel_pt = dist, [i, pt]
        if min_dist < 200:
            lat, lng = xy2bl(sp.coord[0], sp.coord[1])
            print min_dist, sel_pt[0], sel_pt[1][NAME], lng, lat, sp.arv_time, sp.dpt_time
            plt.text(sp.coord[0] + 20, sp.coord[1] + 20, "{0}".format(sel_pt[0]))
        else:
            lat, lng = xy2bl(sp.coord[0], sp.coord[1])
            # print lng, lat
    x, y = zip(*xy_list)
    plt.plot(x, y, linestyle='', marker='o', alpha=1, color='r')


def print_stay_point(stay_pts, pt_list):
    for sp in stay_pts:
        min_dist, sel_pt = 1e10, None
        for pt in pt_list:
            dist = calc_dist(sp.coord, [pt[0], pt[1]])
            if dist < min_dist:
                min_dist, sel_pt = dist, pt
        if min_dist < 100:
            print sel_pt[NAME], min_dist


def check_pos_list(pos_list):
    pos_num = defaultdict(int)
    for pos_set in pos_list:
        for pos in pos_set:
            pos_num[pos] += 1
    for pos, num in pos_num.items():
        print pos, num


@debug_time
def calc_trace(dt, pt_list):
    trace_dict = get_data(dt)
    set_list = []
    for veh, trace in trace_dict.items():
        pts = detect_stay_point(trace)
        # print_stay_point(pts, pt_list)
        draw_stay_points(pts, pt_list)
        check_ratio(trace)
        _, pos_set = check_5p(trace, pt_list)
        set_list.append(pos_set)
        check_10m(trace, pt_list)
        # cluster(trace)
        draw_data(trace)
        plt.show()
    return set_list[0]


def mean_coord(trace):
    xy_list = []
    for data in trace:
        xy_list.append([data.px, data.py])
    vec = np.array(xy_list)
    return np.mean(vec, axis=0)


def detect_stay_point(trace, time_thread=300, dist_thread=100):
    n = len(trace)
    i = 0
    stay_pts = []
    while i < n:
        j = i + 1
        while j < n:
            if calc_dist([trace[i].px, trace[i].py], [trace[j].px, trace[j].py]) > dist_thread:
                if trace[j] - trace[i] > time_thread:
                    sp = StayPoint(trace[i].stime, trace[j].stime, mean_coord(trace[i:j + 1]))
                    stay_pts.append(sp)
                break
            j += 1
        i = j + 1
    return stay_pts


def main():
    pt_list = get_jq_points("../data/mzc_jq.csv")
    dt = datetime(2018, 5, 1)
    ft = dt + timedelta(weeks=1)
    pos_list = []
    while dt < ft:
        print dt
        pos_set = calc_trace(dt, pt_list)
        pos_list.append(pos_set)
        dt += timedelta(days=1)
    check_pos_list(pos_list)
    # show_map()
    # plt.show()


main()
