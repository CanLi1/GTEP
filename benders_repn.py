__author__ = "Can Li"
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


from scenarioTree import create_scenario_tree
import deterministic.readData_days as readData_det
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
# filepath = os.path.join(curPath, 'data/GTEP_data_15years.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2039.db')
filepath = os.path.join(curPath, 'data/GTEPdata_2020_2024.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2029.db')

n_stages = 5  # number od stages in the scenario tree
formulation = "improved"
outputfile = "input_15days_5years_mediumtax.csv"
# num_days =4
# print(formulation, outputfile, num_days)
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

#cluster 
from cluster import *
result = run_cluster(data=load_input_data(), method="kmedoid_exact", n_clusters=15)
readData_det.read_data(filepath, curPath, stages, n_stage, t_per_stage, result['medoids'], result['weights'])
sc_headers = list(sc_nodes.keys())


# create blocks
m = b.create_model(n_stages, time_periods, t_per_stage, max_iter, formulation, readData_det)
start_time = time.time()



# converting sets to lists:
rn_r = list(m.rn_r)
th_r = list(m.th_r)
j_r = [(j, r) for j in m.j for r in m.r]
l_new = list(m.l_new)

# request the dual variables for all (locally) defined blocks
for bloc in m.Bl.values():
    bloc.dual = Suffix(direction=Suffix.IMPORT)

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
# opt = SolverFactory("cplex")
# opt.options['mipgap'] = 0.001
# opt.options['TimeLimit'] = 36000
# opt.solve(m, tee=True)
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
 
opt.options['threads'] = 6
opt.options['timelimit'] = 36000
opt.set_instance(m)
opt.set_benders_annotation()
opt.set_benders_strategy(1)
opt.set_mip_rel_gap(0.005)
opt._solver_model.parameters.emphasis.numerical.set(1)
opt._solver_model.parameters.preprocessing.repeatpresolve.set(0)
#set master variables 
investment_vars = ["ntb","nte","nte_prev","ngr_rn","nge_rn","ngr_th","nge_th","ngo_rn","ngb_rn","ngo_th","ngb_th","ngo_rn_prev","ngo_th_prev","nsr","nsb","nso","nso_prev", "alphafut", "RES_def"]
for v in m.component_objects(Var):
    if v.getname() in investment_vars:
        for index in v:
            opt.set_master_variable(v[index])

#set subproblems
operating_vars = []
if formulation == "standard":
  operating_vars = ["theta", "P", "cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]
elif formulation == "hull":
  operating_vars = ["theta", "P", "d_theta_1", "d_theta_2","cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]
elif formulation == "improved":
  operating_vars = ["theta", "P", "d_theta_plus", "d_theta_minus", "d_P_flow_plus", "d_P_flow_minus", "cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]  
map_d = {'fall':3, 'summer':2, 'spring':1, 'winter':4}
for v in m.component_objects(Var):
    if v.getname() in operating_vars:
        for index in v:
            t = index[-3]
            opt.set_subproblem_variable(v[index], t)


results = opt.solve(m, tee=True)

from util import * 
#write results
write_GTEP_results(m, outputfile, opt, readData_det, t_per_stage, results)
# #==============fix the investment decisions and evaluate them ========================
# #create a new model with a single representative day per year 
import deterministic.readData_single as readData_single
readData_single.read_data(filepath, curPath, stages, n_stage, t_per_stage, 1)
new_model = b.create_model(n_stages, time_periods, t_per_stage, max_iter, formulation, readData_single)
a = TransformationFactory("core.relax_integrality")
a.apply_to(new_model)
new_model = fix_investment(m, new_model)
investment_cost = 0.0
for i in m.stages:
  investment_cost += m.Bl[i].total_investment_cost.expr()
# total_operating_cost = 0.0
# for day in range(1, 3):
#   total_operating_cost += eval_investment_single_day(new_model, day, n_stages) 
import pymp
NumProcesses =6
operating_cost = pymp.shared.dict()
with pymp.Parallel(NumProcesses) as p:
  for day in p.range(1, 366):
    operating_cost[day] = eval_investment_single_day(new_model, day, n_stages, readData_det, t_per_stage) 

write_repn_results(operating_cost, outputfile)   


