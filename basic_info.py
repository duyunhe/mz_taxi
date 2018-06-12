# -*- coding: utf-8 -*-
# @Time    : 2018/6/12 14:45
# @Author  : 
# @简介    : 
# @File    : basic_info.py

import cx_Oracle
import time


def split_into_cars(data_list):
    """
    :param data_list: vehicle num, px, py, state, stime
    :return: 
    """
    taxi_map = {}
    for data in data_list:
        veh, px, py, state, stime = data[0:5]
        tup = (px, py, state, stime)
        try:
            taxi_map[veh].append(tup)
        except KeyError:
            taxi_map[veh] = [tup,]
    return taxi_map


def main():
    conn = cx_Oracle.connect('hz', 'hz', '192.168.11.88:1521/orcl')
    cursor = conn.cursor()
    bt = time.clock()
    sql = "select vehicle_num, px, py, state, speed_time from TB_GPS_1805 t" \
          " where speed_time > to_date('2018-05-02 08:00:00', 'yyyy-mm-dd HH24:mi:ss') " \
          "and speed_time < to_date('2018-05-02 20:00:00', 'yyyy-mm-dd HH24:mi:ss')"
    cursor.execute(sql)
    info_list = []
    for item in cursor.fetchall():
        info_list.append(item)
    et = time.clock()
    print len(info_list)
    print et - bt
    bt = time.clock()
    dic = split_into_cars(info_list)
    et = time.clock()
    print et - bt


main()
