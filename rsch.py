# -*- coding: utf-8 -*-
# @Time    : 2018/7/6 17:42
# @Author  : 
# @简介    : 研究不同的区域对gps的影响
# @File    : rsch.py

from DBConn import oracle_util
import os
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
            print veh, value
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


def get_gps_cnt(veh, date):
    sql = "select map_row, map_col, cnt from tb_gps_cnt where vehicle_num = '{0}' and dbtime" \
          " = to_date('{1}', 'yyyy-mm-dd')".format(veh, date)
    cursor = conn.cursor()
    cursor.execute(sql)
    gps_cnt = [0] * 64
    for item in cursor:
        row, col, cnt = map(int, item[0:3])
        if row == -1 and col == -1:
            rid = 63
        else:
            rid = row * 7 + col
        gps_cnt[rid] = cnt
    gps_cnt_sum = sum(gps_cnt)
    if gps_cnt_sum == 0:
        return gps_cnt[:-1]
    for i in range(64):
        gps_cnt[i] = float(gps_cnt[i]) / gps_cnt_sum
    return gps_cnt[:-1]


def main():
    mz_set = get_abnormal()
    for veh in mz_set:
        mz_date_list = get_record(veh)
        for date in mz_date_list:
            gps_area_cnt = get_gps_cnt(veh, date)
            flag = 0


get_normal()
