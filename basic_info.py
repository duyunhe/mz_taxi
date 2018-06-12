# -*- coding: utf-8 -*-
# @Time    : 2018/6/12 14:45
# @Author  : 
# @简介    : 
# @File    : basic_info.py


import cx_Oracle
import time

conn = cx_Oracle.connect('hz', 'hz', '192.168.11.88:1521/orcl')
cursor = conn.cursor()
sql = "select vehi_no from tb_VEHICLE t"
cursor.execute(sql)
bt = time.clock()
for item in cursor.fetchall():
    pass
et = time.clock()
print et - bt
