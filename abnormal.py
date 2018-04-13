# -*- coding: utf-8 -*-
# @Time    : 2018/4/12 8:56
# @Author  : 
# @简介    : 
# @File    : abnormal.py

from DBConn import oracle_util
from datetime import datetime
from statis import get_area, process, get_stop_point
from read_map import get_dist, main_vehicle
from logistic_regression import predict, load_model
import numpy as np


def get_vehicle(conn):
    cursor = conn.cursor()
    sql = "select vehicle_num from tb_vehicle where mark = 1"
    cursor.execute(sql)
    veh_set = set()
    for item in cursor.fetchall():
        veh = item[0]
        veh_set.add(veh)
    veh_list = []
    for veh in veh_set:
        veh_list.append(veh)
    cursor.close()
    return veh_list


def save_record(conn, tup_list):
    cursor = conn.cursor()
    sql = "insert into tb_record (vehicle_num, gps_count, stop_in_count, " \
          "stop_out_count, gps_in_per, gps_date, type) values(:1, :2, :3, :4, :5, :6, 1)"
    cursor.executemany(sql, tup_list)
    conn.commit()
    cursor.close()


def load_from_data(record_list):
    data_list = []
    for data in record_list:
        stop_in, stop_out, per = map(float, data[2: 5])
        data_list.append([1.0, stop_in / 10, stop_out / 10, per / 100])
    data_mat = np.mat(data_list)
    return data_mat


def main():
    conn = oracle_util.get_connection()
    jq_area = get_area(conn)
    tup_list = []
    ab_list = get_vehicle(conn)
    print len(ab_list)
    # main_vehicle(conn, 'AT8240')
    # return
    for veh in ab_list:
        for d in range(1, 5):
            begin_time = datetime(2017, 9, d, 8, 0, 0)
            str_bt = begin_time.strftime('%Y-%m-%d')
            taxi_trace = get_dist(conn, begin_time, veh)
            per, gps_cnt = process(taxi_trace, jq_area)
            stop_in, stop_out = get_stop_point(taxi_trace, jq_area)
            # if per > 30:
            #     print str_bt, "%.2f %d %d %d" % (per, gps_cnt, stop_in, stop_out)
            if gps_cnt > 180:
                tup = (veh, gps_cnt, stop_in, stop_out, per, str_bt)
                tup_list.append(tup)

    data_mat = load_from_data(tup_list)
    weights = load_model('model.txt')
    ans = predict(data_mat, weights)
    n = np.shape(ans)[0]
    for i in range(n):
        if ans[i][0] == 1.0:
            print tup_list[i]


main()
