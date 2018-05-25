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
import sys
from area import get_key_area
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

color = ['k-', 'k-', 'k-', 'k-', 'k-', 'k-', 'k-', 'k-', 'k-', 'brown', 'm--', 'y--', 'c--', 'k--', 'r:']
# region = {'primary': 0, 'secondary': 1, 'tertiary': 2,
#           'unclassified': 5, 'trunk': 3, 'service': 4, 'trunk_link': 6,
#           'primary_link': 7, 'secondary_link': 8, 'residential': 9}
region = {'primary': 0, 'secondary': 1, 'tertiary': 2, 'trunk': 3, 'unclassified': 5}
plt_color = ['r', 'b', 'g', 'gold', 'm', 'c']


class TaxiData:
    def __init__(self, px, py, stime, state, speed):
        self.px, self.py, self.stime, self.state, self.speed = px, py, stime, state, speed
        self.stop_index = -1

    def set_index(self, index):
        self.stop_index = index


def cmp1(data1, data2):
    if data1.stime > data2.stime:
        return 1
    elif data1.stime < data2.stime:
        return -1
    else:
        return 0


def calc_ms(size):
    ans = (math.log10(float(size) / 20) + 1) * 8
    ans = max(8.0, ans)
    return ans


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
        plt.plot(x, y, c, alpha=0.1)


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


def draw_traj(trace, i):
    s0 = trace[0].stime.strftime('%H:%M')
    s1 = trace[-1].stime.strftime('%H:%M')
    trace_list = []
    for data in trace:
        trace_list.append([data.px, data.py])
    x, y = zip(*trace_list)
    plt.plot(x, y, plt_color[i % 6], marker='+', ls='--', alpha=0.75, ms=6)
    # plt.text(trace[0].px, trace[0].py, s0)
    # plt.text(trace[-1].px, trace[-1].py, s1)


def draw_labels(x_dict, y_dict):
    draw_colors = ['crimson', 'darkorange', 'gold', 'lawngreen', 'c', 'deepskyblue', 'violet']
    markers = ['o', 'H']
    xmean, ymean, sz = [], [], []
    for n, x_list in x_dict.iteritems():
        if n != -1:
            vec = np.array(x_list)
            x = np.mean(vec)
            xmean.append(x)
    for n, y_list in y_dict.iteritems():
        if n != -1:
            vec = np.array(y_list)
            y = np.mean(vec)
            ymean.append(y)
            sz.append(len(y_list))
    for n in x_dict:
        if n != -1:
            plt.plot(xmean[n], ymean[n], color=draw_colors[n % 7], marker=markers[(n / 7) % 2], ms=calc_ms(sz[n]))


def draw(trace, vehi_num, str_time, labels, X):
    way, node, edge = read_xml('jq.xml')
    draw_map(way, node, edge)

    plt.xlim(68638, 86954)
    plt.ylim(75749, 84721)
    plt.title(vehi_num + ' ' + str_time)

    xy_list = []
    last_point = None
    idx = 0
    all_list = []
    for data in trace:
        if 1 == 1:
            cur_point = [data.px, data.py]
            all_list.append(cur_point)
            if last_point is not None:
                # dist = calc_dist(cur_point, last_point)
                # str_time = data.stime.strftime('%H:%M')
                if data.speed > 5:
                    continue
                xy_list.append(cur_point)
                # plt.text(data.px, data.py, "{0},{1}".format(idx, str_time))
                idx += 1
            last_point = cur_point

    if len(xy_list) == 0:
        return
    # x, y = zip(*xy_list)
    # db = DBSCAN(eps=50, min_samples=15).fit(X)
    #
    # labels = db.labels_
    x_dict = {}
    y_dict = {}
    label = set(labels)
    for t in label:
        x_dict[t] = []
        y_dict[t] = []
    for i in range(0, len(labels)):
        x_dict[labels[i]].append(X[:, 0][i])
        y_dict[labels[i]].append(X[:, 1][i])

    colors = ['ro', 'yo', 'co', 'go', 'mo', 'rp', 'yp', 'cp', 'gp', 'mp', 'ms', 'y*', 'cs', 'ks', 'r^', 'g^', 'k^', 'c^',
             'm^', 'b^', 'yd', 'r*', 'b*', 'g*', 'm*', 'c*', 'k*', 'y^', 'b+', 'g+', 'c+', 'm+', 'k+', 'rp',
             'bp', 'gp', 'cp', 'yp', 'mp', 'kp', 'rd', 'r+', 'gd', 'cd', 'ys', 'kd', 'md', 'bd', 'rx', 'bx', 'gx', 'cx',
             'mx', 'yx', 'kx', 'r>', 'b>', 'g>', 'y>', 'm>', 'c>', 'k>', 'y.', 'k+']

    draw_labels(x_dict, y_dict)
    # for n in x_dict:
    #     if n != -1:
    #         plt.plot(x_dict[n], y_dict[n], colors[n % 10], markersize=8)


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
    """
    通过计算得到的营运常驻点，对当日轨迹进行分隔
    :param trace: list(Taxi_Data)
    :param labels: dbscan label
    :return: trace_list
    """
    if len(trace) == 0:
        return
    trace_list = []
    stop_list, period_list = [], []
    # step 1
    # 提取stop点
    for i, data in enumerate(trace):
        if data.stop_index != -1:
            l = labels[data.stop_index]
            if l != -1:
                stop_list.append([l, i])
    # step 2
    # 合并相近stop点，形成(label, begin_index, end_index)三元组stop list
    last_l = -1
    for item in stop_list:
        l, i = item[:]
        if l == last_l:     # merge
            ei = i
        else:               # change
            if last_l != -1:
                tup = (last_l, bi, ei)
                period_list.append(tup)
            bi, ei, last_l = i, i, l
    period_list.append((last_l, bi, ei))
    # step 3
    # (trace_begin_index, trace_end_index)
    for i, item in enumerate(period_list[1:]):
        trace_list.append((period_list[i][2], item[1]))
    for i, traj in enumerate(trace_list):
        bi, ei = traj[:]
        draw_traj(trace[bi:ei + 1], i)
    return trace_list


def get_dist(conn, bt, vehi_num):
    _bt = clock()
    str_bt = bt.strftime('%Y-%m-%d %H:%M:%S')
    end_time = bt + timedelta(hours=10)
    str_et = end_time.strftime('%Y-%m-%d %H:%M:%S')
    sql = "select px, py, speed_time, state, speed from " \
          "TB_GPS_1803 t where speed_time >= to_date('{1}', 'yyyy-mm-dd hh24:mi:ss') " \
          "and speed_time < to_date('{2}', 'yyyy-MM-dd hh24:mi:ss')" \
          " and vehicle_num = '浙{0}'".format(vehi_num, str_bt, str_et)

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
    _et = clock()
    # print 'step1', _et - _bt

    new_trace = []
    for data in trace:
        cur_point = data
        if last_point is not None:
            dist = calc_dist([cur_point.px, cur_point.py], [last_point.px, last_point.py])
            del_time = (cur_point.stime - last_point.stime).total_seconds()
            if dist > 2000 and del_time < 60:
                continue
            elif del_time <= 5:
                continue
            else:
                new_trace.append(data)
        else:
            new_trace.append(data)
        last_point = cur_point
    _et = clock()
    # print sys._getframe().f_code.co_name, _et - _bt
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
    bt = clock()
    xy_list = []
    for data in trace:
        if data.speed < 5:
            xy_list.append([data.px, data.py])
    X = np.array(xy_list)
    if len(X) == 0:
        return None, X
    db = DBSCAN(eps=50, min_samples=15).fit(X)
    et = clock()
    # print sys._getframe().f_code.co_name, et - bt
    return db.labels_, X


def get_label(trace):
    _bt = clock()
    xy_list = []
    idx = 0
    for data in trace:
        if data.speed < 5:
            data.set_index(idx)
            idx += 1
            xy_list.append([data.px, data.py])
    X = np.array(xy_list)
    if len(xy_list) == 0:
        return None, X
    db = DBSCAN(eps=50, min_samples=15).fit(X)
    _et = clock()
    # print sys._getframe().f_code.co_name, _et - _bt
    return db.labels_, X


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
        # print key, lng, lat, cnt[key]
        area_list.append((lng, lat))
    # save_area(area_list)
    return area_list


def draw_data(trace):
    xy_list = []
    stop_list = []
    for data in trace:
        if data.speed < 5:
            stop_list.append([data.px, data.py])
            # plt.text(data.px, data.py, '{0}'.format(data.direction))
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
    _bt = clock()
    label, X = get_label(trace)
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
    _et = clock()
    # print sys._getframe().f_code.co_name, _et - _bt
    return cnt_in, cnt_out, label, X


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


def get_cluster_name(veh, str_time, centers, areas):
    """
    针对每一个cluster中心点计算最近的已知常驻营运地点
    :param centers: center list
    :param areas: area list [[px, py, address], ...]
    :return: address list, 如没有临近500米内的已知点，返回未知
    """
    fp = open('area.txt', 'a')
    fp.write(veh + ',' + str_time + '\n')
    for center in centers:
        x, y = bl2xy(center[1], center[0])
        min_dist, sel_address = 1e20, None
        for a in areas:
            px, py = bl2xy(a[1], a[0])
            dist = calc_dist([x, y], [px, py])
            if min_dist > dist:
                min_dist, sel_address = dist, a[2]
        if min_dist > 500:
            sel_address = '未知'
        # print sel_address, min_dist
        str_line = str(center[0]) + ',' + str(center[1]) + ',' + sel_address + '\n'
        fp.write(str_line)
    fp.close()


def get_type(conn, veh, str_time):
    cursor = conn.cursor()
    sql = "select type from tb_record1 where vehicle_num = '{0}' and gps_date = '{1}'".format(veh, str_time)
    cursor.execute(sql)
    tp = 0
    for item in cursor.fetchall():
        tp = int(item[0])
    return tp


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
    mkdir("./pic/{0}".format(vehi_num))
    for d in range(20, 32):
        begin_time = datetime(2018, 3, d, 8, 0, 0)
        str_bt = begin_time.strftime('%Y-%m-%d')
        print str_bt
        tp = get_type(conn, vehi_num, str_bt)
        # if tp == 0:
        #     continue

        fig1 = plt.figure(figsize=(12, 6))
        ax = fig1.add_subplot(111)
        taxi_trace = get_dist(conn, begin_time, vehi_num)
        labels, X = get_label(taxi_trace)
        # ent = label_entropy(labels)
        # key_areas = get_key_area(conn)
        # center_list = get_cluster_centers(taxi_trace, labels)
        # get_cluster_name(vehi_num, str_bt, center_list, key_areas)
        str_title = './pic/{0}/'.format(vehi_num) + vehi_num + ' ' + str_bt + '.png'
        trace_list = split_trace(taxi_trace, labels)
        # per, gps_cnt = process(taxi_trace, jq_area)
        # stop_in, stop_out = get_stop_point(taxi_trace, jq_area)
        # tup = (vehi_num, gps_cnt, stop_in, stop_out, per, ent, str_bt)
        # print tup

        draw(taxi_trace, vehi_num, str_bt, labels, X)
        plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
        plt.savefig(str_title, dpi=200)
        # plt.show()

        # for trace in trace_list
        # draw_trace_list(trace_list, 14, 14)
        plt.close(fig1)
    print 'over'


def main():
    conn = oracle_util.get_connection()
    way, node, edge = read_xml('jq0.xml')
    draw_map(way, node, edge)
    begin_time = datetime(2018, 3, 7, 8)
    vehicle = ['AT3404']
    for veh in vehicle:
        taxi_trace = get_data(conn, begin_time, veh)
        draw_data(taxi_trace)

# main()
# plt.show()
