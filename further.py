# -*- coding: utf-8 -*-
# @Time    : 2018/6/14 9:51
# @Author  : 
# @简介    : 对初步筛查后的车辆进行进一步的无监督学习
# @File    : further.py

from DBConn import oracle_util
import os
import matplotlib.pyplot as plt
from read_map import TaxiData, cmp1, show_map, draw_data
from geo import bl2xy, calc_dist
import time
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'
conn = oracle_util.get_connection()


def select():
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
    return valid_list


def main():
    taxi_list = select()
    for taxi in taxi_list:
        check_veh(taxi)
        break


def split_trace(trace):
    for i, data in enumerate(trace[1:-1]):
        if data.state == 0 and trace[i].state == 1 and trace[i + 2].state == 1:
            data.state = 1
        elif data.state == 1 and trace[i].state == 0 and trace[i + 2].state == 0:
            data.state = 0
    last_state, bi, ei = -1, -1, -1
    last_time = None
    split_list = []
    for i, data in enumerate(trace):
        # print data.stime, data.state
        if data.state != last_state:
            if bi != -1:
                split_list.append((bi, ei, last_state))
            bi = i
        else:
            ei = i
        last_state = data.state
    split_list.append((bi, ei, last_state))
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
            if bi != -1 and ei - bi >= 6:       # 区分出大于两分钟的连续停止轨迹
                stop_list.append((bi, ei))
                bi = -1
    if ei - bi >= 6:
        stop_list.append((bi, ei))

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
        show_map()
        draw_data(trace[bi:ei + 1])
        plt.show()


def check_veh(vehi_num):
    sql = "select vehicle_num, px, py, state, speed, speed_time" \
          " from tb_gps_1805 where vehicle_num = '{0}'".format(vehi_num)
    sql = "select vehicle_num, px, py, state, speed, speed_time" \
          " from tb_gps_1805 where vehicle_num = '{0}' and speed_time > to_date" \
          "('2018-05-01', 'yyyy-mm-dd') and speed_time < to_date('2018-05-03', '" \
          "yyyy-mm-dd')".format(vehi_num)
    cursor = conn.cursor()
    cursor.execute(sql)
    bt = time.clock()
    trace = []
    for item in cursor.fetchall():
        veh, lng, lat, state, speed, stime = item[0:6]
        px, py = bl2xy(lat, lng)
        state = int(state)
        taxi_data = TaxiData(px, py, stime, state, speed)
        trace.append(taxi_data)
    et = time.clock()
    print et - bt
    print len(trace)
    trace_list = pre_trace(trace)

    mod_list = []
    for trace in trace_list:
        sp_list = split_trace(trace)
        mod_list.extend(sp_list)

    for tr in mod_list:
        bi, ei, st = tr[0:3]
        if st == 1:
            dist = calc_trace_dist(trace[bi:ei + 1])
            print trace[bi].stime, trace[ei].stime, st, dist

    mod_list0 = pre_trace0(trace, mod_list)
    for tr in mod_list0:
        bi, ei = tr[0:2]
        dist = calc_trace_dist(trace[bi:ei + 1])
        try:
            print trace[bi].stime, trace[ei].stime, dist
        except IndexError:
            print bi, ei

    mod_list1 = []
    for tr in mod_list:
        if tr[2] == 1:
            mod_list1.append(tr)

    test_draw(trace, mod_list1)
    test_draw(trace, mod_list0)


main()
