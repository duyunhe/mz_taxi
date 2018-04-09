# -*- coding: utf-8 -*-
# @Time    : 2018/3/28 15:35
# @Author  : 
# @简介    : 
# @File    : read_map.py

import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from xml.etree import ElementTree as ET
from geo import bl2xy, calc_dist
from DBConn import oracle_util
import numpy as np
from time import clock
from datetime import datetime, timedelta
import os

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'

EDGE_ONEWAY = 3
EDGES = 2
EDGE_INDEX = 4
EDGE_LENGTH = 5
NODE_EDGELIST = 2
conn = oracle_util.get_connection()

color = ['r-', 'b-', 'g-', 'c-', 'm-', 'y-', 'c-', 'r-', 'b-', 'brown', 'm--', 'y--', 'c--', 'k--', 'r:']
# region = {'primary': 0, 'secondary': 1, 'tertiary': 2,
#           'unclassified': 5, 'trunk': 3, 'service': 4, 'trunk_link': 6,
#           'primary_link': 7, 'secondary_link': 8, 'residential': 9}
region = {'primary': 0, 'secondary': 1, 'tertiary': 2, 'trunk': 3}
point_color = ['blue', 'red']


class TaxiData:
    def __init__(self, px, py, stime, state, speed):
        self.px, self.py, self.stime, self.state, self.speed = px, py, stime, state, speed
        self.flag = 0

    def set_flag(self, flag):
        self.flag = flag


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
        plt.plot(x, y, c, alpha=0.3)


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


def draw(trace, vehi_num):
    t0 = clock()
    way, node, edge = read_xml('jq.xml')
    t1 = clock()
    # print t1 - t0
    draw_map(way, node, edge)
    t2 = clock()
    # print t2 - t0
    plt.xlim(73126, 85276)
    plt.ylim(75749, 82509)
    plt.title(vehi_num)

    xy_list = []
    last_point = None
    idx = 0
    for data in trace:
        if 1 == 1:
            cur_point = [data.px, data.py]
            if last_point is not None:
                # dist = calc_dist(cur_point, last_point)
                # str_time = data.stime.strftime('%H:%M')
                if data.speed > 10:
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
    db = DBSCAN(eps=80, min_samples=20).fit(X)

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


def split_trace(trace):
    stop_list = []
    bi, ei = -1, -1
    idx = 0
    for data in trace:
        if data.speed < 5:
            if bi == -1:
                bi = idx
            ei = idx
        else:
            if bi != -1 and ei - bi >= 4:
                stop_list.append([bi, ei])
                bi = -1
            elif bi != -1 and ei - bi < 4:
                bi = -1
        idx += 1
    trace_list = []
    lasti = 0
    for stop in stop_list:
        bi, ei = stop[0], stop[1]
        if bi - lasti > 1:
            trace_list.append(trace[lasti: bi])
        lasti = ei + 1
    idx = 0
    for trace in trace_list:
        print idx, trace[0].stime, trace[-1].stime, len(trace)
        idx += 1
    return trace_list


def get_dist(bt, vehi_num):
    str_bt = bt.strftime('%Y-%m-%d %H:%M:%S')
    end_time = bt + timedelta(hours=12)
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

    new_trace = []
    for data in trace:
        cur_point = data
        if last_point is not None:
            dist = calc_dist([cur_point.px, cur_point.py], [last_point.px, last_point.py])
            del_time = (cur_point.stime - last_point.stime).total_seconds()
            if dist > 2000 and del_time < 60:
                continue
            else:
                new_trace.append(data)
        else:
            new_trace.append(data)
        last_point = cur_point
    return new_trace

    # total_minutes = 12 * 60
    # interval_minute = 2
    # total_cnt = total_minutes / interval_minute
    # milleage = [0.0] * total_cnt
    # e_cnt, f_cnt = [0] * 301, [0] * 601
    # xlabels = []
    # ct = bt
    # label_cnt = total_minutes / 30
    # for i in range(label_cnt):
    #     xlabels.append(ct.strftime('%H:%M'))
    #     data_span = timedelta(minutes=30)
    #     ct = ct + data_span
    # last_point = None
    # cl, cb = 120.148906, 30.229587
    # cx, cy = bl2xy(cb, cl)
    # leifengta_point = [cx, cy]
    # leave, cnt = [0.0] * total_cnt, [0] * total_cnt
    # for data in trace:
    #     cur_point = [data.px, data.py]
    #     if last_point is not None:
    #         cur_index = int((data.stime - bt).total_seconds() / (60 * interval_minute))
    #         dist = calc_dist(last_point, cur_point)
    #         dist0 = calc_dist(leifengta_point, cur_point)
    #         milleage[cur_index] += dist
    #         leave[cur_index] += dist0
    #         cnt[cur_index] += 1
    #     last_point = cur_point
    #
    # x = [i for i in range(total_cnt)]
    # ly = []
    # for i in range(total_cnt):
    #     try:
    #         ly.append(leave[i] / cnt[i])
    #     except ZeroDivisionError:
    #         if i == 0:
    #             ly.append(0)
    #         else:
    #             ly.append(ly[i - 1])
    #
    # return trace


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


def traj_entropy(trace):
    xy_list = []
    for data in trace:
        xy_list.append([data.px, data.py])
    X = np.array(xy_list)
    print "size", len(xy_list),
    print "cov", cov_xy(X)


def draw_trace(trace):
    xy_list = []
    color_list = []
    for data in trace:
        xy_list.append([data.px, data.py])
        if data.speed < 5:
            color_list.append('peru')
        elif data.state == 0:
            color_list.append('g')
        else:
            color_list.append('crimson')

    btime = trace[0].stime.strftime('%H:%M:%S')
    etime = trace[-1].stime.strftime('%H:%M:%S')
    x, y = zip(*xy_list)
    plt.plot(x, y, 'k--')
    plt.scatter(x, y, c=color_list)
    plt.text(x[0], y[0], btime)
    plt.text(x[-1], y[-1], etime)


def draw_trace_list(trace_list, bi, ei):
    way, node, edge = read_xml('jq.xml')
    draw_map(way, node, edge)
    for i in range(bi, ei + 1):
        draw_trace(trace_list[i])
    plt.xlim(73126, 85276)
    plt.ylim(75749, 82509)

    plt.show()


def main_vehicle(vehi_num):
    print vehi_num
    mkdir("./pic/{0}".format(vehi_num))
    # for d in range(1, 9):
    #     begin_time = datetime(2017, 10, d, 8, 0, 0)
    #     str_bt = begin_time.strftime('%Y-%m-%d')
    #     fig1 = plt.figure(figsize=(12, 6))
    #     ax = fig1.add_subplot(111)
    #     taxi_trace = get_dist(begin_time, vehi_num)
    #     print str_bt,
    #     traj_entropy(taxi_trace)
    #     str_title = './pic/{0}/'.format(vehi_num) + vehi_num + ' ' + str_bt + '.png'
    #     draw(taxi_trace, vehi_num)
    #     plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
    #     plt.savefig(str_title, dpi=150)
    #     # plt.show()
    #     plt.close(fig1)
    for d in range(22, 23):
        begin_time = datetime(2017, 9, d, 8, 0, 0)
        str_bt = begin_time.strftime('%Y-%m-%d')
        fig1 = plt.figure(figsize=(12, 6))
        ax = fig1.add_subplot(111)
        taxi_trace = get_dist(begin_time, vehi_num)
        str_title = './pic/{0}/'.format(vehi_num) + vehi_num + ' ' + str_bt + '.png'
        # draw(taxi_trace, vehi_num)
        plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
        # plt.savefig(str_title, dpi=150)
        # plt.show()
        trace_list = split_trace(taxi_trace)
        # for trace in trace_list:
        draw_trace_list(trace_list, 3, 7)
        plt.close(fig1)
    print 'over'


def main():
    # vehicle_list = ['AT9344', 'AT1385', 'ATE559', 'ATG185', 'AT5310',
    #                 'ATD792', 'ATD669', 'AT9966', 'ATB533', 'ATB541',
    #                 'ATD105', 'ATF286', 'ATF288', 'ATF299', 'ATF358',
    #                 'AQT371', 'AT9501', 'ATA879', 'ATA888', 'ATC709',
    #                 'ATE027', 'ATE077', 'AT8884', 'ATD326', 'ATD560',
    #                 'ATD565', 'ATD568', 'ATD581', 'ATE792', 'ATF266']
    vehicle_list = ['ATF266']
    for veh in vehicle_list:
        main_vehicle(veh)


main()
