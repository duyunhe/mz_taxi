# -*- coding: utf-8 -*-
# @Time    : 2018/6/13 14:17
# @Author  : 
# @简介    : 
# @File    : jq.py

from DBConn import oracle_util

try:
    conn = oracle_util.get_connection()
    cursor = conn.cursor()
    sql = "insert into tb_jq (px, py, seq) values(:1, :2, :3)"
    fp = open("./data/jq.txt")
    line = fp.readline().strip('\n').split(';')
    tup_list = []
    for i, item in enumerate(line):
        px, py = map(float, item.split(',')[0:2])
        tup = (px, py, i)
        tup_list.append(tup)
    cursor.executemany(sql, tup_list)
    conn.commit()
    conn.close()
except Exception as e:
    print e.message

