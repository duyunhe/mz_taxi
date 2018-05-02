# -*- coding: utf-8 -*-
# @Time    : 2018/5/2 10:23
# @Author  : 
# @简介    : 预处理轨迹
# @File    : pre.py

from DBConn import oracle_util
from datetime import datetime, timedelta
from geo import bl2xy, calc_dist
from time import clock
import os

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'


class TaxiData:
    def __init__(self, px, py, stime, state, speed, direction):
        self.px, self.py, self.stime, self.state, self.speed = px, py, stime, state, speed
        self.stop_index, self.direction = 0, direction

    def set_index(self, index):
        self.stop_index = index


def cmp1(data1, data2):
    if data1.stime > data2.stime:
        return 1
    elif data1.stime < data2.stime:
        return -1
    else:
        return 0


def get_data(conn, bt, vehi_num):
    str_bt = bt.strftime('%Y-%m-%d %H:%M:%S')
    end_time = bt + timedelta(hours=10)
    str_et = end_time.strftime('%Y-%m-%d %H:%M:%S')
    sql = "select px, py, speed_time, state, speed, direction from " \
          "TB_GPS_1803 t where speed_time >= to_date('{1}', 'yyyy-mm-dd hh24:mi:ss') " \
          "and speed_time < to_date('{2}', 'yyyy-MM-dd hh24:mi:ss')" \
          " and vehicle_num = '浙{0}'".format(vehi_num, str_bt, str_et)

    cursor = conn.cursor()
    cursor.execute(sql)
    trace = []

    last_point = None
    for item in cursor.fetchall():
        lng, lat = map(float, item[0:2])
        if 119 < lng < 121 and 29 < lat < 31:
            px, py = bl2xy(lat, lng)
            state = int(item[3])
            stime = item[2]
            speed = float(item[4])
            direction = float(item[5])
            taxi_data = TaxiData(px, py, stime, state, speed, direction)
            trace.append(taxi_data)
    # print len(trace)
    trace.sort(cmp1)
    print len(trace)

    new_trace = []
    for data in trace:
        cur_point = data
        if last_point is not None:
            dist = calc_dist([cur_point.px, cur_point.py], [last_point.px, last_point.py])
            del_time = (cur_point.stime - last_point.stime).total_seconds()
            if del_time < 5:
                continue
            elif data.speed != 0 and last_point.speed == data.speed and last_point.direction == data.direction:
                continue
            elif del_time * 40 < dist:
                continue
            else:
                new_trace.append(data)
        else:
            new_trace.append(data)
        last_point = cur_point
    print len(new_trace)
    return new_trace


def get_vehicle_mark(conn, mark):
    # type: (object, int) -> list
    sql = 'select rownum, t.vehicle_num from TB_VEHICLE t where rownum <= 1000'
    cursor = conn.cursor()
    cursor.execute(sql)
    veh_list = []
    for item in cursor.fetchall():
        rownum, veh = item[0:2]
        if rownum % 10 == mark:
            veh_list.append(veh)
    return veh_list


def main():
    conn = oracle_util.get_connection()
    bt = clock()
    vehicle = get_vehicle_mark(conn, 0)
    vehicle = ['AT8019']
    bd = datetime(2018, 3, 1, 8)
    for v in vehicle:
        print v
        data = get_data(conn, bd, v)
        print(len(data))
    et = clock()
    print et - bt

