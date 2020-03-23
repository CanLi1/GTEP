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
import deterministic.optBlocks_det as b
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
# filepath = os.path.join(curPath, 'data/GTEP_data_15years.db')
filepath = os.path.join(curPath, 'data/GTEPdata_2020_2039.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2024.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2029.db')

n_stages = 20  # number od stages in the scenario tree
stages = range(1, n_stages + 1)
scenarios = ['M']
single_prob = {'M': 1.0}

# time_periods = 10
time_periods = 20
set_time_periods = range(1, time_periods + 1)
# t_per_stage = {1:[1], 2:[2], 3:[3]}
# t_per_stage = {1: [1, 2], 2: [3, 4], 3: [5, 6], 4: [7, 8], 5: [9, 10]}
# t_per_stage = {1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}
# t_per_stage = {1: [1], 2: [2], 3: [3], 4: [4], 5: [5], 6: [6], 7: [7], 8: [8], 9: [9], 10: [10]}
# t_per_stage = {1: [1], 2: [2], 3: [3], 4: [4], 5: [5], 6: [6], 7: [7], 8: [8], 9: [9], 10: [10],
#                11: [11], 12: [12], 13: [13], 14: [14], 15: [15]}
t_per_stage = {1: [1], 2: [2], 3: [3], 4: [4], 5: [5], 6: [6], 7: [7], 8: [8], 9: [9], 10: [10],
               11: [11], 12: [12], 13: [13], 14: [14], 15: [15], 16:[16],17:[17], 18:[18], 19:[19], 20:[20]}

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


m.obj = Objective(expr=0, sense=minimize)

for stage in m.stages:
    m.Bl[stage].obj.deactivate()
    m.obj.expr += m.Bl[stage].obj.expr


# # solve relaxed model
a = TransformationFactory("core.relax_integrality")
a.apply_to(m)
# operating_integer_vars = ["u", "su", "sd"]
                                                 
# import time

lopt = SolverFactory("cplex")
b = m.Bl[1]
b.obj.activate()
lopt.solve(b)
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


# opt.set_instance(m)
# opt.set_benders_annotation()
# opt.set_benders_strategy(1)

# #set master variables 
investment_vars = ["ntb","nte","nte_prev","ngr_rn","nge_rn","ngr_th","nge_th","ngo_rn","ngb_rn","ngo_th","ngb_th","ngo_rn_prev","ngo_th_prev","nsr","nsb","nso","nso_prev", "alphafut", "RES_def"]
for v in b.component_objects(Var):
    if v.getname() in investment_vars:
        print("investment_vars")
        for index in v:            
            lb, ub = v[index].bounds
            v[index].setlb(lb)
            v[index].setub(ub)
lopt.solve(b)            
# # for stage in m.stages:
# #     for t in t_per_stage[stage]:
# #         # print('stage', stage, 't_prev', t_prev)
# #         for (rn, r) in m.rn_r:
# #             opt.set_master_variable(m.Bl[stage].ngo_rn[rn, r, t])
# #             opt.set_master_variable(m.Bl[stage].ngb_rn[rn, r, t])
# #             opt.set_master_variable(m.Bl[stage].nge_rn[rn, r, t])
# #             opt.set_master_variable(m.Bl[stage].ngr_rn[rn, r, t])
# #         for (th, r) in m.th_r:
# #             opt.set_master_variable(m.Bl[stage].ngo_th[th, r, t]  )
# #             opt.set_master_variable(m.Bl[stage].ngb_th[th, r, t]  )
# #             opt.set_master_variable(m.Bl[stage].nge_th[th, r, t]  )
# #             opt.set_master_variable(m.Bl[stage].ngr_th[th, r, t]  )            
# #         for (j, r) in j_r:
# #             opt.set_master_variable(m.Bl[stage].nso[j, r, t])
# #             opt.set_master_variable(m.Bl[stage].nsb[j, r, t])
# #             opt.set_master_variable(m.Bl[stage].nsr[j, r, t])

# #         for l in m.l_new:
# #             opt.set_master_variable(m.Bl[stage].nte[l, t])
# #             opt.set_master_variable(m.Bl[stage].ntb[l, t])
# #set subproblems
# operating_vars = ["theta", "P", "cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]
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
#     for t in t_per_stage[stage]:
#         # print('stage', stage, 't_prev', t_prev)
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
               

# upper_bound_obj = 0.0
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
# solar_capacity = []
# wind_capacity = []
# nuclear_capacity = []
# coal_capacity = []
# natural_gas_capacity = []
# solar_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
# wind_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
# nuclear_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
# coal_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
# natural_gas_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
# power_flow = []
# solar_energy_generated = []
# wind_energy_generated = []
# nuclear_energy_generated = []
# coal_energy_generated = []
# natural_gas_energy_generated = []
# total_energy_generated = []




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
#     coal_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.co) )
#     natural_gas_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.ng) )
#     nuclear_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.nu) )
#     solar_capacity.append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, r in m.i_r if (rn in m.pv or rn in m.csp)) )
#     wind_capacity.append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, r in m.i_r if rn in m.wi) )
#     for r in m.r:
#         coal_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for  th, rr in m.i_r if (rr==r and th in m.co) ))
#         natural_gas_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, rr in m.i_r if (rr==r and th in m.ng) ))
#         nuclear_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, rr in m.i_r if (rr==r  and th in m.nu) ))
#         solar_capacity_region[r].append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, rr in m.i_r if (rr == r and (rn in m.pv or rn in m.csp))) )
#         wind_capacity_region[r].append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, rr in m.i_r if( rr==r and rn in m.wi) ))
#     total_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for (i,r)
#      in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours))
#     coal_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for 
#         (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.co))
#     natural_gas_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for
#      (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.ng))
#     nuclear_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for 
#         (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.nu))
#     solar_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for
#      (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if (i in m.pv or i in m.csp)))
#     wind_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d] * pow(10,-6) for 
#         (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.wi ))
#     temp_power_flow = {}
#     for r in m.r:
#         temp_power_flow[r] = {}
#         for rr in m.r:
#             temp_power_flow[r][rr] = 0
#     for l in m.l:
#         for t in t_per_stage[stage]:
#             for d in m.d:
#                 for s in m.hours:
#                     er = m.l_er[l][1]
#                     sr = m.l_sr[l][1]
#                     if m.Bl[stage].P_flow[l,t,d,s].value > 0:
#                         temp_power_flow[sr][er] += m.Bl[stage].P_flow[l,t,d,s].value * m.n_d[d] * pow(10,-6)
#                     else:
#                         temp_power_flow[er][sr] -= m.Bl[stage].P_flow[l,t,d,s].value * m.n_d[d] * pow(10,-6)
#     # for r in m.r_Panhandle:
#     #     for t in t_per_stage[stage]:
#     #         for d in m.d:
#     #             for s in m.hours:  
#     #                 temp_power_flow['Panhandle'][r]  += m.Bl[stage].P_Panhandle[r,t,d,s].value * m.n_d[d] * pow(10,-6)
#     power_flow.append(temp_power_flow)

    



# # print("variable_operating_cost")
# # print(variable_operating_cost)
# # print(sum(variable_operating_cost))
# # print("fixed_operating_cost")
# # print(fixed_operating_cost)
# # print(sum(fixed_operating_cost))
# # print("startup_cost")
# # print(startup_cost)
# # print(sum(startup_cost))
# # print("thermal_generator_cost")
# # print(thermal_generator_cost)
# # print(sum(thermal_generator_cost))
# # print("extending_thermal_generator_cost")
# # print(extending_thermal_generator_cost)
# # print(sum(extending_thermal_generator_cost))
# # print("renewable_generator_cost")
# # print(renewable_generator_cost)
# # print(sum(renewable_generator_cost))
# # print("extending_renewable_generator_cost")
# # print(extending_renewable_generator_cost)
# # print(sum(extending_renewable_generator_cost))
# # print("storage_investment_cost")
# # print(storage_investment_cost)
# # print(sum(storage_investment_cost))
# # print("penalty_cost")
# # print(penalty_cost)
# # print(sum(penalty_cost))
# # print("renewable_capacity")
# # print(renewable_capacity)
# # print(sum(renewable_capacity))
# # print("thermal_capacity")
# # print(thermal_capacity)
# # print(sum(thermal_capacity))
# # print("total_capacity")
# # print(total_capacity)
# # print(sum(total_capacity))
# # print("transmission_line_cost")
# # print(transmission_line_cost)
# # print(sum(transmission_line_cost))

# import csv
# energy_region_dict ={"solar":solar_capacity_region,
# "nuc":nuclear_capacity_region, 
# "coal":coal_capacity_region,
# "natural gas": natural_gas_capacity_region,
# "wind":wind_capacity_region}
with open('results/cheaplines_medium_tx_CO2_lowgrowth.csv', 'w', newline='') as results_file:
            results_writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            results_writer.writerow(["ratio_N ", self.ratio_N , " ratio_M " , self.ratio_M])
            # results_writer.writerow(["best_UB_lo", self.best_UB_lo, "best_UB_up", self.best_UB_up])
            # results_writer.writerow(["best binary", self.best_binary])
            # results_writer.writerow(["is OA infeasible", self.is_OA_infeasible])
            # results_writer.writerow(["post_analysis_time", self.post_analysis_time])
#             fieldnames = ["Time", "variable_operating_cost",
#                         "fixed_operating_cost",
#                         "startup_cost",
#                         "thermal_generator_cost",
#                         "extending_thermal_generator_cost",
#                         "renewable_generator_cost",
#                         "extending_renewable_generator_cost",
#                         "storage_investment_cost",
#                         "penalty_cost",
#                         "renewable_capacity",
#                         "thermal_capacity",                        
#                         "transmission_line_cost",
#                         "coal_capacity",
#                         "natural_gas_capacity",
#                         "nuclear_capacity",
#                         "solar_capacity",
#                         "wind_capacity",
#                         "total_capacity",
#                         "power_flow",
#                         "solar_energy_generated",
#                         "wind_energy_generated",
#                         "nuclear_energy_generated",
#                         "coal_energy_generated",
#                         "natural_gas_energy_generated",
#                         "total_energy_generated"
#                         ]
#             for r in m.r:
#                 for gen in ["coal", "natural gas", "nuc", "solar", "wind"]:
#                     fieldnames.append(r+ " " + gen)
#             writer = csv.DictWriter(results_file, fieldnames=fieldnames)
#             writer.writeheader()
#             for i in range(len(m.stages)):
#                 new_row = {"Time":i + 1,
#                     "variable_operating_cost":variable_operating_cost[i],
#                     "fixed_operating_cost":fixed_operating_cost[i],
#                     "startup_cost":startup_cost[i],
#                     "thermal_generator_cost":thermal_generator_cost[i],
#                     "extending_thermal_generator_cost":extending_thermal_generator_cost[i],
#                     "renewable_generator_cost":renewable_generator_cost[i],
#                     "extending_renewable_generator_cost":extending_renewable_generator_cost[i],
#                     "storage_investment_cost":storage_investment_cost[i],
#                     "penalty_cost":penalty_cost[i],
#                     "renewable_capacity":renewable_capacity[i],
#                     "thermal_capacity":thermal_capacity[i],
#                     "total_capacity":total_capacity[i],
#                     "transmission_line_cost":transmission_line_cost[i],
#                     "coal_capacity":coal_capacity[i],
#                     "natural_gas_capacity":natural_gas_capacity[i],
#                     "nuclear_capacity":nuclear_capacity[i],
#                     "solar_capacity":solar_capacity[i],
#                     "wind_capacity":wind_capacity[i],
#                     "power_flow":power_flow[i],
#                     "solar_energy_generated":solar_energy_generated[i],
#                     "wind_energy_generated":wind_energy_generated[i],
#                     "nuclear_energy_generated":nuclear_energy_generated[i],
#                     "coal_energy_generated":coal_energy_generated[i],
#                     "natural_gas_energy_generated":natural_gas_energy_generated[i],
#                     "total_energy_generated":total_energy_generated[i]}
#                 for r in m.r:
#                     for gen in ["coal", "natural gas", "nuc", "solar", "wind"]:
#                         key = r+ " " + gen
#                         new_row[key] = energy_region_dict[gen][r][i]
#                 writer.writerow(new_row)
#             results_writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#             # for i in range(len(m.stages)):
#             #     results_writer.writerow([" "])
#             #     results_writer.writerow(["t=" + str(i+1), 'Northeast', 'West', 'Coastal', 'South', 'Panhandle'])
#             #     for r in m.r:
#             #         new_row = [r]
#             #         for rr in m.r:
#             #             new_row.append(power_flow[i][r][rr])
#             #         results_writer.writerow(new_row)
#             #get the transmission line expansion 
#             for stage in m.stages:                
#                 for l in m.l_new:
#                     if m.Bl[stage].ntb[l,stage].value > 0.1:
#                         temp_row = [stage, readData_det.tielines[l-1]["Near Area Name"], readData_det.tielines[l-1]["Far Area Name"]]
#                         results_writer.writerow(temp_row)
#                  #get the peak demand network structure in the last year  
#             last_stage = len(m.stages)                          
#             # m.L = Param(m.r, m.t, m.d, m.hours, default=0, initialize=readData_det.L_by_scenario[0], mutable=True) 
#             largest_d, largest_s =  0, 0
#             largest_load = 0.0
#             for r in m.r:
#                 for d in m.d:
#                     for s in m.hours:
#                         if m.L[r, last_stage,d,s].value > largest_load:
#                             largest_load = m.L[r, last_stage,d,s].value
#                             largest_d = d 
#                             largest_s = s 
#             #write down the load of each region 
#             results_writer.writerow([" at last year ",  d, s])
#             results_writer.writerow([" ", 'Northeast', 'West', 'Coastal', 'South', 'Panhandle'])
#             results_writer.writerow(["load ", m.L["Northeast", last_stage, largest_d, largest_s].value, 
#                 m.L["West", last_stage, largest_d, largest_s].value,m.L["Coastal", last_stage, largest_d, largest_s].value,
#                 m.L["South", last_stage, largest_d, largest_s].value,m.L["Panhandle", last_stage, largest_d, largest_s].value])
#             new_row = ["power generation"]
#             for r in m.r:
#                 new_row.append(sum(m.Bl[last_stage].P[i, r, last_stage, largest_d, largest_s].value for i,rr in m.i_r if rr==r))
#             results_writer.writerow(new_row)
#             new_row = ["power charged"]
#             for r in m.r:
#                 new_row.append(sum(m.Bl[last_stage].p_charged[j, r, last_stage, largest_d, largest_s].value for j in m.j)) 
#             results_writer.writerow(new_row)
#             new_row = ["power discharged"]    
#             for r in m.r:
#                 new_row.append(sum(m.Bl[last_stage].p_discharged[j, r, last_stage, largest_d, largest_s].value for j in m.j))     
#             results_writer.writerow(new_row)
#             new_row = ["transmission power "]
#             for r in m.r:
#                 temp_P = 0
#                 for l in m.l:
#                     er = m.l_er[l][1]
#                     sr = m.l_sr[l][1]
#                     if er == r:
#                         temp_P += m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value
#                     if sr == r:
#                         temp_P -= m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value
#                 new_row.append(temp_P)
#             results_writer.writerow(new_row)
#             new_row = ["curtailment "]
#             for r in m.r:
#                 new_row.append(m.Bl[last_stage].cu[r, last_stage, largest_d, largest_s].value)
#             results_writer.writerow(new_row)
#                #power transmission of each line 
#             results_writer.writerow([])
#             results_writer.writerow(["transmission at peak load "])
#             for l in m.l:
#                 if abs(m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value) > 0.1:
#                     results_writer.writerow([readData_det.tielines[l-1]["Near Area Name"], readData_det.tielines[l-1]["Far Area Name"], m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value ])
#             results_writer.writerow([])        
#             results_writer.writerow(["ub_time", ub_time, "cplex benders time", opt.results['Solver'][0]['Wallclock time']])
#             results_writer.writerow(["ub", upper_bound_obj, "lb", opt.results['Problem'][0]['Lower bound']])

