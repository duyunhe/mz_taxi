# -*- coding: utf-8 -*-
# @Time    : 2018/4/10 10:37
# @Author  : 
# @简介    : 
# @File    : check.py

from DBConn import oracle_util
from datetime import datetime, timedelta
import time
import numpy as np
import os
from geo import bl2xy
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'

conn = oracle_util.get_connection()


def main():
    sql = "select px, py from tb_area where mark = 0"
    cursor = conn.cursor()
    cursor.execute(sql)
    xy_list = []
    for item in cursor.fetchall():
        lng, lat = float(item[0]), float(item[1])
        px, py = bl2xy(lat, lng)
        xy_list.append([px, py])
    X = np.array(xy_list)
    db = DBSCAN(eps=80, min_samples=5).fit(X)

    labels = db.labels_
    x_dict = {}
    y_dict = {}
    label = set(labels)
    for t in label:
        x_dict[t] = []
        y_dict[t] = []
    for i in range(0, len(labels)):
        x_dict[labels[i]].append(X[:, 0][i])
        y_dict[labels[i]].append(X[:, 1][i])

    color = ['ro', 'bo', 'go', 'co', 'mo', 'yo', 'ko', 'rs', 'bs', 'gs', 'ms', 'y*', 'cs', 'ks', 'r^', 'g^', 'k^', 'c^',
             'm^', 'b^', 'yd', 'r*', 'b*', 'g*', 'm*', 'c*', 'k*', 'y^', 'b+', 'g+', 'c+', 'm+', 'k+', 'rp',
             'bp', 'gp', 'cp', 'yp', 'mp', 'kp', 'rd', 'r+', 'gd', 'cd', 'ys', 'kd', 'md', 'bd', 'rx', 'bx', 'gx', 'cx',
             'mx', 'yx', 'kx', 'r>', 'b>', 'g>', 'y>', 'm>', 'c>', 'k>', 'y.', 'k+']
    for n in x_dict:
        if n == -1:
            plt.plot(x_dict[n], y_dict[n], color[-1], alpha=0.3)
        elif n < 20:
            plt.plot(x_dict[n], y_dict[n], color[0])
    plt.show()


def insert():
    cursor = conn.cursor()
    sql = "delete from tb_jq"
    cursor.execute(sql)
    conn.commit()

    jq_str = "120.134506,30.262681;120.144377,30.266388;120.147038,30.26624;120.153561,30.261569;120.158281,30.262014;120.159741,30.259271;120.164204,30.258456;120.164976,30.251857;120.166178,30.248595;120.171585,30.246;120.171156,30.23903;120.169783,30.231837;120.169525,30.225756;120.170212,30.219748;120.168324,30.21426;120.160513,30.209439;120.147982,30.202985;120.141287,30.199647;120.133734,30.195048;120.1194,30.186219;120.108929,30.176871;120.102234,30.168931;120.096312,30.166779;120.085411,30.166557;120.073567,30.175016;120.061636,30.186442;120.05949,30.200092;120.063267,30.212554;120.060349,30.227091;120.055456,30.232727;120.06773,30.240809;120.075798,30.251635;120.087128,30.257714;120.100346,30.260902;120.105066,30.254897;120.112877,30.248595;120.119229,30.257195;120.12455,30.258011;120.125752,30.261421;120.131159,30.259642;120.134506,30.262681"
    pts = jq_str.split(';')
    sql = "insert into tb_jq (area_id, seq, px, py) values(0, :0, :1, :2)"

    idx = 0
    for pt in pts:
        px, py = map(float, pt.split(','))
        tup = (idx, px, py)
        idx += 1
        cursor.execute(sql, tup)
    conn.commit()


insert()
