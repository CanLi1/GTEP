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
import deterministic.readData_means as readData_det
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
method = "input"
# extreme_day_method = "load_shedding_cost"
extreme_day_method = "highest_cost_infeasible"
load_shedding = True
if method == "cost":
    outputfile = 'repn_results/' +  method + "_15days_5years_mediumtax_no_reserve_LP.csv"
    data, cluster_obj = load_cost_data(n_stages)
    result = run_cluster(data=data, method="kmedoid_exact", n_clusters=15)
    initial_cluster_result = result
elif method == "input":
    outputfile ='repn_results/' +  method + "_5days_5years_picksoln_mediumtax_no_reserve.csv"
    data= load_input_data()
    initial_cluster_result = run_cluster(data=data, method="kmeans_exact", n_clusters=5)

readData_det.read_data(filepath, curPath, stages, n_stage, t_per_stage, initial_cluster_result["labels"], 5)
















