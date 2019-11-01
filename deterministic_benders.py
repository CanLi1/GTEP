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
for stage in m.stages:
    if stage != 1:
        # print('stage', stage, 't_prev', t_prev)
        for (rn, r) in m.rn_r:
            m.Bl[stage].link_equal1.add(expr=(m.Bl[stage].ngo_rn_prev[rn, r] ==
                                              m.Bl[stage-1].ngo_rn[rn, r, t_per_stage[stage-1][-1]] ))
        for (th, r) in m.th_r:
            m.Bl[stage].link_equal2.add(expr=(m.Bl[stage].ngo_th_prev[th, r] ==
                                                m.Bl[stage-1].ngo_th[th, r, t_per_stage[stage-1][-1]]  ))
        for (j, r) in j_r:
            m.Bl[stage].link_equal3.add(expr=(m.Bl[stage].nso_prev[j, r] ==
                                                 m.Bl[stage-1].nso[j, r, t_per_stage[stage-1][-1]]))

        for l in m.l_new:
            m.Bl[stage].link_equal4.add(expr=(m.Bl[stage].nte_prev[l] ==
                                                 m.Bl[stage-1].nte[l, t_per_stage[stage-1][-1]]))
m.obj = Objective(expr=0, sense=minimize)

for stage in m.stages:
    m.Bl[stage].obj.deactivate()
    m.obj.expr += m.Bl[stage].obj.expr


# # solve relaxed model
# a = TransformationFactory("core.relax_integrality")
# a.apply_to(m)
operating_integer_vars = ["u", "su", "sd"]
for stage in m.stages:
    for t in t_per_stage[stage]:
        for d in m.d:
            for s in m.hours:
                for (th, r) in m.th_r:
                    lb, ub = m.Bl[stage].u[th, r, t, d, s].bounds
                    m.Bl[stage].u[th, r, t, d, s].domain = Reals
                    m.Bl[stage].u[th, r, t, d, s].setlb(lb)
                    m.Bl[stage].u[th, r, t, d, s].setub(ub)     
                    lb, ub = m.Bl[stage].su[th, r, t, d, s].bounds
                    m.Bl[stage].su[th, r, t, d, s].domain = Reals
                    m.Bl[stage].su[th, r, t, d, s].setlb(lb)
                    m.Bl[stage].su[th, r, t, d, s].setub(ub)  
                    lb, ub = m.Bl[stage].sd[th, r, t, d, s].bounds
                    m.Bl[stage].sd[th, r, t, d, s].domain = Reals
                    m.Bl[stage].sd[th, r, t, d, s].setlb(lb)
                    m.Bl[stage].sd[th, r, t, d, s].setub(ub)                                                     
import time

opt = SolverFactory("cplex_persistent")
 

opt.set_instance(m)
opt.set_benders_annotation()
opt.set_benders_strategy(2)

#set master variables 
for stage in m.stages:
    for t in t_per_stage[stage]:
        # print('stage', stage, 't_prev', t_prev)
        for (rn, r) in m.rn_r:
            opt.set_master_variable(m.Bl[stage].ngo_rn[rn, r, t])
            opt.set_master_variable(m.Bl[stage].ngb_rn[rn, r, t])
            opt.set_master_variable(m.Bl[stage].nge_rn[rn, r, t])
            opt.set_master_variable(m.Bl[stage].ngr_rn[rn, r, t])
        for (th, r) in m.th_r:
            opt.set_master_variable(m.Bl[stage].ngo_th[th, r, t]  )
            opt.set_master_variable(m.Bl[stage].ngb_th[th, r, t]  )
            opt.set_master_variable(m.Bl[stage].nge_th[th, r, t]  )
            opt.set_master_variable(m.Bl[stage].ngr_th[th, r, t]  )            
        for (j, r) in j_r:
            opt.set_master_variable(m.Bl[stage].nso[j, r, t])
            opt.set_master_variable(m.Bl[stage].nsb[j, r, t])
            opt.set_master_variable(m.Bl[stage].nsr[j, r, t])

        for l in m.l_new:
            opt.set_master_variable(m.Bl[stage].nte[l, t])
            opt.set_master_variable(m.Bl[stage].ntb[l, t])

opt.solve(m, tee=True)

#fix the integer variables from Benders and resolve the original problem by stages
m.obj.deactivate()
for stage in m.stages:
    m.Bl[stage].obj.activate() ####To do
for stage in m.stages:
    for t in t_per_stage[stage]:
        for d in m.d:
            for s in m.hours:
                for (th, r) in m.th_r:
                    lb, ub = m.Bl[stage].u[th, r, t, d, s].bounds
                    m.Bl[stage].u[th, r, t, d, s].domain = NonNegativeIntegers
                    m.Bl[stage].u[th, r, t, d, s].setlb(lb)
                    m.Bl[stage].u[th, r, t, d, s].setub(ub)     
                    lb, ub = m.Bl[stage].su[th, r, t, d, s].bounds
                    m.Bl[stage].su[th, r, t, d, s].domain = NonNegativeIntegers
                    m.Bl[stage].su[th, r, t, d, s].setlb(lb)
                    m.Bl[stage].su[th, r, t, d, s].setub(ub)  
                    lb, ub = m.Bl[stage].sd[th, r, t, d, s].bounds
                    m.Bl[stage].sd[th, r, t, d, s].domain = NonNegativeIntegers
                    m.Bl[stage].sd[th, r, t, d, s].setlb(lb)
                    m.Bl[stage].sd[th, r, t, d, s].setub(ub)        

for stage in m.stages:
    #clear the linking constraints to solve each block separately
    m.Bl[stage].link_equal1.clear()
    m.Bl[stage].link_equal2.clear()
    m.Bl[stage].link_equal3.clear()
    m.Bl[stage].link_equal4.clear()

    for t in t_per_stage[stage]:
        # print('stage', stage, 't_prev', t_prev)
        for (rn, r) in m.rn_r:
            value = m.Bl[stage].ngo_rn[rn, r, t].value
            m.Bl[stage].ngo_rn[rn, r, t].fix(value)
            value = m.Bl[stage].ngb_rn[rn, r, t].value
            m.Bl[stage].ngb_rn[rn, r, t].fix(value)
            value = m.Bl[stage].nge_rn[rn, r, t].value
            m.Bl[stage].nge_rn[rn, r, t].fix(value)
            value = m.Bl[stage].ngr_rn[rn, r, t].value
            m.Bl[stage].ngr_rn[rn, r, t].fix(value)                                    
        for (th, r) in m.th_r:
            value = m.Bl[stage].ngo_th[th, r, t].value
            m.Bl[stage].ngo_th[th, r, t].fix(value)
            value = m.Bl[stage].ngb_th[th, r, t].value
            m.Bl[stage].ngb_th[th, r, t].fix(value)
            value = m.Bl[stage].nge_th[th, r, t].value
            m.Bl[stage].nge_th[th, r, t].fix(value)
            value = m.Bl[stage].ngr_th[th, r, t].value
            m.Bl[stage].ngr_th[th, r, t].fix(value)                                    
        for (j, r) in j_r:
            value = m.Bl[stage].nso[j, r, t].value
            m.Bl[stage].nso[j, r, t].fix(value)
            value = m.Bl[stage].nsb[j, r, t].value
            m.Bl[stage].nsb[j, r, t].fix(value)
            value = m.Bl[stage].nsr[j, r, t].value
            m.Bl[stage].nsr[j, r, t].fix(value)                        

        for l in m.l_new:
            value = m.Bl[stage].nte[l, t].value
            m.Bl[stage].nte[l, t].fix(value)   
            value = m.Bl[stage].ntb[l, t].value
            m.Bl[stage].ntb[l, t].fix(value)                

upper_bound_obj = 0.0
lopt = SolverFactory("cplex")
lopt.options['mipgap'] = 0.01
for stage in m.stages:
    lopt.solve(m.Bl[stage], tee=True)
    upper_bound_obj += m.Bl[stage].obj.value 


# variable_operating_cost = []
# fixed_operating_cost =[]
# startup_cost = []
# thermal_generator_cost = []
# extending_thermal_generator_cost = []
# renewable_generator_cost = []
# extending_renewable_generator_cost = []
# storage_investment_cost = []
# penalty_cost = []
# renewable_capacity = []
# thermal_capacity = []
# total_capacity = []
# transmission_line_cost = []
# for stage in m.stages:
#     variable_operating_cost.append(m.Bl[stage].variable_operating_cost.expr())
#     fixed_operating_cost.append(m.Bl[stage].fixed_operating_cost.expr())
#     startup_cost.append(m.Bl[stage].startup_cost.expr())
#     thermal_generator_cost.append(m.Bl[stage].thermal_generator_cost.expr())
#     extending_thermal_generator_cost.append(m.Bl[stage].extending_thermal_generator_cost.expr())
#     renewable_generator_cost.append(m.Bl[stage].renewable_generator_cost.expr())
#     extending_renewable_generator_cost.append(m.Bl[stage].extending_renewable_generator_cost.expr())
#     storage_investment_cost.append(m.Bl[stage].storage_investment_cost.expr())
#     penalty_cost.append(m.Bl[stage].penalty_cost.expr())
#     renewable_capacity.append(m.Bl[stage].renewable_capacity.expr())
#     thermal_capacity.append(m.Bl[stage].thermal_capacity.expr())
#     total_capacity.append(m.Bl[stage].total_capacity.expr())
#     transmission_line_cost.append(m.Bl[stage].transmission_line_cost.expr())

# print("variable_operating_cost")
# print(variable_operating_cost)
# print(sum(variable_operating_cost))
# print("fixed_operating_cost")
# print(fixed_operating_cost)
# print(sum(fixed_operating_cost))
# print("startup_cost")
# print(startup_cost)
# print(sum(startup_cost))
# print("thermal_generator_cost")
# print(thermal_generator_cost)
# print(sum(thermal_generator_cost))
# print("extending_thermal_generator_cost")
# print(extending_thermal_generator_cost)
# print(sum(extending_thermal_generator_cost))
# print("renewable_generator_cost")
# print(renewable_generator_cost)
# print(sum(renewable_generator_cost))
# print("extending_renewable_generator_cost")
# print(extending_renewable_generator_cost)
# print(sum(extending_renewable_generator_cost))
# print("storage_investment_cost")
# print(storage_investment_cost)
# print(sum(storage_investment_cost))
# print("penalty_cost")
# print(penalty_cost)
# print(sum(penalty_cost))
# print("renewable_capacity")
# print(renewable_capacity)
# print(sum(renewable_capacity))
# print("thermal_capacity")
# print(thermal_capacity)
# print(sum(thermal_capacity))
# print("total_capacity")
# print(total_capacity)
# print(sum(total_capacity))
# print("transmission_line_cost")
# print(transmission_line_cost)
# print(sum(transmission_line_cost))
