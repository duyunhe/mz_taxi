# -*- coding: utf-8 -*-
# @Time    : 2018/5/2 10:23
# @Author  : 
# @简介    : 预处理轨迹
# @File    : pre.py

# from DBConn import oracle_util
from datetime import datetime, timedelta
from geo import bl2xy, calc_dist
from time import clock
import matplotlib.pyplot as plt
from map_matching import read_xml, draw_map, draw_trace
import os

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'


class TaxiData:
    def __init__(self, px, py, stime, state, speed, direction, cstate):
        self.px, self.py, self.stime, self.state, self.speed = px, py, stime, state, speed
        self.stop_index, self.direction, car_state = 0, direction, cstate

    def set_index(self, index):
        self.stop_index = index


def cmp1(data1, data2):
    if data1.stime > data2.stime:
        return 1
    elif data1.stime < data2.stime:
        return -1
    else:
        return 0


def get_data_by_time(conn, begin_time, end_time, veh):
    """
    获取GPS数据
    :param conn: oracle连接 
    :param begin_time: 起始时间
    :param end_time: 结束时间
    :param veh: 车牌号
    :return: list of TaxiData
    """
    str_bt = begin_time.strftime('%Y-%m-%d %H:%M:%S')
    str_et = end_time.strftime('%Y-%m-%d %H:%M:%S')
    sql = "select px, py, speed_time, state, speed, direction, carstate from " \
          "TB_GPS_1709 t where speed_time >= to_date('{1}', 'yyyy-mm-dd hh24:mi:ss') " \
          "and speed_time < to_date('{2}', 'yyyy-MM-dd hh24:mi:ss')" \
          " and vehicle_num = '{0}'".format(veh, str_bt, str_et)
    # 存放到TaxiData中
    # 返回TaxiData的list
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        trace = []
        for item in cursor.fetchall():
            lng, lat = map(float, item[0:2])
            if 119 < lng < 121 and 29 < lat < 31:
                px, py = bl2xy(lat, lng)
                state = int(item[3])
                stime = item[2]
                speed = float(item[4])
                direction = float(item[5])
                car_state = int(item[6])
                taxi_data = TaxiData(px, py, stime, state, speed, direction, car_state)
                trace.append(taxi_data)
    except Exception as e:
        print e.message
        return []
    # print len(trace)
    trace.sort(cmp1)      # 排序
    print len(trace)
    return trace


def get_data(conn, bt, vehi_num):
    str_bt = bt.strftime('%Y-%m-%d %H:%M:%S')
    end_time = bt + timedelta(hours=16)
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
            elif last_point.speed == data.speed >= 5 and last_point.direction == data.direction:
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


def pre_process_data(trace):
    """
    预处理轨迹
    :param trace: list of TaxiData 
    :return: 处理后的轨迹: list of TaxiData
    """
    new_trace = trace
    return new_trace


def main():
    try:
        conn = oracle_util.get_connection()
        bt = clock()
        # vehicle = get_vehicle_mark(conn, 0)
        vehicle = ['AT5639']
        bd = datetime(2017, 9, 1, 10)
        ed = datetime(2017, 9, 1, 12)
        for v in vehicle:
            data = get_data_by_time(conn, bd, ed, v)
            modified_data = pre_process_data(data)
            draw_trace(modified_data)
        et = clock()
        print 'load data', et - bt
    except Exception as e:
        print e.message
    read_xml('hz.xml')
    draw_map()
    plt.show()


# main()


