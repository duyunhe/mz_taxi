# -*- coding: utf-8 -*-
# @Time    : 2018/4/12 8:56
# @Author  : 
# @简介    : 
# @File    : abnormal.py

from DBConn import oracle_util
from datetime import datetime
from read_map import get_dist, main_vehicle, get_area, process, get_stop_point, get_area_label, label_entropy
from logistic_regression import predict, load_model
import numpy as np
import time


def get_vehicle(conn, mark):
    print mark
    cursor = conn.cursor()
    sql = "select vehicle_num from tb_vehicle where mark = {0}".format(mark)
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
    sql = "insert into tb_record1 (vehicle_num, gps_count, stop_in_count, " \
          "stop_out_count, gps_in_per, stop_in_entropy, gps_date, type) values(:1, :2, :3, :4, :5, :6, :7, :8)"
    cursor.executemany(sql, tup_list)
    conn.commit()
    cursor.close()


def load_from_data(record_list):
    data_list = []
    for data in record_list:
        stop_in, stop_out, per, ent = map(float, data[2: 6])
        data_list.append([1.0, stop_in / 10, stop_out / 10, per])
    data_mat = np.mat(data_list)
    return data_mat


def load_from_txt():
    veh_set = set()
    veh_list = []
    fp = open('look.txt')
    for line in fp.readlines():
        if line[0] != '(':
            continue
        item = line.lstrip('(').split(',')
        veh = item[0][1:-1]
        if veh not in veh_set:
            veh_list.append(veh)
        veh_set.add(veh)
    return veh_list


def main():
    conn = oracle_util.get_connection()
    jq_area = get_area(conn)

    ab_list = get_vehicle(conn, 0)
    # ab_list = ['AT9344', 'AT1385', 'ATE559', 'ATG185', 'AT5310',
    #            'ATD792', 'ATD669', 'AT9966', 'ATB533', 'ATB541',
    #            'ATD105', 'ATF286', 'ATF288', 'ATF299', 'ATF358',
    #            'AQT371', 'AT9501', 'ATA879', 'ATA888', 'ATC709',
    #            'ATE027', 'ATE077', 'AT8884', 'ATD326', 'ATD560',
    #            'ATD565', 'ATD568', 'ATD581', 'ATE792', 'ATF266']
    print len(ab_list)
    weights = load_model('model.txt')
    cnt = 0

    for veh in ab_list:
        bt = time.clock()
        # print veh
        tup_list = []
        cnt += 1
        if cnt % 10 == 0:
            print cnt
        for d in range(20, 32):
            begin_time = datetime(2018, 3, d, 8, 0, 0)
            str_bt = begin_time.strftime('%Y-%m-%d')
            taxi_trace = get_dist(conn, begin_time, veh, jq_area)
            per, gps_cnt = process(taxi_trace, jq_area)
            if gps_cnt > 360:
                stop_in, stop_out, ent = get_stop_point(taxi_trace, jq_area)
                # labels = get_area_label(taxi_trace, jq_area)
                # ent = label_entropy(labels)
                if ent > 0.15:
                    tup = (veh, gps_cnt, stop_in, stop_out, per, ent, str_bt)
                    tup_list.append(tup)
        mz_flag = 0
        if len(tup_list) > 0:
            data_mat = load_from_data(tup_list)
            ans = predict(data_mat, weights)
            n = np.shape(ans)[0]
            ans_list = []
            overcnt = 0
            for i in range(n):
                if ans[i][0] == 1.0:
                    overcnt += 1
                # print tup_list[i], ans[i][0]
                    mz_flag = 1
                    tup = tup_list[i] + (int(ans[i][0]),)
                    ans_list.append(tup)
            if overcnt >= 5:
                print veh
            if mz_flag:
                save_record(conn, ans_list)
        # main_vehicle(conn, ab_list[0])
        et = time.clock()
        # print et - bt
    conn.close()

main()
