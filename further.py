# -*- coding: utf-8 -*-
# @Time    : 2018/6/14 9:51
# @Author  : 
# @简介    : 对初步筛查后的车辆进行进一步的无监督学习
# @File    : further.py

from DBConn import oracle_util
import os
from read_map import TaxiData, cmp1
from geo import bl2xy, calc_dist
import time
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'
conn = oracle_util.get_connection()


def select():
    sql = "select vehicle_num from tb_record"
    cursor = conn.cursor()
    cursor.execute(sql)
    veh_cnt = {}
    for item in cursor.fetchall():
        veh = item[0]
        try:
            veh_cnt[veh] += 1
        except KeyError:
            veh_cnt[veh] = 1
    cursor.close()

    sorted_cnt = sorted(veh_cnt, key=lambda x: veh_cnt[x], reverse=True)
    # sorted_dict = map(lambda x: {x: veh_cnt[x]}, sorted_cnt)
    valid_list = []
    for veh in sorted_cnt:
        if veh_cnt[veh] > 4:
            valid_list.append(veh)
    return valid_list


def main():
    taxi_list = select()
    for taxi in taxi_list:
        check_veh(taxi)
        break


def split_trace(trace):



def check_veh(vehi_num):
    sql = "select vehicle_num, px, py, state, speed, speed_time" \
          " from tb_gps_1805 where vehicle_num = '{0}'".format(vehi_num)
    cursor = conn.cursor()
    cursor.execute(sql)
    bt = time.clock()
    trace = []
    for item in cursor.fetchall():
        veh, lng, lat, state, speed, stime = item[0:6]
        px, py = bl2xy(lat, lng)
        taxi_data = TaxiData(px, py, stime, state, speed)
        trace.append(taxi_data)
    et = time.clock()
    print et - bt
    print len(trace)
    trace.sort(cmp1)
    new_trace = []
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
    while True:
        time.sleep(1)


main()
