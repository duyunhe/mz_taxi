# -*- coding: utf-8 -*-
# @Time    : 2018/5/22 15:37
# @Author  : 
# @简介    : insert key areas collected from gps center manually
# @File    : area.py
import os
from DBConn import oracle_util
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'


def main():
    fp = open('mzc_jq.csv')
    idx = 0
    sql = "insert into tb_area (area_id, px, py, address) values(:1, :2, :3, :4)"
    tup_list = []
    for line in fp.readlines():
        item = line.strip('\n').split(',')
        if idx != 0:
            try:
                name = item[0]
                px, py = float(item[1]), float(item[2])
                tup = (idx, px, py, name)
                tup_list.append(tup)
            except ValueError as e:
                print e.message, idx
        idx += 1
    try:
        conn = oracle_util.get_connection()
        cursor = conn.cursor()
        cursor.executemany(sql, tup_list)
        conn.commit()
        conn.close()
    except Exception as e:
        print e.message


main()

