# -*- coding: utf-8 -*-
# @Time    : 2018/4/16 14:43
# @Author  : 
# @简介    : 
# @File    : oracle_105.py
import cx_Oracle
import ConfigParser
from DBUtils.PooledDB import PooledDB


def get_connection():
    abs_file = __file__
    filename = abs_file[:abs_file.rfind("\\")] + '\config105.ini'
    cf = ConfigParser.ConfigParser()
    fp = open(filename)
    cf.readfp(fp)

    host = cf.get('db', 'host')
    port = int(cf.get('db', 'port'))
    pswd = cf.get('db', 'pswd')
    sid = cf.get('db', 'sid')
    user = cf.get('db', 'user')
    sql_settings = {'oracle': {'user': user,
                               'password': pswd,
                               'dsn': '{0}:{1}/{2}'.format(host, port, sid)}}
    pool = PooledDB(creator=cx_Oracle,
                    mincached=10,
                    maxcached=100,
                    **sql_settings['oracle'])
    db_conn = pool.connection()
    return db_conn

