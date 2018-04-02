# -*- coding: utf-8 -*-
# @Time    : 2018/3/28 15:35
# @Author  : 
# @简介    : 
# @File    : read_map.py

import matplotlib.pyplot as plt
from xml.etree import ElementTree as ET
from geo import bl2xy, calc_dist
from DBConn import oracle_util
from time import clock
from datetime import datetime, timedelta
import os

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'

EDGE_ONEWAY = 3
EDGES = 2
EDGE_INDEX = 4
EDGE_LENGTH = 5
NODE_EDGELIST = 2

color = ['r-', 'b-', 'g-', 'c-', 'm-', 'y-', 'c-', 'r-', 'b-', 'brown', 'm--', 'y--', 'c--', 'k--', 'r:']
# region = {'primary': 0, 'secondary': 1, 'tertiary': 2,
#           'unclassified': 5, 'trunk': 3, 'service': 4, 'trunk_link': 6,
#           'primary_link': 7, 'secondary_link': 8, 'residential': 9}
region = {'primary': 0}
point_color = ['blue', 'red']


class TaxiData:
    def __init__(self, px, py, stime, state, dbtime):
        self.px, self.py, self.stime, self.state, self.dbtime = px, py, stime, state, dbtime


def cmp1(data1, data2):
    if data1.stime > data2.stime:
        return 1
    elif data1.stime < data2.stime:
        return -1
    elif data1.dbtime > data2.dbtime:
        return 1
    else:
        return -1


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


def draw(trace):
    way, node, edge = read_xml('hz.xml')
    draw_map(way, node, edge)
    xy_list = []
    for data in trace:
        if datetime(2017, 9, 27, 14, 30, 0) > data.stime > datetime(2017, 9, 27, 13, 0, 0):
            xy_list.append([data.px, data.py])
    if len(xy_list) > 0:
        x, y = zip(*xy_list)
        plt.plot(x, y, 'k--', marker='+')


fig = plt.figure(figsize=(12, 6))
ax = fig.add_subplot(111)

conn = oracle_util.get_connection()
vehi_num = 'AT9344'
begin_time = datetime(2017, 9, 27, 8, 0, 0)
end_time = datetime(2017, 9, 27, 20, 0, 0)
str_bt = begin_time.strftime('%Y-%m-%d %H:%M:%S')
str_et = end_time.strftime('%Y-%m-%d %H:%M:%S')


def get_dist(bt):
    sql = "select px, py, speed_time, state, db_time from hzgps_taxi." \
          "TB_GPS_1709@taxilink t where speed_time >= to_date('{1}', 'yyyy-mm-dd hh24:mi:ss') " \
          "and speed_time < to_date('{2}', 'yyyy-MM-dd hh24:mi:ss')" \
          " and vehicle_num = '浙{0}'".format(vehi_num, str_bt, str_et)

    cursor = conn.cursor()
    cursor.execute(sql)
    trace = []

    for item in cursor.fetchall():
        lng, lat = map(float, item[0:2])
        if 119 < lng < 121 and 29 < lat < 31:
            px, py = bl2xy(lat, lng)
            state = int(item[3])
            stime = item[2]
            dbtime = item[4]
            taxi_data = TaxiData(px, py, stime, state, dbtime)
            trace.append(taxi_data)
    print len(trace)
    trace.sort(cmp1)

    total_minutes = 12 * 60
    interval_minute = 2
    total_cnt = total_minutes / interval_minute
    milleage = [0.0] * total_cnt
    e_cnt, f_cnt = [0] * 301, [0] * 601
    xlabels = []
    ct = bt
    label_cnt = total_minutes / 30
    for i in range(label_cnt):
        xlabels.append(ct.strftime('%H:%M'))
        data_span = timedelta(minutes=30)
        ct = ct + data_span
    last_point = None
    for data in trace:
        cur_point = [data.px, data.py]
        if last_point is not None:
            cur_index = int((data.stime - bt).total_seconds() / (60 * interval_minute))
            dist = calc_dist(last_point, cur_point)
            milleage[cur_index] += dist
        last_point = cur_point

    x = [i for i in range(total_cnt)]
    plt.plot(x, milleage)
    xticks = range(min(x), max(x) + 1, 30 / interval_minute)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels, rotation=15)
    plt.title(vehi_num + ' ' + str_bt)
    return trace


taxi_trace = get_dist(begin_time)
plt.show()
# draw(taxi_trace)
# plt.show()


