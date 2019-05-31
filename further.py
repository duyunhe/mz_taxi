# -*- coding: utf-8 -*-
# @Time    : 2018/6/14 9:51
# @Author  :
# @简介    : 对初步筛查后的车辆进行进一步的无监督学习
# @File    : further.py

from DBConn import oracle_util
from area import get_key_area
import os
import numpy as np
import matplotlib.pyplot as plt
from read_map import TaxiData, cmp1, draw_labels
from geo import bl2xy, calc_dist, xy2bl, calc_bl_dist
from sklearn.cluster import DBSCAN
import time
import urllib2
import json
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
conn = oracle_util.get_connection()
g_mark = 4


def select(mark):
    sql = "select vehicle_num from tb_record"
    cursor = conn.cursor()
    cursor.execute(sql)
    veh_cnt = {}
    for item in cursor.fetchall():
        veh = item[0]
        try:
            veh_cnt[veh] += 1
        except KeyError:
            veh_cnt[veh] = 1
    cursor.close()

    sorted_cnt = sorted(veh_cnt, key=lambda x: veh_cnt[x], reverse=True)
    # sorted_dict = map(lambda x: {x: veh_cnt[x]}, sorted_cnt)
    valid_list = []
    for veh in sorted_cnt:
        if veh_cnt[veh] > 4:
            valid_list.append(veh)
    if mark == -1:
        return valid_list
    else:
        return valid_list[mark::5]


def save2db(veh_num, area_list, ep_dict, cnt_dict):
    # TODO
    return


def save_csv_header():
    fp = open("E:/mzc/data/mz.csv", 'w')
    str_list = ["车辆", "常驻营运地点"]
    for i in range(1, 32):
        str_list.append("5-" + str(i))
    str_header = ','.join(str_list)
    fp.write(str_header + '\n')
    fp.close()


def save_csv_context(veh_num, area_list, ep_dict, cnt_dict):
    fp = open("./data/mz{0}.csv".format(g_mark), 'w')
    slist = [veh_num]
    sa = "\"" + '\n'.join(area_list) + "\""
    # sa = sa.encode('gbk')
    slist.append(sa)
    for d in range(1, 32):
        if cnt_dict[d] == 0:
            slist.append("无数据")
        elif len(ep_dict[d]) == 0:
            slist.append("正常营运")
        else:
            sa = "\"" + '\n'.join(ep_dict[d]) + "\""
            slist.append(sa)
    str_context = ','.join(slist)
    fp.write(str_context + '\n')
    fp.close()


def west_lake():
    """
    西湖新能源
    :return: 
    """
    taxi_list = ['浙ATE077']
    save_csv_header()
    for taxi in taxi_list:
        try:
            check_veh(taxi)
        except Exception as e:
            print e.message


def main(mark):
    """
    :param mark: 当mark=-1时，查询所有车辆，否则查询部分车辆，详见select函数
    :return: 
    """
    print mark
    taxi_list = select(mark)
    save_csv_header()
    for taxi in taxi_list:
        try:
            check_veh(taxi)
        except Exception as e:
            print e.message


def split_trace(trace, begin_idx):
    for i, data in enumerate(trace[1:-1]):
        if data.state == 0 and trace[i].state == 1 and trace[i + 2].state == 1:
            data.state = 1
        elif data.state == 1 and trace[i].state == 0 and trace[i + 2].state == 0:
            data.state = 0
    last_state, bi, ei = -1, -1, -1
    # last_time = None
    split_list = []
    for i, data in enumerate(trace):
        # print data.stime, data.state
        if data.state != last_state:
            if bi != -1:
                split_list.append((begin_idx + bi, begin_idx + ei, last_state))
            bi = i
        else:
            ei = i
        last_state = data.state
    split_list.append((begin_idx + bi, begin_idx + ei, last_state))
    return split_list


def pre_trace(trace):
    trace.sort(cmp1)
    trace_list, new_trace = [], []
    last_point = None
    for data in trace:
        cur_point = data
        if last_point is not None:
            dist = calc_dist([cur_point.px, cur_point.py], [last_point.px, last_point.py])
            del_time = (cur_point.stime - last_point.stime).total_seconds()
            if del_time > 3600:
                if len(new_trace) != 0:
                    trace_list.append(new_trace)
                    new_trace = []
            if dist > 2000 and del_time < 60:
                continue
            elif del_time <= 5:
                continue
            else:
                new_trace.append(data)
        else:
            new_trace.append(data)
        last_point = cur_point
    trace_list.append(new_trace)
    return trace_list


def point_to_addr_new(point):
    ulr = "http://restapi.amap.com/v3/geocode/regeo?location={0},{1}" \
          "&key=0a54a59bdc431189d9405b3f2937921a&radius=150&extensions=all".format(point[0], point[1])
    for fails in range(0, 4):
        try:
            if fails >= 3:
                print 'timeout'
                return None
            temp = urllib2.urlopen(ulr, timeout=10)
            t = temp.read()
        except Exception, e:
                print e
                print '网络连接出现问题, 正在尝试再次请求:'.decode('utf8'), fails
        else:
            try:
                temp = json.loads(t)
                min_dist = 1e10
                list0 = None
                pois = temp['regeocode']['pois']
                for poi in pois:
                    dist = float(poi['distance'])
                    if dist < min_dist and poi['address'] != []:
                        list0, min_dist = poi['address'], dist
                # list0 = temp['regeocode']['pois'][0]['address']
                if list0 is None:
                    return u"无名"
                else:
                    return list0
            except KeyError:
                print 'error'
                return temp['regeocode']['formatted_address']


def exact_run_trace(trace, begin_index, end_index):
    # 切分stop list
    bi, ei = -1, 0
    stop_list = []
    for i, data in enumerate(trace[begin_index:end_index + 1]):
        if data.speed < 5:
            if bi == -1:
                bi = i
            ei = i
        else:
            if bi != -1:       # 区分出大于五分钟的连续停止轨迹
                itv_time = (trace[ei].stime - trace[bi].stime).total_seconds()
                if itv_time > 300:
                    stop_list.append((bi, ei))
                bi = -1
    try:
        itv_time = (trace[ei].stime - trace[bi].stime).total_seconds()
        if itv_time > 300:
            stop_list.append((bi, ei))
    except IndexError:
        pass

    run_list = []
    last_stop = [-1, 0]
    for stop in stop_list:
        if stop[0] - last_stop[1] >= 6:
            run_list.append([last_stop[1], stop[0] - 1, 0])
        last_stop = stop

    # 返回index
    for run in run_list:
        for i in range(2):
            run[i] += begin_index
    return run_list


def pre_trace0(trace, sp_list):
    """
    对空车状态下的轨迹进行划分
    :param trace: all trace collected
    :param sp_list: 
    :return: new_sp_list, contains all trace in empty state
    """
    new_sp_list = []
    for sp in sp_list:
        if sp[2] == 1:
            continue
        bi, ei = sp[0:2]
        new_sp = exact_run_trace(trace, bi, ei)
        new_sp_list.extend(new_sp)
    return new_sp_list


def calc_direct_dist(trace):
    max_dist = 0
    for data in trace:
        dist = calc_dist([trace[0].px, trace[0].py], [data.px, data.py])
        max_dist = max(dist, max_dist)
    return max_dist


def calc_trace_dist(trace):
    last_point = None
    tot_dist = 0
    for data in trace:
        point = (data.px, data.py)
        try:
            dist = calc_dist(last_point, point)
            tot_dist += dist
        except TypeError:
            pass
        last_point = point
    return tot_dist


def test_draw(trace, sp_list):
    for tr in sp_list:
        bi, ei = tr[0:2]
        fig1 = plt.figure(figsize=(12, 6))
        ax = fig1.add_subplot(111)
        plt.xlim(73126, 85276)
        plt.ylim(75749, 82509)
        # show_map()
        # draw_data(trace[bi:ei + 1])
        plt.show()


def test_draw2(ep_list):
    """
    :param ep_list: all end points
    :return: 
    """
    plt.xlim(70059, 83333)
    plt.ylim(76429, 83468)
    plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
    # show_map()

    x, y = zip(*ep_list)
    plt.plot(x, y, 'k+', alpha=0.3)


def save_file(center_points, key_area, ep_list, trace, label, veh_num):
    """
    save report to csv file
    :param center_points: 聚类中心点
    :param key_area: 数据库中预先存放的重点区域
    :param ep_list: 起终点
    :param trace: 全轨迹
    :param label: 聚类标签
    :param veh_num
    :return: 
    """
    area_list = []
    for pt in center_points:
        lat, lng = xy2bl(pt[0], pt[1])
        min_dist = 1e10
        name = None
        for i, area in enumerate(key_area):
            # x, y = bl2xy(area[1], area[0])
            dist = calc_bl_dist([area[0], area[1]], [lng, lat])
            # print i, dist, area[2].decode('gbk')

            if dist < min_dist:
                min_dist, name = dist, area[2]
        if min_dist > 400:
            lat, lng = xy2bl(pt[0], pt[1])
            # name = point_to_addr_new([lng, lat])
            name = str(lat) + "," + str(lng)
        # show text on map
        print lng, lat, name, min_dist
        # try:
        #     plt.text(pt[0] + 100, pt[1] + 100, name, fontproperties='SimHei', fontsize=10)
        # except Exception as e:
        #     print e.message
        area_list.append(name)

    bp_daily, ep_daily = {}, {}
    cnt_daily = {}
    for day in range(1, 32):
        ep_daily[day] = set()
        cnt_daily[day] = 0
    for i, eps in enumerate(ep_list):
        bi = eps[0]
        date = trace[bi].stime.day
        cnt_daily[date] += 1
        # print date
        if label[i * 2] != -1:
            idx = label[i * 2]
            try:
                ep_daily[date].add(area_list[idx])
            except TypeError:
                print i, area_list[idx]
        if label[i * 2 + 1] != -1:
            idx = label[i * 2 + 1]
            ep_daily[date].add(area_list[idx])
    for date in range(1, 32):
        print date, cnt_daily[date], "area:",
        for area in ep_daily[date]:
            print area,
        print

    save_csv_context(veh_num, area_list, ep_daily, cnt_daily)


def extract_endpoint(trace, mod_list):
    """
    提取出端点
    :param trace: 
    :param mod_list: [begin_index, end_index, state], ...
    :return: 
    """
    ep_list = []
    for tr in mod_list:
        bi, ei = tr[0:2]
        try:
            point = (trace[bi].px, trace[bi].py)
            ep_list.append(point)
            point = (trace[ei].px, trace[ei].py)
            ep_list.append(point)
        except IndexError:
            print bi, ei
    return ep_list


def check_veh(vehi_num):
    # if vehi_num[-6:] != "ATF255":
    #     return
    fig1 = plt.figure(figsize=(12, 6))
    ax = fig1.add_subplot(111)
    print vehi_num
    sql = "select vehicle_num, px, py, state, speed, speed_time" \
          " from tb_gps_1805 where vehicle_num = '{0}' order by speed_time".format(vehi_num)
    sql = "select vehicle_num, px, py, state, speed, speed_time" \
          " from tb_gps_1805 where vehicle_num = '{0}' and speed_time >= to_date" \
          "('2018-05-15', 'yyyy-mm-dd') and speed_time < to_date('2018-05-30', '" \
          "yyyy-mm-dd')".format(vehi_num)

    # ********* step 1. 取数据 **********
    cursor = conn.cursor()
    cursor.execute(sql)
    bt = time.clock()
    trace_month = []
    for item in cursor.fetchall():
        veh, lng, lat, state, speed, stime = item[0:6]
        if lat > 31 or lat < 29 or lng > 121 or lng < 119:
            continue
        px, py = bl2xy(lat, lng)
        state = int(state)
        taxi_data = TaxiData(px, py, stime, state, speed)
        trace_month.append(taxi_data)
    et = time.clock()
    print et - bt
    print len(trace_month)

    # ********* step 2. 预处理 **********
    # 按时间分成几段
    trace_list = pre_trace(trace_month)

    mod_list = []
    bi = 0
    for trace in trace_list:
        sp_list = split_trace(trace, bi)
        bi += len(trace)
        mod_list.extend(sp_list)

    # 重车营运
    tr_list1 = []
    for tr in mod_list:
        bi, ei, st = tr[0:3]
        if st == 1:
            dist = calc_trace_dist(trace_month[bi:ei + 1])
            dist2 = calc_direct_dist(trace_month[bi:ei + 1])
            if dist > 1000:
                tr_list1.append(tr)

    # 空车提取
    mod_list0 = pre_trace0(trace_month, mod_list)
    tr_list0 = []
    for tr in mod_list0:
        bi, ei = tr[0:2]
        dist = calc_trace_dist(trace_month[bi:ei + 1])
        dist2 = calc_direct_dist(trace_month[bi:ei + 1])
        if dist > 1000:
            tr_list0.append(tr)

    mod_list = []
    mod_list.extend(tr_list1)
    mod_list.extend(tr_list0)
    # 提取端点
    trs = extract_endpoint(trace_month, mod_list)
    test_draw2(trs)

    # ********* step 3. 聚类 **********
    X = np.array(trs)
    db = DBSCAN(eps=100, min_samples=10).fit(X)

    x_dict = {}
    y_dict = {}
    labels = db.labels_
    for t in labels:
        x_dict[t] = []
        y_dict[t] = []
    for i in range(len(labels)):
        x_dict[labels[i]].append(X[:, 0][i])
        y_dict[labels[i]].append(X[:, 1][i])
    points = draw_labels(x_dict, y_dict)

    # ********* step 4. 存档 **********
    key_area = get_key_area(conn)
    save_file(points, key_area, mod_list, trace_month, labels, vehi_num)

    # str_file = "./pic/" + vehi_num.decode('gbk') + ".png"
    # plt.savefig(str_file, dpi=200)
    # plt.show()
    plt.close(fig1)


# main(g_mark)
west_lake()
