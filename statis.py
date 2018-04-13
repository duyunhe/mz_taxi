# -*- coding: utf-8 -*-
# @Time    : 2018/4/10 15:10
# @Author  : 
# @简介    : 统计
# @File    : statis.py

from DBConn import oracle_util
from read_map import read_xml, draw_map, get_dist, get_label
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from geo import bl2xy, xy2bl
from matplotlib.path import Path


def get_stop_point(trace, area):
    label = get_label(trace)
    sumx, sumy = {}, {}
    cnt = {}
    if label is None:
        return 0, 0
    n = len(label)
    for data in trace:
        if data.speed < 5:
            i = label[data.stop_index]
            if i == -1:
                continue
            try:
                sumx[i] += data.px
                sumy[i] += data.py
                cnt[i] += 1
            except KeyError:
                sumx[i], sumy[i], cnt[i] = data.px, data.py, 1

    cnt_in, cnt_out = 0, 0
    for key, value in cnt.items():
        px, py = sumx[key] / cnt[key], sumy[key] / cnt[key]
        if area.contains_point([px, py]):
            cnt_in += 1
        else:
            cnt_out += 1
    # print cnt_in, cnt_out,
    return cnt_in, cnt_out


def draw_area(conn):
    way, node, edge = read_xml('jq.xml')
    draw_map(way, node, edge)
    cursor = conn.cursor()
    sql = "select px, py from tb_jq order by seq"
    cursor.execute(sql)
    xy_list = []
    for item in cursor.fetchall():
        lng, lat = item[0:2]
        x, y = bl2xy(lat, lng)
        xy_list.append([x, y])
    x, y = map(list, zip(*xy_list))
    plt.plot(x, y, '-.')
    plt.show()


def get_area(conn):
    cursor = conn.cursor()
    sql = "select px, py from tb_jq order by seq"
    cursor.execute(sql)
    xy_list = []
    for item in cursor.fetchall():
        lng, lat = item[0:2]
        x, y = bl2xy(lat, lng)
        xy_list.append([x, y])

    path = Path(xy_list)
    return path


def process(trace, area):
    cnt = 0
    for data in trace:
        if area.contains_point([data.px, data.py]):
            cnt += 1
    in_per = -1
    if len(trace) != 0:
        in_per = float(cnt) / len(trace) * 100
    # print "%.2f %d" % (in_per, len(trace)),
    return in_per, len(trace)


def main_vehicle(vehi_num):
    print vehi_num
    jq = get_area()
    for d in range(1, 9):
        begin_time = datetime(2017, 10, d, 8, 0, 0)
        str_bt = begin_time.strftime('%Y-%m-%d')
        # print str_bt,
        taxi_trace = get_dist(begin_time, vehi_num)
        per, gps_cnt = process(taxi_trace, jq)
        cnt_in, cnt_out = get_stop_point(taxi_trace, jq)
        print str_bt
    for d in range(21, 31):
        begin_time = datetime(2017, 9, d, 8, 0, 0)
        str_bt = begin_time.strftime('%Y-%m-%d')
        # print str_bt,
        taxi_trace = get_dist(begin_time, vehi_num)
        per, gps_cnt = process(taxi_trace, jq)
        cnt_in, cnt_out = get_stop_point(taxi_trace, jq)
        print str_bt
    print 'over'


def main():
    abnormal = ['AT9344', 'AT1385', 'ATE559', 'ATG185', 'AT5310',
                'ATD792', 'ATD669', 'AT9966', 'ATB533', 'ATB541']

    for veh in abnormal:
        main_vehicle(veh)
    for i in range(2):
        print '====================================================='
    normal = ['ATD716', 'ATD799', 'AT4616', 'ATB090', 'AT1663',
              'AQT038', 'ATA069', 'ATG166', 'ATC201', 'ATG267']
    for veh in normal:
        main_vehicle(veh)



