# -*- coding: utf-8 -*-
# @Time    : 2019/7/3 15:57
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : predict.py


from network import NeuralNetwork
import numpy as np
from math import log
from sklearn.neural_network import MLPClassifier


def read_data():
    f_list = []
    with open('../data/all_feature.csv') as fp:
        for line in fp:
            items = map(float, line.strip('\n').split(','))
            items[3] = log(items[3] + 1)
            f_list.append(items)
    x = np.array(f_list)
    x_norm = x / x.max(axis=0)
    return x_norm


def judge(x):
    return 1 if x > .5 else 0


def main():
    X = read_data()
    i_num, h_num, o_num, learning_rate = 5, 6, 1, 0.005
    nn = NeuralNetwork(i_num, h_num, o_num, learning_rate)
    data = X[:, 0:i_num]
    o = X[:, i_num:].T

    ret = nn.load_param()
    if ret == 0:
        min_cost = nn.calc_loss(data, o)
    else:
        min_cost = 1e20
    print 'min cost', min_cost
    nn.reset_param()

    beta = .95
    last_cost = 1e20
    for i in range(10000):
        row = X.shape[0]
        for j in range(row):
            input_list, target = X[j, :i_num], X[j, i_num:]
            nn.train(input_list, target)
        learning_rate *= beta
        if i % 10 == 0:
            cost = nn.calc_loss(data, o)
            print i, cost
            if last_cost - cost < 1e-6:
                break
            last_cost = cost

    cost = nn.calc_loss(data, o)
    if cost < min_cost:
        print "new param found"
        nn.save_param()

    q = [0, 0, 0.5, 0, 0]
    print nn.query(q)


def main2():
    X = read_data()
    i_num = 5
    data = X[:, 0:i_num]
    o = X[:, i_num:].T


def query():
    nn = NeuralNetwork()
    nn.load_param()


main()
