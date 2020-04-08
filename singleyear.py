import time
import math
import random
from copy import deepcopy
import os.path
from pyomo.environ import *
import csv


from scenarioTree import create_scenario_tree
import deterministic.readData_det as readData_det
import deterministic.gtep_optBlocks_det as b
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
formulation = "improved"

num_days = 4
print(formulation, num_days)
stages = range(1, n_stages + 1)
scenarios = ['M']
single_prob = {'M': 1.0}

# time_periods = 10
time_periods = n_stages
set_time_periods = range(1, time_periods + 1)
t_per_stage = {}
for i in range(1, n_stages+1):
  t_per_stage[i] = [i]



# ######################################################################################################################

# create scenarios and input data
nodes, n_stage, parent_node, children_node, prob, sc_nodes = create_scenario_tree(stages, scenarios, single_prob)
readData_det.read_data(filepath, curPath, stages, n_stage, t_per_stage, num_days)
sc_headers = list(sc_nodes.keys())
max_iter = 100


# create blocks
m = b.create_model(n_stages, time_periods, t_per_stage, max_iter, formulation)
start_time = time.time()



# Add equality constraints (solve the full space)


# # solve relaxed model
# a = TransformationFactory("core.relax_integrality")
# a.apply_to(m)
opt = SolverFactory("cplex_persistent")
# opt.options['mipgap'] = 0.001
# opt.options['TimeLimit'] = 36000
# opt.options['threads'] = 1
# # opt.options['LPMethod'] = 1
opt.set_instance(m)
results=opt.solve(m, tee=True)
# print(results)
# print(results['Problem'][0]['Lower bound'], opt.results['Problem'][0]['Upper bound'])
# print(results.Solver[0]['Wall time'])
# print(opt.options['LPMethod'])


