# -*- coding: utf-8 -*-
# @Time    : 2019/6/30 16:34
# @Author  : yhdu@tongwoo.cn
# @简介    :
# @File    : stat.py


import cx_Oracle
from collections import defaultdict
from datetime import timedelta, datetime


def check_3d(conn, bt):
    cur = conn.cursor()
    lt = bt - timedelta(days=2)
    sql = "select * from tb_mz1p where dbtime >= :1 and dbtime <= :2 order by dbtime"
    tup = (lt, bt)
    cur.execute(sql, tup)
    veh_list = defaultdict(list)
    for item in cur:
        veh, pset, dbtime = item[:]
        pids = pset.split(',')
        id_set = set()
        for pid in pids:
            id_set.add(pid)
        veh_list[veh].append([id_set, dbtime])

    tup_list = []
    for veh, id_list in veh_list.items():
        daily_time = {}
        daily_set = {}
        for pid in id_list:
            id_set, db_time = pid[:]
            idx = (db_time - lt).days
            daily_set[idx] = id_set
            daily_time[idx] = db_time

        try:
            pos_set = daily_set[0]
        except KeyError:
            pos_set = set()
        for i in range(1, 3):
            try:
                pos_set &= daily_set[i]
            except KeyError:
                pos_set = set()
        if len(pos_set) > 0:
            for pos in pos_set:
                tup_list.append((veh, pos, bt))
    sql = "insert into tb_mz3d values(:1,:2,:3)"
    cur.executemany(sql, tup_list)
    conn.commit()
    cur.close()


def delete_taxi(conn):
    sql = "delete from tb_mz_taxi"
    cur = conn.cursor()
    cur.execute(sql)
    sql = "delete from tb_mz3d"
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()


def check_taxi_day(conn, dt):
    cur = conn.cursor()
    set5p = set()
    sql = "select distinct(vehiclenum) from tb_mz5p where dbtime = :1"
    tup = (dt, )
    cur.execute(sql, tup)
    for item in cur:
        veh = item[0]
        set5p.add(veh)

    ft = dt + timedelta(days=3)
    # 前后三天都算
    # 假如后面三天中产生连续数据,则当天也计入内
    sql = "select distinct(vehiclenum) from tb_mz3d where dbtime >= :1 and dbtime < :2"
    set3d = set()
    tup = (dt, ft)
    cur.execute(sql, tup)
    for item in cur:
        veh = item[0]
        set3d.add(veh)

    sql = "select distinct(vehiclenum) from tb_mz10m where dbtime = :1"
    set10m = set()
    tup = (dt,)
    cur.execute(sql, tup)
    for item in cur:
        veh = item[0]
        set10m.add(veh)

    sql = "select distinct(vehiclenum) from tb_mz_ratio where dbtime = :1 and ratio >= 50"
    setr = set()
    tup = (dt,)
    cur.execute(sql, tup)
    for item in cur:
        veh = item[0]
        setr.add(veh)

    set_all = set3d & set5p & set10m & setr
    tup_list = []
    for veh in set_all:
        # print veh, dt
        tup_list.append((veh, dt))
    sql = "insert into tb_mz_taxi values(:1, :2)"
    cur.executemany(sql, tup_list)
    conn.commit()
    cur.close()


def st():
    conn = cx_Oracle.connect('hzgps_taxi/twkjhzjtgps@192.168.0.69/orcl')
    delete_taxi(conn)
    bt = datetime(2019, 5, 1)
    et = datetime(2019, 6, 1)
    dt = bt
    while dt < et:
        check_3d(conn, dt)
        check_taxi_day(conn, dt)
        dt += timedelta(days=1)
    conn.close()



