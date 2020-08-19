# -*- coding: utf-8 -*-
# @Author: Zedong Peng
# @Date:   2019-09-22 22:36:24
# @Last Modified by:   zedongpeng
# @Last Modified time: 2020-06-09 20:53:27


'''
ModelGeneration3_block.py
Stochastic model
remove scheduling variables
Goal: solvable for large case
'''

from __future__ import division
from pyomo.environ import *
from pyomo.gdp import *
import time
import itertools


def Crangeset(c, s, e):
    '''
    returns a rangeset from s to e with a string 's' in front of numbers
    c: charactor, string
    s: start number, integer
    e: end number, integer
    '''
    temp = list(range(s, e + 1))
    result = [c + str(i) for i in temp]
    return result


def ModelGeneration(case_flag, shutin_flag, pipeline_flag, aggregated_flag, shutin_formulation_flag, pipeline_state_action_flag):
    '''
    case_flag: 1 means large case, 2 means medium case, 3 means small case, 4 means tiny case, 5 means tiny tiny case
    shutin_flag: True means shut in is included, False means shut in is not included
    pipeline_flag: True means include connectivivty constraint and False means only consider pipeline diameter constraints
    aggregated_flag: True means aggregated, False means disaggregate
    shutin_formulation_flag: True means shutin constraints are formulated as big-m, False means convex hull
    pipeline_state_action_flag: True means pipeline variables are defined as state variable, False means action variable
    '''

    model = ConcreteModel()

    if case_flag == 1:

        ###############################################################################
        ################################  Large case (start)###########################
        ############################# 80 wells and 60 pads ############################
        ###############################################################################

        # set

        model.w = Set(ordered=True, initialize=Crangeset('w', 1, 80))
        model.p = Set(ordered=True, initialize=Crangeset('p', 1, 60))
        model.f = Set(ordered=True, initialize=Crangeset('f', 1, 2))
        model.j = Set(ordered=True, initialize=Crangeset('j', 1, 12))
        model.q = Set(initialize=['q'])
        q = 'q'
        model.jq = model.j | model.q
        model.m = model.p | model.j
        model.n = model.m | model.q
        model.d = Set(ordered=True, initialize=Crangeset(
            'd', 1, 3))  # number of pipeline diameters
        model.r = Set(ordered=True, initialize=Crangeset(
            'r', 1, 4))  # number of rigs

        # length of period and related parameter
        model.t = Set(ordered=True, initialize=list(range(1, 37)))
        model.t_ = Set(ordered=True, initialize=list(range(2, 37)))
        num_periods_per_month = 2
        model.g = Param(initialize=20)

        # model.s = Set(ordered=True, initialize=Crangeset('s', 1, 64))
        model.s = Set(ordered=True, initialize=Crangeset('s', 1, 16))
        # model.ss_tuple = Set(ordered=True, initialize=list(
        #     itertools.combinations(list(model.s.data()), 2)))

        def _ss_tuple(model):
            temp = list(itertools.combinations(list(model.s.data()), 2))
            res = []
            for (s1, s2) in temp:
                num1 = int(s1[1:]) - 1
                num2 = int(s2[1:]) - 1
                if bin(num1 ^ num2)[2:].count('1') == 1:
                    res.append((s1, s2))
            return res
        model.ss_tuple = Set(dimen=2, ordered=True, initialize=_ss_tuple)

        # each section is different
        # def _w_ss(model, s1, s2):
        #     num1 = int(s1[1:]) - 1
        #     num2 = int(s2[1:]) - 1
        #     temp = []
        #     for index, i in enumerate(bin(num1 ^ num2)[2:]):
        #         if i == '1':
        #             for j in range(5):
        #                 temp.append(
        #                     'w' + str((len(bin(num1 ^ num2)[2:]) - index - 1) * 5 + j + 1))
        #     return temp

        # each 4 sections are different
        def _w_ss(model, s1, s2):
            num1 = int(s1[1:]) - 1
            num2 = int(s2[1:]) - 1
            temp = []
            for index, i in enumerate(bin(num1 ^ num2)[2:]):
                if i == '1':
                    if index == 0:
                        begin = 1
                    elif index == 1:
                        begin = 11
                    elif index == 2:
                        begin = 41
                    elif index == 3:
                        begin = 51
                    for j in range(10):
                        temp.append('w' + str(begin + j))
                        temp.append('w' + str(begin + j + 20))
            return temp

        model.w_ss = Set(model.ss_tuple, initialize=_w_ss)

        def _prob(model, s):
            return 1 / 16
            # return 1 / 64
        model.prob = Param(model.s, initialize=_prob)

        model.tau_d = Param(initialize=1)
        model.tau_c1 = Param(initialize=1)
        model.tau_c2 = Param(initialize=1)

        def _w_w(model, w):
            if int(w[1:]) % 20 == 1:
                return ['w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]
            elif int(w[1:]) % 20 == 2:
                return ['w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]
            elif int(w[1:]) % 20 == 19:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1)]
            elif int(w[1:]) % 20 == 0:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1)]
            else:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]

        model.w_w = Set(model.w, initialize=_w_w)
        model.w_p = Set(model.p, initialize={'p1': ['w1', 'w2', 'w21', 'w22'],
                                             'p2': ['w1', 'w2', 'w3', 'w21', 'w22', 'w23'],
                                             'p3': ['w2', 'w3', 'w4', 'w22', 'w23', 'w24'],
                                             'p4': ['w3', 'w4', 'w5', 'w23', 'w24', 'w25'],
                                             'p5': ['w4', 'w5', 'w24', 'w25'],
                                             'p6': ['w6', 'w7', 'w26', 'w27'],
                                             'p7': ['w6', 'w7', 'w8', 'w26', 'w27', 'w28'],
                                             'p8': ['w7', 'w8', 'w9', 'w27', 'w28', 'w29'],
                                             'p9': ['w8', 'w9', 'w10', 'w28', 'w29', 'w30'],
                                             'p10': ['w9', 'w10', 'w29', 'w30'],
                                             'p11': ['w11', 'w12', 'w31', 'w32'],
                                             'p12': ['w11', 'w12', 'w13', 'w31', 'w32', 'w33'],
                                             'p13': ['w12', 'w13', 'w14', 'w32', 'w33', 'w34'],
                                             'p14': ['w13', 'w14', 'w15', 'w33', 'w34', 'w35'],
                                             'p15': ['w14', 'w15', 'w34', 'w35'],
                                             'p16': ['w16', 'w17', 'w36', 'w37'],
                                             'p17': ['w16', 'w17', 'w18', 'w36', 'w37', 'w38'],
                                             'p18': ['w17', 'w18', 'w19', 'w37', 'w38', 'w39'],
                                             'p19': ['w18', 'w19', 'w20', 'w38', 'w39', 'w40'],
                                             'p20': ['w19', 'w20', 'w39', 'w40'],
                                             'p21': ['w21', 'w22', 'w41', 'w42'],
                                             'p22': ['w21', 'w22', 'w23', 'w41', 'w42', 'w43'],
                                             'p23': ['w22', 'w23', 'w24', 'w42', 'w43', 'w44'],
                                             'p24': ['w23', 'w24', 'w25', 'w43', 'w44', 'w45'],
                                             'p25': ['w24', 'w25', 'w44', 'w45'],
                                             'p26': ['w26', 'w27', 'w46', 'w47'],
                                             'p27': ['w26', 'w27', 'w28', 'w46', 'w47', 'w48'],
                                             'p28': ['w27', 'w28', 'w29', 'w47', 'w48', 'w49'],
                                             'p29': ['w28', 'w29', 'w30', 'w48', 'w49', 'w50'],
                                             'p30': ['w29', 'w30', 'w49', 'w50'],
                                             'p31': ['w31', 'w32', 'w51', 'w52'],
                                             'p32': ['w31', 'w32', 'w33', 'w51', 'w52', 'w53'],
                                             'p33': ['w32', 'w33', 'w34', 'w52', 'w53', 'w54'],
                                             'p34': ['w33', 'w34', 'w35', 'w53', 'w54', 'w55'],
                                             'p35': ['w34', 'w35', 'w54', 'w55'],
                                             'p36': ['w36', 'w37', 'w56', 'w57'],
                                             'p37': ['w36', 'w37', 'w38', 'w56', 'w57', 'w58'],
                                             'p38': ['w37', 'w38', 'w39', 'w57', 'w58', 'w59'],
                                             'p39': ['w38', 'w39', 'w40', 'w58', 'w59', 'w60'],
                                             'p40': ['w39', 'w40', 'w59', 'w60'],
                                             'p41': ['w41', 'w42', 'w61', 'w62'],
                                             'p42': ['w41', 'w42', 'w43', 'w61', 'w62', 'w63'],
                                             'p43': ['w42', 'w43', 'w44', 'w62', 'w63', 'w64'],
                                             'p44': ['w43', 'w44', 'w45', 'w63', 'w64', 'w65'],
                                             'p45': ['w44', 'w45', 'w64', 'w65'],
                                             'p46': ['w46', 'w47', 'w66', 'w67'],
                                             'p47': ['w46', 'w47', 'w48', 'w66', 'w67', 'w68'],
                                             'p48': ['w47', 'w48', 'w49', 'w67', 'w68', 'w69'],
                                             'p49': ['w48', 'w49', 'w50', 'w68', 'w69', 'w70'],
                                             'p50': ['w49', 'w50', 'w69', 'w70'],
                                             'p51': ['w51', 'w52', 'w71', 'w72'],
                                             'p52': ['w51', 'w52', 'w53', 'w71', 'w72', 'w73'],
                                             'p53': ['w52', 'w53', 'w54', 'w72', 'w73', 'w74'],
                                             'p54': ['w53', 'w54', 'w55', 'w73', 'w74', 'w75'],
                                             'p55': ['w54', 'w55', 'w74', 'w75'],
                                             'p56': ['w56', 'w57', 'w76', 'w77'],
                                             'p57': ['w56', 'w57', 'w58', 'w76', 'w77', 'w78'],
                                             'p58': ['w57', 'w58', 'w59', 'w77', 'w78', 'w79'],
                                             'p59': ['w58', 'w59', 'w60', 'w78', 'w79', 'w80'],
                                             'p60': ['w59', 'w60', 'w79', 'w80'],
                                             })

        def _wp(model):
            return ((w, p) for p in model.p for w in model.w_p[p])

        model.wp_tuple = Set(dimen=2, initialize=_wp)

        def _wwp(model):
            return ((w, w2, p) for p in model.p for w in model.w_p[p] for w2 in model.w_w[w])

        model.wwp_tuple = Set(dimen=3, initialize=_wwp)

        def _p_w(model, m):
            temp = []
            for k, v in model.wp_tuple.data():
                if k == m:
                    temp.append(v)
            return temp

        model.p_w = Set(model.w, initialize=_p_w)

        model.j_q = Set(initialize=['j12'])
        j_q = 'j12'

        def _n_m(model, m):
            temp = []
            if m[0] == 'j':
                temp.append('p' + str(int(m[1:]) * 5))
                if int(m[1:]) % 4 != 0:
                    temp.append('p' + str(int(m[1:]) * 5 + 1))
                if (int(m[1:]) - 1) // 4 == 0:
                    temp.append('j' + str(int(m[1:]) + 4))
                elif (int(m[1:]) - 1) // 4 == 1:
                    temp.append('j' + str(int(m[1:]) + 4))
                    temp.append('j' + str(int(m[1:]) - 4))
                elif (int(m[1:]) - 1) // 4 == 2:
                    temp.append('j' + str(int(m[1:]) - 4))
                if m == j_q:
                    temp.append(q)
            if m[0] == 'p':
                if int(m[1:]) % 5 == 1:
                    temp.append('p' + str(int(m[1:]) + 1))
                    if int(m[1:]) % 20 != 1:
                        temp.append('j' + str(int(m[1:]) // 5))
                elif int(m[1:]) % 5 == 0:
                    temp.append('p' + str(int(m[1:]) - 1))
                    temp.append('j' + str(int(m[1:]) // 5))
                else:
                    temp.append('p' + str(int(m[1:]) - 1))
                    temp.append('p' + str(int(m[1:]) + 1))

            return temp

        model.n_m = Set(model.m, initialize=_n_m)

        def _m_n(model):
            return ((m, n) for m in model.m for n in model.n_m[m])

        model.m_n_tuple = Set(dimen=2, initialize=_m_n)
        model.n_n_tuple = model.m_n_tuple | Set(dimen=2, initialize=[(q, j_q)])

        def _m_n_in(model, m):
            temp = []
            if m[0] == 'j':
                temp.append('p' + str(int(m[1:]) * 5))
                if int(m[1:]) % 4 == 0 and int(m[1:]) // 4 > 1:
                    temp.append('j' + str(int(m[1:]) - 4))
            if m[0] == 'p':
                if int(m[1:]) % 20 == 1:
                    return temp
                elif int(m[1:]) % 5 == 1:
                    temp.append('j' + str(int(m[1:]) // 5))
                else:
                    temp.append('p' + str(int(m[1:]) - 1))
            return temp

        model.n_m_in = Set(model.m, initialize=_m_n_in)
        # model.n_m_in.pprint()

        def _m_n_out(model, m):
            temp = []
            if m[0] == 'j':
                if m == j_q:
                    temp.append(q)
                elif int(m[1:]) % 4 == 0:
                    temp.append('j' + str(int(m[1:]) + 4))
                else:
                    temp.append('p' + str(int(m[1:]) * 5 + 1))
            if m[0] == 'p':
                if int(m[1:]) % 5 == 0:
                    temp.append('j' + str(int(m[1:]) // 5))
                else:
                    temp.append('p' + str(int(m[1:]) + 1))
            return temp

        model.n_m_out = Set(model.m, initialize=_m_n_out)
        # model.n_m_out.pprint()

        def _m_n_tuple_fixed(model):
            return ((m, n) for m in model.m for n in model.n_m_out[m])

        model.m_n_tuple_fixed = Set(dimen=2, initialize=_m_n_tuple_fixed)
        # model.m_n_tuple_fixed.pprint()

        def _wpss_tuple(model):
            return ((w, p, s1, s2) for s1, s2 in model.ss_tuple for w in model.w_ss[s1, s2] for p in model.p_w[w])
        model.wpss_tuple = Set(dimen=4, initialize=_wpss_tuple)

        def _tt(model):
            return ((t, t2) for t in model.t for t2 in model.t if t2 < t)

        model.tt_tuple = Set(dimen=2, initialize=_tt)

        def _t_t(model):
            return ((t, t2) for t in model.t_ for t2 in model.t_ if t2 < t)

        model.t_t_tuple = Set(dimen=2, initialize=_t_t)

        # parameter

        def _l(model, n, n2):
            if n[0] == 'p' and n2[0] == 'p':
                return 20
            if (n[0] == 'p' and n2[0] == 'j') or (n[0] == 'j' and n2[0] == 'p'):
                return 10
            else:
                return 100

        model.l = Param(model.n_n_tuple, initialize=_l)
        model.K = Param(initialize=73)    # the number of gas junction node

        # def _ProductionFactor(model, w):
        #     data = [0.8, 0.95, 1.1, 1.2, 0.95, 0.85, 1,
        #             1.20, 1.05, 1, 0.9, 1.05, 1.2, 1.1, 1, 0.95]
        #     return data[int((int(w[1:]) - 1) / 5)]

        # model.ProductionFactor = Param(model.w, initialize=_ProductionFactor)

        # each section is different, # scenario 2^16
        # def _ProductionFactor(model, w, s):
        #     data = [0.8, 0.95, 1.1, 1.2, 0.95, 0.85, 1,
        #             1.20, 1.05, 1, 0.9, 1.05, 1.2, 1.1, 1, 0.95]
        #     temp = s[1:]
        #     temp = bin(int(temp)-1)[2:]
        #     if len(temp) < len(data):
        #         temp = '0'*(len(data)-len(temp))+temp
        #     for i in range(len(data)):
        #         if temp[i] == '0':
        #             data[i] = data[i]*0.9
        #         elif temp[i] == '1':
        #             data[i] = data[i]*1.1
        #     return data[int((int(w[1:]) - 1) / 5)]

        # each 4 sections are different, # scenario 2^4
        def _ProductionFactor(model, w, s):
            data = [0.8, 0.95, 1.1, 1.2, 0.95, 0.85, 1,
                    1.20, 1.05, 1, 0.9, 1.05, 1.2, 1.1, 1, 0.95]
            temp = s[1:]
            temp = bin(int(temp) - 1)[2:]
            index = [[0, 1, 4, 5], [2, 3, 6, 7],
                     [8, 9, 12, 13], [10, 11, 14, 15]]
            if len(temp) < 4:
                temp = '0'*(4-len(temp))+temp
            for i in range(4):
                if temp[i] == '0':
                    for j in index[i]:
                        data[j] = data[j] * 0.9
                elif temp[i] == '1':
                    for j in index[i]:
                        data[j] = data[j] * 1.1
            return data[int((int(w[1:]) - 1) / 5)]

        model.ProductionFactor = Param(
            model.w, model.s, initialize=_ProductionFactor)

        def _drill_cost(model, w, p, f):
            if f == 'f1':
                if int(w[1:]) == int(p[1:]) or int(w[1:]) == int(p[1:]) + 20:
                    return 1187100
                else:
                    return 1457100
            elif f == 'f2':
                if int(w[1:]) == int(p[1:]) or int(w[1:]) == int(p[1:]) + 20:
                    return 1208700
                else:
                    return 1478700
        model.drill_cost = Param(
            model.wp_tuple, model.f, initialize=_drill_cost)

        ###############################################################################
        ################################  Large case (end)#############################
        ###############################################################################

    elif case_flag == 2:
        ###############################################################################
        ################################  Medium case (start)##########################
        ############################# 30 wells and 20 pads ############################
        ###############################################################################

        # set

        model.w = Set(ordered=True, initialize=Crangeset('w', 1, 30))
        model.p = Set(ordered=True, initialize=Crangeset('p', 1, 20))
        model.f = Set(ordered=True, initialize=Crangeset('f', 1, 2))
        model.j = Set(ordered=True, initialize=Crangeset('j', 1, 4))
        model.q = Set(initialize=['q'])
        q = 'q'
        model.jq = model.j | model.q
        model.m = model.p | model.j
        model.n = model.m | model.q
        model.d = Set(ordered=True, initialize=Crangeset(
            'd', 1, 3))  # number of pipeline diameters
        model.r = Set(ordered=True, initialize=Crangeset(
            'r', 1, 4))  # number of rigs

        # length of period and related parameter
        model.t = Set(ordered=True, initialize=list(range(1, 37)))
        model.t_ = Set(ordered=True, initialize=list(range(2, 37)))
        num_periods_per_month = 2
        model.g = Param(initialize=20)

        model.s = Set(ordered=True, initialize=Crangeset('s', 1, 64))
        # model.ss_tuple = Set(ordered=True, initialize=list(
        #     itertools.combinations(list(model.s.data()), 2)))
        # model.ss_tuple.pprint()

        def _ss_tuple(model):
            temp = list(itertools.combinations(list(model.s.data()), 2))
            res = []
            for (s1, s2) in temp:
                num1 = int(s1[1:]) - 1
                num2 = int(s2[1:]) - 1
                if bin(num1 ^ num2)[2:].count('1') == 1:
                    res.append((s1, s2))
            return res
        model.ss_tuple = Set(dimen=2, ordered=True, initialize=_ss_tuple)

        def _w_ss(model, s1, s2):
            num1 = int(s1[1:]) - 1
            num2 = int(s2[1:]) - 1
            temp = []
            for index, i in enumerate(bin(num1 ^ num2)[2:]):
                if i == '1':
                    for j in range(5):
                        temp.append(
                            'w' + str((len(bin(num1 ^ num2)[2:]) - index - 1) * 5 + j + 1))
            return temp

        model.w_ss = Set(model.ss_tuple, initialize=_w_ss)

        def _prob(model, s):
            return 1 / 64
        model.prob = Param(model.s, initialize=_prob)

        model.tau_d = Param(initialize=1)
        model.tau_c1 = Param(initialize=1)
        model.tau_c2 = Param(initialize=1)

        def _w_w(model, w):
            if int(w[1:]) % 10 == 1:
                return ['w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]
            elif int(w[1:]) % 10 == 2:
                return ['w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]
            elif int(w[1:]) % 10 == 9:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1)]
            elif int(w[1:]) % 10 == 0:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1)]
            else:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]

        model.w_w = Set(model.w, initialize=_w_w)

        model.w_p = Set(model.p, initialize={'p1': ['w1', 'w2', 'w11', 'w12'],
                                             'p2': ['w1', 'w2', 'w3', 'w11', 'w12', 'w13'],
                                             'p3': ['w2', 'w3', 'w4', 'w12', 'w13', 'w14'],
                                             'p4': ['w3', 'w4', 'w5', 'w13', 'w14', 'w15'],
                                             'p5': ['w4', 'w5', 'w14', 'w15'],
                                             'p6': ['w6', 'w7', 'w16', 'w17'],
                                             'p7': ['w6', 'w7', 'w8', 'w16', 'w17', 'w18'],
                                             'p8': ['w7', 'w8', 'w9', 'w17', 'w18', 'w19'],
                                             'p9': ['w8', 'w9', 'w10', 'w18', 'w19', 'w20'],
                                             'p10': ['w9', 'w10', 'w19', 'w20'],
                                             'p11': ['w11', 'w12', 'w21', 'w22'],
                                             'p12': ['w11', 'w12', 'w13', 'w21', 'w22', 'w23'],
                                             'p13': ['w12', 'w13', 'w14', 'w22', 'w23', 'w24'],
                                             'p14': ['w13', 'w14', 'w15', 'w23', 'w24', 'w25'],
                                             'p15': ['w14', 'w15', 'w24', 'w25'],
                                             'p16': ['w16', 'w17', 'w26', 'w27'],
                                             'p17': ['w16', 'w17', 'w18', 'w26', 'w27', 'w28'],
                                             'p18': ['w17', 'w18', 'w19', 'w27', 'w28', 'w29'],
                                             'p19': ['w18', 'w19', 'w20', 'w28', 'w29', 'w30'],
                                             'p20': ['w19', 'w20', 'w29', 'w30'],
                                             })

        def _wp(model):
            return ((w, p) for p in model.p for w in model.w_p[p])

        model.wp_tuple = Set(dimen=2, initialize=_wp)

        def _wwp(model):
            return ((w, w2, p) for p in model.p for w in model.w_p[p] for w2 in model.w_w[w])

        model.wwp_tuple = Set(dimen=3, initialize=_wwp)

        def _p_w(model, m):
            temp = []
            for k, v in model.wp_tuple.data():
                if k == m:
                    temp.append(v)
            return temp

        model.p_w = Set(model.w, initialize=_p_w)

        model.j_q = Set(initialize=['j4'])
        j_q = 'j4'

        def _n_m(model, m):
            temp = []
            if m[0] == 'j':
                temp.append('p' + str(int(m[1:]) * 5))
                if int(m[1:]) % 2 != 0:
                    temp.append('p' + str(int(m[1:]) * 5 + 1))
                if (int(m[1:]) - 1) // 2 == 0:
                    temp.append('j' + str(int(m[1:]) + 2))
                elif (int(m[1:]) - 1) // 2 == 1:
                    temp.append('j' + str(int(m[1:]) - 2))
                if m == j_q:
                    temp.append(q)
            if m[0] == 'p':
                if int(m[1:]) % 5 == 1:
                    temp.append('p' + str(int(m[1:]) + 1))
                    if int(m[1:]) % 10 != 1:
                        temp.append('j' + str(int(m[1:]) // 5))
                elif int(m[1:]) % 5 == 0:
                    temp.append('p' + str(int(m[1:]) - 1))
                    temp.append('j' + str(int(m[1:]) // 5))
                else:
                    temp.append('p' + str(int(m[1:]) - 1))
                    temp.append('p' + str(int(m[1:]) + 1))

            return temp

        model.n_m = Set(model.m, initialize=_n_m)

        def _m_n(model):
            return ((m, n) for m in model.m for n in model.n_m[m])

        model.m_n_tuple = Set(dimen=2, initialize=_m_n)
        model.n_n_tuple = model.m_n_tuple | Set(dimen=2, initialize=[(q, j_q)])

        def _m_n_in(model, m):
            temp = []
            if m[0] == 'j':
                temp.append('p' + str(int(m[1:]) * 5))
                if int(m[1:]) % 2 == 0 and int(m[1:]) // 2 > 1:
                    temp.append('j' + str(int(m[1:]) - 2))
            if m[0] == 'p':
                if int(m[1:]) % 10 == 1:
                    return temp
                elif int(m[1:]) % 5 == 1:
                    temp.append('j' + str(int(m[1:]) // 5))
                else:
                    temp.append('p' + str(int(m[1:]) - 1))
            return temp

        model.n_m_in = Set(model.m, initialize=_m_n_in)
        # model.n_m_in.pprint()

        def _m_n_out(model, m):
            temp = []
            if m[0] == 'j':
                if m == j_q:
                    temp.append(q)
                elif int(m[1:]) % 2 == 0:
                    temp.append('j' + str(int(m[1:]) + 2))
                else:
                    temp.append('p' + str(int(m[1:]) * 5 + 1))
            if m[0] == 'p':
                if int(m[1:]) % 5 == 0:
                    temp.append('j' + str(int(m[1:]) // 5))
                else:
                    temp.append('p' + str(int(m[1:]) + 1))
            return temp

        model.n_m_out = Set(model.m, initialize=_m_n_out)
        # model.n_m_out.pprint()

        def _m_n_tuple_fixed(model):
            return ((m, n) for m in model.m for n in model.n_m_out[m])

        model.m_n_tuple_fixed = Set(dimen=2, initialize=_m_n_tuple_fixed)
        # model.m_n_tuple_fixed.pprint()

        def _wpss_tuple(model):
            return ((w, p, s1, s2) for s1, s2 in model.ss_tuple for w in model.w_ss[s1, s2] for p in model.p_w[w])
        model.wpss_tuple = Set(dimen=4, initialize=_wpss_tuple)

        def _tt(model):
            return ((t, t2) for t in model.t for t2 in model.t if t2 < t)

        model.tt_tuple = Set(dimen=2, initialize=_tt)

        def _t_t(model):
            return ((t, t2) for t in model.t_ for t2 in model.t_ if t2 < t)

        model.t_t_tuple = Set(dimen=2, initialize=_t_t)

        # parameter

        def _l(model, n, n2):
            if n[0] == 'p' and n2[0] == 'p':
                return 20
            if (n[0] == 'p' and n2[0] == 'j') or (n[0] == 'j' and n2[0] == 'p'):
                return 10
            else:
                return 100

        model.l = Param(model.n_n_tuple, initialize=_l)
        model.K = Param(initialize=25)    # the number of gas junction node

        def _ProductionFactor(model, w, s):
            data = [0.8, 0.95, 0.95, 0.85, 1.05, 1]
            temp = s[1:]
            temp = bin(int(temp)-1)[2:]
            if len(temp) < len(data):
                temp = '0'*(len(data)-len(temp))+temp
            for i in range(len(data)):
                if temp[i] == '0':
                    data[i] = data[i]*0.9
                elif temp[i] == '1':
                    data[i] = data[i]*1.1
            return data[int((int(w[1:]) - 1) / 5)]

        model.ProductionFactor = Param(
            model.w, model.s, initialize=_ProductionFactor)

        def _drill_cost(model, w, p, f):
            if f == 'f1':
                if int(w[1:]) == int(p[1:]) or int(w[1:]) == int(p[1:]) + 10:
                    return 1187100
                else:
                    return 1457100
            elif f == 'f2':
                if int(w[1:]) == int(p[1:]) or int(w[1:]) == int(p[1:]) + 10:
                    return 1208700
                else:
                    return 1478700
        model.drill_cost = Param(
            model.wp_tuple, model.f, initialize=_drill_cost)

        ###############################################################################
        ################################  Medium case (end)############################
        ###############################################################################
    elif case_flag == 3:
        ###############################################################################
        ################################  Small case (start)###########################
        ############################# 20 wells and 10 pads ############################
        ###############################################################################

        # set

        model.w = Set(ordered=True, initialize=Crangeset('w', 1, 20))
        model.p = Set(ordered=True, initialize=Crangeset('p', 1, 10))
        model.f = Set(ordered=True, initialize=Crangeset('f', 1, 2))
        model.j = Set(ordered=True, initialize=Crangeset('j', 1, 2))
        model.q = Set(initialize=['q'])
        q = 'q'
        model.jq = model.j | model.q
        model.m = model.p | model.j
        model.n = model.m | model.q
        model.d = Set(ordered=True, initialize=Crangeset(
            'd', 1, 3))  # number of pipeline diameters
        model.r = Set(ordered=True, initialize=Crangeset(
            'r', 1, 4))  # number of rigs

        # length of period and related parameter
        model.t = Set(ordered=True, initialize=list(range(1, 37)))
        model.t_ = Set(ordered=True, initialize=list(range(2, 37)))
        num_periods_per_month = 2
        model.g = Param(initialize=20)

        model.s = Set(ordered=True, initialize=Crangeset('s', 1, 16))
        # model.ss_tuple = Set(ordered=True, initialize=list(
        #     itertools.combinations(list(model.s.data()), 2)))
        # model.ss_tuple.pprint()

        def _ss_tuple(model):
            temp = list(itertools.combinations(list(model.s.data()), 2))
            res = []
            for (s1, s2) in temp:
                num1 = int(s1[1:]) - 1
                num2 = int(s2[1:]) - 1
                if bin(num1 ^ num2)[2:].count('1') == 1:
                    res.append((s1, s2))
            return res
        model.ss_tuple = Set(dimen=2, ordered=True, initialize=_ss_tuple)
        # model.ss_tuple.pprint()

        def _w_ss(model, s1, s2):
            num1 = int(s1[1:]) - 1
            num2 = int(s2[1:]) - 1
            temp = []
            for index, i in enumerate(bin(num1 ^ num2)[2:]):
                if i == '1':
                    for j in range(5):
                        temp.append(
                            'w' + str((len(bin(num1 ^ num2)[2:]) - index - 1) * 5 + j + 1))
            return temp

        model.w_ss = Set(model.ss_tuple, initialize=_w_ss)

        def _prob(model, s):
            return 1 / 16
        model.prob = Param(model.s, initialize=_prob)

        model.tau_d = Param(initialize=1)
        model.tau_c1 = Param(initialize=1)
        model.tau_c2 = Param(initialize=1)

        def _w_w(model, w):
            if int(w[1:]) % 10 == 1:
                return ['w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]
            elif int(w[1:]) % 10 == 2:
                return ['w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]
            elif int(w[1:]) % 10 == 9:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1)]
            elif int(w[1:]) % 10 == 0:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1)]
            else:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]

        model.w_w = Set(model.w, initialize=_w_w)

        model.w_p = Set(model.p, initialize={'p1': ['w1', 'w2', 'w11', 'w12'],
                                             'p2': ['w1', 'w2', 'w3', 'w11', 'w12', 'w13'],
                                             'p3': ['w2', 'w3', 'w4', 'w12', 'w13', 'w14'],
                                             'p4': ['w3', 'w4', 'w5', 'w13', 'w14', 'w15'],
                                             'p5': ['w4', 'w5', 'w14', 'w15'],
                                             'p6': ['w6', 'w7', 'w16', 'w17'],
                                             'p7': ['w6', 'w7', 'w8', 'w16', 'w17', 'w18'],
                                             'p8': ['w7', 'w8', 'w9', 'w17', 'w18', 'w19'],
                                             'p9': ['w8', 'w9', 'w10', 'w18', 'w19', 'w20'],
                                             'p10': ['w9', 'w10', 'w19', 'w20'],
                                             })

        def _wp(model):
            return ((w, p) for p in model.p for w in model.w_p[p])

        model.wp_tuple = Set(dimen=2, initialize=_wp)

        def _wwp(model):
            return ((w, w2, p) for p in model.p for w in model.w_p[p] for w2 in model.w_w[w])

        model.wwp_tuple = Set(dimen=3, initialize=_wwp)

        def _p_w(model, m):
            temp = []
            for k, v in model.wp_tuple.data():
                if k == m:
                    temp.append(v)
            return temp

        model.p_w = Set(model.w, initialize=_p_w)

        model.j_q = Set(initialize=['j2'])
        j_q = 'j2'

        def _n_m(model, m):
            temp = []
            if m[0] == 'j':
                temp.append('p' + str(int(m[1:]) * 5))
                if int(m[1:]) % 2 != 0:
                    temp.append('p' + str(int(m[1:]) * 5 + 1))
                # if (int(m[1:]) - 1) // 2 == 0:
                #     temp.append('j' + str(int(m[1:]) + 2))
                # elif (int(m[1:]) - 1) // 2 == 1:
                #     temp.append('j' + str(int(m[1:]) - 2))
                if m == j_q:
                    temp.append(q)
            if m[0] == 'p':
                if int(m[1:]) % 5 == 1:
                    temp.append('p' + str(int(m[1:]) + 1))
                    if int(m[1:]) % 10 != 1:
                        temp.append('j' + str(int(m[1:]) // 5))
                elif int(m[1:]) % 5 == 0:
                    temp.append('p' + str(int(m[1:]) - 1))
                    temp.append('j' + str(int(m[1:]) // 5))
                else:
                    temp.append('p' + str(int(m[1:]) - 1))
                    temp.append('p' + str(int(m[1:]) + 1))

            return temp

        model.n_m = Set(model.m, initialize=_n_m)

        def _m_n_in(model, m):
            temp = []
            if m[0] == 'j':
                temp.append('p' + str(int(m[1:]) * 5))
            if m[0] == 'p':
                if int(m[1:]) % 10 == 1:
                    return temp
                elif int(m[1:]) % 5 == 1:
                    temp.append('j' + str(int(m[1:]) // 5))
                else:
                    temp.append('p' + str(int(m[1:]) - 1))
            return temp

        model.n_m_in = Set(model.m, initialize=_m_n_in)
        # model.n_m_in.pprint()

        def _m_n_out(model, m):
            temp = []
            if m[0] == 'j':
                if m == j_q:
                    temp.append(q)
                else:
                    temp.append('p' + str(int(m[1:]) * 5 + 1))
            if m[0] == 'p':
                if int(m[1:]) % 5 == 0:
                    temp.append('j' + str(int(m[1:]) // 5))
                else:
                    temp.append('p' + str(int(m[1:]) + 1))
            return temp

        model.n_m_out = Set(model.m, initialize=_m_n_out)
        # model.n_m_out.pprint()

        def _m_n_tuple_fixed(model):
            return ((m, n) for m in model.m for n in model.n_m_out[m])

        model.m_n_tuple_fixed = Set(dimen=2, initialize=_m_n_tuple_fixed)
        # model.m_n_tuple_fixed.pprint()
        # model.m_n_tuple_fixed = Set(dimen=2, initialize=[('p1', 'p2'), ('p2', 'p3'), ('p3', 'p4'), ('p4', 'p5'), ('p5', 'j1'), ('j1', 'q')])

        def _m_n(model):
            return ((m, n) for m in model.m for n in model.n_m[m])

        model.m_n_tuple = Set(dimen=2, initialize=_m_n)
        model.n_n_tuple = model.m_n_tuple | Set(dimen=2, initialize=[(q, j_q)])

        def _wpss_tuple(model):
            return ((w, p, s1, s2) for s1, s2 in model.ss_tuple for w in model.w_ss[s1, s2] for p in model.p_w[w])
        model.wpss_tuple = Set(dimen=4, initialize=_wpss_tuple)

        def _tt(model):
            return ((t, t2) for t in model.t for t2 in model.t if t2 < t)

        model.tt_tuple = Set(dimen=2, initialize=_tt)

        def _t_t(model):
            return ((t, t2) for t in model.t_ for t2 in model.t_ if t2 < t)

        model.t_t_tuple = Set(dimen=2, initialize=_t_t)

        # parameter

        def _l(model, n, n2):
            if n[0] == 'p' and n2[0] == 'p':
                return 20
            if (n[0] == 'p' and n2[0] == 'j') or (n[0] == 'j' and n2[0] == 'p'):
                return 10
            else:
                return 100

        model.l = Param(model.n_n_tuple, initialize=_l)
        model.K = Param(initialize=25)    # the number of gas junction node

        def _ProductionFactor(model, w, s):
            data = [0.8, 0.95, 0.95, 0.85]
            temp = s[1:]
            temp = bin(int(temp)-1)[2:]
            if len(temp) < len(data):
                temp = '0'*(len(data)-len(temp))+temp
            for i in range(len(data)):
                if temp[i] == '0':
                    data[i] = data[i]*0.9
                elif temp[i] == '1':
                    data[i] = data[i]*1.1
            return data[int((int(w[1:]) - 1) / 5)]

        model.ProductionFactor = Param(
            model.w, model.s, initialize=_ProductionFactor)

        def _drill_cost(model, w, p, f):
            if f == 'f1':
                if int(w[1:]) == int(p[1:]) or int(w[1:]) == int(p[1:]) + 10:
                    return 1187100
                else:
                    return 1457100
            elif f == 'f2':
                if int(w[1:]) == int(p[1:]) or int(w[1:]) == int(p[1:]) + 10:
                    return 1208700
                else:
                    return 1478700
        model.drill_cost = Param(
            model.wp_tuple, model.f, initialize=_drill_cost)

        ###############################################################################
        ################################  Small case (end)#############################
        ###############################################################################
    if case_flag == 4:

        ###############################################################################
        ################################  Tiny case (start)############################
        ############################# 10 wells and 5 pads #############################
        ###############################################################################

        # set

        model.w = Set(ordered=True, initialize=Crangeset('w', 1, 10))
        model.p = Set(ordered=True, initialize=Crangeset('p', 1, 5))
        model.f = Set(ordered=True, initialize=Crangeset('f', 1, 2))
        model.j = Set(ordered=True, initialize=Crangeset('j', 1, 1))
        model.q = Set(initialize=['q'])
        q = 'q'
        model.jq = model.j | model.q
        model.m = model.p | model.j
        model.n = model.m | model.q
        model.d = Set(ordered=True, initialize=Crangeset(
            'd', 1, 3))  # number of pipeline diameters
        model.r = Set(ordered=True, initialize=Crangeset(
            'r', 1, 4))  # number of rigs

        # length of period and related parameter
        model.t = Set(ordered=True, initialize=list(range(1, 37)))
        model.t_ = Set(ordered=True, initialize=list(range(2, 37)))
        # model.t = Set(ordered=True, initialize=list(range(1, 25)))
        # model.t = Set(ordered=True, initialize=list(range(1, 13)))
        num_periods_per_month = 2
        model.g = Param(initialize=20)

        model.s = Set(ordered=True, initialize=Crangeset('s', 1, 4))

        def _ss_tuple(model):
            temp = list(itertools.combinations(list(model.s.data()), 2))
            res = []
            for (s1, s2) in temp:
                num1 = int(s1[1:]) - 1
                num2 = int(s2[1:]) - 1
                if bin(num1 ^ num2)[2:].count('1') == 1:
                    res.append((s1, s2))
            return res
        model.ss_tuple = Set(dimen=2, ordered=True, initialize=_ss_tuple)
        # model.ss_tuple = Set(ordered=True, initialize=list(
        #     itertools.combinations(list(model.s.data()), 2)))
        # model.ss_tuple.pprint()

        def _w_ss(model, s1, s2):
            num1 = int(s1[1:]) - 1
            num2 = int(s2[1:]) - 1
            temp = []
            for index, i in enumerate(bin(num1 ^ num2)[2:]):
                if i == '1':
                    for j in range(5):
                        temp.append(
                            'w' + str((len(bin(num1 ^ num2)[2:]) - index - 1) * 5 + j + 1))
            return temp

        model.w_ss = Set(model.ss_tuple, initialize=_w_ss)
        # model.w_ss.pprint()
        # model.w_ss = Set(model.ss_tuple, initialize={('s1', 's2'): ['w6', 'w7', 'w8', 'w9', 'w10'],
        #                                              ('s1', 's3'): ['w1', 'w2', 'w3', 'w4', 'w5'],
        #                                              ('s1', 's4'): ['w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8', 'w9', 'w10'],
        #                                              ('s2', 's3'): ['w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8', 'w9', 'w10'],
        #                                              ('s2', 's4'): ['w1', 'w2', 'w3', 'w4', 'w5'],
        #                                              ('s3', 's4'): ['w6', 'w7', 'w8', 'w9', 'w10'],
        #                                              })
        # model.w_ss.pprint()
        model.prob = Param(model.s, initialize={'s1': 0.25,
                                                's2': 0.25,
                                                's3': 0.25,
                                                's4': 0.25})

        model.tau_d = Param(initialize=1)
        model.tau_c1 = Param(initialize=1)
        model.tau_c2 = Param(initialize=1)

        def _w_w(model, w):
            if int(w[1:]) % 5 == 1:
                return ['w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]
            elif int(w[1:]) % 5 == 2:
                return ['w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]
            elif int(w[1:]) % 5 == 4:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1)]
            elif int(w[1:]) % 5 == 0:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1)]
            else:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]

        model.w_w = Set(model.w, initialize=_w_w)

        model.w_p = Set(model.p, initialize={'p1': ['w1', 'w2', 'w6', 'w7'],
                                             'p2': ['w1', 'w2', 'w3', 'w6', 'w7', 'w8'],
                                             'p3': ['w2', 'w3', 'w4', 'w7', 'w8', 'w9'],
                                             'p4': ['w3', 'w4', 'w5', 'w8', 'w9', 'w10'],
                                             'p5': ['w4', 'w5', 'w9', 'w10'],
                                             })

        def _wp(model):
            return ((w, p) for p in model.p for w in model.w_p[p])

        model.wp_tuple = Set(dimen=2, initialize=_wp)

        def _wwp(model):
            return ((w, w2, p) for p in model.p for w in model.w_p[p] for w2 in model.w_w[w])

        model.wwp_tuple = Set(dimen=3, initialize=_wwp)

        def _p_w(model, m):
            temp = []
            for k, v in model.wp_tuple.data():
                if k == m:
                    temp.append(v)
            return temp

        model.p_w = Set(model.w, initialize=_p_w)

        model.j_q = Set(initialize=['j1'])
        j_q = 'j1'

        def _n_m(model, m):
            temp = []
            if m[0] == 'j':
                temp.append('p' + str(int(m[1:]) * 5))
                if m == j_q:
                    temp.append(q)
            if m[0] == 'p':
                if int(m[1:]) % 5 == 1:
                    temp.append('p' + str(int(m[1:]) + 1))
                    if int(m[1:]) % 10 != 1:
                        temp.append('j' + str(int(m[1:]) // 5))
                elif int(m[1:]) % 5 == 0:
                    temp.append('p' + str(int(m[1:]) - 1))
                    temp.append('j' + str(int(m[1:]) // 5))
                else:
                    temp.append('p' + str(int(m[1:]) - 1))
                    temp.append('p' + str(int(m[1:]) + 1))

            return temp

        model.n_m = Set(model.m, initialize=_n_m)

        def _m_n(model):
            return ((m, n) for m in model.m for n in model.n_m[m])

        model.m_n_tuple = Set(dimen=2, initialize=_m_n)
        model.n_n_tuple = model.m_n_tuple | Set(dimen=2, initialize=[(q, j_q)])

        model.n_m_in = Set(model.m, initialize={'p1': '',
                                                'p2': ['p1'],
                                                'p3': ['p2'],
                                                'p4': ['p3'],
                                                'p5': ['p4'],
                                                'j1': ['p5']})
        # model.n_m_in.pprint()
        model.n_m_out = Set(model.m, initialize={'p1': ['p2'],
                                                 'p2': ['p3'],
                                                 'p3': ['p4'],
                                                 'p4': ['p5'],
                                                 'p5': ['j1'],
                                                 'j1': ['q']})
        # model.n_m_out.pprint()
        model.m_n_tuple_fixed = Set(dimen=2, initialize=[(
            'p1', 'p2'), ('p2', 'p3'), ('p3', 'p4'), ('p4', 'p5'), ('p5', 'j1'), ('j1', 'q')])

        def _wpss_tuple(model):
            return ((w, p, s1, s2) for s1, s2 in model.ss_tuple for w in model.w_ss[s1, s2] for p in model.p_w[w])
        model.wpss_tuple = Set(dimen=4, initialize=_wpss_tuple)

        def _tt(model):
            return ((t, t2) for t in model.t for t2 in model.t if t2 < t)

        model.tt_tuple = Set(dimen=2, initialize=_tt)

        def _t_t(model):
            return ((t, t2) for t in model.t_ for t2 in model.t_ if t2 < t)

        model.t_t_tuple = Set(dimen=2, initialize=_t_t)

        # parameter

        def _l(model, n, n2):
            if n[0] == 'p' and n2[0] == 'p':
                return 20
            if (n[0] == 'p' and n2[0] == 'j') or (n[0] == 'j' and n2[0] == 'p'):
                return 10
            else:
                return 100

        model.l = Param(model.n_n_tuple, initialize=_l)
        # model.l.pprint()
        model.K = Param(initialize=25)    # the number of gas junction node

        # def _ProductionFactor(model, w):
        #     data = [0.8, 0.95]
        #     return data[int((int(w[1:]) - 1) / 5)]

        # model.ProductionFactor = Param(model.w, initialize=_ProductionFactor)

        # def _ProductionFactor(model, w, s):
        #     data = [0.8, 0.95]
        #     temp = s[1:]
        #     temp = bin(int(temp)-1)[2:]
        #     if len(temp) < len(data):
        #         temp = '0'*(len(data)-len(temp))+temp
        #     for i in range(len(data)):
        #         if temp[i] == '0':
        #             data[i] = data[i]*0.9
        #         elif temp[i] == '1':
        #             data[i] = data[i]*1.1
        #     return data[int((int(w[1:]) - 1) / 5)]

        # to test the [0.81,0.99] and [0.66,1.54]
        def _ProductionFactor(model, w, s):
            data = [0.9, 1.1]
            temp = s[1:]
            temp = bin(int(temp)-1)[2:]
            if len(temp) < len(data):
                temp = '0'*(len(data)-len(temp))+temp
            if int(w[1:]) <= 5:
                for i in range(len(data)):
                    if temp[i] == '0':
                        data[i] = data[i]*0.9
                    elif temp[i] == '1':
                        data[i] = data[i]*1.1
            else:
                for i in range(len(data)):
                    if temp[i] == '0':
                        data[i] = data[i]*0.6
                    elif temp[i] == '1':
                        data[i] = data[i]*1.4
            return data[int((int(w[1:]) - 1) / 5)]

        model.ProductionFactor = Param(
            model.w, model.s, initialize=_ProductionFactor)
        # model.ProductionFactor.pprint()

        def _drill_cost(model, w, p, f):
            if f == 'f1':
                if int(w[1:]) == int(p[1:]) or int(w[1:]) == int(p[1:]) + 5:
                    return 1187100
                else:
                    return 1457100
            elif f == 'f2':
                if int(w[1:]) == int(p[1:]) or int(w[1:]) == int(p[1:]) + 5:
                    return 1208700
                else:
                    return 1478700
        model.drill_cost = Param(
            model.wp_tuple, model.f, initialize=_drill_cost)

        ###############################################################################
        ################################  Tiny case (end)##############################
        ###############################################################################

    if case_flag == 5:
        ###############################################################################
        #############################  Tiny tiny case (start)##########################
        ############################## 5 wells and 5 pads #############################
        ###############################################################################

        # set

        model.w = Set(ordered=True, initialize=Crangeset('w', 1, 5))
        model.p = Set(ordered=True, initialize=Crangeset('p', 1, 5))
        model.f = Set(ordered=True, initialize=Crangeset('f', 1, 2))
        model.j = Set(ordered=True, initialize=Crangeset('j', 1, 1))
        model.q = Set(initialize=['q'])
        q = 'q'
        model.jq = model.j | model.q
        model.m = model.p | model.j
        model.n = model.m | model.q
        model.d = Set(ordered=True, initialize=Crangeset(
            'd', 1, 3))  # number of pipeline diameters
        model.r = Set(ordered=True, initialize=Crangeset(
            'r', 1, 4))  # number of rigs

        # length of period and related parameter
        model.t = Set(ordered=True, initialize=list(range(1, 49)))
        # model.t = Set(ordered=True, initialize=list(range(1, 25)))
        # model.t = Set(ordered=True, initialize=list(range(1, 13)))
        num_periods_per_month = 2
        model.g = Param(initialize=20)

        model.tau_d = Param(initialize=1)
        model.tau_c1 = Param(initialize=1)
        model.tau_c2 = Param(initialize=1)

        def _w_w(model, w):
            if int(w[1:]) % 5 == 1:
                return ['w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]
            elif int(w[1:]) % 5 == 2:
                return ['w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]
            elif int(w[1:]) % 5 == 4:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1)]
            elif int(w[1:]) % 5 == 0:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1)]
            else:
                return ['w' + str(int(w[1:]) - 2), 'w' + str(int(w[1:]) - 1), 'w' + str(int(w[1:]) + 1), 'w' + str(int(w[1:]) + 2)]

        model.w_w = Set(model.w, initialize=_w_w)

        model.w_p = Set(model.p, initialize={'p1': ['w1', 'w2'],
                                             'p2': ['w1', 'w2', 'w3'],
                                             'p3': ['w2', 'w3', 'w4'],
                                             'p4': ['w3', 'w4', 'w5'],
                                             'p5': ['w4', 'w5'],
                                             })

        def _wp(model):
            return ((w, p) for p in model.p for w in model.w_p[p])

        model.wp_tuple = Set(dimen=2, initialize=_wp)

        def _wwp(model):
            return ((w, w2, p) for p in model.p for w in model.w_p[p] for w2 in model.w_w[w])

        model.wwp_tuple = Set(dimen=3, initialize=_wwp)

        def _p_w(model, m):
            temp = []
            for k, v in model.wp_tuple.data():
                if k == m:
                    temp.append(v)
            return temp

        model.p_w = Set(model.w, initialize=_p_w)

        model.j_q = Set(initialize=['j1'])
        j_q = 'j1'

        def _n_m(model, m):
            temp = []
            if m[0] == 'j':
                temp.append('p' + str(int(m[1:]) * 5))
                if m == j_q:
                    temp.append(q)
            if m[0] == 'p':
                if int(m[1:]) % 5 == 1:
                    temp.append('p' + str(int(m[1:]) + 1))
                    if int(m[1:]) % 10 != 1:
                        temp.append('j' + str(int(m[1:]) // 5))
                elif int(m[1:]) % 5 == 0:
                    temp.append('p' + str(int(m[1:]) - 1))
                    temp.append('j' + str(int(m[1:]) // 5))
                else:
                    temp.append('p' + str(int(m[1:]) - 1))
                    temp.append('p' + str(int(m[1:]) + 1))

            return temp

        model.n_m = Set(model.m, initialize=_n_m)

        # model.n_m.pprint()

        def _m_n(model):
            return ((m, n) for m in model.m for n in model.n_m[m])

        model.m_n_tuple = Set(dimen=2, initialize=_m_n)
        model.n_n_tuple = model.m_n_tuple | Set(dimen=2, initialize=[(q, j_q)])

        model.n_m_in = Set(model.m, initialize={'p1': '',
                                                'p2': ['p1'],
                                                'p3': ['p2'],
                                                'p4': ['p3'],
                                                'p5': ['p4'],
                                                'j1': ['p5']})
        # model.n_m_in.pprint()
        model.n_m_out = Set(model.m, initialize={'p1': ['p2'],
                                                 'p2': ['p3'],
                                                 'p3': ['p4'],
                                                 'p4': ['p5'],
                                                 'p5': ['j1'],
                                                 'j1': ['q']})
        # model.n_m_out.pprint()
        model.m_n_tuple_fixed = Set(dimen=2, initialize=[(
            'p1', 'p2'), ('p2', 'p3'), ('p3', 'p4'), ('p4', 'p5'), ('p5', 'j1'), ('j1', 'q')])

        # parameter

        def _l(model, n, n2):
            if n[0] == 'p' and n2[0] == 'p':
                return 20
            if (n[0] == 'p' and n2[0] == 'j') or (n[0] == 'j' and n2[0] == 'p'):
                return 10
            else:
                return 100

        model.l = Param(model.n_n_tuple, initialize=_l)
        # model.l.pprint()
        model.K = Param(initialize=25)    # the number of gas junction node

        def _ProductionFactor(model, w):
            data = [0.8, 0.95]
            return data[int((int(w[1:]) - 1) / 5)]

        model.ProductionFactor = Param(model.w, initialize=_ProductionFactor)

        def _drill_cost(model, w, p, f):
            if f == 'f1':
                if int(w[1:]) == int(p[1:]):
                    return 1187100
                else:
                    return 1457100
            elif f == 'f2':
                if int(w[1:]) == int(p[1:]):
                    return 1208700
                else:
                    return 1478700
        model.drill_cost = Param(
            model.wp_tuple, model.f, initialize=_drill_cost)

    ###############################################################################
    ##############################  Tiny tiny case (end)###########################
    ###############################################################################
    model.extended_t = Set(ordered=True, initialize=list(range(1, 91)))
    model.H = Param(initialize=100)

    model.max_well = Param(initialize=6)
    model.max_swd = Param(initialize=6)
    model.max_oil = Param(initialize=12)
    model.max_heater = Param(initialize=6)
    model.max_separator = Param(initialize=6)
    model.swd_capacity = Param(initialize=100000)
    # model.relocation_duration = Param(initialize=4)
    # model.fracprep_duration = Param(initialize=2)
    # model.fracshutin_duration = Param(initialize=14)
    # model.drill_duration = Param(model.f, initialize={'f1': 14,
    #                                                   'f2': 16})

    model.relocation_cost = Param(initialize=100000)
    model.comp_cost = Param(model.f, initialize={'f1': 2807100,
                                                 'f2': 2537100})

    gamma_gas_f1 = [369, 585, 929, 1077, 941, 838, 757, 692, 637, 592, 553, 519, 489, 463, 440, 419, 400,
                    383, 368, 354, 341, 329, 318, 307, 298, 289, 280, 272, 265, 258, 251, 245, 239, 234, 228, 223,
                    218, 212, 207, 202, 198, 194, 189, 185, 181, 178, 174, 170,
                    167, 163, 160, 157, 154, 152, 149, 147, 145, 144, 142, 141]

    gamma_gas_f2 = [307, 707, 664, 626, 591, 560, 531, 505, 481, 459, 439, 420, 403, 386, 371, 357, 344,
                    332, 320, 309, 299, 289, 280, 271, 263, 255, 248, 241, 234, 228, 222, 216, 210, 205, 200, 195,
                    190, 185, 181, 177, 173, 169, 166, 163, 160, 157, 154, 151,
                    148, 145, 142, 140, 138, 136, 134, 132, 130, 128, 126, 124, ]

    def _gamma_gas(model, f, t):
        if f == 'f1':
            return gamma_gas_f1[(t - 1) // num_periods_per_month]
        elif f == 'f2':
            return gamma_gas_f2[(t - 1) // num_periods_per_month]

    model.gamma_gas = Param(model.f, model.extended_t, initialize=_gamma_gas)

    gamma_oil_f1 = [147, 233, 370, 378, 274, 218, 182, 157, 139, 124, 113, 104, 96, 89, 83,
                    79, 74, 70, 67, 64, 61, 59, 56, 54, 52, 50, 49, 47, 46, 44, 43, 42, 41, 40, 39, 38,
                    37, 36, 35, 34, 33, 33, 32, 32, 31, 31, 30, 30,
                    29, 29, 29, 28, 28, 27, 27, 27, 26, 26, 26, 25
                    ]

    gamma_oil_f2 = [190, 434, 340, 282, 242, 212, 190, 172, 157, 145, 135, 126, 119, 112, 106,
                    101, 96, 92, 88, 85, 82, 79, 76, 73, 71, 69, 67, 65, 63, 61, 60, 58, 57, 55, 54, 53,
                    52, 51, 50, 49, 48, 48, 47, 47, 46, 46, 45, 45,
                    45, 44, 44, 44, 43, 43, 43, 42, 42, 42, 41, 41,
                    ]

    def _gamma_oil(model, f, t):
        if f == 'f1':
            return gamma_oil_f1[(t - 1) // num_periods_per_month]
        elif f == 'f2':
            return gamma_oil_f2[(t - 1) // num_periods_per_month]

    model.gamma_oil = Param(model.f, model.extended_t, initialize=_gamma_oil)
    model.max_f = Param(initialize=28707.4333103344)  # for lineariztion

    c_loe_v_f1 = [412, 383, 459, 485, 419, 369, 330, 300, 275, 254, 237, 221, 208, 196, 186, 176, 168,
                  161, 154, 148, 142, 137, 132, 128, 123, 120, 116, 113, 110, 106, 104, 101, 98, 96, 94, 92,
                  90, 88, 86, 84, 82, 80, 78, 76, 74, 72, 71, 70,
                  69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 60, 59,
                  ]

    c_loe_v_f2 = [338, 415, 365, 329, 302, 279, 260, 244, 230, 217, 206, 196, 187, 178, 171, 164,
                  158, 151, 146, 140, 136, 131, 127, 123, 119, 115, 113, 109, 106, 103, 100, 97, 95, 93, 90, 88,
                  86, 84, 82, 80, 78, 77, 76, 75, 74, 73, 72, 71,
                  70, 70, 69, 69, 68, 68, 67, 67, 67, 66, 66, 66,
                  ]

    def _c_loe_v(model, f, t):
        if f == 'f1':
            return c_loe_v_f1[(t - 1) // num_periods_per_month]
        elif f == 'f2':
            return c_loe_v_f2[(t - 1) // num_periods_per_month]

    model.c_loe_v = Param(model.f, model.extended_t, initialize=_c_loe_v)
    # model.c_loe_v.pprint()

    def _c_loe_f(model, f, t):
        if (t // num_periods_per_month) <= 12:
            return 14400
        elif (t // num_periods_per_month) <= 24:
            return 9000
        elif (t // num_periods_per_month) <= 36:
            return 5400
        elif (t // num_periods_per_month) <= 48:
            return 3000
        else:
            return 1800

    model.c_loe_f = Param(model.f, model.extended_t, initialize=_c_loe_f)
    # model.c_loe_f.pprint()

    # model.oil
    model.pipe_water_cap = Param(model.d, initialize={'d1': 24603.3534336139,
                                                      'd2': 44172.0563037985,
                                                      'd3': 71253.4657075114, })
    model.pipe_gas_cap = Param(model.d, initialize={'d1': 9723.68100443547,
                                                    'd2': 17643.3251424038,
                                                    'd3': 28707.4333103344, })
    model.pipe_cost = Param(model.d, initialize={'d1': 13.23,
                                                 'd2': 21.006,
                                                 'd3': 29.511, })

    model.pad_fixed_acres = Param(initialize=1.8)
    model.pad_var_acres = Param(initialize=0.2)
    model.return2pad_acres = Param(initialize=0.5)
    model.pad_damage_cost = Param(initialize=9000)
    model.pad_con_cost = Param(initialize=45000)
    model.return2pad_cost = Param(initialize=18000)
    model.annual_discount_factor = Param(initialize=0.10)
    # model.tax = Param(initialize=[(0.02, 36), (0.07, 600)])
    model.gas_price = Param(initialize=69.1)
    model.oil_price = Param(initialize=2.72)
    # model.dr = Param(initialize=13.5 / 400)
    model.dr = Param(initialize=10 / (100 * 24))
    model.rig_relocation = Param(initialize=100000)
    model.tax = Param(initialize=0.09)

    def _scenario_block(b, s):

        # variable

        # binary
        # model.y_dev = Var(model.wp_tuple, model.f, model.t, domain=Binary)

        b.y_drill = Var(model.wp_tuple, model.f,
                        model.t, domain=Binary)
        # model.y_comp = Var(model.wp_tuple, model.f, model.t, domain=Binary)
        b.y_rig = Var(model.r, model.p, model.t, domain=Binary)

        if shutin_flag == True:
            b.y_shut_in = Var(model.wp_tuple, model.f,
                              model.t, domain=Binary)

        if pipeline_flag == True:
            b.y_node = Var(model.m, model.t,  domain=Binary)
            b.y_pipe = Var(model.n_n_tuple, model.t,
                           domain=Binary)
            b.z_pipe = Var(model.n_n_tuple, model.d,
                           model.t, domain=Binary)
            b.f_pipe = Var(model.n_n_tuple, model.t, domain=NonNegativeReals)
            b.v = Var(model.n, model.t, domain=NonNegativeReals)
        else:
            b.f_pipe = Var(model.m_n_tuple_fixed,
                           model.extended_t, domain=NonNegativeReals)
            b.z_pipe = Var(model.m_n_tuple_fixed, model.d,
                           model.t, domain=Binary)

        # continuous
        b.f_gas = Var(model.m, model.extended_t, domain=NonNegativeReals)
        b.f_oil = Var(model.p, model.extended_t, domain=NonNegativeReals)
        b.y_active = Var(model.p, model.t, domain=Binary)
        b.y_rtp_signal = Var(model.p, model.t, domain=Binary)
        b.y_rtp = Var(model.p, model.t, domain=Binary)
        b.rev = Var(model.extended_t, domain=NonNegativeReals)
        b.loe = Var(model.extended_t, domain=NonNegativeReals)
        b.sce = Var(model.t, domain=NonNegativeReals)
        b.fpe = Var(model.t, domain=NonNegativeReals)
        b.dve = Var(model.t, domain=NonNegativeReals)

        ##############
        # Constraint #
        ##############

        ############################################################################################

        # def _comp_together(model, w, p, f, t):
        #     return sum(model.y_comp[w2, p, f2, t] for w2 in model.w_p[p] for f2 in model.f) >= 2 * model.y_comp[w, p, f, t]

        # model.comp_together = Constraint(model.wp_tuple, model.f, model.t, rule=_comp_together)

        # model.y_comp['w3', 'p3', 'f1', 3].fix(1)
        # model.y_comp['w3', 'p3', 'f2', 3].fix(1)

        ############################################################################################
        # Fixed network
        '''
        # model.wpf_drill = Set(dimen=3, initialize=[('w1', 'p2', 'f2'), ('w2', 'p2', 'f1'),
        #                                            ('w3', 'p2', 'f1'), ('w6', 'p6', 'f2'),
        #                                            ('w7', 'p8', 'f2'), ('w8', 'p8', 'f2'),
        #                                            ('w9', 'p8', 'f1'), ('w12', 'p12', 'f2'),
        #                                            ('w13', 'p12', 'f1')
        #                                            ])

        # model.wpf_drill = Set(dimen=3, initialize=[('w1', 'p1', 'f2'), ('w2', 'p2', 'f1'),
        #                                            ('w3', 'p3', 'f1'), ('w6', 'p6', 'f2'),
        #                                            ('w7', 'p7', 'f2'), ('w8', 'p8', 'f2'),
        #                                            ('w9', 'p9', 'f1'), ('w12', 'p12', 'f2'),
        #                                            ('w13', 'p13', 'f1')
        #                                            ])

        model.wpf_drill = Set(dimen=3, initialize=[('w1', 'p2', 'f2'), ('w2', 'p2', 'f1'),
                                                ('w3', 'p2', 'f1'),
                                                # ('w6', 'p6', 'f2'),
                                                # ('w7', 'p7', 'f2'), ('w8', 'p8', 'f2'),
                                                # ('w9', 'p9', 'f1'), ('w12', 'p12', 'f2'),
                                                # ('w13', 'p12', 'f1')
                                                ])


        model.wpf_not_drill = model.wp_tuple * model.f - model.wpf_drill


        def _fix_network1(model, w, p, f):
            return sum(model.y_drill[w, p, f, t] for t in model.t) == 1


        model.fix_network1 = Constraint(model.wpf_drill, rule=_fix_network1)


        def _fix_network2(model, w, p, f):
            return sum(model.y_drill[w, p, f, t] for t in model.t) == 0


        model.fix_network2 = Constraint(
            model.wpf_not_drill, rule=_fix_network2)
        '''
        ############################################################################################

        # 1.  well production constraints
        # a. each well can only be assigned to one formation and one pad once. If well is assigned, it cannot be changed

        def _well_prod(b, w, f):
            return sum(b.y_drill[w, p, f, t] for p in model.p_w[w] for t in model.t) <= 1

        b.well_prod = Constraint(model.w, model.f, rule=_well_prod)
        # print(model.well_prod['w1'].expr)

        # def _well_prod2(model, w, f):
        #     return sum(model.y_comp[w, p, f, t] for p in model.p_w[w] for t in model.t) <= 1

        # model.well_prod2 = Constraint(model.w, model.f, rule=_well_prod2)

        # b.  pad capacity
        # The total number of wells that can be drilled in a pad all over the planning horizon is bounded.

        def _pad_cap_t(b, p, t):
            return sum(b.y_drill[w, p, f, t2] for w in model.w_p[p] for f in model.f for t2 in model.t if ((model.t.ord(t2) >= model.t.ord(t) - model.tau_d + 1) and model.t.ord(t2) <= model.t.ord(t))) <= 1

        b.pad_cap_t = Constraint(model.p, model.t, rule=_pad_cap_t)
        # print(model.pad_cap_t['p3', 5].expr)

        # d. completion scequence
        # disaggregate

        # if aggregated_flag == False:
        #     # disaggregate
        #     def _com_sqc(model, w, p, f, t):
        #         return model.y_comp[w, p, f, t] <= sum(model.y_drill[w, p, f, t2] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t) - model.tau_d)
        #     model.com_sqc = Constraint(model.wp_tuple, model.f, model.t, rule=_com_sqc)
        # elif aggregated_flag == True:
        #     # aggregated
        #     def _com_sqc(model, w, p, f):
        #         return sum(t * model.y_comp[w, p, f, t] for t in model.t) >= sum((t + model.tau_d) * model.y_drill[w, p, f, t] for t in model.t)
        #     model.com_sqc = Constraint(model.wp_tuple, model.f, rule=_com_sqc)

        # # e. drill_batch

        # def _drill_batch(model, w, p, f, t):
        #     return model.y_comp[w, p, f, t] <= 1 - sum(model.y_drill[w2, p, f2, t2] for w2 in model.w_p[p] for f2 in model.f for t2 in model.t if model.t.ord(t2) >= model.t.ord(t) - model.tau_d + 1 and model.t.ord(t2) <= model.t.ord(t))

        # model.drill_batch = Constraint(model.wp_tuple, model.f, model.t, rule=_drill_batch)
        # print(model.drill_batch['w10', 'p10', 'f1', 5].expr)

        # new added constraint(with Diego)

        # def _drill_batch2(model, p, t):
        #     return sum(model.y_comp[w, p, f, t2] for w in model.w_p[p] for f in model.f for t2 in model.t if model.t.ord(t2) >= model.t.ord(t) - model.tau_c2 + 1 and model.t.ord(t2) <= model.t.ord(t)) / 2 <= 1 - sum(model.y_drill[w2, p, f2, t2] for w2 in model.w_p[p] for f2 in model.f for t2 in model.t if model.t.ord(t2) >= model.t.ord(t) - model.tau_d + 1 and model.t.ord(t2) <= model.t.ord(t))

        # model.drill_batch2 = Constraint(model.p, model.t, rule=_drill_batch2)

        # def _drill_batch2(model, w, p, f, t):
        #     if t == model.t.last():
        #         return Constraint.Skip
        #     else:
        #         return model.y_comp[w, p, f, t + 1] >= model.y_drill[w, p, f, t] - sum(model.y_drill[w2, p, f2, t + 1] for w2 in model.w_p[p] for f2 in model.f)

        # model.drill_batch2 = Constraint(model.wp_tuple, model.f, model.t, rule=_drill_batch2)

        # def _drill_batch3(model, w, p, f, t):
        #     return sum(model.y_drill[w, p, f, t2] - model.y_comp[w, p, f, t2] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t)) <= sum(model.y_drill[w2, p, f2, t] + model.y_comp[w2, p, f2, t] for w2 in model.w_p[p] for f2 in model.f)

        # model.drill_batch3 = Constraint(model.wp_tuple, model.f, model.t, rule=_drill_batch3)

        # f. completion starts as soon as drilling operations are finished

        # def _as_soon_as(model, w, p, f, t):
        #     if model.t.ord(t) <= model.tau_d:
        #         return Constraint.Skip
        #     else:
        #         return model.y_comp[w, p, f, t] <= sum(model.y_drill[w2, p, f2, model.t[model.t.ord(t) - model.tau_d]] for w2 in model.w_p[p] for f2 in model.f)
        #         # return model.y_comp[w, p, f, t] <= sum(model.y_drill[w2, p, f2, model.t[max(model.t.ord(t) - model.tau_d, 0)]] for w2 in model.w_p[p] for f2 in model.f)

        # model.as_soon_as = Constraint(model.wp_tuple, model.f, model.t, rule=_as_soon_as)

        # g. All operations on wellwmust be finished in the planning horizon if the drilling operation startsin the planning horizon,
        #    i.e, no well can be left unfinished within the planning horizon.

        # def _not_unfinished(model, w, p, f):
        #     return sum(model.y_drill[w, p, f, t] for t in model.t) == sum(model.y_comp[w, p, f, t] for t in model.t)

        # model.not_unfinished = Constraint(model.wp_tuple, model.f, rule=_not_unfinished)

        # # h. There is an upper limit number of wells that can be hydraulically fractured in each time period.

        # def _max_comp(model, p, t):
        #     return sum(model.y_comp[w, p, f, t] for w in model.w_p[p] for f in model.f) <= 2

        # model.max_comp = Constraint(model.p, model.t, rule=_max_comp)

        ############################################################################################

        # 2.  shut-in related constraints
        # a.  Shut-in should only happen after the well w is completed.
        # option2

        if shutin_flag == True:

            def _shut2comp(b, w, p, f, t):
                return b.y_shut_in[w, p, f, t] <= sum(b.y_comp[w, p, f, t2] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t) - model.tau_c2)

            b.shut2comp = Constraint(
                model.wp_tuple, model.f, model.t, rule=_shut2comp)

            def _nearby3(b, w, p, f, t):
                return b.y_shut_in[w, p, f, t] <= sum(b.y_comp[w2, p2, f, t2] for w2 in model.w_w[w] for p2 in model.p_w[w2] for t2 in model.t if (model.t.ord(t2) >= model.t.ord(t) - model.tau_c2 + 1) and (model.t.ord(t2) <= model.t.ord(t))) + sum(b.y_comp[w3, p, f2, t2] for w3 in model.w_p[p] for f2 in model.f for t2 in model.t if (model.t.ord(t2) >= model.t.ord(t) - model.tau_c2 + 1) and (model.t.ord(t2) <= model.t.ord(t)))

            b.nearby3 = Constraint(
                model.wp_tuple, model.f, model.t, rule=_nearby3)

            # # b.  production should stop while other nearby wells are being completed.

            if shutin_formulation_flag == True:

                # 1. Big M formulation

                def _nearby1(b, w, p, f, t):
                    return b.y_shut_in[w, p, f, t] >= sum(b.y_comp[w2, p2, f, t] for w2 in model.w_w[w] for p2 in model.p_w[w2]) / model.H \
                        + sum(b.y_comp[w, p, f, t2] for t2 in model.t if model.t.ord(
                            t2) <= model.t.ord(t) - model.tau_c2) - 1

                b.nearby1 = Constraint(
                    model.wp_tuple, model.f, model.t, rule=_nearby1)

                def _nearby2(model, w, p, f, t):
                    return model.y_shut_in[w, p, f, t] >= sum(model.y_comp[w2, p, f2, t2] for w2 in model.w_p[p] for f2 in model.f for t2 in model.t if (model.t.ord(t2) >= model.t.ord(t) - model.tau_c2 + 1) and (model.t.ord(t2) <= model.t.ord(t))) / model.H + sum(model.y_comp[w, p, f, t2] for t2 in model.t if model.t.ord(
                        t2) <= model.t.ord(t) - model.tau_c2) - 1

                b.nearby2 = Constraint(
                    model.wp_tuple, model.f, model.t, rule=_nearby2)

            elif shutin_formulation_flag == False:
                # 2. Convex Hull derive from GDP
                # new set
                def _wwpp(model):
                    return ((w, w2, p, p2) for w in model.w for w2 in model.w_w[w] for p in model.p_w[w] for p2 in model.p_w[w2])

                model.wwpp_tuple = Set(dimen=4, initialize=_wwpp)

                def _nearby1(b, w, w2, p, p2, f, t):
                    return b.y_shut_in[w, p, f, t] >= sum(b.y_comp[w2, p2, f, t2] for t2 in model.t if (model.t.ord(t2) >= model.t.ord(t) - model.tau_c2 + 1) and (model.t.ord(t2) <= model.t.ord(t))) + sum(b.y_comp[w, p, f, t2] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t) - model.tau_c2) - 1

                b.nearby1 = Constraint(
                    b.wwpp_tuple, model.f, model.t, rule=_nearby1)

                # new set
                # w'!=w should not be added here
                def _wwp2(model):
                    return ((w, w2, p) for w in model.w for p in model.p_w[w] for w2 in model.w_p[p])

                model.wwp2_tuple = Set(dimen=3, initialize=_wwp2)

                def _nearby2(b, w, w2, p, f, f2, t):
                    return b.y_shut_in[w, p, f, t] >= sum(b.y_comp[w2, p, f2, t2] for t2 in model.t if (model.t.ord(t2) >= model.t.ord(t) - model.tau_c2 + 1) and (model.t.ord(t2) <= model.t.ord(t))) + sum(b.y_comp[w, p, f, t2] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t) - model.tau_c2) - 1

                b.nearby2 = Constraint(
                    model.wwp2_tuple, model.f, model.f, model.t, rule=_nearby2)

            ############################################################################################
            ############################################################################################

            # def _shutin_fix(model, w, p, f, t):
            #     return model.y_shut_in[w, p, f, t] == 0

            # model.shutin_fix = Constraint(model.wp_tuple, model.f, model.t, rule=_shutin_fix)

            ## GDP ##

            ##########################################
            ## Disjunctions (SHUT-IN means disappear)#
            ##########################################
            b.f_gas_w = Var(model.wp_tuple, model.f, model.t,
                            model.s, bounds=(0, 3000))
            b.f_oil_w = Var(model.wp_tuple, model.f, model.t,
                            model.s, bounds=(0, 3000))
            b.loe_w = Var(model.wp_tuple, model.f, model.t,
                          model.s, bounds=(0, 30000))

            # model.f_gas_w = Var(model.wp_tuple, model.f, model.t, bounds=(0, 200000))
            # model.f_oil_w = Var(model.wp_tuple, model.f, model.t, bounds=(0, 200000))
            # model.loe_w = Var(model.wp_tuple, model.f, model.t, bounds=(0, 1000000))

            def _shut_in_disjunct(disjunct, flag, w, p, f, t):
                # model = disjunct.model()
                if flag:
                    def _gas_balance_gpd1(disjunct):
                        # since shut in will not happen in the first period, so we don't need Constraint.Skip here.
                        return b.f_gas_w[w, p, f, t] == sum(b.y_comp[w, p, f, t2] * model.ProductionFactor[w, s] * model.gamma_gas[f, t - t2] for t2 in model.t if model.t.ord(t2) < model.t.ord(t))

                    disjunct.gas_balance_gpd1 = Constraint(
                        rule=_gas_balance_gpd1)

                    def _oil_balance_gdp1(disjunct):
                        return b.f_oil_w[w, p, f, t] == sum(b.y_comp[w, p, f, t2] * model.ProductionFactor[w, s] * model.gamma_oil[f, t - t2] for t2 in model.t if model.t.ord(t2) < model.t.ord(t))

                    disjunct.oil_balance_gpd1 = Constraint(
                        rule=_oil_balance_gdp1)

                    def _loe_computation_gdp1(disjunct):
                        return b.loe_w[w, p, f, t] == sum(b.y_comp[w, p, f, t2] * model.ProductionFactor[w, s] * (model.g * model.c_loe_v[f, t - t2] + model.c_loe_f[f, t - t2]) for t2 in model.t if model.t.ord(t2) < model.t.ord(t))

                    disjunct.loe_computation_gdp1 = Constraint(
                        rule=_loe_computation_gdp1)
                else:
                    def _gas_balance_gpd2(disjunct):
                        return b.f_gas_w[w, p, f, t] == 0
                    disjunct.gas_balance_gpd2 = Constraint(
                        rule=_gas_balance_gpd2)

                    def _oil_balance_gdp2(disjunct):
                        return b.f_oil_w[w, p, f, t] == 0
                    disjunct.oil_balance_gpd2 = Constraint(
                        rule=_oil_balance_gdp2)

                    def _loe_computation_gdp2(disjunct):
                        return b.loe_w[w, p, f, t] == 0
                    disjunct.loe_computation_gdp2 = Constraint(
                        rule=_loe_computation_gdp2)

            b.shut_in_disjunct = Disjunct(
                [0, 1], model.wp_tuple, model.f, model.t, rule=_shut_in_disjunct)

            def _shut_in_disjunction(model, w, p, f, t):
                return [model.shut_in_disjunct[flag, w, p, f, t] for flag in [0, 1]]

            model.shut_in_disjunction = Disjunction(
                model.wp_tuple, model.f, model.t, rule=_shut_in_disjunction)

            ##########################################
            ### Disjunctions (SHUT-IN means delay)####
            ##########################################
            '''

            model.f_gas_w = Var(model.wp_tuple, model.f,
                                model.t, bounds=(0, 3000))
            model.f_oil_w = Var(model.wp_tuple, model.f,
                                model.t, bounds=(0, 3000))
            model.loe_w = Var(model.wp_tuple, model.f,
                              model.t, bounds=(0, 30000))
            model.s_gas_w = Var(model.wp_tuple, model.f,
                                model.t, bounds=(0, 3000))
            model.s_oil_w = Var(model.wp_tuple, model.f,
                                model.t, bounds=(0, 3000))

            # model.f_gas_w = Var(model.wp_tuple, model.f, model.t, bounds=(0, 200000))
            # model.f_oil_w = Var(model.wp_tuple, model.f, model.t, bounds=(0, 200000))
            # model.loe_w = Var(model.wp_tuple, model.f, model.t, bounds=(0, 1000000))
            # model.s_gas_w = Var(model.wp_tuple, model.f, model.t, bounds=(0, 200000))
            # model.s_oil_w = Var(model.wp_tuple, model.f, model.t, bounds=(0, 200000))

            def _shut_in_disjunct(disjunct, flag, w, p, f, t):
                # model = disjunct.model()
                if flag:
                    def _gas_balance_gpd1(disjunct):
                        # since shut in will not happen in the first period, so we don't need Constraint.Skip here.
                        if t == model.t.first():
                            return model.f_gas_w[w, p, f, t] == sum(model.y_comp[w, p, f, t2] * model.ProductionFactor[w] * model.gamma_gas[f, t - t2] for t2 in model.t if model.t.ord(t2) < model.t.ord(t))
                        else:
                            return model.f_gas_w[w, p, f, t] == sum(model.y_comp[w, p, f, t2] * model.ProductionFactor[w] * model.gamma_gas[f, t - t2] for t2 in model.t if model.t.ord(t2) < model.t.ord(t)) + 0.1 * model.s_gas_w[w, p, f, t - 1]

                    disjunct.gas_balance_gpd1 = Constraint(
                        rule=_gas_balance_gpd1)

                    def _oil_balance_gdp1(disjunct):
                        if t == model.t.first():
                            return model.f_oil_w[w, p, f, t] == sum(model.y_comp[w, p, f, t2] * model.ProductionFactor[w] * model.gamma_oil[f, t - t2] for t2 in model.t if model.t.ord(t2) < model.t.ord(t))
                        else:
                            return model.f_oil_w[w, p, f, t] == sum(model.y_comp[w, p, f, t2] * model.ProductionFactor[w] * model.gamma_oil[f, t - t2] for t2 in model.t if model.t.ord(t2) < model.t.ord(t)) + 0.1 * model.s_oil_w[w, p, f, t - 1]

                    disjunct.oil_balance_gpd1 = Constraint(
                        rule=_oil_balance_gdp1)

                    def _gas_balance_gpd3(disjunct):
                        return model.s_gas_w[w, p, f, t] == 0

                    disjunct.gas_balance_gpd3 = Constraint(
                        rule=_gas_balance_gpd3)

                    def _oil_balance_gpd3(disjunct):
                        return model.s_oil_w[w, p, f, t] == 0
                    disjunct.oil_balance_gpd3 = Constraint(
                        rule=_oil_balance_gpd3)

                    def _loe_computation_gdp1(disjunct):
                        return model.loe_w[w, p, f, t] == sum(model.y_comp[w, p, f, t2] * model.ProductionFactor[w] * (model.g * model.c_loe_v[f, t - t2] + model.c_loe_f[f, t - t2]) for t2 in model.t if model.t.ord(t2) < model.t.ord(t))

                    disjunct.loe_computation_gdp1 = Constraint(
                        rule=_loe_computation_gdp1)
                else:
                    def _gas_balance_gpd2(disjunct):
                        return model.f_gas_w[w, p, f, t] == 0
                    disjunct.gas_balance_gpd2 = Constraint(
                        rule=_gas_balance_gpd2)

                    def _oil_balance_gdp2(disjunct):
                        return model.f_oil_w[w, p, f, t] == 0
                    disjunct.oil_balance_gpd2 = Constraint(
                        rule=_oil_balance_gdp2)

                    def _gas_balance_gpd4(disjunct):
                        # since shut in will not happen in the first period, so we don't need Constraint.Skip here.
                        return model.s_gas_w[w, p, f, t] == sum(model.y_comp[w, p, f, t2] * model.ProductionFactor[w] * model.gamma_gas[f, t - t2] for t2 in model.t if model.t.ord(t2) < model.t.ord(t))

                    disjunct.gas_balance_gpd4 = Constraint(
                        rule=_gas_balance_gpd4)

                    def _oil_balance_gdp4(disjunct):
                        return model.s_oil_w[w, p, f, t] == sum(model.y_comp[w, p, f, t2] * model.ProductionFactor[w] * model.gamma_oil[f, t - t2] for t2 in model.t if model.t.ord(t2) < model.t.ord(t))

                    disjunct.oil_balance_gpd4 = Constraint(
                        rule=_oil_balance_gdp4)

                    def _loe_computation_gdp2(disjunct):
                        return model.loe_w[w, p, f, t] == 0
                    disjunct.loe_computation_gdp2 = Constraint(
                        rule=_loe_computation_gdp2)

            model.shut_in_disjunct = Disjunct(
                [0, 1], model.wp_tuple, model.f, model.t, rule=_shut_in_disjunct)

            def _shut_in_disjunction(model, w, p, f, t):
                return [model.shut_in_disjunct[flag, w, p, f, t] for flag in [0, 1]]

            model.shut_in_disjunction = Disjunction(
                model.wp_tuple, model.f, model.t, rule=_shut_in_disjunction)
            '''

            ######################
            ## Logic Constraints #
            ######################

            def _logic_rule(b, w, p, f, t):
                return b.shut_in_disjunct[0, w, p, f, t].indicator_var == b.y_shut_in[w, p, f, t]

            b.logic_rule = Constraint(
                model.wp_tuple, model.f, model.t, rule=_logic_rule)

            ######################
            ## Sum Constraints ###
            ######################

            def _gas_sum(b, p, t):
                return b.f_gas[p, t] == sum(b.f_gas_w[w, p, f, t] for w in model.w_p[p] for f in model.f)

            b.gas_sum = Constraint(model.p, model.t, rule=_gas_sum)

            def _oil_sum(model, p, t):
                return b.f_oil[p, t] == sum(b.f_oil_w[w, p, f, t] for w in model.w_p[p] for f in model.f)

            b.oil_sum = Constraint(model.p, model.t, rule=_oil_sum)

            def _loe_sum(model, t):
                return b.loe[t] == sum(b.loe_w[w, p, f, t] for w in model.w for p in model.p_w[w] for f in model.f)

            b.loe_sum = Constraint(model.t, rule=_loe_sum)

        elif shutin_flag == False:

            def _flow_balance1(b, p, t):
                return b.f_gas[p, t] == sum(b.y_drill[w, p, f, t2] * model.ProductionFactor[w, s] * model.gamma_gas[f, t - t2] for t2 in model.t if model.extended_t.ord(t2) < model.extended_t.ord(t) for w in model.w_p[p] for f in model.f)

            b.flow_balance1 = Constraint(
                model.p, model.extended_t, rule=_flow_balance1)

            def _flow_balance2(b, p, t):
                return b.f_oil[p, t] == sum(b.y_drill[w, p, f, t2] * model.ProductionFactor[w, s] * model.gamma_oil[f, t - t2] for t2 in model.t if model.extended_t.ord(t2) < model.extended_t.ord(t) for w in model.w_p[p] for f in model.f)

            b.flow_balance2 = Constraint(
                model.p, model.extended_t, rule=_flow_balance2)

            def _loe_computation(b, t):
                return b.loe[t] == sum(b.y_drill[w, p, f, t2] * model.ProductionFactor[w, s] * (model.g * model.c_loe_v[f, t - t2] + model.c_loe_f[f, t - t2]) for t2 in model.t if model.extended_t.ord(t2) < model.extended_t.ord(t) for w in model.w for p in model.p_w[w] for f in model.f)

            b.loe_computation = Constraint(
                model.extended_t, rule=_loe_computation)

        ############################################################################################

        # 3.  rig allocation constraints
        # a.  A drilling rigris on site for as long as any wellwis being developed at a candidate padlocation.

        def _onsite1(b, p, t):
            return sum(b.y_drill[w, p, f, t2] for w in model.w_p[p] for f in model.f for t2 in model.t if model.t.ord(t2) >= model.t.ord(t) - model.tau_d + 1 and model.t.ord(t2) <= model.t.ord(t)) <= sum(b.y_rig[r, p, t] for r in model.r)
            # return sum(model.y_drill[w, p, f, t2] for w in model.w_p[p] for f in model.f for t2 in model.t if model.t.ord(t2) >= model.t.ord(t) - model.tau_d + 1 and model.t.ord(t2) <= model.t.ord(t)) == sum(model.y_rig[r, p, t] for r in model.r)

        b.onsite1 = Constraint(model.p, model.t, rule=_onsite1)

        def _onewell(b, r, t):
            return sum(b.y_rig[r, p, t] for p in model.p) <= 1

        b.onewell = Constraint(model.r, model.t, rule=_onewell)

        def _cap_rig(b, p, t):
            return sum(b.y_rig[r, p, t] for r in model.r) <= 1

        b.cap_rig = Constraint(model.p, model.t, rule=_cap_rig)

        ############################################################################################
        # 4. Pipeline installation constraints
        if pipeline_flag == True:

            if pipeline_state_action_flag == True:
                # 1. state variables based

                # a.  pipeline between pad and gas junction point
                # Each selected pad p needs to be connected to a gas junction pointj.

                # Big-M #
                def _PadConnection(b, p, t):
                    return model.H * b.y_node[p, t] >= sum(b.y_drill[w, p, f, t2] for w in model.w_p[p] for f in model.f for t2 in model.t if model.t.ord(t2) <= model.t.ord(t))

                b.PadConnection = Constraint(
                    model.p, model.t, rule=_PadConnection)

                # Convex Hull #
                # def _PadConnection(model, w, p, f, t):
                #     return model.y_node[p, t] >= sum(model.y_drill[w, p, f, t2] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t))

                # model.PadConnection = Constraint(model.wp_tuple, model.f, model.t, rule=_PadConnection)

                # b.  Each selected junction gas point need to be connected to delivery point at every period t,
                # i.e.,the pipeline network is a connected graph including the gas delivery point at every period t.

                def _node2pipeline(b, m, t):
                    return b.y_node[m, t] == sum(b.y_pipe[m, n, t] for n in model.n_m[m])

                b.node2pipeline = Constraint(
                    model.m, model.t, rule=_node2pipeline)

                def _DeliveryNoOut(b, t):
                    return b.y_pipe[q, j_q, t] == 0

                b.DeliveryNoOut = Constraint(
                    model.t, rule=_DeliveryNoOut)

                def _binary2level(b, m, n, t):
                    return b.v[m, t] >= b.v[n, t] + b.y_pipe[m, n, t] - model.K * (1 - b.y_pipe[m, n, t])

                b.binary2level = Constraint(
                    model.m_n_tuple, model.t, rule=_binary2level)

                def _LevelOfdelivery(b, t):
                    return b.v[q, t] == 0

                b.LevelOfdelivery = Constraint(
                    model.t, rule=_LevelOfdelivery)

                # Big-M #

                def _indegree2outdegree(b, m, t, s):
                    return model.H * sum(b.y_pipe[m, n, t] for n in model.n_m[m]) >= sum(b.y_pipe[n, m, t] for n in model.n_m[m])

                b.indegree2outdegree = Constraint(
                    model.m, model.t, rule=_indegree2outdegree)

                # Convex Hull #
                # def _indegree2outdegree(model, m, n, t):
                #     return sum(model.y_pipe[m, n2, t] for n2 in model.n_m[m]) >= model.y_pipe[n, m, t]

                # model.indegree2outdegree = Constraint(model.m_n_tuple, model.t, rule=_indegree2outdegree)

                def _add_bounding1(b, m, t):
                    return b.v[m, t] <= model.K - 1

                b.add_bounding1 = Constraint(
                    model.m, model.t, rule=_add_bounding1)

                # def _add_bounding2(model, m, t):
                #     return model.v[m, t] >= 1

                # model.add_bounding2 = Constraint(model.m, model.t, rule=_add_bounding2)

                # def _add_bounding3(model, m, n, t):
                #     return model.y_pipe[m, n, t] + model.y_pipe[n, m, t] <= 1

                # model.add_bounding3 = Constraint(model.m_n_tuple, model.t, rule=_add_bounding3)

            elif pipeline_state_action_flag == False:

                # 2. action variables based

                # a.  pipeline between pad and gas junction point
                # Each selected pad p needs to be connected to a gas junction pointj.
                # each pipeline can be installed only once

                def _node_1(b, m):
                    return sum(b.y_node[m, t] for t in model.t) <= 1

                b.node_1 = Constraint(model.m, rule=_node_1)

                def _PadConnection(b, w, p, f, t):
                    return sum(b.y_node[p, t2] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t)) >= b.y_drill[w, p, f, t]

                b.PadConnection = Constraint(
                    model.wp_tuple, model.f, model.t, rule=_PadConnection)

                # def _PadConnection(model, p, t):
                #     return model.H * sum(model.y_node[p, t2] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t)) >= sum(model.y_drill[w, p, f, t2] for w in model.w_p[p] for f in model.f for t2 in model.t if model.t.ord(t2) <= model.t.ord(t))

                # model.PadConnection = Constraint(model.p, model.t, rule=_PadConnection)

                # b.  Each selected junction gas point need to be connected to delivery point at every period t,
                # i.e.,the pipeline network is a connected graph including the gas delivery point at every period t.

                def _node2pipeline(b, m, t):
                    return b.y_node[m, t] == sum(b.y_pipe[m, n, t] for n in model.n_m[m])

                b.node2pipeline = Constraint(
                    model.m, model.t, rule=_node2pipeline)

                def _DeliveryNoOut(b, t):
                    return b.y_pipe[q, j_q, t] == 0

                b.DeliveryNoOut = Constraint(model.t, rule=_DeliveryNoOut)

                def _binary2level(b, m, n, t):
                    return b.v[m, t] >= b.v[n, t] + sum(b.y_pipe[m, n, t2] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t)) - model.K * (1 - sum(b.y_pipe[m, n, t2] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t)))

                b.binary2level = Constraint(
                    model.m_n_tuple, model.t, rule=_binary2level)

                def _LevelOfdelivery(b, t):
                    return b.v[q, t] == 0

                b.LevelOfdelivery = Constraint(
                    model.t, rule=_LevelOfdelivery)

                # Big-M #

                def _indegree2outdegree(b, m, t):
                    return model.H * sum(model.y_pipe[m, n, t2] for n in model.n_m[m] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t)) >= sum(model.y_pipe[n, m, t2] for n in model.n_m[m] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t))

                b.indegree2outdegree = Constraint(
                    model.m, model.t, rule=_indegree2outdegree)

                # Convex Hull #
                # def _indegree2outdegree(model, m, n, t):
                #     return sum(model.y_pipe[m, n2, t2] for n2 in model.n_m[m] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t)) >= sum(model.y_pipe[n, m, t2] for t2 in model.t if model.t.ord(t2) <= model.t.ord(t))

                # model.indegree2outdegree = Constraint(model.m_n_tuple, model.t, rule=_indegree2outdegree)

                def _add_bounding1(b, m, t):
                    return b.v[m, t] <= model.K - 1

                b.add_bounding1 = Constraint(
                    model.m, model.t, rule=_add_bounding1)

                # def _add_bounding2(model, m, t):
                #     return model.v[m, t] >= 1

                # model.add_bounding2 = Constraint(model.m, model.t, rule=_add_bounding2)

                def _add_bounding3(b, m, n, t):
                    return b.y_pipe[m, n, t] + b.y_pipe[n, m, t] <= 1

                b.add_bounding3 = Constraint(
                    model.m_n_tuple, model.t, rule=_add_bounding3)

        ############################################################################################

        # 5. flow balance

        def _flow_balance3(b, j, t):
            return b.f_gas[j, t] == 0

        b.flow_balance3 = Constraint(
            model.j, model.extended_t, rule=_flow_balance3)

        # flow balance at each node(including pads and gas junction points)

        def _flow_balance4(b, m, t):
            if pipeline_flag == True:
                return sum(b.f_pipe[n, m, t] for n in model.n_m[m]) + b.f_gas[m, t] == sum(b.f_pipe[m, n, t] for n in model.n_m[m])
            elif pipeline_flag == False:
                return sum(b.f_pipe[n, m, t] for n in model.n_m_in[m]) + b.f_gas[m, t] == sum(b.f_pipe[m, n, t] for n in model.n_m_out[m])

        b.flow_balance4 = Constraint(
            model.m, model.extended_t, rule=_flow_balance4)

        ############################################################################################
        # 6.  pipeline sizing constraint

        ############################################################################################

        # 6.  pipeline sizing constraint

        if pipeline_flag == True:
            if pipeline_state_action_flag == True:

                # (state variable based)

                # a.  pipeline between gas junction points

                def _pipe_gjp1(b, n, n2, t):
                    return b.y_pipe[n, n2, t] == sum(b.z_pipe[n, n2, d, t] for d in model.d)

                b.pipe_gjp1 = Constraint(
                    model.n_n_tuple, model.t, rule=_pipe_gjp1)

                def _pipe_gjp2(b, n, n2, t):
                    return b.f_pipe[n, n2, t] <= sum(b.pipe_gas_cap[d] * model.z_pipe[n, n2, d, t] for d in model.d)

                b.pipe_gjp2 = Constraint(
                    model.n_n_tuple, model.t, rule=_pipe_gjp2)

                # d.  the diameter of pipelines cannot be change if determined.

                def _diameter_junc(b, n, n2, d, t):
                    return b.z_pipe[n, n2, d, t] <= b.z_pipe[n, n2, d, model.t[-1]]

                b.diameter_junc = Constraint(
                    model.n_n_tuple, model.d, model.t, rule=_diameter_junc)

            elif pipeline_state_action_flag == False:
                # (action variable based)
                # a.  pipeline between gas junction points
                def _pipe_gjp1(b, n, n2, t):
                    return b.y_pipe[n, n2, t] == sum(b.z_pipe[n, n2, d, t] for d in model.d)

                b.pipe_gjp1 = Constraint(
                    model.n_n_tuple, model.t, rule=_pipe_gjp1)

                def _pipe_gjp2(b, n, n2, t):
                    return b.f_pipe[n, n2, t] <= sum(model.pipe_gas_cap[d] * b.z_pipe[n, n2, d, t2] for d in model.d for t2 in model.t if model.t.ord(t2) <= model.t.ord(t))

                b.pipe_gjp2 = Constraint(
                    model.n_n_tuple, model.t, rule=_pipe_gjp2)

        elif pipeline_flag == False:
            # fixed network
            def _pipe_gjp1(b, m, n):
                return sum(b.z_pipe[m, n, d, t] for d in model.d for t in model.t) <= 1
            b.pipe_gjp1 = Constraint(
                model.m_n_tuple_fixed, rule=_pipe_gjp1)

            def _pipe_gjp2(b, m, n, t):
                return b.f_pipe[m, n, t] <= sum(model.pipe_gas_cap[d] * b.z_pipe[m, n, d, t2] for d in model.d for t2 in model.t if model.extended_t.ord(t2) <= model.extended_t.ord(t))

            b.pipe_gjp2 = Constraint(
                model.m_n_tuple_fixed, model.extended_t, rule=_pipe_gjp2)

        ############################################################################################

        # Objective function

        def _rev_computation(b, t):
            return b.rev[t] == (1 - model.tax) * (model.gas_price * model.g * sum(b.f_gas[p, t] for p in model.p) + model.oil_price * model.g * sum(b.f_oil[p, t] for p in model.p))

        b.rev_computation = Constraint(
            model.extended_t, rule=_rev_computation)

        ##############################################

        # def _rtp1(model, p, t):
        #     return model.H * model.y_active[p, t] >= sum(model.y_dev[w, p, f, t] for w in model.w_p[p] for f in model.f)

        # model.rtp1 = Constraint(model.p, model.t, rule=_rtp1)

        # def _rtp2(model, p, t):
        #     return model.y_active[p, t] <= sum(model.y_dev[w, p, f, t] for w in model.w_p[p] for f in model.f)

        # model.rtp2 = Constraint(model.p, model.t, rule=_rtp2)

        def _rtp3(b, p, t):
            # return model.y_rtp_signal[p, t] <= model.y_active[p, t]
            return b.y_rtp_signal[p, t] <= sum(b.y_drill[w, p, f, t] for w in model.w_p[p] for f in model.f)

        b.rtp3 = Constraint(model.p, model.t, rule=_rtp3)

        def _rtp4(b, p, t):
            if model.t.ord(t) == 1:
                return Constraint.Skip
            else:
                return b.y_rtp_signal[p, t] <= 1 - sum(b.y_drill[w, p, f, model.t.prev(t)] for w in model.w_p[p] for f in model.f)

        b.rtp4 = Constraint(model.p, model.t, rule=_rtp4)

        def _rtp5(b, p, t):
            if model.t.ord(t) == 1:
                return b.y_rtp_signal[p, t] == sum(b.y_drill[w, p, f, t] for w in model.w_p[p] for f in model.f)
            else:
                return b.y_rtp_signal[p, t] >= sum(b.y_drill[w, p, f, t] for w in model.w_p[p] for f in model.f) - sum(b.y_drill[w, p, f, model.t.prev(t)] for w in model.w_p[p] for f in model.f)

        b.rtp5 = Constraint(model.p, model.t, rule=_rtp5)

        # remove the first signal

        def _rtp6(b, p, t):
            return b.y_rtp[p, t] <= b.y_rtp_signal[p, t]

        b.rtp6 = Constraint(model.p, model.t, rule=_rtp6)

        def _rtp7(b, p, t):
            return b.y_rtp[p, t] <= sum(b.y_rtp_signal[p, t2] for t2 in model.t if model.t.ord(t2) < model.t.ord(t))

        b.rtp7 = Constraint(model.p, model.t, rule=_rtp7)
        # Big-M #

        def _rtp8(b, p, t):
            return b.y_rtp[p, t] >= sum(b.y_rtp_signal[p, t2] for t2 in model.t if model.t.ord(t2) < model.t.ord(t)) / model.H + b.y_rtp_signal[p, t] - 1

        b.rtp8 = Constraint(model.p, model.t, rule=_rtp8)

        # Convex Hull #
        # def _rtp8(model, p, t, t2):
        #     return model.y_rtp[p, t] >= model.y_rtp_signal[p, t2] + model.y_rtp_signal[p, t] - 1

        # model.rtp8 = Constraint(model.p, model.tt_tuple, rule=_rtp8)

        ##############################################

        def _sce_computation(b, t):
            # return model.sce[t] == (model.pad_damage_cost + model.pad_con_cost) * \
            #     (model.pad_fixed_acres * sum((model.y_rtp_signal[p, t] - model.y_rtp[p, t])for p in model.p)
            #      + model.pad_var_acres * sum(model.y_drill[w, p, f, t]
            #                                  for w in model.w for p in model.p_w[w] for f in model.f)
            #      + model.return2pad_acres * sum(model.y_rtp[p, t] for p in model.p)) + model.return2pad_cost * sum(model.y_rtp[p, t] for p in model.p)
            return b.sce[t] == (model.pad_damage_cost + model.pad_con_cost) * \
                (model.pad_fixed_acres * sum((b.y_rtp_signal[p, t] - b.y_rtp[p, t])for p in model.p)
                 + model.pad_var_acres * sum(b.y_drill[w, p, f, t]
                                             for w in model.w for p in model.p_w[w] for f in model.f)
                 + model.return2pad_acres * sum(b.y_rtp[p, t] for p in model.p)) + model.return2pad_cost * sum(b.y_rtp[p, t] for p in model.p) \
                + model.rig_relocation * sum(b.y_rtp_signal[p, t]
                                             for p in model.p)  # add rig relocation constraint

        b.sce_computation = Constraint(model.t, rule=_sce_computation)

        if pipeline_flag == True:
            if pipeline_state_action_flag == True:
                # fpe state variable based

                def _fpe_computation(b, t):
                    if t == model.t.first():
                        return b.fpe[t] == 50 * sum(model.l[n, n2] * model.pipe_cost[d] * b.z_pipe[n, n2, d, t] for (n, n2) in model.n_n_tuple for d in model.d)
                    else:
                        return b.fpe[t] == 50 * sum(model.l[n, n2] * model.pipe_cost[d] * (b.z_pipe[n, n2, d, t] - b.z_pipe[n, n2, d, model.t.prev(t)]) for (n, n2) in model.n_n_tuple for d in model.d)

            elif pipeline_state_action_flag == False:
                # fpe action variable based

                def _fpe_computation(b, t):
                    return b.fpe[t] == 50 * sum(model.l[n, n2] * model.pipe_cost[d] * b.z_pipe[n, n2, d, t] for (n, n2) in model.n_n_tuple for d in model.d)

        elif pipeline_flag == False:
            def _fpe_computation(b, t):
                return b.fpe[t] == 50 * sum(model.l[n, n2] * model.pipe_cost[d] * b.z_pipe[n, n2, d, t] for (n, n2) in model.m_n_tuple_fixed for d in model.d)

        b.fpe_computation = Constraint(model.t, rule=_fpe_computation)

        def _dve_computation(b, t):
            return b.dve[t] == sum(model.relocation_cost * b.y_rtp_signal[p, t] for p in model.p) + sum((model.drill_cost[w, p, f] + model.comp_cost[f]) * b.y_drill[w, p, f, t] for w in model.w for f in model.f for p in model.p_w[w])

        b.dve_computation = Constraint(model.t, rule=_dve_computation)

        # model.z = Var(domain=NonNegativeReals)

        # def _new_constraint(model):
        #     return model.z <= sum(((1 + model.dr)**(-t)) * (model.rev[t] - model.loe[t] - model.sce[t] - model.fpe[t] - model.dve[t]) for t in model.t)

        # model.new_constraint = Constraint(rule=_new_constraint)

        def _npv_compuation(b):
            #     return sum(((1 + model.dr)**(-t)) * (b.rev[t] - b.loe[t]) * model.prob[s] for t in model.extended_t) \
            #         - sum(((1 + model.dr)**(-t)) *
            #               (b.sce[t] + b.fpe[t] + b.dve[t]) * model.prob[s] for t in model.t)

            # b.npv = Objective(rule=_npv_compuation, sense=maximize)
            return -(sum(((1 + model.dr)**(-t)) * (b.rev[t] - b.loe[t]) * model.prob[s] for t in model.extended_t)
                     - sum(((1 + model.dr)**(-t)) *
                           (b.sce[t] + b.fpe[t] + b.dve[t]) * model.prob[s] for t in model.t))

        b.npv = Objective(rule=_npv_compuation, sense=minimize)
    model.scenario_block = Block(model.s, rule=_scenario_block)

    def _total_npv_computation(model):
        #     return sum(((1 + model.dr)**(-t)) * (model.scenario_block[s].rev[t] - model.scenario_block[s].loe[t]) * model.prob[s] for t in model.extended_t for s in model.s) - sum(((1 + model.dr)**(-t)) * (model.scenario_block[s].sce[t] + model.scenario_block[s].fpe[t] + model.scenario_block[s].dve[t]) * model.prob[s] for t in model.t for s in model.s)

        # model.total_npv = Objective(rule=_total_npv_computation, sense=maximize)
        return -(sum(((1 + model.dr)**(-t)) * (model.scenario_block[s].rev[t] - model.scenario_block[s].loe[t]) * model.prob[s] for t in model.extended_t for s in model.s) - sum(((1 + model.dr)**(-t)) * (model.scenario_block[s].sce[t] + model.scenario_block[s].fpe[t] + model.scenario_block[s].dve[t]) * model.prob[s] for t in model.t for s in model.s))

    model.total_npv = Objective(rule=_total_npv_computation, sense=minimize)

    model.cuts = ConstraintList()

    ############################################################################################################
    ############################# Initial non-anticipativity constraints #######################################
    ############################################################################################################

    model.inac = ConstraintList()

    for w, p in model.wp_tuple.data():
        for f in model.f.data():
            for s1, s2 in model.ss_tuple.data():
                model.inac.add(
                    expr=model.scenario_block[s1].y_drill[w, p, f, 1] == model.scenario_block[s2].y_drill[w, p, f, 1])

    # def _inac1(model, w, p, f, s1, s2):
    #     return model.y_drill[w, p, f, 1, s1] == model.y_drill[w, p, f, 1, s2]

    # model.inac1 = Constraint(model.wp_tuple, model.f,
    #                          model.ss_tuple, rule=_inac1)

    for r in model.r.data():
        for p in model.p.data():
            for s1, s2 in model.ss_tuple.data():
                model.inac.add(
                    expr=model.scenario_block[s1].y_rig[r, p, 1] == model.scenario_block[s2].y_rig[r, p, 1])

    # def _inac2(model, r, p, s1, s2):
    #     return model.y_rig[r, p, 1, s1] == model.y_rig[r, p, 1, s2]

    # model.inac2 = Constraint(model.r, model.p, model.ss_tuple, rule=_inac2)

    if pipeline_flag == True:

        for n in model.n.data():
            for s1, s2 in model.ss_tuple.data():
                model.inac.add(
                    expr=model.scenario_block[s1].y_node[n, 1] == model.scenario_block[s2].y_node[n, 1])

        # def _inac3(model, n, s1, s2):
        #     return model.y_node[n, 1, s1] == model.y_node[n, 1, s2]

        # model.inac3 = Constraint(model.n, model.ss_tuple, rule=_inac3)

        for n1, n2 in model.n_n_tuple:
            for s1, s2 in model.ss_tuple:
                model.inac.add(
                    expr=model.scenario_block[s1].y_pipe[n1, n2, 1] == model.scenario_block[s2].y_pipe[n1, n2, 1])
        # def _inac4(model, n1, n2, s1, s2):
        #     return model.y_pipe[n1, n2, 1, s1] == model.y_pipe[n1, n2, 1, s2]

        # model.inac4 = Constraint(model.n_n_tuple, model.ss_tuple, rule=_inac4)

        for n1, n2 in model.n_n_tuple:
            for d in model.d:
                for s1, s2 in model.ss_tuple:
                    model.inac.add(
                        expr=model.scenario_block[s1].z_pipe[n1, n2, d, 1] == model.scenario_block[s2].z_pipe[n1, n2, d, 1])
        # def _inac5(model, n1, n2, d, s1, s2):
        #     return model.z_pipe[n1, n2, d, 1, s1] == model.z_pipe[n1, n2, d, 1, s2]

        # model.inac5 = Constraint(
        #     model.n_n_tuple, model.d, model.ss_tuple, rule=_inac5)

        # def _inac6(model, n1, n2, s1, s2):
        #     return model.f_pipe[n1, n2, 1, s1] == model.f_pipe[n1, n2, 1, s2]

        # model.inac6 = Constraint(model.n_n_tuple, model.s, rule=_inac6)

    elif pipeline_flag == False:

        for n1, n2 in model.m_n_tuple_fixed:
            for d in model.d:
                for s1, s2 in model.ss_tuple:
                    model.inac.add(
                        expr=model.scenario_block[s1].z_pipe[n1, n2, d, 1] == model.scenario_block[s2].z_pipe[n1, n2, d, 1])
        # def _inac5(model, n1, n2, d, s1, s2):
        #     return model.z_pipe[n1, n2, d, 1, s1] == model.z_pipe[n1, n2, d, 1, s2]

        # model.inac5 = Constraint(
        #     model.m_n_tuple_fixed, model.d, model.ss_tuple, rule=_inac5)

        # def _inac6(model, n1, n2, s1, s2):
        #     return model.f_pipe[n1, n2, 1, s1] == model.f_pipe[n1, n2, 1, s2]

        # model.inac6 = Constraint(model.m_n_tuple_fixed, model.ss_tuple, rule=_inac6)

    ############################################################################################################
    ############################## Conditional non-anticipativity constraints ##################################
    ############################################################################################################

    def _cnac_disjunct(disjunct, flag, t, s1, s2):
        # model = disjunct.model()
        # if t==model.t.last()
        if flag:
            def _cnac1(disjunct, w, p, f):
                return model.scenario_block[s1].y_drill[w, p, f, t] == model.scenario_block[s2].y_drill[w, p, f, t]

            disjunct.cnac1 = Constraint(model.wp_tuple, model.f, rule=_cnac1)

            def _cnac2(disjunct, r, p):
                return model.scenario_block[s1].y_rig[r, p, t] == model.scenario_block[s2].y_rig[r, p, t]

            disjunct.cnac2 = Constraint(model.r, model.p, rule=_cnac2)

            if pipeline_flag == True:
                def _cnac3(disjunct, n):
                    return model.scenario_block[s1].y_node[n, t] == model.scenario_block[s2].y_node[n, t]

                disjunct.cnac3 = Constraint(model.n, rule=_cnac3)

                def _cnac4(disjunct, n1, n2):
                    return model.scenario_block[s1].y_pipe[n1, n2, t] == model.scenario_block[s2].y_pipe[n1, n2, t]

                disjunct.cnac4 = Constraint(model.n_n_tuple, rule=_cnac4)

                def _cnac5(disjunct, n1, n2, d):
                    return model.scenario_block[s1].z_pipe[n1, n2, d, t] == model.scenario_block[s2].z_pipe[n1, n2, d, t]

                disjunct.cnac5 = Constraint(
                    model.n_n_tuple, model.d, rule=_cnac5)

                # def _inac6(disjunct, n1, n2):
                #     return model.f_pipe[n1, n2, t + 1, s1] == model.f_pipe[n1, n2, t + 1, s2]

                # disjunct.inac6 = Constraint(model.n_n_tuple, rule=_inac6)

            elif pipeline_flag == False:
                def _cnac5(disjunct, n1, n2, d):
                    return model.scenario_block[s1].z_pipe[n1, n2, d, t] == model.scenario_block[s1].z_pipe[n1, n2, d, t]

                disjunct.cnac5 = Constraint(
                    model.m_n_tuple_fixed, model.d, rule=_cnac5)

                # def _inac6(disjunct, n1, n2):
                #     return model.f_pipe[n1, n2, t + 1, s1] == model.f_pipe[n1, n2, t + 1, s2]

                # disjunct.inac6 = Constraint(model.m_n_tuple_fixed, rule=_inac6)

        else:
            pass

    model.cnac_disjunct = Disjunct(
        [0, 1], model.t_, model.ss_tuple, rule=_cnac_disjunct)

    def _cnac_disjunction(model, t, s1, s2):
        # if t == model.t.last():
        #     Disjunction.Skip
        # else:
        return [model.cnac_disjunct[flag, t, s1, s2] for flag in [0, 1]]

    model.cnac_disjunction = Disjunction(
        model.t_, model.ss_tuple, rule=_cnac_disjunction)

    ######################
    ## Logic Constraints #
    ######################

    def _logic_rule21(model, t, s1, s2):
        return model.cnac_disjunct[1, t, s1, s2].indicator_var >= 1 - sum(model.scenario_block[s1].y_drill[w, p, f, t2] for w in model.w_ss[s1, s2] for p in model.p_w[w] for f in model.f for t2 in model.t if model.t.ord(t2) < model.t.ord(t))

    model.logic_rule21 = Constraint(
        model.t_, model.ss_tuple, rule=_logic_rule21)

    # This constraint has two formulations: big-m and convex-hull

    # Convex hull
    # def _logic_rule23(model, w, p, s1, s2, f, t, t2):
    #     return model.cnac_disjunct[1, t, s1, s2].indicator_var <= 1 - model.scenario_block[s1].y_drill[w, p, f, t2]

    # model.logic_rule23 = Constraint(
    #     model.wpss_tuple, model.f, model.t_t_tuple, rule=_logic_rule23)

    # Big-M
    def _logic_rule23(model, t, s1, s2):
        return model.cnac_disjunct[1, t, s1, s2].indicator_var <= 1 - sum(model.scenario_block[s1].y_drill[w, p, f, t2] for w in model.w_ss[s1, s2] for p in model.p_w[w] for f in model.f for t2 in model.t if model.t.ord(t2) < model.t.ord(t)) / 10
    model.logic_rule23 = Constraint(
        model.t_, model.ss_tuple, rule=_logic_rule23)

    return model


'''
mastermodel = ModelGeneration(case_flag=4, shutin_flag=False, pipeline_flag=False,
                              aggregated_flag=True, shutin_formulation_flag=True, pipeline_state_action_flag=False)

for s in mastermodel.s.data():
    mastermodel.scenario_block[s].npv.deactivate()
mastermodel.compute_statistics()
print(mastermodel.statistics)

TransformationFactory('gdp.bigm').apply_to(mastermodel)
# TransformationFactory('gdp.chull').apply_to(mastermodel)
print('mastermodel transformed')

# opt = SolverFactory('cplex')
opt = SolverFactory('gurobi')
opt.options['timelimit'] = 3600 * 10
# opt.options['threads'] = 1
opt.options["mipgap"] = 0.001
opt.options['mip display'] = 4
# opt.options['preprocessing repeatpresolve'] = 3

result = opt.solve(mastermodel, tee=True)
print(result)
'''
