# -*- coding: utf-8 -*-
# @Time    : 2019/3/7 17:31
# @Author  : yhdu@tongwoo.cn
# @简介    : 提取数据
# @File    : exact_data.py


import cx_Oracle
from datetime import datetime, timedelta


def main():
    db = cx_Oracle.connect("hz", "hz", "192.168.11.88/orcl")
    sql = "select vehicle_num, px, py, state, speed, speed_time" \
          " from tb_gps_1805 where speed_time > :1 and speed_time < :2"
    cursor = db.cursor()
    bt = datetime(2018, 5, 15, 12, 0, 0)
    et = bt + timedelta(hours=1)
    tup = (bt, et)
    cursor.execute(sql, tup)
    fp = open('1.csv', 'w')
    for item in cursor:
        vehicle_num, px, py, state, speed, speed_time = item[:]
        px, py = float(px), float(py)
        if 120.142225 < px < 120.177802 and 30.273166 < py < 30.293475:
            str_line = "{0},{1},{2},{3},{4},{5}\n".format(vehicle_num, px, py, state, speed, speed_time)
            fp.write(str_line)
    fp.close()


main()
