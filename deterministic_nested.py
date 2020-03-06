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
# filepath = os.path.join(curPath, 'data/GTEP_data_5years.db')
filepath = os.path.join(curPath, 'data/GTEPdata_2020_2039.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2024.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2029.db')

n_stages = 20  # number od stages in the scenario tree
formulation = "hull"
outputfile = "nested_medium_tx_CO2_lowgrowthallregion_cheaplines_hull_benders_scaleCF.csv"
stages = range(1, n_stages + 1)
scenarios = ['M']
single_prob = {'M': 1.0}

# time_periods = 10
time_periods = n_stages
set_time_periods = range(1, time_periods + 1)
t_per_stage = {}
for i in range(1, n_stages+1):
  t_per_stage[i] = [i]
# Define parameters of the decomposition
max_iter = 100
max_time = 36000
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
m = b.create_model(n_stages, time_periods, t_per_stage, max_iter, formulation)
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
relax_integrality = 1
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
solar_capacity = []
wind_capacity = []
nuclear_capacity = []
coal_capacity = []
natural_gas_capacity = []
solar_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
wind_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
nuclear_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
coal_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
natural_gas_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
power_flow = []
solar_energy_generated = []
wind_energy_generated = []
nuclear_energy_generated = []
coal_energy_generated = []
natural_gas_energy_generated = []
total_energy_generated = []




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
    coal_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.co) )
    natural_gas_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.ng) )
    nuclear_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.nu) )
    solar_capacity.append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, r in m.i_r if (rn in m.pv or rn in m.csp)) )
    wind_capacity.append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, r in m.i_r if rn in m.wi) )
    for r in m.r:
        coal_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for  th, rr in m.i_r if (rr==r and th in m.co) ))
        natural_gas_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, rr in m.i_r if (rr==r and th in m.ng) ))
        nuclear_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, rr in m.i_r if (rr==r  and th in m.nu) ))
        solar_capacity_region[r].append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, rr in m.i_r if (rr == r and (rn in m.pv or rn in m.csp))) )
        wind_capacity_region[r].append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, rr in m.i_r if( rr==r and rn in m.wi) ))
    total_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for (i,r)
     in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours))
    coal_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for 
        (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.co))
    natural_gas_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for
     (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.ng))
    nuclear_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for 
        (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.nu))
    solar_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for
     (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if (i in m.pv or i in m.csp)))
    wind_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for 
        (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.wi ))
    temp_power_flow = {}
    for r in m.r:
        temp_power_flow[r] = {}
        for rr in m.r:
            temp_power_flow[r][rr] = 0
    for l in m.l:
        for t in t_per_stage[stage]:
            for d in m.d:
                for s in m.hours:
                    er = m.l_er[l][1]
                    sr = m.l_sr[l][1]
                    if m.Bl[stage].P_flow[l,t,d,s].value > 0:
                        temp_power_flow[sr][er] += m.Bl[stage].P_flow[l,t,d,s].value * m.n_d[d] * pow(10,-6)
                    else:
                        temp_power_flow[er][sr] -= m.Bl[stage].P_flow[l,t,d,s].value * m.n_d[d] * pow(10,-6)
    # for r in m.r_Panhandle:
    #     for t in t_per_stage[stage]:
    #         for d in m.d:
    #             for s in m.hours:  
    #                 temp_power_flow['Panhandle'][r]  += m.Bl[stage].P_Panhandle[r,t,d,s].value * m.n_d[d] * pow(10,-6)
    power_flow.append(temp_power_flow)

    



import csv
energy_region_dict ={"solar":solar_capacity_region,
"nuc":nuclear_capacity_region, 
"coal":coal_capacity_region,
"natural gas": natural_gas_capacity_region,
"wind":wind_capacity_region}
with open('results/' + outputfile, 'w', newline='') as results_file:
            # results_writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # results_writer.writerow(["ratio_N ", self.ratio_N , " ratio_M " , self.ratio_M])
            # results_writer.writerow(["best_UB_lo", self.best_UB_lo, "best_UB_up", self.best_UB_up])
            # results_writer.writerow(["best binary", self.best_binary])
            # results_writer.writerow(["is OA infeasible", self.is_OA_infeasible])
            # results_writer.writerow(["post_analysis_time", self.post_analysis_time])
            fieldnames = ["Time", "variable_operating_cost",
                        "fixed_operating_cost",
                        "startup_cost",
                        "thermal_generator_cost",
                        "extending_thermal_generator_cost",
                        "renewable_generator_cost",
                        "extending_renewable_generator_cost",
                        "storage_investment_cost",
                        "penalty_cost",
                        "renewable_capacity",
                        "thermal_capacity",                        
                        "transmission_line_cost",
                        "coal_capacity",
                        "natural_gas_capacity",
                        "nuclear_capacity",
                        "solar_capacity",
                        "wind_capacity",
                        "total_capacity",
                        "power_flow",
                        "solar_energy_generated",
                        "wind_energy_generated",
                        "nuclear_energy_generated",
                        "coal_energy_generated",
                        "natural_gas_energy_generated",
                        "total_energy_generated"
                        ]
            for r in m.r:
                for gen in ["coal", "natural gas", "nuc", "solar", "wind"]:
                    fieldnames.append(r+ " " + gen)
            writer = csv.DictWriter(results_file, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(len(m.stages)):
                new_row = {"Time":i + 1,
                    "variable_operating_cost":variable_operating_cost[i],
                    "fixed_operating_cost":fixed_operating_cost[i],
                    "startup_cost":startup_cost[i],
                    "thermal_generator_cost":thermal_generator_cost[i],
                    "extending_thermal_generator_cost":extending_thermal_generator_cost[i],
                    "renewable_generator_cost":renewable_generator_cost[i],
                    "extending_renewable_generator_cost":extending_renewable_generator_cost[i],
                    "storage_investment_cost":storage_investment_cost[i],
                    "penalty_cost":penalty_cost[i],
                    "renewable_capacity":renewable_capacity[i],
                    "thermal_capacity":thermal_capacity[i],
                    "total_capacity":total_capacity[i],
                    "transmission_line_cost":transmission_line_cost[i],
                    "coal_capacity":coal_capacity[i],
                    "natural_gas_capacity":natural_gas_capacity[i],
                    "nuclear_capacity":nuclear_capacity[i],
                    "solar_capacity":solar_capacity[i],
                    "wind_capacity":wind_capacity[i],
                    "power_flow":power_flow[i],
                    "solar_energy_generated":solar_energy_generated[i],
                    "wind_energy_generated":wind_energy_generated[i],
                    "nuclear_energy_generated":nuclear_energy_generated[i],
                    "coal_energy_generated":coal_energy_generated[i],
                    "natural_gas_energy_generated":natural_gas_energy_generated[i],
                    "total_energy_generated":total_energy_generated[i]}
                for r in m.r:
                    for gen in ["coal", "natural gas", "nuc", "solar", "wind"]:
                        key = r+ " " + gen
                        new_row[key] = energy_region_dict[gen][r][i]
                writer.writerow(new_row)
            results_writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # for i in range(len(m.stages)):
            #     results_writer.writerow([" "])
            #     results_writer.writerow(["t=" + str(i+1), 'Northeast', 'West', 'Coastal', 'South', 'Panhandle'])
            #     for r in m.r:
            #         new_row = [r]
            #         for rr in m.r:
            #             new_row.append(power_flow[i][r][rr])
            #         results_writer.writerow(new_row)
            #get the transmission line expansion 
            for stage in m.stages:                
                for l in m.l_new:
                    if m.Bl[stage].ntb[l,stage].value > 0.1:
                        temp_row = [stage, readData_det.tielines[l-1]["Near Area Name"], readData_det.tielines[l-1]["Far Area Name"]]
                        results_writer.writerow(temp_row)
                 #get the peak demand network structure in the last year  
            last_stage = len(m.stages)                          
            # m.L = Param(m.r, m.t, m.d, m.hours, default=0, initialize=readData_det.L_by_scenario[0], mutable=True) 
            largest_d, largest_s =  0, 0
            largest_load = 0.0
            for r in m.r:
                for d in m.d:
                    for s in m.hours:
                        if m.L[r, last_stage,d,s].value > largest_load:
                            largest_load = m.L[r, last_stage,d,s].value
                            largest_d = d 
                            largest_s = s 
            #write down the load of each region 
            results_writer.writerow([" at last year ",  d, s])
            results_writer.writerow([" ", 'Northeast', 'West', 'Coastal', 'South', 'Panhandle'])
            results_writer.writerow(["load ", m.L["Northeast", last_stage, largest_d, largest_s].value, 
                m.L["West", last_stage, largest_d, largest_s].value,m.L["Coastal", last_stage, largest_d, largest_s].value,
                m.L["South", last_stage, largest_d, largest_s].value,m.L["Panhandle", last_stage, largest_d, largest_s].value])
            new_row = ["power generation"]
            for r in m.r:
                new_row.append(sum(m.Bl[last_stage].P[i, r, last_stage, largest_d, largest_s].value for i,rr in m.i_r if rr==r))
            results_writer.writerow(new_row)
            new_row = ["power charged"]
            for r in m.r:
                new_row.append(sum(m.Bl[last_stage].p_charged[j, r, last_stage, largest_d, largest_s].value for j in m.j)) 
            results_writer.writerow(new_row)
            new_row = ["power discharged"]    
            for r in m.r:
                new_row.append(sum(m.Bl[last_stage].p_discharged[j, r, last_stage, largest_d, largest_s].value for j in m.j))     
            results_writer.writerow(new_row)
            new_row = ["transmission power "]
            for r in m.r:
                temp_P = 0
                for l in m.l:
                    er = m.l_er[l][1]
                    sr = m.l_sr[l][1]
                    if er == r:
                        temp_P += m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value
                    if sr == r:
                        temp_P -= m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value
                new_row.append(temp_P)
            results_writer.writerow(new_row)
            new_row = ["curtailment "]
            for r in m.r:
                new_row.append(m.Bl[last_stage].cu[r, last_stage, largest_d, largest_s].value)
            results_writer.writerow(new_row)
               #power transmission of each line 
            results_writer.writerow([])
            results_writer.writerow(["transmission at peak load "])
            for l in m.l:
                if abs(m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value) > 0.1:
                    results_writer.writerow([readData_det.tielines[l-1]["Near Area Name"], readData_det.tielines[l-1]["Far Area Name"], m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value ])
            results_writer.writerow([])        
            results_writer.writerow(["Upper Bound", cost_forward[last_iter], "Lower Bound", cost_LB[last_iter]])
            results_writer.writerow(["Optimality gap (%)", (cost_forward[last_iter]-cost_LB[last_iter])/ cost_forward[last_iter] * 100, "CPU Time (s)", elapsed_time])
            results_writer.writerow(["forward pass value"])
            results_writer.writerow([cost_UB[key] for key in cost_UB.keys()])
            results_writer.writerow("backward_pass value")
            results_writer.writerow([cost_LB[key] for key in cost_LB.keys()])
