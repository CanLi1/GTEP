__author__ = "Cristiana L. Lara"
# Stochastic Dual Dynamic Integer Programming (SDDiP) description at:
# https://link.springer.com/content/pdf/10.1007%2Fs10107-018-1249-5.pdf

# This algorithm scenario tree satisfies stage-wise independence

import time
import math
import random
from copy import deepcopy
import os.path
from pyomo.environ import *
import csv
import sys
sys.path.insert(0, os.path.abspath( os.path.join(os.path.dirname(__file__), 
                                               '../') ))

import dataloader.load_investment as InvestData
import dataloader.load_operational as OperationalData
import models.gtep_optBlocks_det as b
from forward_gtep import forward_pass
from backward_SDDiP_gtep import backward_pass
from scenarioTree import create_scenario_tree

# ######################################################################################################################
# USER-DEFINED PARAMS

# Define case-study

filepath = "../data/test.db"
outputfile = "15days_5years_mediumtax.csv"
n_stages = 5  # number od stages in the scenario tree
formulation = "hull"

stages = range(1, n_stages + 1)
scenarios = ['M']
single_prob = {'M': 1.0}

# time_periods = 10
time_periods = n_stages
t_per_stage = {}
for i in range(1, n_stages+1):
  t_per_stage[i] = [i]


# Define parameters of the decomposition
max_iter = 100
max_time = 36000
opt_tol = 1  # %

# ######################################################################################################################



# operating scenarios
prob_op = 1
# print(operating_scenarios)

# list of thermal generators:
th_generators = ['coal-st-old1', 'coal-igcc-new', 'coal-igcc-ccs-new', 'ng-ct-old', 'ng-cc-old', 'ng-st-old',
                 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new']
# 'nuc-st-old', 'nuc-st-new'

# Shared data among processes
ngo_rn_par_k = {}
ngo_th_par_k = {}
nso_par_k = {}
nsb_par_k = {}
nte_par_k = {}
cost_forward = {}
cost_scenario_forward = {}
mltp_o_rn = {}
mltp_o_th = {}
mltp_so = {}
mltp_te = {}
cost_backward = {}
if_converged = {}

# Map stage by time_period
stage_per_t = {t: k for k, v in t_per_stage.items() for t in v}


# print(stage_per_t)

# create blocks
InvestData.read_data(filepath, n_stages)
days = [1,2,3]
weights = [100, 100, 165]
OperationalData.read_representative_days(n_stages, days, weights)
OperationalData.read_strategic_uncertainty(n_stages)

m = b.create_model(n_stages, t_per_stage, formulation, InvestData, OperationalData)

start_time = time.time()

# Decomposition Parameters
m.ngo_rn_par = Param(m.rn_r, m.stages, default=0, initialize=0, mutable=True)
m.ngo_th_par = Param(m.th_r, m.stages, default=0, initialize=0, mutable=True)
m.nso_par = Param(m.j, m.r, m.stages, default=0, initialize=0, mutable=True)
m.nte_par = Param(m.l_new, m.stages, default=0, initialize=0, mutable=True)

# Parameters to compute upper and lower bounds
mean = {}
std_dev = {}
cost_tot_forward = {}
cost_UB = {}
cost_LB = {}
gap = {}
scenarios_iter = {}

# create scenarios
nodes, n_stage, parent_node, children_node, prob, sc_nodes = create_scenario_tree(stages, scenarios, single_prob)
sc_headers = list(sc_nodes.keys())

# converting sets to lists:
rn_r = list(m.rn_r)
th_r = list(m.th_r)
j_r = [(j, r) for j in m.j for r in m.r]
l_new = list(m.l_new)

# request the dual variables for all (locally) defined blocks
for b in m.Bl.values():
    b.dual = Suffix(direction=Suffix.IMPORT)


# solve with nested benders
for stage in m.stages:
    if stage != 1:
        # print('stage', stage, 't_prev', t_prev)
        for (rn, r) in m.rn_r:
            m.Bl[stage].link_equal1.add(expr=(m.Bl[stage].ngo_rn_prev[rn, r] ==
                                              m.ngo_rn_par[rn, r, stage]))
        for (th, r) in m.th_r:
            m.Bl[stage].link_equal2.add(expr=(m.Bl[stage].ngo_th_prev[th, r] ==
                                                 m.ngo_th_par[th, r, stage]))
        for (j, r) in j_r:
            m.Bl[stage].link_equal3.add(expr=(m.Bl[stage].nso_prev[j, r] ==
                                                 m.nso_par[j, r, stage]))
        for l in m.l_new:
            m.Bl[stage].link_equal4.add(expr=(m.Bl[stage].nte_prev[l] ==
                                                 m.nte_par[l, stage]))


# Stochastic Dual Dynamic integer Programming Algorithm (SDDiP)
relax_integrality = 1
iter_limit = 10
for iter_ in range(1, iter_limit+1):

    # ####### Forward Pass ############################################################
    # solve ORIGIN node:
    stage = 1
    n = 'O'
    print("Forward Pass: ", "Stage", stage, "Current Node", n)
    op = 0

    ngo_rn, ngo_th, nso, nte, cost = forward_pass(m.Bl[stage], rn_r, th_r, j_r, l_new, t_per_stage[stage], relax_integrality)

    for t in t_per_stage[stage]:
        for (rn, r) in rn_r:
            ngo_rn_par_k[rn, r, t, n, iter_] = ngo_rn[rn, r, t]
        for (th, r) in th_r:
            ngo_th_par_k[th, r, t, n, iter_] = ngo_th[th, r, t]
        for (j, r) in j_r:
            nso_par_k[j, r, t, n, iter_] = nso[j, r, t]
        for l in l_new:
          nte_par_k[l, t, n, iter_] = nte[l, t]
    cost_forward[stage, n, iter_] = cost
    print('cost', cost_forward[stage, n, iter_])

    for stage in m.stages:
        if stage != 1:
            for n in n_stage[stage]:
                print("Forward Pass: ", "Stage", stage, "Current Node", n)

                # randomly select which operating data profile to solve and populate uncertainty parameters:
                op = 0
                print("operating scenario", op)

                # populate current state from parent node
                for (rn, r) in rn_r:
                    t_prev = t_per_stage[stage - 1][-1]
                    m.ngo_rn_par[rn, r, stage] = ngo_rn_par_k[rn, r, t_prev, parent_node[n], iter_]
                for (th, r) in th_r:
                    t_prev = t_per_stage[stage - 1][-1]
                    m.ngo_th_par[th, r, stage] = ngo_th_par_k[th, r, t_prev, parent_node[n], iter_]
                for (j, r) in j_r:
                    t_prev = t_per_stage[stage - 1][-1]
                    m.nso_par[j, r, stage] = nso_par_k[j, r, t_prev, parent_node[n], iter_]
                for l in l_new:
                    t_prev = t_per_stage[stage - 1][-1]
                    m.nte_par[l, stage] = nte_par_k[l, t_prev, parent_node[n], iter_]                    

                ngo_rn, ngo_th, nso, nte, cost = forward_pass(m.Bl[stage], rn_r, th_r, j_r, l_new, t_per_stage[stage], relax_integrality)

                for t in t_per_stage[stage]:
                    for (rn, r) in rn_r:
                        ngo_rn_par_k[rn, r, t, n, iter_] = ngo_rn[rn, r, t]
                    for (th, r) in th_r:
                        ngo_th_par_k[th, r, t, n, iter_] = ngo_th[th, r, t]
                    for (j, r) in j_r:
                        nso_par_k[j, r, t, n, iter_] = nso[j, r, t]
                    for l in l_new:
                        nte_par_k[l, t, n, iter_] = nte[l, t]                        
                cost_forward[stage, n, iter_] = cost
                print('cost', cost_forward[stage, n, iter_])

    # Compute cost per scenario solved inside of a process
    cost_forward[iter_] = sum(prob[n] * cost_forward[stage, n, iter_] for stage in m.stages for n in n_stage[stage])
    # print(cost_scenario_forward)

    print("finished forward pass")

    cost_UB[iter_] = min(cost_forward[kk] for kk in range(1, iter_limit+1) if kk <= iter_)
    print(cost_UB)
    elapsed_time = time.time() - start_time
    print("CPU Time (s)", elapsed_time)

    # ####### Backward Pass ############################################################

    for stage in reversed(list(m.stages)):
        if stage != n_stages:
            for n in n_stage[stage]:
                for cn in children_node[n]:
                    for op in [0]:
                        print("Children Node", cn, "of stage", stage + 1, "op scenario", op)

                        # populate current state from parent node
                        for (rn, r) in rn_r:
                            t_prev = t_per_stage[stage][-1]
                            m.ngo_rn_par[rn, r, stage+1] = ngo_rn_par_k[rn, r, t_prev, n, iter_]

                        for (th, r) in th_r:
                            t_prev = t_per_stage[stage][-1]
                            m.ngo_th_par[th, r, stage+1] = ngo_th_par_k[th, r, t_prev, n, iter_]

                        for (j, r) in j_r:
                            t_prev = t_per_stage[stage][-1]
                            m.nso_par[j, r, stage+1] = nso_par_k[j, r, t_prev, n, iter_]

                        for l in l_new: 
                            t_prev = t_per_stage[stage][-1]
                            m.nte_par[l, stage+1] = nte_par_k[l, t_prev, n, iter_]                                                        

                        mltp_rn, mltp_th, mltp_s, mltp_t, cost = backward_pass(stage + 1, m.Bl[stage + 1], n_stages,
                                                                       rn_r, th_r, j_r, l_new)

                        cost_backward[stage + 1, cn, op, iter_] = cost
                        print('cost', stage + 1, cn, op, cost_backward[stage + 1, cn, op, iter_])

                        for (rn, r) in rn_r:
                            mltp_o_rn[rn, r, stage + 1, cn, op, iter_] = mltp_rn[rn, r]
                        for (th, r) in th_r:
                            mltp_o_th[th, r, stage + 1, cn, op, iter_] = mltp_th[th, r]
                        for (j, r) in j_r:
                            mltp_so[j, r, stage + 1, cn, op, iter_] = mltp_s[j, r]
                        for l in l_new:
                            mltp_te[l, stage + 1, cn, op, iter_] = mltp_t[l]                            

            # add Benders cut for current iteration
            t = t_per_stage[stage][-1]
            op = 0
            m.Bl[stage].fut_cost.add(expr=(m.Bl[stage].alphafut >=
                                              sum((prob[cn] / prob[n]) * (
                                                      cost_backward[stage + 1, cn, op, iter_]
                                                      + sum(mltp_o_rn[rn, r, stage + 1, cn, op, iter_] *
                                                            (ngo_rn_par_k[rn, r, t, n, iter_] -
                                                             m.Bl[stage].ngo_rn[rn, r, t])
                                                            for rn, r in m.rn_r)
                                                      + sum(mltp_o_th[th, r, stage + 1, cn, op, iter_] *
                                                            (ngo_th_par_k[th, r, t, n, iter_] -
                                                             m.Bl[stage].ngo_th[th, r, t])
                                                            for th, r in m.th_r)
                                                      + sum(mltp_so[j, r, stage + 1, cn, op, iter_] *
                                                            (nso_par_k[j, r, t, n, iter_] -
                                                             m.Bl[stage].nso[j, r, t])
                                                            for j in m.j for r in m.r)
                                                      + sum(mltp_te[l, stage + 1, cn, op, iter_] *
                                                            (nte_par_k[l, t, n, iter_] -
                                                             m.Bl[stage].nte[l, t])
                                                            for l in m.l_new))
                                                  for cn in children_node[n])))

        # solve node in first stage
    op = 0
    stage = 1
    n = 'O'

    opt = SolverFactory('cplex')
    opt.options['timelimit'] = 1000
    opt.options['mipgap'] = 0.0001
    opt.options['threads'] = 1
    opt.options['relax_integrality'] = 1
    opt.solve(m.Bl[stage], tee=False)
    cost_backward[stage, n, iter_] = m.Bl[stage].obj()

    # Compute lower bound
    cost_LB[iter_] = cost_backward[stage, n, iter_]
    print(cost_LB)
    # Compute optimality gap
    gap[iter_] = (cost_UB[iter_] - cost_LB[iter_]) / cost_UB[iter_] * 100
    print("gap: ", gap[iter_])

    if gap[iter_] <= opt_tol:                           
        if_converged[iter_] = True
    else:
        if_converged[iter_] = False

    elapsed_time = time.time() - start_time
    print("CPU Time (s)", elapsed_time)
    print(cost_UB)
    print(cost_LB)
    if (if_converged[iter_] or  iter_ == max_iter - 1 or elapsed_time > max_time ) and relax_integrality == 0:
        last_iter = iter_
        break    
    if if_converged[iter_] or iter_ == max_iter - 2 or elapsed_time > max_time:      
      relax_integrality = 0



elapsed_time = time.time() - start_time


