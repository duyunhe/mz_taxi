# -*- coding: utf-8 -*-
# @Time    : 2019/7/1 10:29
# @Author  : yhdu@tongwoo.cn
# @简介    :
# @File    : feature.py


import cx_Oracle
import os
from collections import defaultdict
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'


class TaxiFeature:
    def __init__(self, dbtime=None, veh=""):
        self.dbtime = dbtime
        self.veh = veh
        self.stop_time = 0
        self.stop_count = 0
        self.emerge_count = 0
        self.d3_count = 0
        self.ratio = 0

    def set_stop_time(self, stop_time):
        self.stop_time = stop_time

    def set_stop_count(self, stop_count):
        self.stop_count = stop_count

    def set_emerge_count(self, emerge_count):
        self.emerge_count = emerge_count

    def set_day3_count(self, d3_count):
        self.d3_count = d3_count

    def set_ratio(self, ratio):
        self.ratio = ratio


def extract_feature_for_day(dt, total_dict):
    feature_dict = {}
    conn = cx_Oracle.connect("hzgps_taxi/twkjhzjtgps@192.168.0.69/orcl")
    cur = conn.cursor()

    # dt = datetime(2019, 5, 1)
    et = dt + timedelta(days=1)
    sql = "select vehiclenum, ratio, dbtime from tb_mz_ratio where dbtime >= :1 and dbtime < :2"
    cur.execute(sql, (dt, et))
    for item in cur:
        veh, ratio, dt = item[:]
        ratio = float(ratio) / 100
        feature = TaxiFeature(dt, veh)
        feature.set_ratio(ratio)
        feature_dict[veh] = feature

    sql = "select vehiclenum, sum(stoptime), sum(stopcount), dbtime from tb_mz10m" \
          " where dbtime >= :1 and dbtime < :2 group by vehiclenum, dbtime"
    cur.execute(sql, (dt, et))
    rec_list = []
    x_list, y_list = [], []
    for item in cur:
        veh_num, stop_time, stop_count, dt = item[:]
        x_list.append(stop_time)
        y_list.append(stop_count)
        rec_list.append(item[:])
        try:
            feature = feature_dict[veh_num]
        except KeyError:
            feature = TaxiFeature(dt)
        feature.set_stop_count(stop_count)
        feature.set_stop_time(stop_time)

    sql = "select vehiclenum, count(distinct(pointid)), dbtime from tb_mz5p where dbtime >= :1" \
          " and dbtime < :2 group by vehiclenum, dbtime"
    cur.execute(sql, (dt, et))
    for item in cur:
        veh_num, emerge_cnt, dt = item[:]
        try:
            feature = feature_dict[veh_num]
        except KeyError:
            feature = TaxiFeature(dt)
        feature.set_emerge_count(emerge_cnt)

    sql = "select vehiclenum, count(distinct(pointid)), dbtime from tb_mz3d where dbtime >= :1" \
          " and dbtime < :2 group by vehiclenum, dbtime"
    cur.execute(sql, (dt, et))
    for item in cur:
        veh, d3_cnt, dt = item[:]
        try:
            feature = feature_dict[veh]
        except KeyError:
            feature = TaxiFeature(dt)
        feature.set_day3_count(d3_cnt)

    cur.close()
    conn.close()
    # plt.plot(x_list, y_list, linestyle='', marker='+')
    # plt.show()
    for veh, feature in feature_dict.items():
        total_dict[veh].append(feature)


def extract_feature():
    ft = datetime(2019, 6, 1)
    bt = datetime(2019, 5, 1)
    dt = bt
    feature_dict = defaultdict(list)
    while dt < ft:
        print dt
        extract_feature_for_day(dt, feature_dict)
        dt += timedelta(days=1)
    return feature_dict


def check_veh():
    conn = cx_Oracle.connect("hzgps_taxi/twkjhzjtgps@192.168.0.69/orcl")
    cur = conn.cursor()
    veh_cnt = defaultdict(int)
    sql = "select * from tb_mz_taxi"
    cur.execute(sql)
    for item in cur:
        veh = item[0]
        veh_cnt[veh] += 1
    veh_list = []
    for veh, cnt in veh_cnt.items():
        if cnt >= 10:
            print veh
            veh_list.append(veh)
    cur.close()
    conn.close()
    return veh_list


def main():
    veh_list = check_veh()
    f_dict = extract_feature()
    for veh in veh_list:
        feature_list = f_dict[veh]
        pass


main()
