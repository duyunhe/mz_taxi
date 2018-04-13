# -*- coding: utf-8 -*-
# @Time    : 2018/4/11 13:54
# @Author  : 
# @简介    : 正常车辆鉴定
# @File    : normal.py

from DBConn import oracle_util
from datetime import datetime
from statis import get_area, process, get_stop_point
from read_map import get_dist, main_vehicle
import numpy as np


def get_vehicle(conn):
    cursor = conn.cursor()
    sql = "select vehicle_num from tb_vehicle where mark = 0"
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


def get_vehicle_from_gps(conn):
    cursor = conn.cursor()
    sql = "select vehicle_num from tb_gps_1709 where speed_time" \
          " >= to_date('2017-09-01 09:00:00', 'yyyy-mm-dd hh24:mi:ss') " \
          "and speed_time < to_date('2017-09-01 12:00:00', 'yyyy-MM-dd hh24:mi:ss') and rownum < 8000"
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


def get_data(conn, veh):
    cursor = conn.cursor()
    sql = "select speed_time from tb_gps_1709 where vehicle_num = '{0}'".format(veh)
    cursor.execute(sql)
    speed_list = []
    for item in cursor.fetchall():
        speed_list.append(item[0])
    cursor.close()
    print len(speed_list)


def save_veh(conn, veh_list):
    cursor = conn.cursor()
    sql = "delete from tb_vehicle"
    cursor.execute(sql)
    sql = "insert into tb_vehicle (vehicle_num, mark) values(:1, :2)"
    for veh in veh_list:
        last_num = int(veh[-1])
        tup = (veh, last_num % 2)
        cursor.execute(sql, tup)
    conn.commit()
    cursor.close()


def save_record(conn, tup_list):
    cursor = conn.cursor()
    sql = "insert into tb_record (vehicle_num, gps_count, stop_in_count, " \
          "stop_out_count, gps_in_per, gps_date, type) values(:1, :2, :3, :4, :5, :6, 0)"
    cursor.executemany(sql, tup_list)
    conn.commit()
    cursor.close()


def save_normal_veh(conn, veh_list):
    cursor = conn.cursor()
    for veh in veh_list:
        sql = "update tb_vehicle set mark = 0 where vehicle_num = '{0}'".format(veh)
        cursor.execute(sql)
    conn.commit()
    cursor.close()


def main():
    conn = oracle_util.get_connection()
    jq_area = get_area(conn)
    veh_list = get_vehicle_from_gps(conn)
    save_veh(conn, veh_list)
    return
    normal_list = []
    tup_list = []
    for veh in veh_list:
        print veh
        if veh != 'ATC536':
            continue
        rec_list = []
        for d in range(1, 5):
            begin_time = datetime(2017, 9, d, 8, 0, 0)
            str_bt = begin_time.strftime('%Y-%m-%d')
            taxi_trace = get_dist(conn, begin_time, veh)
            per, gps_cnt = process(taxi_trace, jq_area)
            stop_in, stop_out = get_stop_point(taxi_trace, jq_area)
            # if per > 30:
            #     print str_bt, "%.2f %d %d %d" % (per, gps_cnt, stop_in, stop_out)
            if gps_cnt > 180:
                rec_list.append(per)
                tup = (veh, gps_cnt, stop_in, stop_out, per, str_bt)
                tup_list.append(tup)

    # save_record(conn, tup_list)

main()


