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
import pymp
import csv


from scenarioTree import create_scenario_tree
import deterministic.readData_det as readData_det
import deterministic.gtep_optBlocks_det as b
# import deterministic.optBlocks_det as b
from forward_gtep import forward_pass
from backward_SDDiP_gtep import backward_pass

# ######################################################################################################################
# USER-DEFINED PARAMS

# Define case-study
curPath = os.path.abspath(os.path.curdir)
curPath = curPath.replace('/deterministic', '')
print(curPath)
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2034_no_nuc.db')
filepath = os.path.join(curPath, 'data/GTEP_data_5years.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2039.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2024.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2029.db')

n_stages = 5  # number od stages in the scenario tree
stages = range(1, n_stages + 1)
scenarios = ['M']
single_prob = {'M': 1.0}

# time_periods = 10
time_periods = 5
set_time_periods = range(1, time_periods + 1)
# t_per_stage = {1:[1], 2:[2], 3:[3]}
# t_per_stage = {1: [1, 2], 2: [3, 4], 3: [5, 6], 4: [7, 8], 5: [9, 10]}
t_per_stage = {1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}
# t_per_stage = {1: [1], 2: [2], 3: [3], 4: [4], 5: [5], 6: [6], 7: [7], 8: [8], 9: [9], 10: [10]}
# t_per_stage = {1: [1], 2: [2], 3: [3], 4: [4], 5: [5], 6: [6], 7: [7], 8: [8], 9: [9], 10: [10],
#                11: [11], 12: [12], 13: [13], 14: [14], 15: [15]}

# Define parameters of the decomposition
max_iter = 100
opt_tol = 1  # %

# ######################################################################################################################

# create scenarios and input data
nodes, n_stage, parent_node, children_node, prob, sc_nodes = create_scenario_tree(stages, scenarios, single_prob)
readData_det.read_data(filepath, curPath, stages, n_stage, t_per_stage)
sc_headers = list(sc_nodes.keys())

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
m = b.create_model(n_stages, time_periods, t_per_stage, max_iter)
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

# converting sets to lists:
rn_r = list(m.rn_r)
th_r = list(m.th_r)
j_r = [(j, r) for j in m.j for r in m.r]
l_new = list(m.l_new)

# request the dual variables for all (locally) defined blocks
for b in m.Bl.values():
    b.dual = Suffix(direction=Suffix.IMPORT)

# Add equality constraints (solve the full space)
# for stage in m.stages:
#     if stage != 1:
#         # print('stage', stage, 't_prev', t_prev)
#         for (rn, r) in m.rn_r:
#             m.Bl[stage].link_equal1.add(expr=(m.Bl[stage].ngo_rn_prev[rn, r] ==
#                                               m.Bl[stage-1].ngo_rn[rn, r, t_per_stage[stage-1][-1]] ))
#         for (th, r) in m.th_r:
#             m.Bl[stage].link_equal2.add(expr=(m.Bl[stage].ngo_th_prev[th, r] ==
#                                                 m.Bl[stage-1].ngo_th[th, r, t_per_stage[stage-1][-1]]  ))
#         for (j, r) in j_r:
#             m.Bl[stage].link_equal3.add(expr=(m.Bl[stage].nso_prev[j, r] ==
#                                                  m.Bl[stage-1].nso[j, r, t_per_stage[stage-1][-1]]))

#         for l in m.l_new:
#             m.Bl[stage].link_equal4.add(expr=(m.Bl[stage].nte_prev[l] ==
#                                                  m.Bl[stage-1].nte[l, t_per_stage[stage-1][-1]]))
# m.obj = Objective(expr=0, sense=minimize)

# for stage in m.stages:
#     m.Bl[stage].obj.deactivate()
#     m.obj.expr += m.Bl[stage].obj.expr


# # solve relaxed model
# a = TransformationFactory("core.relax_integrality")
# a.apply_to(m)

# opt = SolverFactory("cplex")
# opt.options['mipgap'] = 0.01
# opt.solve(m, tee=True)

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
for iter_ in m.iter:

    # ####### Forward Pass ############################################################
    # solve ORIGIN node:
    stage = 1
    n = 'O'
    print("Forward Pass: ", "Stage", stage, "Current Node", n)
    op = 0
    # for r in m.r:
    #     for t in t_per_stage[stage]:
    #         for d in m.d:
    #             for s in m.hours:
    #                 m.L[r, t, d, s] = readData_det.L_by_scenario[op][r, t, d, s]
    #                 for rn in m.rn:
    #                     if (rn, r) in rn_r:
    #                         m.cf[rn, r, t, d, s] = readData_det.cf_by_scenario[op][rn, r, t, d, s]

    # # populate strategic uncertainty parameter
    # for t in t_per_stage[stage]:
    #     node = n[-1]
    #     m.tx_CO2[t, stage] = readData_det.tx_CO2[t, stage, node]

    ngo_rn, ngo_th, nso, nte, cost = forward_pass(m.Bl[stage], rn_r, th_r, j_r, l_new, t_per_stage[stage])

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
                # for r in m.r:
                #     for t in t_per_stage[stage]:
                #         for d in m.d:
                #             for s in m.hours:
                #                 m.L[r, t, d, s] = readData_det.L_by_scenario[op][r, t, d, s]
                #                 for rn in m.rn:
                #                     if (rn, r) in rn_r:
                #                         m.cf[rn, r, t, d, s] = readData_det.cf_by_scenario[op][rn, r, t, d, s]

                # # populate strategic uncertainty parameter
                # for t in t_per_stage[stage]:
                #     node = n[-1]
                #     m.tx_CO2[t, stage] = readData_det.tx_CO2[t, stage, node]

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

                ngo_rn, ngo_th, nso, nte, cost = forward_pass(m.Bl[stage], rn_r, th_r, j_r, l_new, t_per_stage[stage])

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

    cost_UB[iter_] = min(cost_forward[kk] for kk in m.iter if kk <= iter_)
    print(cost_UB)
    elapsed_time = time.time() - start_time
    print("CPU Time (s)", elapsed_time)

    # ####### Backward Pass ############################################################
    m.k.add(iter_)

    for stage in reversed(list(m.stages)):
        if stage != n_stages:
            for n in n_stage[stage]:
                for cn in children_node[n]:
                    for op in [0]:
                        print("Children Node", cn, "of stage", stage + 1, "op scenario", op)

                        # # update operating data for current realization of op_scenario
                        # for r in m.r:
                        #     for t in t_per_stage[stage+1]:
                        #         for d in m.d:
                        #             for s in m.hours:
                        #                 m.L[r, t, d, s] = readData_det.L_by_scenario[op][r, t, d, s]
                        #                 for rn in m.rn:
                        #                     if (rn, r) in rn_r:
                        #                         m.cf[rn, r, t, d, s] = readData_det.cf_by_scenario[op][
                        #                             rn, r, t, d, s]

                        # populate strategic uncertainty parameter
                        # for t in t_per_stage[stage + 1]:
                        #     node = cn[-1]
                        #     m.tx_CO2[t, stage+1] = readData_det.tx_CO2[t, stage+1, node]

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
    # update operating data for current realization of op_scenario
    # for r in m.r:
    #     for t in t_per_stage[stage]:
    #         for d in m.d:
    #             for s in m.hours:
    #                 m.L[r, t, d, s] = readData_det.L_by_scenario[op][r, t, d, s]
    #                 for rn in m.rn:
    #                     if (rn, r) in rn_r:
    #                         m.cf[rn, r, t, d, s] = readData_det.cf_by_scenario[op][
    #                             rn, r, t, d, s]
    # # populate strategic uncertainty parameter
    # for t in t_per_stage[stage]:
    #     node = n[-1]
    #     m.tx_CO2[t, stage] = readData_det.tx_CO2[t, stage, node]

    opt = SolverFactory('gurobi')
    opt.options['timelimit'] = 500
    opt.options['mipgap'] = 0.001
    opt.solve(m.Bl[stage], tee=True)
    cost_backward[stage, n, iter_] = m.Bl[stage].obj()

    # Compute lower bound
    cost_LB[iter_] = cost_backward[stage, n, iter_]
    print(cost_LB)
    # Compute optimality gap
    gap[iter_] = (cost_UB[iter_] - cost_LB[iter_]) / cost_UB[iter_] * 100
    print("gap: ", gap[iter_])

    if gap[iter_] <= opt_tol:
        with open('results_deterministic.csv', mode='w') as results_file:
            results_writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for stage in stages:
                for n in n_stage[stage]:
                    for t in t_per_stage[stage]:
                        for (rn, r) in rn_r:
                            if ngo_rn_par_k[rn, r, t, n, iter_] != 0:
                                results_writer.writerow([rn, r, t, n, ngo_rn_par_k[rn, r, t, n, iter_]])
                        for (th, r) in th_r:
                            if ngo_th_par_k[th, r, t, n, iter_] != 0:
                                results_writer.writerow([th, r, t, n, ngo_th_par_k[th, r, t, n, iter_]])
                        for (j, r) in j_r:
                            if nso_par_k[j, r, t, n, iter_] != 0:
                                results_writer.writerow([j, r, t, n, nso_par_k[j, r, t, n, iter_]])
                        for l in l_new:
                            if nte_par_k[l, t, n, iter_] != 0:
                                results_writer.writerow([l, t, n, nte_par_k[l, t, n, iter_]])                                
        if_converged[iter_] = True
    else:
        if_converged[iter_] = False

    elapsed_time = time.time() - start_time
    print("CPU Time (s)", elapsed_time)

    if if_converged[iter_]:
        last_iter = iter_
        break

elapsed_time = time.time() - start_time
print("Upper Bound", cost_UB[last_iter])
print("Lower Bound", cost_LB[last_iter])
print("Optimality gap (%)", gap[last_iter])
print("CPU Time (s)", elapsed_time)

variable_operating_cost = []
fixed_operating_cost =[]
startup_cost = []
thermal_generator_cost = []
extending_thermal_generator_cost = []
renewable_generator_cost = []
extending_renewable_generator_cost = []
storage_investment_cost = []
penalty_cost = []
renewable_capacity = []
thermal_capacity = []
total_capacity = []
transmission_line_cost = []
for stage in m.stages:
    variable_operating_cost.append(m.Bl[stage].variable_operating_cost.expr())
    fixed_operating_cost.append(m.Bl[stage].fixed_operating_cost.expr())
    startup_cost.append(m.Bl[stage].startup_cost.expr())
    thermal_generator_cost.append(m.Bl[stage].thermal_generator_cost.expr())
    extending_thermal_generator_cost.append(m.Bl[stage].extending_thermal_generator_cost.expr())
    renewable_generator_cost.append(m.Bl[stage].renewable_generator_cost.expr())
    extending_renewable_generator_cost.append(m.Bl[stage].extending_renewable_generator_cost.expr())
    storage_investment_cost.append(m.Bl[stage].storage_investment_cost.expr())
    penalty_cost.append(m.Bl[stage].penalty_cost.expr())
    renewable_capacity.append(m.Bl[stage].renewable_capacity.expr())
    thermal_capacity.append(m.Bl[stage].thermal_capacity.expr())
    total_capacity.append(m.Bl[stage].total_capacity.expr())
    transmission_line_cost.append(m.Bl[stage].transmission_line_cost.expr())

print("variable_operating_cost")
print(variable_operating_cost)
print(sum(variable_operating_cost))
print("fixed_operating_cost")
print(fixed_operating_cost)
print(sum(fixed_operating_cost))
print("startup_cost")
print(startup_cost)
print(sum(startup_cost))
print("thermal_generator_cost")
print(thermal_generator_cost)
print(sum(thermal_generator_cost))
print("extending_thermal_generator_cost")
print(extending_thermal_generator_cost)
print(sum(extending_thermal_generator_cost))
print("renewable_generator_cost")
print(renewable_generator_cost)
print(sum(renewable_generator_cost))
print("extending_renewable_generator_cost")
print(extending_renewable_generator_cost)
print(sum(extending_renewable_generator_cost))
print("storage_investment_cost")
print(storage_investment_cost)
print(sum(storage_investment_cost))
print("penalty_cost")
print(penalty_cost)
print(sum(penalty_cost))
print("renewable_capacity")
print(renewable_capacity)
print(sum(renewable_capacity))
print("thermal_capacity")
print(thermal_capacity)
print(sum(thermal_capacity))
print("total_capacity")
print(total_capacity)
print(sum(total_capacity))
print("transmission_line_cost")
print(transmission_line_cost)
print(sum(transmission_line_cost))
