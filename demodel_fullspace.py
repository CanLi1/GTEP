__author__ = "Can Li"

import time
import math
import random
from copy import deepcopy
import os.path
from pyomo.environ import *
import csv
import copy 
from util import *
from scenarioTree import create_scenario_tree
import deterministic.readData_det as readData_det
import endogenous.endo_gtep_optBlocks_det as b
import  endogenous.gtep_optBlocks_det as sub
from endogenous.util import * 
import time


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

start_time = time.time()

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

# a = TransformationFactory("core.relax_integrality")
# a.apply_to(m)
# opt = SolverFactory("cplex")
# opt.options['LPMethod'] = 4
# opt.options['solutiontype'] =2 
# opt.options['mipgap'] = 0.001
# opt.options['TimeLimit'] = 36000
# opt.options['threads'] = 6
# # opt.solve(m.scenario_block[1], )
# for s in range(1, 4):
#     opt.solve(m.scenario_block[s], tee=True)

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
                if t == 1:
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
        m.scenario_block[s2].link_equal3.add( sum(m.scenario_block[s2].ngb_th[s2, th, r, tt] for (th,r) in m.th_r for tt in m.t if (tt <= t and th == "coal-first-new") )  <= 10*t * (1-m.Y[s1,s2,t])  )
        m.scenario_block[s2].link_equal3.add( sum(m.scenario_block[s2].ngb_th[s2, th, r, tt] for (th,r) in m.th_r for tt in m.t if (tt <= t and th == "coal-first-new") ) >= (1-m.Y[s1,s2,t])  )

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
opt.options['TimeLimit'] = 36000
opt.options['threads'] = 6
lp_results = opt.solve(m, tee=True)
time_distinguished = n_stages + 1
tol = 1e-3 
#find when the scenarios pairs can be distinguished 
#we assume that if the value of coal-first-plant> 1e-5 then it is implemented 
for pair in scenario_pair:
    time_distinguished
    for t in m.t:
        s1 = pair[0]
        s2 = pair[1]
        if sum(m.scenario_block[s1].ngb_th[s1, "coal-first-new", r, t].value + m.scenario_block[s2].ngb_th[s2, "coal-first-new", r, t].value for r in m.r) > tol:
            if t < time_distinguished:
                time_distinguished = t 
            break 



#apply a heuristic to find the optimal investment decisions 
#and solve the deterministic model for each scenario to obtain a feasible solution
time_periods = n_stages
t_per_stage = {}
for i in range(1, n_stages+1):
    t_per_stage[i] = [i]
max_iter = 1
scenario_time_blocks = {}
for w in range(1, num_scenario+1):      
    time_blocks = sub.create_model(n_stages, time_periods, t_per_stage, max_iter, formulation, readData_det)
    for i in m.i:
        for t in m.t:
            if i == 'coal-first-new':
                time_blocks.DIC[i, t] = readData_det.DIC[i,t] * ratio[w-1]  
    scenario_time_blocks[w] = time_blocks

mipopt = SolverFactory("cplex")
mipopt.options['TimeLimit'] = 36000
mipopt.options['threads'] = 6
mipopt.options['mipgap'] = 0.001

def fix_investment_and_solve(m, w, t, scenario_time_blocks, opt):
    time_blocks = scenario_time_blocks[w]
    for r_r in range(7):
        num_existing_lines = sum(m.scenario_block[w].nte[w,l,t].value for l in range(r_r*10+1, r_r*10+11))
        for l in range(10): 
            if l < round(num_existing_lines):
                time_blocks.Bl[t].nte[r_r*10+1+l,t].setlb(1)
    #fix generation related constraints 
    for (rn, r) in m.rn_r:
        lb = m.scenario_block[w].ngo_rn[w,rn,r,t].value if m.scenario_block[w].ngo_rn[w,rn,r,t].value > 1e-3 else 0
        time_blocks.Bl[t].ngo_rn[rn, r, t].setlb(lb)
        # time_blocks.Bl[t].ngo_rn[rn, r, t].setub(min(time_blocks.Bl[t].ngo_rn[rn, r, t].ub, lb + 1))
    for (th, r) in m.th_r:
        lb = round(m.scenario_block[w].ngo_th[w,th,r,t].value)
        time_blocks.Bl[t].ngo_th[th, r, t].setlb(lb)
        # time_blocks.Bl[t].ngo_th[th, r, t].setub(min(time_blocks.Bl[t].ngo_th[th, r, t].ub , lb+1))
    #we need to set at least one coal first plant to 1 at time_distinguished
    if t == time_distinguished:
        max_value = 0 
        max_region = 0 
        for r in m.r:
            if m.scenario_block[w].ngo_th[w,"coal-first-new",r,t].value > max_value:
                max_value =  m.scenario_block[w].ngo_th[w,th,r,t].value 
                max_region = r 
        if round(max_value) < 1:
            time_blocks.Bl[t].ngo_th["coal-first-new", r, t].setlb(1)
    for j in m.j:
        for r in m.r:
            lb = m.scenario_block[w].nso[w,j,r,t].value if m.scenario_block[w].nso[w,j,r,t].value > 1e-3 else 0
            time_blocks.Bl[t].nso[j,r,t].setlb(lb)
            # time_blocks.Bl[t].nso[j,r,t].setub(lb+1)
    results = opt.solve(time_blocks.Bl[t], tee=True)
    #set the variables for the next stage 
    if t < n_stages:
        set_next_stage_vars(time_blocks, t)

def set_next_stage_vars(time_blocks, t):       
    for l in m.l_new:
        time_blocks.Bl[t+1].nte_prev[l].fix(time_blocks.Bl[t].nte[l,t].value)
    for (rn, r) in m.rn_r:
        time_blocks.Bl[t+1].ngo_rn_prev[rn, r].fix(time_blocks.Bl[t].ngo_rn[rn, r, t].value)
    for (th, r) in m.th_r:
        time_blocks.Bl[t+1].ngo_th_prev[th, r].fix(time_blocks.Bl[t].ngo_th[th, r, t].value)
    for j in m.j:
        for r in m.r:
            time_blocks.Bl[t+1].nso_prev[j,r].fix(time_blocks.Bl[t].nso[j, r, t].value)



def copy_investment_vars(w1, w2, t):
    for v in scenario_time_blocks[w1].Bl[t].component_objects(Var):
        if v.getname() in investment_vars:
            new_var = getattr(scenario_time_blocks[w2].Bl[t], v.getname())
            for index in v:  
                if not v[index].stale:             
                    new_var[index].fix(v[index].value)
    if t < n_stages:
        set_next_stage_vars(scenario_time_blocks[w2], t)

def copy_operating_vars(w1, w2, t):
    for v in scenario_time_blocks[w1].Bl[t].component_objects(Var):
        if v.getname() in operating_vars:
            new_var = getattr(scenario_time_blocks[w2].Bl[t], v.getname())
            for index in v:               
                new_var[index].fix(v[index].value)

heuristic_wall_time = time.time()

#fix to to scenario 1 when t<= time_distinguished
if time_distinguished > n_stages:
    for t in range(1, n_stages+1):
        fix_investment_and_solve(m, 1, t, scenario_time_blocks, mipopt)
        for w in range(2, num_scenario+1):
            copy_investment_vars(1, w, t)
            copy_operating_vars(1, w, t)
else:
    for t in range(1, time_distinguished+1):
        fix_investment_and_solve(m, 1, t, scenario_time_blocks, mipopt)
        for w in range(2, num_scenario+1):
            copy_investment_vars(1, w, t)
            if t < time_distinguished:
                copy_operating_vars(1, w, t)
            else:
                mipopt.solve(scenario_time_blocks[w].Bl[t], tee=True)
    #solve each scenario separately for t> time_distinguished
    if time_distinguished < n_stages:
        for t in range(time_distinguished+1, n_stages+1):
            for w in range(1, num_scenario+1):
                fix_investment_and_solve(m, w, t, scenario_time_blocks, mipopt)

heuristic_wall_time = time.time() - heuristic_wall_time 
fieldnames = ["scenario", "obj"]
lines = ["Coastal_South", "Coastal_Northeast", "South_Northeast", "South_West", "West_Northeast", "West_Panhandle", "Northeast_Panhandle"]      
for t in m.t:
    for line in lines:
        fieldnames.append(line + "[" + str(t) + "]")
    for (rn, r) in m.rn_r:
        fieldnames.append("ngo_rn[" + rn + "," + r + "," + str(t) + "]")  
    for (th,r) in m.th_r:
        fieldnames.append("ngo_th[" + th + "," + r + "," + str(t) + "]")
    for j in m.j:
        for r in m.r:
            fieldnames.append("nso["+j + ","+r+"," +  str(t) +"]")




          
with open(outputfile, 'w', newline='') as results_file:      
    writer = csv.DictWriter(results_file, fieldnames=fieldnames)    
    writer.writeheader()
    heuristic_solve_time = 0.0 
    heuristic_obj = 0.0
    for w in range(1, num_scenario+1):
        # for t in m.t:
        #     #fix transmission related variables for each region pair r_r
        #     for r_r in range(7):
        #         num_existing_lines = sum(m.scenario_block[w].nte[w,l,t].value for l in range(r_r*10+1, r_r*10+11))
        #         for l in range(10): 
        #             if l < round(num_existing_lines):
        #                 time_blocks.Bl[t].nte[r_r*10+1+l,t].fix(1)
        #                 if t < n_stages: 
        #                     time_blocks.Bl[t+1].nte_prev[r_r*10+1+l].fix(1)
        #             else:
        #                 time_blocks.Bl[t].nte[r_r*10+1+l,t].fix(0)
        #                 if t < n_stages: 
        #                     time_blocks.Bl[t+1].nte_prev[r_r*10+1+l].fix(0)
        #     #fix generation related constraints 
        #     for (rn, r) in m.rn_r:
        #         time_blocks.Bl[t].ngo_rn[rn, r, t].fix(m.scenario_block[w].ngo_rn[w,rn,r,t].value if m.scenario_block[w].ngo_rn[w,rn,r,t].value > 1e-3 else 0)
        #         if t < n_stages:
        #             time_blocks.Bl[t+1].ngo_rn_prev[rn, r].fix(m.scenario_block[w].ngo_rn[w,rn,r,t].value if m.scenario_block[w].ngo_rn[w,rn,r,t].value > 1e-3 else 0)
        #     for (th, r) in m.th_r:
        #         time_blocks.Bl[t].ngo_th[th, r, t].fix(round(m.scenario_block[w].ngo_th[w,th,r,t].value))
        #         if t < n_stages:
        #             time_blocks.Bl[t+1].ngo_th_prev[th,r].fix(round(m.scenario_block[w].ngo_th[w,th,r,t].value))
        #     for j in m.j:
        #         for r in m.r:
        #             time_blocks.Bl[t].nso[j,r,t].fix(m.scenario_block[w].nso[w,j,r,t].value if m.scenario_block[w].nso[w,j,r,t].value > 1e-3 else 0)
        #             if t < n_stages:
        #                 time_blocks.Bl[t+1].nso_prev[j,r].fix(m.scenario_block[w].nso[w,j,r,t].value if m.scenario_block[w].nso[w,j,r,t].value > 1e-3 else 0)
        #     results = mipopt.solve(time_blocks.Bl[t], tee=True)#, keepfiles=True)
        #     if 'Time' in results['Solver'][0]:                
        #         heuristic_solve_time += results['Solver'][0]['Time']
        time_blocks = scenario_time_blocks[w]
        #write objective and results
        new_row = {"scenario":w,  "obj":sum(time_blocks.Bl[t].obj.expr() for t in m.t)}
        heuristic_obj += sum(time_blocks.Bl[t].obj.expr() for t in m.t) * m.probability[w].value  
        for t in time_blocks.t: 
            for line in lines:
                new_row[line + "[" + str(t) + "]"] = 0
            for l in time_blocks.l_new:
                value = time_blocks.Bl[t].nte[l,t].value
                key = readData_det.tielines[l-1]['Near Area Name'] + "_" + readData_det.tielines[l-1]['Far Area Name'] + "[" + str(t) + "]"
                new_row[key] += value 
            for (rn, r) in time_blocks.rn_r:
                value = time_blocks.Bl[t].ngo_rn[rn, r, t].value 
                key = "ngo_rn[" + rn + "," + r + "," +  str(t) +"]"
                new_row[key] = value 
            for (th, r) in time_blocks.th_r:
                value = time_blocks.Bl[t].ngo_th[th, r, t].value 
                key = "ngo_th[" + th + "," + r + "," +  str(t) + "]"
                new_row[key] = value  
            for j in time_blocks.j:
                for r in time_blocks.r:
                    value =time_blocks.Bl[t].nso[j, r, t].value 
                    key = "nso[" + j + "," + r + "," +  str(t) + "]"
                    new_row[key] = value 
        writer.writerow(new_row)  
        write_GTEP_results(time_blocks, outputfile.split(".")[0]+"_w" + str(w) + ".csv", opt, readData_det, t_per_stage)
    results_writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)        
    results_writer.writerow(["LP relaxation obj", m.obj.expr()])
    results_writer.writerow(["heuristic obj", heuristic_obj])
    results_writer.writerow(["gap", (heuristic_obj-m.obj.expr())/ heuristic_obj])
    results_writer.writerow(["LP relaxation solve time", lp_results['Solver'][0]['Time']])
    results_writer.writerow(["heuristic_solve_time", heuristic_wall_time])
    results_writer.writerow(["total wall time", time.time()-start_time])




            







