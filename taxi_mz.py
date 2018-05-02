# -*- coding: utf-8 -*-
# @Time    : 2018/4/12 16:05
# @Author  : 
# @简介    : 
# @File    : taxi_mz.py

from numpy import *
from logistic_regression import lr_train, predict, save_model
from DBConn import oracle_util


def load_data(filename):
    data_list, label_list = [], []
    fr = open(filename)
    for line in fr.readlines():
        line_arr = line.strip().split(',')
        data_list.append([1.0, float(line_arr[0]) / 10, float(line_arr[1]) / 10, float(line_arr[2]) / 100])
        label_list.append(int(line_arr[3]))
    data_mat = mat(data_list)
    label_mat = mat(label_list)
    label_mat = label_mat.T
    return data_mat, label_mat


def load_database():
    conn = oracle_util.get_connection()
    sql = "select stop_in_count, stop_out_count, gps_in_per, stop_in_entropy, type from tb_record " \
          "where mark = 1"
    cursor = conn.cursor()
    cursor.execute(sql)
    data_list, label_list = [], []
    for item in cursor.fetchall():
        stop_in_count, stop_out_count, gps_in_per, stop_in_entropy = map(float, item[0:4])
        type = int(item[4])
        data_list.append([1.0, stop_in_count / 10, stop_out_count / 10, gps_in_per, stop_in_entropy])
        label_list.append(type)
    data_mat = mat(data_list)
    label_mat = mat(label_list)
    label_mat = label_mat.T
    return data_mat, label_mat


def main_mz():
    dataMat, labelMat = load_database()
    weights = lr_train(dataMat, labelMat)
    save_model('model.txt', weights)
    # test_data, test_label = load_data("record_test.csv")
    # ans = predict(test_data, weights.T)
    # n = shape(ans)[0]
    # for i in range(n):
    #     if ans[i][0] != test_label[i, 0]:
    #         print i, test_data[i, 1:], ans[i, 0], test_label[i, 0]


main_mz()

