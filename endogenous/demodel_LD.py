__author__ = "Can Li"

import time
import math
import random
from copy import deepcopy
import os.path
from pyomo.environ import *
import csv
import copy 

from scenarioTree import create_scenario_tree
import deterministic.readData_det as readData_det
import endogenous.endo_gtep_optBlocks_det as b
from endogenous.util import * 


# ######################################################################################################################
# USER-DEFINED PARAMS

# Define case-study
curPath = os.path.abspath(os.path.curdir)
print(curPath)
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2034_no_nuc.db')
# filepath = os.path.join(curPath, 'data/GTEP_data_15years.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2039.db')
filepath = os.path.join(curPath, 'data/GTEPdata_2020_2024.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2029.db')

n_stages = 5  # number od stages in the scenario tree
formulation = "improved"
outputfile = "endoresults/5years.csv"
num_days =5
print(formulation, outputfile, num_days)
stages = range(1, n_stages + 1)
scenarios = ['M']
single_prob = {'M': 1.0}


time_periods = n_stages
set_time_periods = range(1, time_periods + 1)
t_per_stage = {}
for i in range(1, n_stages+1):
  t_per_stage[i] = [i]

# Define parameters of the decomposition
max_iter = 100
opt_tol = 1  # %

# ######################################################################################################################

# create scenarios and input data
nodes, n_stage, parent_node, children_node, prob, sc_nodes = create_scenario_tree(stages, scenarios, single_prob)


readData_det.read_data(filepath, curPath, stages, n_stage, t_per_stage, num_days)


# create blocks
num_scenario = 3
m = b.create_model(time_periods, formulation, readData_det, num_scenario)








ratio = [0.7, 1.0, 1.3]
#set uncertain parameters for the stochastic model 
for w in range(1, num_scenario+1):
    for i in m.i:
        for t in m.t:
            if i == 'coal-first-new':
                m.DIC[i, t, w] = readData_det.DIC[i,t] * ratio[w-1]
            else:
                m.DIC[i,t,w] = readData_det.DIC[i,t]

a = TransformationFactory("core.relax_integrality")
a.apply_to(m)
opt = SolverFactory("cplex")
opt.options['LPMethod'] = 4
opt.options['solutiontype'] =2 
opt.options['mipgap'] = 0.001
opt.options['TimeLimit'] = 36000
opt.options['threads'] = 6
# opt.solve(m.scenario_block[1], )
for s in range(1, 4):
    opt.solve(m.scenario_block[s], tee=True)

#define investment variables and operating variables
investment_vars = ["ntb","nte","nte_prev","ngr_rn","nge_rn","ngr_th","nge_th","ngo_rn","ngb_rn","ngo_th","ngb_th","ngo_rn_prev","ngo_th_prev","nsr","nsb","nso","nso_prev", "alphafut", "RES_def"]
operating_vars = []
if formulation == "standard":
  operating_vars = ["theta", "P", "cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]
elif formulation == "hull":
  operating_vars = ["theta", "P", "d_theta_1", "d_theta_2","cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]
elif formulation == "improved":
  operating_vars = ["theta", "P", "d_theta_plus", "d_theta_minus", "d_P_flow_plus", "d_P_flow_minus", "cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]  
map_d = {'fall':3, 'summer':2, 'spring':1, 'winter':4}

#add initial NACs
for w in range(2, num_scenario + 1):
    for v in m.scenario_block[w].component_objects(Var):
        if v.getname() in investment_vars:
            for index in v:
                t = index[-1]
                new_index = list(copy.deepcopy(index))
                new_index[0] = 1
                new_index = tuple(new_index)
                new_var = getattr(m.scenario_block[1], v.getname())
                m.scenario_block[w].link_equal1.add(v[index] == new_var[new_index])

#add conditional NACs
scenario_pair = [(1,2), (1,3)]
m.s_pair = Set(initialize=scenario_pair)
m.Y = Var(m.s_pair, m.t, within=Binary)


#add NACs when Y equals 1 
for pair in scenario_pair:
    first_scenario = pair[0]
    second_scenario = pair[1]
    for v in m.scenario_block[second_scenario].component_objects(Var):
        new_var = getattr(m.scenario_block[first_scenario], v.getname())
        for index in v:
            if v.getname() in investment_vars:
                t = index[-1]
                if t != 1:
                    new_index = list(copy.deepcopy(index))
                    new_index[0] = first_scenario
                    new_index = tuple(new_index)                                        
                    m.scenario_block[second_scenario].link_equal2.add(v[index]- new_var[new_index]<= (v[index].ub - new_var[new_index].lb) * (1 - m.Y[pair, t-1]) ) 
                    m.scenario_block[second_scenario].link_equal2.add(v[index]- new_var[new_index]>= (v[index].lb - new_var[new_index].ub) * (1 - m.Y[pair, t-1]) ) 
            elif v.getname() in operating_vars:
                t = index[-3]
                new_index = list(copy.deepcopy(index))
                new_index[0] = first_scenario
                new_index = tuple(new_index)                      
                m.scenario_block[second_scenario].link_equal2.add(v[index]- new_var[new_index]<= (v[index].ub - new_var[new_index].lb) * (1 - m.Y[pair, t]) ) 
                m.scenario_block[second_scenario].link_equal2.add(v[index]- new_var[new_index]>= (v[index].lb - new_var[new_index].ub) * (1 - m.Y[pair, t]) )                


#determine the relationship between Y and the investment decisions
for pair in scenario_pair:
    for t in m.t:
        s1 = pair[0]
        s2 = pair[1]
        for th, r in m.th_r:
            if th == "coal-first-new":
                m.scenario_block[s2].link_equal3.add( sum(m.scenario_block[s2].ngb_th[s2, th, r, tt] for tt in m.t if tt <= t) <= m.scenario_block[s2].ngb_th[s2, th, r, t].ub * t * (1-m.Y[s1,s2,t])  )
                m.scenario_block[s2].link_equal3.add( sum(m.scenario_block[s2].ngb_th[s2, th, r, tt] for tt in m.t if tt <= t) >= (1-m.Y[s1,s2,t])  )

#set probability 
for s in m.scenarios:
    m.probability[s] = 1/num_scenario

#set objective 
m.obj = Objective(expr=0, sense=minimize)

for s in m.scenarios:
    m.scenario_block[s].obj.deactivate()
    m.obj.expr += m.scenario_block[s].obj.expr
a = TransformationFactory("core.relax_integrality")
a.apply_to(m)
opt = SolverFactory("cplex")
opt.options['LPMethod'] = 4
opt.options['solutiontype'] =2 
opt.options['mipgap'] = 0.001
opt.options['TimeLimit'] = 36000
opt.options['threads'] = 6
opt.solve(m, tee=True)

# # converting sets to lists:
# rn_r = list(m.rn_r)
# th_r = list(m.th_r)
# j_r = [(j, r) for j in m.j for r in m.r]
# l_new = list(m.l_new)

# # request the dual variables for all (locally) defined blocks
# for bloc in m.Bl.values():
#     bloc.dual = Suffix(direction=Suffix.IMPORT)

# # Add equality constraints (solve the full space)
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


# # # solve relaxed model
# # a = TransformationFactory("core.relax_integrality")
# # a.apply_to(m)
# # opt = SolverFactory("cplex")
# # opt.options['mipgap'] = 0.001
# # opt.options['TimeLimit'] = 36000
# # opt.solve(m, tee=True)
# operating_integer_vars = ["u", "su", "sd"]
# for stage in m.stages:
#     for t in t_per_stage[stage]:
#         for d in m.d:
#             for s in m.hours:
#                 for (th, r) in m.th_r:
#                     lb, ub = m.Bl[stage].u[th, r, t, d, s].bounds
#                     m.Bl[stage].u[th, r, t, d, s].domain = Reals
#                     m.Bl[stage].u[th, r, t, d, s].setlb(lb)
#                     m.Bl[stage].u[th, r, t, d, s].setub(ub)     
#                     lb, ub = m.Bl[stage].su[th, r, t, d, s].bounds
#                     m.Bl[stage].su[th, r, t, d, s].domain = Reals
#                     m.Bl[stage].su[th, r, t, d, s].setlb(lb)
#                     m.Bl[stage].su[th, r, t, d, s].setub(ub)  
#                     lb, ub = m.Bl[stage].sd[th, r, t, d, s].bounds
#                     m.Bl[stage].sd[th, r, t, d, s].domain = Reals
#                     m.Bl[stage].sd[th, r, t, d, s].setlb(lb)
#                     m.Bl[stage].sd[th, r, t, d, s].setub(ub)                                                     
# import time

# opt = SolverFactory("cplex_persistent")
 
# opt.options['threads'] = 1
# opt.options['timelimit'] = 3600*24
# opt.set_instance(m)
# opt.set_benders_annotation()
# opt.set_benders_strategy(1)
# opt.set_mip_rel_gap(0.005)

# #set master variables 
# investment_vars = ["ntb","nte","nte_prev","ngr_rn","nge_rn","ngr_th","nge_th","ngo_rn","ngb_rn","ngo_th","ngb_th","ngo_rn_prev","ngo_th_prev","nsr","nsb","nso","nso_prev", "alphafut", "RES_def"]
# for v in m.component_objects(Var):
#     if v.getname() in investment_vars:
#         for index in v:
#             opt.set_master_variable(v[index])

# #set subproblems
# operating_vars = []
# if formulation == "standard":
#   operating_vars = ["theta", "P", "cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]
# elif formulation == "hull":
#   operating_vars = ["theta", "P", "d_theta_1", "d_theta_2","cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]
# elif formulation == "improved":
#   operating_vars = ["theta", "P", "d_theta_plus", "d_theta_minus", "d_P_flow_plus", "d_P_flow_minus", "cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]  
# map_d = {'fall':3, 'summer':2, 'spring':1, 'winter':4}
# for v in m.component_objects(Var):
#     if v.getname() in operating_vars:
#         for index in v:
#             t = index[-3]
#             opt.set_subproblem_variable(v[index], t)


# opt.solve(m, tee=True)

# #fix the integer variables from Benders and resolve the original problem by stages
# m.obj.deactivate()
# for stage in m.stages:
#     m.Bl[stage].obj.activate() ####To do
# for stage in m.stages:
#     for t in t_per_stage[stage]:
#         for d in m.d:
#             for s in m.hours:
#                 for (th, r) in m.th_r:
#                     lb, ub = m.Bl[stage].u[th, r, t, d, s].bounds
#                     m.Bl[stage].u[th, r, t, d, s].domain = NonNegativeIntegers
#                     m.Bl[stage].u[th, r, t, d, s].setlb(lb)
#                     m.Bl[stage].u[th, r, t, d, s].setub(ub)     
#                     lb, ub = m.Bl[stage].su[th, r, t, d, s].bounds
#                     m.Bl[stage].su[th, r, t, d, s].domain = NonNegativeIntegers
#                     m.Bl[stage].su[th, r, t, d, s].setlb(lb)
#                     m.Bl[stage].su[th, r, t, d, s].setub(ub)  
#                     lb, ub = m.Bl[stage].sd[th, r, t, d, s].bounds
#                     m.Bl[stage].sd[th, r, t, d, s].domain = NonNegativeIntegers
#                     m.Bl[stage].sd[th, r, t, d, s].setlb(lb)
#                     m.Bl[stage].sd[th, r, t, d, s].setub(ub)        

# for stage in m.stages:
#     #clear the linking constraints to solve each block separately
#     m.Bl[stage].link_equal1.clear()
#     m.Bl[stage].link_equal2.clear()
#     m.Bl[stage].link_equal3.clear()
#     m.Bl[stage].link_equal4.clear()

#     for t in t_per_stage[stage]:
#         for (rn, r) in m.rn_r:
#             value = m.Bl[stage].ngo_rn[rn, r, t].value
#             m.Bl[stage].ngo_rn[rn, r, t].fix(value)
#             value = m.Bl[stage].ngb_rn[rn, r, t].value
#             m.Bl[stage].ngb_rn[rn, r, t].fix(value)
#             value = m.Bl[stage].nge_rn[rn, r, t].value
#             m.Bl[stage].nge_rn[rn, r, t].fix(value)
#             value = m.Bl[stage].ngr_rn[rn, r, t].value
#             m.Bl[stage].ngr_rn[rn, r, t].fix(value)                                    
#         for (th, r) in m.th_r:
#             value = m.Bl[stage].ngo_th[th, r, t].value
#             m.Bl[stage].ngo_th[th, r, t].fix(value)
#             value = m.Bl[stage].ngb_th[th, r, t].value
#             m.Bl[stage].ngb_th[th, r, t].fix(value)
#             value = m.Bl[stage].nge_th[th, r, t].value
#             m.Bl[stage].nge_th[th, r, t].fix(value)
#             value = m.Bl[stage].ngr_th[th, r, t].value
#             m.Bl[stage].ngr_th[th, r, t].fix(value)                                    
#         for (j, r) in j_r:
#             value = m.Bl[stage].nso[j, r, t].value
#             m.Bl[stage].nso[j, r, t].fix(value)
#             value = m.Bl[stage].nsb[j, r, t].value
#             m.Bl[stage].nsb[j, r, t].fix(value)
#             value = m.Bl[stage].nsr[j, r, t].value
#             m.Bl[stage].nsr[j, r, t].fix(value)                        

#         for l in m.l_new:
#             value = m.Bl[stage].nte[l, t].value
#             m.Bl[stage].nte[l, t].fix(value)   
#             value = m.Bl[stage].ntb[l, t].value
#             m.Bl[stage].ntb[l, t].fix(value)                

# upper_bound_obj = 0.0
# lopt = SolverFactory("cplex")
# lopt.options['mipgap'] = 0.005
# lopt.options['threads'] = 1
# ub_time = 0.0 
# a = time.time()
# for stage in m.stages:
#     results = lopt.solve(m.Bl[stage], tee=True)
#     upper_bound_obj += m.Bl[stage].obj.expr()
# b = time.time()
# ub_time = b - a 
# print("ub time")
# print(ub_time)

# print("benders results")
# print(opt.results)
# ub_problem = {"ub time":ub_time, "upper_bound_obj":upper_bound_obj}
# from util import *
# write_GTEP_results(m, outputfile, opt, readData_det, t_per_stage, opt.results, ub_problem)



