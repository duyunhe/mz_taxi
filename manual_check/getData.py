# -*- coding: utf-8 -*-
# @Time    : 2019/5/31 14:14
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : getData.py


from datetime import timedelta, datetime
import cx_Oracle
from time import clock
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'


class TaxiData:
    def __init__(self, veh, px, py, stime, state, speed):
        self.px, self.py, self.stime, self.state, self.speed = px, py, stime, state, speed
        self.veh = veh


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "fetch.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


@debug_time
def get_data(bt):
    conn = cx_Oracle.connect('mz/mz@192.168.11.88:1521/orcl')
    et = bt + timedelta(days=1)
    sql = "select vehicle_num, px, py, speed_time, state, speed from " \
          "hz.TB_GPS_1805 t where speed_time >= :1 and speed_time < :2"
    tup = (bt, et)
    cursor = conn.cursor()
    cursor.execute(sql, tup)
    trace = []

    for item in cursor.fetchall():
        lng, lat = map(float, item[1:3])
        if 119 < lng < 121 and 29 < lat < 31:
            veh = item[0]
            # px, py = bl2xy(lat, lng)
            state = int(item[4])
            stime = item[3]
            speed = float(item[5])
            # taxi_data = TaxiData(veh, lng, lat, stime, state, speed)
            # trace.append(taxi_data)
    # print len(trace)
    # trace.sort(cmp1)
    cursor.close()
    conn.close()
    return trace


def main():
    dt = datetime(2018, 5, 1)
    get_data(dt)


main()
