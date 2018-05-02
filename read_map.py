# -*- coding: utf-8 -*-
# @Time    : 2018/3/28 15:35
# @Author  : 
# @简介    : 
# @File    : read_map.py

import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from xml.etree import ElementTree as ET
from geo import bl2xy, xy2bl, calc_dist
from DBConn import oracle_util
import numpy as np
import math
from time import clock
from datetime import datetime, timedelta
import os
from matplotlib.path import Path
from pre import get_data, get_vehicle_mark


os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'

EDGE_ONEWAY = 3
EDGES = 2
EDGE_INDEX = 4
EDGE_LENGTH = 5
NODE_EDGELIST = 2
# conn = oracle_util.get_connection()

color = ['r-', 'b-', 'g-', 'c-', 'm-', 'y-', 'c-', 'r-', 'b-', 'brown', 'm--', 'y--', 'c--', 'k--', 'r:']
# region = {'primary': 0, 'secondary': 1, 'tertiary': 2,
#           'unclassified': 5, 'trunk': 3, 'service': 4, 'trunk_link': 6,
#           'primary_link': 7, 'secondary_link': 8, 'residential': 9}
region = {'primary': 0, 'secondary': 1, 'tertiary': 2, 'trunk': 3, 'unclassified': 5}
plt_color = ['r--', 'b--', 'g--', 'k--', 'm--', 'c--']


class TaxiData:
    def __init__(self, px, py, stime, state, speed):
        self.px, self.py, self.stime, self.state, self.speed = px, py, stime, state, speed
        self.stop_index = 0

    def set_index(self, index):
        self.stop_index = index


def cmp1(data1, data2):
    if data1.stime > data2.stime:
        return 1
    elif data1.stime < data2.stime:
        return -1
    else:
        return 0


def draw_map(way, node, edge):
    for i in way:
        pl = way[i]
        segid = []
        t = edge[pl['edge'][0]][0]
        segid.append(t)
        for e in pl['edge']:       # e: index
            segid.append(edge[e][1])
        x, y = [], []
        for idx in segid:
            x.append(node[idx][0])
            y.append(node[idx][1])
        try:
            c = color[region[pl['highway']]]
        except KeyError:
            continue
        plt.plot(x, y, c, alpha=0.5)


def read_xml(filename):
    """
    node {id:[dx,dy,[[edge0, n0], [edge1, n1]...[edge, node]]}
    edge [node_id0, node_id1, way_id, oneway(true or false), edge_index, edge_length]
    way {id:{'name':name, 'highway':highway, 'color':color, 'edge':[edge_list]}}
    edge_list: edge的列表
    :return: node, edge, way
    """
    tree = ET.parse(filename)
    node, way, edge = {}, {}, []

    p = tree.find('meta')
    nds = p.findall('node')
    for x in nds:
        node_dic = x.attrib
        dx, dy = bl2xy(float(node_dic['lat']), float(node_dic['lon']))
        node[node_dic['id']] = [dx, dy, []]
    wys = p.findall('way')
    for w in wys:
        way_dic = w.attrib
        wid = way_dic['id']
        node_list = w.findall('nd')
        way[wid] = {}
        oneway = False
        ref = way[wid]
        tag_list = w.findall('tag')
        for tag in tag_list:
            tag_dic = tag.attrib
            ref[tag_dic['k']] = tag_dic['v']
        if 'oneway' in ref:
            oneway = ref['oneway'] == 'yes'

        node_in_way = []
        for nd in node_list:
            node_dic = nd.attrib
            node_in_way.append(node_dic['ref'])
        last_nd = ''
        ref['edge'] = []
        for nd in node_in_way:
            if last_nd != '':
                edge_index = len(edge)
                ref['edge'].append(edge_index)
                # p0, p1 = node[last_nd][0:2], node[nd][0:2]
                edge_length = 0
                edge.append([last_nd, nd, wid, oneway, edge_index, edge_length])
            last_nd = nd

    for e in edge:
        n0, n1 = e[0], e[1]
        if e[EDGE_ONEWAY] is True:
            node[n0][EDGES].append([e, n1])
        else:
            node[n0][EDGES].append([e, n1])
            node[n1][EDGES].append([e, n0])

    return way, node, edge


def draw(trace, vehi_num, str_time):
    t0 = clock()
    way, node, edge = read_xml('jq.xml')
    t1 = clock()
    # print t1 - t0
    draw_map(way, node, edge)
    t2 = clock()
    # print t2 - t0
    plt.xlim(73126, 85276)
    plt.ylim(75749, 82509)
    plt.title(vehi_num + str_time)

    xy_list = []
    last_point = None
    idx = 0
    for data in trace:
        if 1 == 1:
            cur_point = [data.px, data.py]
            if last_point is not None:
                # dist = calc_dist(cur_point, last_point)
                # str_time = data.stime.strftime('%H:%M')
                if data.speed > 5:
                    continue
                xy_list.append(cur_point)
                # plt.text(data.px, data.py, "{0},{1}".format(idx, str_time))
                idx += 1
            last_point = cur_point

    # if len(xy_list) > 0:
    #     x, y = zip(*xy_list)
    #     plt.plot(x, y, 'k', marker='+', ls='None')
    X = np.array(xy_list)
    if len(xy_list) == 0:
        return
    x, y = zip(*xy_list)
    db = DBSCAN(eps=50, min_samples=15).fit(X)

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
            plt.plot(x_dict[n], y_dict[n], color[n])


def get_list_entropy(od_list, index_list):
    cnt = {}
    for idx in index_list:
        if idx == -1:
            continue
        try:
            cnt[idx] += 1
        except KeyError:
            cnt[idx] = 1
    target_index = []
    for o, d in od_list:
        if o == -1 and d != -1:
            i = d
        elif d == -1 and o != -1:
            i = o
        elif d == -1 and o == -1:
            i = -1
        else:
            if cnt[o] > cnt[d]:
                i = o
            else:
                i = d
        target_index.append(i)
    cnt = {}
    n = len(target_index)
    m = max(target_index) + 1
    for idx in target_index:
        if idx == -1:
            idx = m
            m += 1
        try:
            cnt[idx] += 1
        except KeyError:
            cnt[idx] = 1

    entropy = 0.0
    for key, value in cnt.items():
        p = float(value) / n
        entropy += -math.log(p) * p
    return entropy


def get_most(index_list):
    cnt = {}
    for idx in index_list:
        try:
            cnt[idx] += 1
        except KeyError:
            cnt[idx] = 0
    max_value, max_key = -1, -1
    for key, value in cnt.items():
        if value > max_value:
            max_key, max_value = key, value
    return max_key


def split_trace(trace, labels):
    stop_list = []
    bi, ei = -1, -1
    idx = 0
    for data in trace:
        if data.speed < 5:
            if bi == -1:
                bi = idx
            ei = idx
        else:
            if bi != -1:
                if ei - bi >= 5:
                    stop_list.append([bi, ei])
            bi = -1
        idx += 1
    trace_list = []
    lasti, last_index = 0, 0
    diary_index, od_index = [], []
    for stop in stop_list:
        bi, ei = stop[0], stop[1]
        stop_indexes = []
        for i in range(bi, ei + 1):
            stop_indexes.append(labels[trace[i].stop_index])
        cur_index = get_most(stop_indexes)
        diary_index.append(cur_index)
        if bi - lasti > 1:
            trace_list.append([trace[lasti: bi], [last_index, cur_index]])
            od_index.append([last_index, cur_index])
        lasti = ei + 1
        last_index = cur_index
    # entropy = get_list_entropy(od_index, diary_index)
    # print entropy
    idx = 0
    for trace, indexes in trace_list:
        print idx, trace[0].stime, trace[-1].stime, len(trace), indexes[0], indexes[1]
        idx += 1
    return trace_list


def get_dist(conn, bt, vehi_num):
    str_bt = bt.strftime('%Y-%m-%d %H:%M:%S')
    end_time = bt + timedelta(hours=12)
    str_et = end_time.strftime('%Y-%m-%d %H:%M:%S')
    sql = "select px, py, speed_time, state, speed from " \
          "TB_GPS_1709 t where speed_time >= to_date('{1}', 'yyyy-mm-dd hh24:mi:ss') " \
          "and speed_time < to_date('{2}', 'yyyy-MM-dd hh24:mi:ss')" \
          " and vehicle_num = '{0}'".format(vehi_num, str_bt, str_et)

    cursor = conn.cursor()
    cursor.execute(sql)
    trace = []

    last_point = None
    for item in cursor.fetchall():
        lng, lat = map(float, item[0:2])
        if 119 < lng < 121 and 29 < lat < 31:
            px, py = bl2xy(lat, lng)
            state = int(item[3])
            stime = item[2]
            speed = float(item[4])
            taxi_data = TaxiData(px, py, stime, state, speed)
            trace.append(taxi_data)
    # print len(trace)
    trace.sort(cmp1)

    new_trace = []
    for data in trace:
        cur_point = data
        if last_point is not None:
            dist = calc_dist([cur_point.px, cur_point.py], [last_point.px, last_point.py])
            del_time = (cur_point.stime - last_point.stime).total_seconds()
            if dist > 2000 and del_time < 60:
                continue
            elif del_time < 5:
                continue
            else:
                new_trace.append(data)
        else:
            new_trace.append(data)
        last_point = cur_point
    return new_trace


def mkdir(path):
    is_exist = os.path.exists(path)
    if not is_exist:
        os.makedirs(path)


def cov_xy(arr):
    n = arr.shape[0]
    if n == 0:
        return 0.0
    means = np.mean(arr, axis=0)
    meanx, meany = means[0:2]
    sumxy = 0.0
    for i in range(n):
        sumxy += (arr[i][0] - meanx) * (arr[i][1] - meany)
    return sumxy / (n - 1)


def label_entropy(label):
    if label is None:
        return 0
    n = np.shape(label)[0]
    cnt = {}
    ni = np.max(label)
    for i in range(n):
        if label[i] == -1:
            cnt[ni] = 1
            ni += 1
        else:
            try:
                cnt[label[i]] += 1
            except KeyError:
                cnt[label[i]] = 1
    p = 0
    for key, value in cnt.items():
        pi = float(value) / n
        p += -pi * np.log(pi)
    return p


def get_area_label(trace, area):
    xy_list = []
    for data in trace:
        if data.speed < 5 and area.contains_point([data.px, data.py]):
            xy_list.append([data.px, data.py])
    X = np.array(xy_list)
    if len(X) == 0:
        return None
    db = DBSCAN(eps=50, min_samples=15).fit(X)
    return db.labels_


def get_label(trace):
    xy_list = []
    idx = 0
    for data in trace:
        if data.speed < 5:
            data.set_index(idx)
            idx += 1
            xy_list.append([data.px, data.py])
    X = np.array(xy_list)
    if len(xy_list) == 0:
        return None
    db = DBSCAN(eps=50, min_samples=15).fit(X)
    return db.labels_


def save_area(conn, area_list):
    sql = "insert into tb_area (px, py, address, mark) values(:1,:2,:3, 0)"
    cursor = conn.cursor()
    cursor.executemany(sql, area_list)
    conn.commit()
    cursor.close()


def get_cluster_centers(trace, label):
    sumx, sumy = {}, {}
    cnt = {}
    if label is None:
        return
    n = len(label)
    for data in trace:
        if data.speed < 5:
            i = label[data.stop_index]
            if i == -1:
                continue
            try:
                sumx[i] += data.px
                sumy[i] += data.py
                cnt[i] += 1
            except KeyError:
                sumx[i], sumy[i], cnt[i] = data.px, data.py, 1
    area_list = []
    for key, value in cnt.items():
        px, py = sumx[key] / cnt[key], sumy[key] / cnt[key]
        lat, lng = xy2bl(px, py)
        # addr = geo2addr(lng, lat)
        # print key, lng, lat, addr
        # area_list.append((lng, lat, addr))
    # save_area(area_list)


def draw_data(trace):
    xy_list = []
    stop_list = []
    for data in trace:
        if data.speed < 5:
            stop_list.append([data.px, data.py])
        xy_list.append([data.px, data.py])
    x, y = zip(*xy_list)
    plt.plot(x, y, 'k--')
    x, y = zip(*stop_list)
    plt.scatter(x, y, c='b')


def draw_trace(trace, i):
    xy_list = []
    color_list = []
    for data in trace:
        xy_list.append([data.px, data.py])
        if data.speed < 5:
            color_list.append('peru')
            stime = data.stime.strftime('%M:%S')
            plt.text(data.px, data.py, stime)
        elif data.state == 0:
            color_list.append('g')
        else:
            color_list.append('crimson')

    btime = trace[0].stime.strftime('%H:%M:%S')
    etime = trace[-1].stime.strftime('%H:%M:%S')
    x, y = zip(*xy_list)
    plt.plot(x, y, plt_color[i % 6])
    plt.scatter(x, y, c=color_list)
    plt.text(x[0], y[0], btime)
    plt.text(x[-1], y[-1], etime)


def draw_trace_list(trace_list, bi, ei):
    way, node, edge = read_xml('jq.xml')
    draw_map(way, node, edge)
    for i in range(bi, ei + 1):
        draw_trace(trace_list[i][0], i)
    plt.xlim(73126, 85276)
    plt.ylim(75749, 82509)
    plt.show()


def get_stop_point(trace, area):
    label = get_label(trace)
    sumx, sumy = {}, {}
    cnt = {}
    if label is None:
        return 0, 0
    n = len(label)
    for data in trace:
        if data.speed < 5:
            i = label[data.stop_index]
            if i == -1:
                continue
            try:
                sumx[i] += data.px
                sumy[i] += data.py
                cnt[i] += 1
            except KeyError:
                sumx[i], sumy[i], cnt[i] = data.px, data.py, 1

    cnt_in, cnt_out = 0, 0
    for key, value in cnt.items():
        px, py = sumx[key] / cnt[key], sumy[key] / cnt[key]
        if area.contains_point([px, py]):
            cnt_in += 1
        else:
            cnt_out += 1
    # print cnt_in, cnt_out,
    return cnt_in, cnt_out


def get_area(conn):
    cursor = conn.cursor()
    sql = "select px, py from tb_jq order by seq"
    cursor.execute(sql)
    xy_list = []
    for item in cursor.fetchall():
        lng, lat = item[0:2]
        x, y = bl2xy(lat, lng)
        xy_list.append([x, y])

    path = Path(xy_list)
    return path


def process(trace, area):
    cnt = 0
    for data in trace:
        if area.contains_point([data.px, data.py]):
            cnt += 1
    in_per = -1

    if len(trace) != 0:
        in_per = float(cnt) / len(trace)
    # print "%.2f %d" % (in_per, len(trace)),
    return in_per, len(trace)


def main_vehicle(conn, vehi_num):
    jq_area = get_area(conn)
    print vehi_num
    # mkdir("./pic/{0}".format(vehi_num))
    for d in range(1, 5):
        begin_time = datetime(2017, 9, d, 8, 0, 0)
        str_bt = begin_time.strftime('%Y-%m-%d')
        fig1 = plt.figure(figsize=(12, 6))
        ax = fig1.add_subplot(111)
        taxi_trace = get_dist(conn, begin_time, vehi_num)
        # labels = get_area_label(taxi_trace, jq_area)
        # ent = label_entropy(labels)
        # get_cluster_centers(taxi_trace, labels)
        str_title = './pic/{0}/'.format(vehi_num) + vehi_num + ' ' + str_bt + '.png'
        # per, gps_cnt = process(taxi_trace, jq_area)
        # stop_in, stop_out = get_stop_point(taxi_trace, jq_area)
        # tup = (vehi_num, gps_cnt, stop_in, stop_out, per, ent, str_bt)
        # print tup
        draw(taxi_trace, vehi_num, str_bt)
        plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
        # plt.savefig(str_title, dpi=150)
        plt.show()
        # trace_list = split_trace(taxi_trace, labels)
        # for trace in trace_list:
        # draw_trace_list(trace_list, 14, 14)
        plt.close(fig1)
    print 'over'


def main():
    conn = oracle_util.get_connection()
    way, node, edge = read_xml('jq0.xml')
    draw_map(way, node, edge)
    begin_time = datetime(2018, 3, 4, 8)
    vehicle = ['ATF630']
    for veh in vehicle:
        taxi_trace = get_data(conn, begin_time, veh)
        draw_data(taxi_trace)



main()
plt.show()
