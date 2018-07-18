# -*- coding: utf-8 -*-
# @Time    : 2018/6/12 14:45
# @Author  : 
# @简介    : 
# @File    : basic_info.py

import cx_Oracle
import time
from geo import bl2xy, calc_dist
from read_map import show_map, draw_data, get_area, process, get_stop_point, label_entropy
from datetime import datetime
import numpy as np
from logistic_regression import predict, load_model
from abnormal import load_from_data, save_record


class TaxiData:
    def __init__(self, px, py, stime, state, speed):
        self.px, self.py, self.stime, self.state, self.speed = px, py, stime, state, speed
        self.stop_index = -1

    def set_index(self, index):
        self.stop_index = index


def cmp1(data1, data2):
    if data1.stime > data2.stime:
        return 1
    elif data1.stime < data2.stime:
        return -1
    else:
        return 0


def split_into_cars(data_list):
    """
    :param data_list: vehicle num, px, py, state, stime
    :return: taxi_trace_map
    """
    taxi_trace_map = {}
    for data in data_list:
        veh, lng, lat, state, speed, stime = data[0:6]
        px, py = bl2xy(lat, lng)
        taxi_data = TaxiData(px, py, stime, state, speed)
        try:
            taxi_trace_map[veh].append(taxi_data)
        except KeyError:
            taxi_trace_map[veh] = [taxi_data, ]
    return taxi_trace_map


def pre_trace(trace):
    trace.sort(cmp1)
    new_trace = []
    last_point = None
    for data in trace:
        cur_point = data
        if last_point is not None:
            dist = calc_dist([cur_point.px, cur_point.py], [last_point.px, last_point.py])
            del_time = (cur_point.stime - last_point.stime).total_seconds()
            if dist > 2000 and del_time < 60:
                continue
            elif del_time <= 5:
                continue
            else:
                new_trace.append(data)
        else:
            new_trace.append(data)
        last_point = cur_point
    return new_trace


def query_diary(date):
    weights = load_model('model.txt')
    conn = cx_Oracle.connect('hz', 'hz', '192.168.11.88:1521/orcl')
    jq_area = get_area(conn)
    cursor = conn.cursor()
    bt = time.clock()
    begin_time = datetime(2018, 5, date)
    print "date", date
    str_bt = begin_time.strftime('%Y-%m-%d 08:00:00')
    str_et = begin_time.strftime('%Y-%m-%d 20:00:00')

    sql = "select vehicle_num, px, py, state, speed, speed_time from TB_GPS_1805 t" \
          " where speed_time > to_date('{0}', 'yyyy-mm-dd HH24:mi:ss') " \
          "and speed_time < to_date('{1}', 'yyyy-mm-dd HH24:mi:ss')".format(str_bt, str_et)
    cursor.execute(sql)
    info_list = []
    for item in cursor.fetchall():
        info_list.append(item)
    et = time.clock()
    print "select costs", et - bt
    conn.close()
    bt = time.clock()
    trace_map = split_into_cars(info_list)
    et = time.clock()
    print et - bt
    bt = time.clock()

    tup_list = []
    for veh, trace in trace_map.iteritems():
        taxi_trace = pre_trace(trace)
        # taxi_trace = get_dist(conn, begin_time, veh)
        per, gps_cnt = process(taxi_trace, jq_area)
        if gps_cnt > 360:
            stop_in, stop_out, labels, X = get_stop_point(taxi_trace, jq_area)
            # labels, X = get_area_label(taxi_trace, jq_area)
            ent = label_entropy(labels)
            gps_time = begin_time.strftime("%Y-%m-%d")
            tup = (veh, gps_cnt, stop_in, stop_out, per, ent, gps_time)
            # print tup
            if ent > 0.25:
                tup_list.append(tup)

    if len(tup_list) > 0:
        data_mat = load_from_data(tup_list)
        ans = predict(data_mat, weights)
        n = np.shape(ans)[0]
        ans_list = []
        for i in range(n):
            if ans[i][0] == 1.0:
                print tup_list[i]
                tup = tup_list[i] + (int(ans[i][0]),)
                ans_list.append(tup)

    conn = cx_Oracle.connect('hz', 'hz', '192.168.11.88:1521/orcl')
    save_record(conn, ans_list)
    conn.close()
    et = time.clock()
    print et - bt


def main():
    for d in range(21, 32):
        query_diary(d)

main()