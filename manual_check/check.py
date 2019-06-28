# -*- coding: utf-8 -*-
# @Time    : 2019/5/31 16:34
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : check.py


import cx_Oracle
from getData import get_data, get_jq_points, get_jq_path, insert_pos_set, \
    insert_stay_point, insert_pos_rec, insert_ratio, delete_all, get_jq_points_from_db, insert_detail
from datetime import datetime, timedelta
from common import geo_distance, debug_time
import numpy as np
from collections import defaultdict
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
# from read_map import show_map
from geo import xy2bl, bl2xy, calc_dist
from matplotlib.path import Path
from sklearn.neighbors import KDTree
from apscheduler.schedulers.blocking import BlockingScheduler
import logging


NAME = 2
NEAR_DIST = 200
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
def check_5p(trace, tree, pt_list):
    rec_dict = defaultdict(list)
    last_pt = None
    bt, et = None, None
    emerge_rec = EmergeRecord()
    emerge_set = set()
    # kd-tree mode

    vec = [[data.px, data.py] for data in trace]
    dist, idx = tree.query(vec, k=1)

    for i, data in enumerate(trace):
        min_dist, sel_pt = dist[i][0], idx[i][0]
        if min_dist > NEAR_DIST:
            sel_pt = None
        if sel_pt is not None:
            if last_pt is None:
                last_pt = sel_pt
                bt = data.stime
        else:
            if last_pt is not None:
                et = data.stime
                rec_dict[last_pt].append([bt, et])
                last_pt = None
    # print "emerge"
    for idx, rec_list in rec_dict.items():
        name = pt_list[idx][NAME]
        if len(rec_list) >= EMG_CNT:
            # print name
            for rec in rec_list:
                tup = [idx, rec[0], rec[1]]
                # print name, rec[0], rec[1]
                emerge_rec.add_rec(tup)
        emerge_set.add(idx)
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
            if dist < 500 and dist < min_dist:
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


# @debug_time
def check_ratio(trace, path):
    pt_list = []
    for data in trace:
        pt = [data.px, data.py]
        pt_list.append(pt)
    res = path.contains_points(pt_list)
    all_cnt = len(res)
    cnt = 0
    # a = res[175]
    for r in res:
        if r:
            cnt += 1
    # print cnt, all_cnt
    try:
        ratio = round(100.0 * cnt / all_cnt, 1)
    except ZeroDivisionError:
        ratio = 0
    # print ratio, all_cnt
    return ratio


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


def print_stay_point(stay_pts, tree, path_list):
    stay_rec = {}
    if len(stay_pts) == 0:
        return stay_rec
    vec = [pt.coord for pt in stay_pts]
    dist, idx = tree.query(vec, k=1)
    sel_pts = []
    for i, sp in enumerate(stay_pts):
        min_dist, sel_pt = dist[i][0], idx[i][0]        # min dist & selected index
        x, y = sp.coord[:]
        if path_list[sel_pt].contains_point([x, y]):
            b, l = xy2bl(x, y)
            b = round(b, 6)
            l = round(l, 6)
            tup = [str(sel_pt), l, b]
            sel_pts.append(tup)
            # print sel_pt, pt_list[sel_pt][NAME]
            try:
                stay_rec[sel_pt][0] += 1
                stay_rec[sel_pt][1] += (sp.dpt_time - sp.arv_time).total_seconds()
            except KeyError:
                stay_rec[sel_pt] = [1, (sp.dpt_time - sp.arv_time).total_seconds()]
    insert_detail(sel_pts)
    return stay_rec


def check_pos_list(pos_list):
    pos_num = defaultdict(int)
    for pos_set in pos_list:
        for pos in pos_set:
            pos_num[pos] += 1
    for pos, num in pos_num.items():
        print pos, num


def check_3d(conn, bt):
    cur = conn.cursor()
    lt = bt - timedelta(days=2)
    sql = "select * from tb_mz1p where dbtime >= :1 and dbtime <= :2 order by dbtime"
    tup = (lt, bt)
    cur.execute(sql, tup)
    veh_list = defaultdict(list)
    for item in cur:
        veh, pset, dbtime = item[:]
        pids = pset.split(',')
        id_set = set()
        for pid in pids:
            id_set.add(pid)
        veh_list[veh].append([id_set, dbtime])

    for veh, id_list in veh_list.items():
        daily_time = {}
        daily_set = {}
        for pid in id_list:
            id_set, db_time = pid[:]
            idx = (db_time - lt).days
            daily_set[idx] = id_set
            daily_time[idx] = db_time

        tup_list = []
        try:
            pos_set = daily_set[0]
        except KeyError:
            pos_set = set()
        for i in range(1, 3):
            try:
                pos_set &= daily_set[i]
            except KeyError:
                pos_set = set()
        if len(pos_set) > 0:
            for pos in pos_set:
                tup_list.append((veh, pos, bt))
        sql = "insert into tb_mz3d values(:1,:2,:3)"
        cur.executemany(sql, tup_list)
        conn.commit()
    cur.close()


@debug_time
def calc_trace(dt, tree, pt_list, path, all_veh=True, path_list=None):
    trace_dict = get_data(dt, all_veh)
    for veh, trace in trace_dict.items():
        # 1. stay point
        # print veh
        pts = detect_stay_point(trace)
        stay_rec = print_stay_point(pts, tree, path_list)
        insert_stay_point(veh, stay_rec, dt)
        # draw_stay_points(pts, pt_list)
        ratio = check_ratio(trace, path)
        insert_ratio(veh, ratio, dt)
        # 2. emerge
        pos_rec, pos_set = check_5p(trace, tree, pt_list)
        insert_pos_rec(veh, pos_rec, dt)
        insert_pos_set(veh, pos_set, dt)
        # draw_data(trace)
        # plt.show()


def mean_coord(trace):
    xy_list = []
    for data in trace:
        xy_list.append([data.px, data.py])
    vec = np.array(xy_list)
    return np.mean(vec, axis=0)


# @debug_time
def detect_stay_point(trace, time_thread=600, dist_thread=100):
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
    delete_all()
    bt = datetime(2019, 6, 1)
    et = datetime(2019, 6, 10)
    dt = bt
    while dt < et:
        print dt
        calc_daily(dt)
        dt += timedelta(days=1)


def check_taxi_day(conn, dt):
    cur = conn.cursor()
    set5p = set()
    sql = "select distinct(vehiclenum) from tb_mz5p where dbtime = :1"
    tup = (dt, )
    cur.execute(sql, tup)
    for item in cur:
        veh = item[0]
        set5p.add(veh)

    ft = dt + timedelta(days=3)
    sql = "select distinct(vehiclenum) from tb_mz3d where dbtime >= :1 and dbtime < :2"
    set3d = set()
    tup = (dt, ft)
    cur.execute(sql, tup)
    for item in cur:
        veh = item[0]
        set3d.add(veh)

    sql = "select distinct(vehiclenum) from tb_mz10m where dbtime = :1"
    set10m = set()
    tup = (dt,)
    cur.execute(sql, tup)
    for item in cur:
        veh = item[0]
        set10m.add(veh)

    sql = "select distinct(vehiclenum) from tb_mz_ratio where dbtime = :1 and ratio >= 50"
    setr = set()
    tup = (dt,)
    cur.execute(sql, tup)
    for item in cur:
        veh = item[0]
        setr.add(veh)

    set_all = set3d & set5p & set10m & setr
    tup_list = []
    for veh in set_all:
        # print veh, dt
        tup_list.append((veh, dt))
    sql = "insert into tb_mz_taxi values(:1, :2)"
    cur.executemany(sql, tup_list)
    conn.commit()
    cur.close()


def calc_daily(dt, all_veh=True):
    path = get_jq_path("../data/jq.txt")
    # pt_list = get_jq_points("../data/mzc_jq.csv")
    pt_list, path_list = get_jq_points_from_db()
    pt_vec = [[pt[0], pt[1]] for pt in pt_list]
    tree = KDTree(pt_vec, leaf_size=2)
    calc_trace(dt, tree, pt_list, path, all_veh, path_list)
    # conn = cx_Oracle.connect('hzgps_taxi/twkjhzjtgps@192.168.0.69:1521/orcl')
    # check_3d(conn, dt)
    # check_taxi_day(conn, dt)
    # conn.close()


def main_check():
    bt = datetime(2019, 4, 1)
    et = datetime(2019, 5, 1)
    dt = bt
    while dt < et:
        print dt
        calc_daily(dt)
        dt += timedelta(days=1)


def work():
    # delete_all()
    now = datetime.now() - timedelta(days=1)
    dt = datetime(now.year, now.month, now.day)
    calc_daily(dt)


# delete_all()
main_check()
# if __name__ == '__main__':
#     logging.basicConfig()
#     scheduler = BlockingScheduler()
#     scheduler.add_job(work, 'cron', hour='0', minute='40', max_instances=10)
#     scheduler.start()
