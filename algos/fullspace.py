__author__ = "Can Li"


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


# ######################################################################################################################
# USER-DEFINED PARAMS

# Define case-study

filepath = "../data/test.db"
outputfile = "15days_5years_mediumtax.csv"
n_stages = 5  # number od stages in the scenario tree
formulation = "hull"


t_per_stage = {}
for i in range(1, n_stages+1):
  t_per_stage[i] = [i]


InvestData.read_data(filepath, n_stages)
days = [1,2,3]
weights = [100, 100, 165]
OperationalData.read_representative_days(n_stages, days, weights)
OperationalData.read_strategic_uncertainty(n_stages)

m = b.create_model(n_stages, t_per_stage, formulation, InvestData, OperationalData)
# # list of thermal generators:
# th_generators = ['coal-st-old1', 'coal-igcc-new', 'coal-igcc-ccs-new', 'ng-ct-old', 'ng-cc-old', 'ng-st-old',
#                  'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new']
# # 'nuc-st-old', 'nuc-st-new'

# # Shared data among processes
# ngo_rn_par_k = {}
# ngo_th_par_k = {}
# nso_par_k = {}
# nsb_par_k = {}
# nte_par_k = {}
# cost_forward = {}
# cost_scenario_forward = {}
# mltp_o_rn = {}
# mltp_o_th = {}
# mltp_so = {}
# mltp_te = {}
# cost_backward = {}
# if_converged = {}

# # Map stage by time_period
# stage_per_t = {t: k for k, v in t_per_stage.items() for t in v}


# # print(stage_per_t)

# # create blocks

# start_time = time.time()



# # # converting sets to lists:
rn_r = list(m.rn_r)
th_r = list(m.th_r)
j_r = [(j, r) for j in m.j for r in m.r]
l_new = list(m.l_new)


# # Add equality constraints (solve the full space)
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
a = TransformationFactory("core.relax_integrality")
a.apply_to(m)
opt = SolverFactory("cplex")
opt.options['mipgap'] = 0.001
opt.options['TimeLimit'] = 3600
opt.options['threads'] = 1
opt.options['LPMethod'] = 4
opt.options['solutiontype'] =2 
# # opt.options['LPMethod'] = 1
results  = opt.solve(m, tee=True)

# from util import * 
# #write results
# write_GTEP_results(m, outputfile, opt, readData_det, t_per_stage, results)
# # print(results)
# # print(results['Problem'][0]['Lower bound'], opt.results['Problem'][0]['Upper bound'])
# # print(results.Solver[0]['Wall time'])
# # # print(opt.options['LPMethod'])

# # #==============fix the investment decisions and evaluate them ========================
# # #create a new model with a single representative day per year 
# import deterministic.readData_single as readData_single
# readData_single.read_data(filepath, curPath, stages, n_stage, t_per_stage, 1)
# new_model = b.create_model(n_stages, time_periods, t_per_stage, max_iter, formulation, readData_single)
# a = TransformationFactory("core.relax_integrality")
# a.apply_to(new_model)
# new_model = fix_investment(m, new_model)
# investment_cost = 0.0
# # for i in m.stages:
# #   investment_cost += m.Bl[i].total_investment_cost.expr()
# # total_operating_cost = 0.0
# # for day in range(1, 3):
# #   total_operating_cost += eval_investment_single_day(new_model, day, n_stages) 
# import pymp
# NumProcesses =6
# operating_cost = pymp.shared.dict()
# with pymp.Parallel(NumProcesses) as p:
#   for day in p.range(1, 3):
#     operating_cost[day] = eval_investment_single_day(new_model, day, n_stages, readData_det, t_per_stage) 

# write_repn_results(operating_cost, outputfile)     



