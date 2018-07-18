# -*- coding: utf-8 -*-
# @Time    : 2018/6/22 14:43
# @Author  : 
# @简介    : 划分7*9=63个格子 算百分比——一个月数据
# @File    : taxi_63.py
from DBConn import oracle_util
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt, degrees
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'
veh_gps = {}
r = 6371


def get_vehicle(conn, mark):
    global veh_gps
    print mark
    cursor = conn.cursor()
    if mark != -1:
        sql = "select vehi_no from tb_vehicle where mark = '{0}'".format(mark)
    else:
        sql = "select vehi_no from tb_vehicle"
    cursor.execute(sql)
    veh_set = set()
    for item in cursor.fetchall():
        veh = item[0]
        veh_set.add(veh)
    veh_list = []
    for veh in veh_set:
        veh_list.append(veh)
    for i in veh_list:
        veh_gps[i[3:]] = []


def haversine(lon1, lat1, lon2, lat2):  # 经度1，纬度1，经度2，纬度2 （十进制度数）
    """ 
    Calculate the great circle distance between two points  
    on the earth (specified in decimal degrees) 
    """
    # 将十进制度数转化为弧度
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine公式
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # 地球平均半径，单位为公里
    return c * r * 1000

# print haversine(119.959883, 30.102263, 120.178182231, 30.102263)
# print haversine(119.959883, 30.102263, 119.959883+lon_d, 30.102263)
# print haversine(119.959883, 30.102263, 119.959883, 30.102263+lat_d)


def get_elon():  # 20999.9999553
    s_lon, s_lat = 119.959883, 30.102263
    s_lon, s_lat = map(radians, [s_lon, s_lat])
    t1 = sin(21.0/(2*r))
    t2 = cos(s_lat)
    dlon = 2*asin(sqrt((t1**2)/(t2**2)))
    e_lon = dlon + s_lon
    print degrees(e_lon)


def get_elat():  # 27000.0000002
    s_lon, s_lat = 119.959883, 30.102263
    s_lon, s_lat = map(radians, [s_lon, s_lat])
    e_lat = 27.0/r + s_lat
    print degrees(e_lat)

# get_elat()
# get_elon()


def get_area_dic():
    area_dic = {}
    for i in range(9):
        for t in range(7):
            area_dic[(t, i)] = 0
    # restore outside data
    area_dic[(-1, -1)] = 0
    return area_dic


def make_63():
    global veh_gps
    lon_d = (120.178182231 - 119.959883) / 7
    lat_d = (30.3450798336 - 30.102263) / 9
    s_lon, s_lat = 119.959883, 30.102263
    for i in veh_gps:
        vehi = i
        area_dic = get_area_dic()
        record = veh_gps[vehi]
        for gps in record:
            x = int((gps[0]-s_lon)/lon_d)
            y = int((gps[1]-s_lat)/lat_d)
            try:
                area_dic[(x, y)] += 1
            except KeyError:
                area_dic[(-1, -1)] += 1
        veh_gps[vehi] = area_dic


def get_data(conn):
    global veh_gps

    now = datetime.now()
    end_time = now + timedelta(days=-52)
    for i in range(1, 32):
        get_vehicle(conn, -1)
        str_bt = end_time.strftime('%Y-%m-{0} 00:00:00'.format(i))
        if i == 31:
            str_et = '2018-06-01 00:00:00'
        else:
            str_et = end_time.strftime('%Y-%m-{0} 00:00:00'.format(i+1))
        print str_bt, str_et
        sql = "select * from " \
              "TB_GPS_1805 t where speed_time >= to_date('{0}', 'yyyy-mm-dd hh24:mi:ss') " \
              "and speed_time < to_date('{1}', 'yyyy-mm-dd hh24:mi:ss')".format(str_bt, str_et)

        cursor = conn.cursor()
        cursor.execute(sql)

        for item in cursor:
            lng = item[5]
            lat = item[6]
            # if 119.959883 < lng < 120.178182231 and 30.102263 < lat < 30.3450798336:
            try:
                veh_gps[item[2][3:]].append([lng, lat])
            except Exception as e:
                continue
        make_63()
        insert_data(conn, str_bt)


def insert_data(conn, bt):
    global veh_gps
    cursor = conn.cursor()
    sql = "insert into tb_gps_cnt values(:1, :2, :3, :4, to_date(:5, 'yyyy-mm-dd hh24:mi:ss'))"
    tup_list = []
    for i in veh_gps:
        ve = i
        dic = veh_gps[ve]
        for t in dic:
            tup_list.append(('浙{0}'.format(ve), t[0], t[1], dic[t], bt))
    try:
        cursor.executemany(sql, tup_list)
    except Exception as e:
        print e.message
    conn.commit()


conn = oracle_util.get_connection()
get_data(conn)
