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

days = range(1, 366)
list_of_repr_days_per_scenario = list(range(1,len(days)+ 1))
selected_hours = []
i = 1
for day in days:
    selected_hours += list(range((day*24-24),(day*24)))
    i += 1

# ######################################################################################################################

# create scenarios and input data
nodes, n_stage, parent_node, children_node, prob, sc_nodes = create_scenario_tree(stages, scenarios, single_prob)
import pandas as pd 
L_NE_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/L_Northeast_2012.csv'), index_col=0, header=0).iloc[selected_hours, 1]
L_NE_1.columns = list_of_repr_days_per_scenario
L_W_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/L_West_2012.csv'), index_col=0, header=0).iloc[selected_hours, 1]
L_W_1.columns = list_of_repr_days_per_scenario
L_C_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/L_Coastal_2012.csv'), index_col=0, header=0).iloc[selected_hours, 1]
L_C_1.columns = list_of_repr_days_per_scenario
L_S_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/L_South_2012.csv'), index_col=0, header=0).iloc[selected_hours, 1]
L_S_1.columns = list_of_repr_days_per_scenario
L_PH_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/L_South_2012.csv'), index_col=0, header=0).iloc[selected_hours, 1].multiply(0)
L_PH_1.columns = list_of_repr_days_per_scenario


L_1 = {}
# growth_rate = 0.014
growth_rate_high = 0.014
growth_rate_medium = 0.014
growth_rate_low = 0.014
for t in range(1, len(n_stage)+1):
    d_idx = 0
    for d in list_of_repr_days_per_scenario:
        s_idx = 0
        for ss in range(24):
            s = ss + 1
            if t >= 15:
                L_1['Northeast', t, d, s] = L_NE_1.iat[s_idx+24*d_idx] * (1 + growth_rate_medium * (t-1))
                L_1['West', t, d, s] = L_W_1.iat[s_idx+24*d_idx] * (1 + growth_rate_low * (t-1))
                L_1['Coastal', t, d, s] = L_C_1.iat[s_idx+24*d_idx]* (1 + growth_rate_high * (t-1))
                L_1['South', t, d, s] = L_S_1.iat[s_idx+24*d_idx]* (1 + growth_rate_high * (t-1))
                L_1['Panhandle', t, d, s] = L_PH_1.iat[s_idx+24*d_idx]* (1 + growth_rate_low * (t-1))
            else:
                L_1['Northeast', t, d, s] = L_NE_1.iat[s_idx+24*d_idx] * (1 + growth_rate_medium * (t-1))
                L_1['West', t, d, s] = L_W_1.iat[s_idx+24*d_idx] * (1 + growth_rate_low * (t-1))
                L_1['Coastal', t, d, s] = L_C_1.iat[s_idx+24*d_idx]* (1 + growth_rate_high * (t-1))
                L_1['South', t, d, s] = L_S_1.iat[s_idx+24*d_idx]* (1 + growth_rate_high * (t-1))
                L_1['Panhandle', t, d, s] = L_PH_1.iat[s_idx+24*d_idx]* (1 + growth_rate_low * (t-1))                                 

            s_idx += 1
        d_idx += 1

L_max = {}
for t in range(1, len(n_stage)+1):
    L_max[t] = 0 
    for d in list_of_repr_days_per_scenario:
        s_idx = 0
        for ss in range(24):
            s = ss + 1
            L_max[t] =max(L_max[t],  L_1['Northeast', t, d, s] + L_1['West', t, d, s] + L_1['Coastal', t, d, s] + L_1['South', t, d, s] )
 

#select peak load 
L_total = L_NE_1 + L_W_1 + L_C_1 + L_S_1 + L_PH_1
print("peak load day is ", ceil((L_total.argmax()+1)/24))
#select peak ramp
L1 = L_total.to_numpy()[0:-1]
L2 = L_total.to_numpy()[1:]
print("peak ramp day is ", ceil(((L2-L1).argmax()+1)/24))



