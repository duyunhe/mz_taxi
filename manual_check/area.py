# -*- coding: utf-8 -*-
# @Time    : 2019/6/21 10:14
# @Author  : yhdu@tongwoo.cn
# @简介    :
# @File    : area.py

import xlrd
import numpy as np
import cx_Oracle
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'


def center_point(pt_list):
    pt_vec = np.array(pt_list)
    a = np.mean(pt_vec, axis=0)
    return a


def main():
    book = xlrd.open_workbook("mz.xls")
    sht = book.sheet_by_name("SQL Statement")
    row_num = sht.nrows
    conn = cx_Oracle.connect("hzgps_taxi/twkjhzjtgps@192.168.0.69/orcl")
    cursor = conn.cursor()
    sql = "delete from tb_mz_jq"
    cursor.execute(sql)
    conn.commit()
    sql = "insert into tb_mz_jq values(:1, :2, :3, :4)"
    for i in range(1, row_num):
        v = sht.cell_value(i, 4)
        items = v.split(';')
        pt_list = []
        for item in items:
            xyitem = item.split(',')[:]
            xy = map(float, xyitem)
            pt_list.append(xy)
        pt = center_point(pt_list)
        pid, name, lng, lat = i - 1, sht.cell_value(i, 2), pt[0], pt[1]
        print pid, name, lng, lat
        tup = (pid, name, lng, lat)
        cursor.execute(sql, tup)
    conn.commit()
    cursor.close()
    conn.close()


main()
