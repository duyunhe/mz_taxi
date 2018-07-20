# -*- coding: utf-8 -*-
# @Time    : 2018/7/6 17:42
# @Author  : 
# @简介    : 研究不同的区域对gps的影响
# @File    : rsch.py

from DBConn import oracle_util
import os
from datetime import datetime, timedelta
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'

conn = oracle_util.get_connection()


def proc_normal():
    """
    得到正常车辆
    :return: 
    """
    upd_sql = "update TB_VEHICLE set mark = 1 where vehi_no = :1"
    ab_set = set()
    sql = "select * from tb_record"
    cursor = conn.cursor()
    cursor.execute(sql)
    for item in cursor:
        veh = item[0]
        ab_set.add(veh)
    veh_set = set()
    sql = "select * from tb_vehicle"
    cursor = conn.cursor()
    cursor.execute(sql)
    for item in cursor:
        veh = item[0]
        veh_set.add(veh)
    n_set = veh_set - ab_set      # normal
    normal_list = []
    for veh in n_set:
        normal_list.append((veh, ))
    cursor.executemany(upd_sql, normal_list)
    conn.commit()


def get_normal():
    sql = "select * from tb_vehicle where mark = 1 and rownum < 300"
    cursor = conn.cursor()
    cursor.execute(sql)
    normal_set = set()
    for item in cursor:
        veh = item[0]
        normal_set.add(veh)
    return normal_set


def get_abnormal():
    """
    确切的模子车辆
    :return: 
    """
    veh_cnt = {}
    abnormal_set = set()
    sql = "select * from tb_record"
    cursor = conn.cursor()
    cursor.execute(sql)
    for item in cursor:
        veh = item[0]
        try:
            veh_cnt[veh] += 1
        except KeyError:
            veh_cnt[veh] = 1
    cnt = 0
    for veh, value in veh_cnt.iteritems():
        if value > 20:
            # print veh, value
            cnt += 1
            abnormal_set.add(veh)
    print cnt
    return abnormal_set


def get_record(veh):
    sql = "select gps_date from tb_record where vehicle_num = '{0}'".format(veh)
    cursor = conn.cursor()
    cursor.execute(sql)
    date_list = []
    for item in cursor:
        gps_date = item[0]
        date_list.append(gps_date)
    return date_list


def get_gps_cnt(veh):
    sql = "select map_row, map_col, cnt, dbtime from tb_gps_cnt where vehicle_num = '{0}'".format(veh)
    cursor = conn.cursor()
    cursor.execute(sql)
    gps_cnt_map = {}
    for item in cursor:
        row, col, cnt = map(int, item[0:3])
        gps_date = item[3].strftime('%Y-%m-%d')
        if row == -1 and col == -1:
            rid = 63
        else:
            rid = row * 7 + col
        try:
            gps_cnt_map[gps_date][rid] = cnt
        except KeyError:
            gps_cnt_map[gps_date] = [0] * 64
            gps_cnt_map[gps_date][rid] = cnt

    for date, gps_cnt in gps_cnt_map.iteritems():
        gps_cnt_sum = sum(gps_cnt)
        if gps_cnt_sum == 0:
            continue
        for i in range(64):
            gps_cnt[i] = float(gps_cnt[i]) / gps_cnt_sum
    return gps_cnt_map


def get_abnormal_table():
    mz_set = get_abnormal()
    table_list = []
    for veh in mz_set:
        print veh
        mz_date_list = get_record(veh)
        mz_gps_map = get_gps_cnt(veh)
        for date in mz_date_list:
            gps_cnt_table = mz_gps_map[date]
            table_list.append(gps_cnt_table)
    return table_list


def get_date_list(month):
    bt = datetime(2018, month, 1)
    date_list = []
    et = datetime(2018, month + 1, 1)
    while bt < et:
        date_list.append(bt.strftime('%Y-%m-%d'))
        bt += timedelta(days=1)
    return date_list


def get_normal_table():
    normal_set = get_normal()
    table_list = []
    for veh in normal_set:
        print veh
        date_list = get_date_list(5)
        gps_map = get_gps_cnt(veh)
        if gps_map is None:
            continue
        for date in date_list:
            gps_cnt_table = gps_map[date]
            table_list.append(gps_cnt_table)
    return table_list


get_normal_table()
