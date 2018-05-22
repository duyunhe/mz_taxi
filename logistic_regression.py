# -*- coding: utf-8 -*-
# @Time    : 2018/4/12 10:56
# @Author  : 
# @简介    : 逻辑回归分类
# @File    : logistic_regression.py

import numpy as np


def sigmoid(x):
    """
    sigmoid function
    :param x: (mat), feature * w
    :return: (mat) sigmoid value
    """
    return 1.0 / (1 + np.exp(-x))


def lr_train(feature, label, max_iter=150, alpha=0.001):
    """
    梯度下降法训练LR模型
    :param feature: (mat) 数据矩阵 n * r   n:样本个数 r:特征个数
    :param label: (mat) 标签 n * 1
    :param max_iter: 最大迭代次数
    :param alpha: 下降率
    :return: w (mat) weight r * 1
    """
    n = np.shape(feature)[1]        # r * n
    weights = np.mat(np.ones((n, 1)))
    i = 0
    while i <= max_iter:
        i += 1
        h = sigmoid(feature * weights)
        err = label - h
        weights = weights + alpha * feature.T * err
    return weights


def save_model(filename, w):
    m = np.shape(w)[0]
    fp = open(filename, 'w')
    w_array = []
    for i in xrange(m):
        w_array.append(str(w[i, 0]))
    fp.write(','.join(w_array))
    fp.close()


def load_model(filename):
    fp = open(filename)
    str_line = fp.readline()
    items = map(float, str_line.strip('\n').split(','))
    return np.mat(items)


def predict(data, w):
    """
    对测试数据进行预测
    :param data: (mat) n * r
    :param w: (mat) 1 * r
    :return: h (mat) 
    """
    h = sigmoid(data * w.T)
    m = np.shape(h)[0]
    # org = h.copy()
    for i in xrange(m):
        if h[i, 0] < 0.5:
            h[i, 0] = 0
        else:
            h[i, 0] = 1
    return h

