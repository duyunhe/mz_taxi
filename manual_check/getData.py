# -*- coding: utf-8 -*-
# @Time    : 2019/5/31 14:14
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : getData.py


from datetime import timedelta, datetime
import cx_Oracle
from time import clock
import os
from collections import defaultdict
from geo import bl2xy
from matplotlib.path import Path
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'


class TaxiData:
    def __init__(self, veh, px, py, stime, state, speed):
        self.px, self.py, self.stime, self.state, self.speed = px, py, stime, state, speed
        self.veh = veh

    def __sub__(self, other):
        return (self.stime - other.stime).total_seconds()


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "fetch.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


def insert_stay_point(veh, st_rec, dbtime):
    if len(st_rec) == 0:
        return
    conn = cx_Oracle.connect('mz/mz@192.168.11.88:1521/orcl')
    sql = "insert into tb_mz10m values(:1,:2,:3,:4,:5)"
    cur = conn.cursor()
    tup_list = []
    for pt, rec in st_rec.items():
        tup_list.append([veh, str(pt), int(rec[1] / 60), rec[0], dbtime])
    cur.executemany(sql, tup_list)
    conn.commit()
    cur.close()
    conn.close()


def insert_ratio(veh, r, dbtime):
    conn = cx_Oracle.connect('mz/mz@192.168.11.88:1521/orcl')
    sql = "insert into tb_mz_ratio values(:1,:2,:3)"
    tup = (veh, r, dbtime)
    cur = conn.cursor()
    cur.execute(sql, tup)
    conn.commit()
    cur.close()
    conn.close()


def insert_jq_points():
    fp = open("../data/mzc_jq.csv")
    i = 0
    tup_list = []
    for line in fp.readlines():
        item = line.strip('\n').split(',')
        name, lng, lat = item[:]
        lng = float(lng)
        lat = float(lat)
        tup_list.append([i, name, lng, lat])
        i += 1
    fp.close()
    conn = cx_Oracle.connect('mz/mz@192.168.11.88:1521/orcl')
    sql = "insert into tb_mz_jq values(:1,:2,:3,:4)"
    cur = conn.cursor()
    cur.executemany(sql, tup_list)
    conn.commit()
    cur.close()
    conn.close()


def insert_pos_rec(veh, pos_rec, dbtime):
    conn = cx_Oracle.connect('mz/mz@192.168.11.88:1521/orcl')
    sql = "insert into tb_mz5p values(:1,:2,:3,:4,:5)"
    tup_list = []
    for rec in pos_rec.rec_list:
        pid, arv_time, dpt_time = rec[:]
        tup_list.append((veh, str(pid), arv_time, dpt_time, dbtime))
    cur = conn.cursor()
    cur.executemany(sql, tup_list)
    conn.commit()
    cur.close()
    conn.close()


def delete_all():
    conn = cx_Oracle.connect('mz/mz@192.168.11.88:1521/orcl')
    cur = conn.cursor()
    sql = "delete from tb_mz3d"
    cur.execute(sql)
    sql = "delete from tb_mz1p"
    cur.execute(sql)
    sql = "delete from tb_mz5p"
    cur.execute(sql)
    sql = "delete from tb_mz10m"
    cur.execute(sql)
    sql = "delete from tb_mz_ratio"
    cur.execute(sql)
    sql = "delete from tb_mz_taxi"
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


def insert_pos_set(veh, pos_set, dbtime):
    """
    :param veh
    :param pos_set: set of id
    :param dbtime
    :return: 
    """
    if len(pos_set) == 0:
        return
    conn = cx_Oracle.connect('mz/mz@192.168.11.88:1521/orcl')
    sql = "insert into tb_mz1p values(:1,:2,:3)"
    id_list = sorted(map(str, list(pos_set)))
    ptid = ",".join(id_list)
    tup = (veh, ptid, dbtime)
    cur = conn.cursor()
    cur.execute(sql, tup)
    conn.commit()
    cur.close()
    conn.close()


@debug_time
def get_data(bt, all_data=False):
    conn = cx_Oracle.connect('mz/mz@192.168.11.88:1521/orcl')
    et = bt + timedelta(hours=24)
    bt = bt + timedelta(hours=6)
    veh = "浙AT9501"
    sql = "select vehicle_num, px, py, speed_time, state, speed from " \
          "hz.TB_GPS_1805 t where speed_time >= :1 and speed_time < :2 and vehicle_num = :3" \
          " order by speed_time"
    sql_all = "select vehicle_num, px, py, speed_time, state, speed from " \
              "hz.TB_GPS_1805 t where speed_time >= :1 and speed_time < :2 and" \
              " (vehicle_num = '浙AT9501' or vehicle_num = '浙ATD568' or vehicle_num = " \
              "'浙ATD560' or vehicle_num = '浙AT4964') order by speed_time"
    tup = (bt, et, veh)
    tup_all = (bt, et)
    cursor = conn.cursor()
    if all_data:
        cursor.execute(sql_all, tup_all)
    else:
        print veh
        cursor.execute(sql, tup)
    trace_dict = defaultdict(list)

    for item in cursor.fetchall():
        lng, lat = map(float, item[1:3])
        if 119 < lng < 121 and 29 < lat < 31:
            veh = item[0]
            px, py = bl2xy(lat, lng)
            state = int(item[4])
            stime = item[3]
            speed = float(item[5])
            taxi_data = TaxiData(veh, px, py, stime, state, speed)
            trace_dict[veh].append(taxi_data)
    # print len(trace)
    # trace.sort(cmp1)
    cursor.close()
    conn.close()
    return trace_dict


def get_points(filename):
    point_list = []
    fp = open(filename, 'r')
    for line in fp.readlines():
        items = line.strip('\n').split('\t')
        lng, lat = map(float, items[:])
        x, y = bl2xy(lat, lng)
        point_list.append([x, y])
    fp.close()
    return point_list


def get_jq_points(filename):
    point_list = []
    fp = open(filename, 'r')
    for line in fp.readlines():
        items = line.strip('\n').split(',')
        name = items[0]
        lng, lat = map(float, items[1:])
        x, y = bl2xy(lat, lng)
        point_list.append([x, y, name])
    fp.close()
    return point_list


def get_jq_path(filename):
    xy_list = []
    with open(filename, 'r') as fp:
        line = fp.readline()
        coords = line.split(';')
        for coord in coords:
            lng, lat = map(float, coord.split(',')[:])
            x, y = bl2xy(lat, lng)
            xy_list.append([x, y])
    path = Path(xy_list)
    return path


def main():
    dt = datetime(2018, 5, 1)
    get_data(dt)


# insert_jq_points()
