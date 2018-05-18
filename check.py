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

    jq_str = "120.120178,30.271966;120.129019,30.268186;120.1261,30.259364;120.131593,30.258178;120.137172,30.264183;120.150305,30.26144;120.158115,30.261588;120.163952,30.258622;120.171848,30.250615;120.171505,30.240012;120.158544,30.221769;120.152021,30.211089;120.132023,30.195289;120.111595,30.174441;120.09666,30.165685;120.090309,30.171918;120.077778,30.193138;120.077263,30.217468;120.086618,30.236675;120.0946,30.251802;120.106102,30.261069;120.120178,30.271966"
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
