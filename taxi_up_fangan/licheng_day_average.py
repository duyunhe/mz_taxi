# -*- coding: utf-8 -*-
# @Time    : 2018/7/20 14:12
# @Author  : 
# @简介    : 1 以日为统计基础，每个月初，统计每辆出租车上个月日平均营运里程
#           2 以日为统计基础，每个月初，统计每辆出租车上个月日平均营运单次
# @File    : licheng_day_average.py
from DBConn import oracle_util
from datetime import datetime
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'


def get_data():
    conn = oracle_util.get_connection()
    cursor = conn.cursor()
    sql = "select * from TB_CITIZEN_2018 where shangche>=to_date('2018-05-01 00:00:00','yyyy-mm-dd hh24:mi:ss') " \
          "and shangche<to_date('2018-06-01 00:00:00','yyyy-mm-dd hh24:mi:ss') order by shangche desc"
    cursor.execute(sql)
    record = {}
    for i in cursor:
        try:
            record[i[4]].append(i[10])
        except Exception, e:
            record[i[4]] = [i[10]]
    return record


def insert_data(lc_dict, cnt_dict):
    now = datetime.now()
    st = now.strftime("%Y-%m-%d %H:%M:%S")
    conn = oracle_util.get_connection()
    cursor = conn.cursor()
    sql = "insert into TB_DAY_AVE_LC values(:1, :2, :3, to_date(:4,'yyyy-mm-dd hh24:mi:ss'), :5)"
    tup_list = []
    for i in lc_dict:
        tup_list.append((i, float('%.2f' % (lc_dict[i]/310.00)), cnt_dict[i]/31, st, 5))
    cursor.executemany(sql, tup_list)
    conn.commit()
    cursor.close()
    conn.close()


def ave_lic_cnt():
    cnt_dic = {}
    lic_rec = get_data()
    for i in lic_rec:
        record = lic_rec[i]
        jc = 0
        for t in record:
            try:
                jc = int(t) + jc
            except Exception, e:
                print i
        lic_rec[i] = jc
        cnt_dic[i] = len(record)
    insert_data(lic_rec, cnt_dic)


ave_lic_cnt()
