# -*- coding: utf-8 -*-
# @Time    : 2018/5/22 15:37
# @Author  : 
# @简介    : insert key areas collected from gps center manually
# @File    : area.py
import os
from DBConn import oracle_util
import numpy as np
from geo import bl2xy, calc_dist
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'


def main():
    fp = open('./data/mzc_jq.csv')
    idx = 0
    sql = "insert into tb_area (area_id, px, py, address) values(:1, :2, :3, :4)"
    tup_list = []
    for line in fp.readlines():
        item = line.strip('\n').split(',')
        if idx != 0:
            try:
                name = item[0]
                px, py = float(item[1]), float(item[2])
                tup = (idx, px, py, name)
                tup_list.append(tup)
            except ValueError as e:
                print e.message, idx
        idx += 1
    try:
        conn = oracle_util.get_connection()
        cursor = conn.cursor()
        cursor.executemany(sql, tup_list)
        conn.commit()
        conn.close()
    except Exception as e:
        print e.message


def get_key_area(conn):
    cursor = conn.cursor()
    sql = "select px, py, address from TB_AREA t "
    addr_list = []
    cursor.execute(sql)
    for item in cursor.fetchall():
        px, py, address = item[0:3]
        addr_list.append((px, py, address))
    return addr_list


def refine():
    ref_areas = ['青芝坞', ]
    area_dict = {}
    try:
        conn = oracle_util.get_connection()
        area_list = get_key_area(conn)
        for area in area_list:
            px, py, address = area[0:3]
            area_dict[address] = [px, py]
    except Exception as e:
        print e.message
    fp = open('./data/area.txt')
    ref_dist = {}
    for line in fp.readlines():
        item = line.strip('\n').split(',')
        px, py = float(item[0]), float(item[1])
        addr = item[2]
        if addr == '未知':
            continue
        try:
            ref_dist[addr].append([px, py])
        except KeyError:
            ref_dist[addr] = [[px, py]]
    for addr, ref_list in ref_dist.iteritems():
        vec = np.array(ref_list)
        real_pt = list(np.mean(vec, axis=0))
        realx, realy = bl2xy(real_pt[1], real_pt[0])
        try:
            lng, lat = area_dict[addr][0:2]
            x, y = bl2xy(lat, lng)
            dist = calc_dist([realx, realy], [x, y])
        except KeyError:
            continue
        if dist > 150 and len(ref_list) > 50:
            print addr, len(ref_list), "{0},{1}".format(real_pt[0], real_pt[1]), dist
            sql = "update tb_area set px = {0}, py = {1} where address = '{2}'".format(real_pt[0],
                real_pt[1], addr)
            cursor = conn.cursor()
            cursor.execute(sql)
            # conn.commit()
    conn.close()


# refine()


