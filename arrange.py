# -*- coding: utf-8 -*-
# @Time    : 2018/5/21 14:27
# @Author  : 
# @简介    : 
# @File    : arrange.py


import cx_Oracle
from DBConn import oracle_util
from read_map import main_vehicle


def delete():
    conn = oracle_util.get_connection()
    sql = "select t.vehicle_num, t.gps_date, rowid from TB_RECORD1 t"
    cursor = conn.cursor()
    cursor.execute(sql)
    rec_set = set()
    for items in cursor.fetchall():
        veh, gps_date, rowid = items[0:3]
        vid = veh + gps_date
        if vid not in rec_set:
            rec_set.add(vid)
        else:
            print veh, gps_date
            del_sql = "delete from tb_record1 where rowid = '{0}'".format(rowid)
            cursor.execute(del_sql)
    conn.commit()


def query(mark):
    ab_list = []
    conn = cx_Oracle.connect("lishui", "lishui", "192.168.11.88/orcl")
    sql = "select count(*), vehicle_num from tb_record1 where gps_date < '2018-03-20' group by vehicle_num "
    cursor = conn.cursor()
    cursor.execute(sql)
    # flag = 0
    for items in cursor.fetchall():
        cnt, veh = items[0:2]
        ldig = int(ord(veh[-1]) - ord('0'))
        if ldig != mark:
            continue
        if cnt >= 4:
            print veh, cnt
            ab_list.append(veh)
    cursor.close()
    conn.close()
    return ab_list


def save_png():
    # ab_list = ['AT9344', 'AT1385', 'ATE559', 'ATG185', 'AT5310',
    #            'ATD792', 'ATD669', 'AT9966', 'ATB533', 'ATB541',
    #            'ATD105', 'ATF286', 'ATF288', 'ATF299', 'ATF358',
    #            'AQT371', 'AT9501', 'ATA879', 'ATA888', 'ATC709',
    #            'ATE027', 'ATE077', 'AT8884', 'ATD326', 'ATD560',
    #            'ATD565', 'ATD568', 'ATD581', 'ATE792', 'ATF266']
    ab_list = ['ATG185']
    # ab_list = query(8)
    try:
        conn = cx_Oracle.connect("lishui", "lishui", "192.168.11.88/orcl")
    except Exception as e:
        print e.message
        return
    for veh in ab_list:
        main_vehicle(conn, veh)
    conn.close()

save_png()
