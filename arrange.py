# -*- coding: utf-8 -*-
# @Time    : 2018/5/21 14:27
# @Author  : 
# @简介    : 
# @File    : arrange.py


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


def query():
    ab_list = []
    conn = oracle_util.get_connection()
    sql = "select count(*), vehicle_num from tb_record1 group by vehicle_num"
    cursor = conn.cursor()
    cursor.execute(sql)
    tot = 0
    for items in cursor.fetchall():
        cnt, veh = items[0:2]
        if cnt >= 4:
            print veh, cnt
            tot += 1
            ab_list.append(veh)
    print tot
    return ab_list


def savepng():
    ab_list = ['AT9344', 'AT1385', 'ATE559', 'ATG185', 'AT5310',
               'ATD792', 'ATD669', 'AT9966', 'ATB533', 'ATB541',
               'ATD105', 'ATF286', 'ATF288', 'ATF299', 'ATF358',
               'AQT371', 'AT9501', 'ATA879', 'ATA888', 'ATC709',
               'ATE027', 'ATE077', 'AT8884', 'ATD326', 'ATD560',
               'ATD565', 'ATD568', 'ATD581', 'ATE792', 'ATF266']
    # ab_list = ['AT9501']
    # ab_list = query()
    conn = oracle_util.get_connection()
    for veh in ab_list:
        main_vehicle(conn, veh)


savepng()