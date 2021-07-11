import time
import math
import random
from copy import deepcopy
import os.path
from pyomo.environ import *
import csv


from scenarioTree import create_scenario_tree
import deterministic.readData_single as readData_single
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
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2039.db')
filepath = os.path.join(curPath, 'data/GTEPdata_2020_2024.db')
# filepath = os.path.join(curPath, 'data/GTEPdata_2020_2029.db')

n_stages = 5 # number od stages in the scenario tree
formulation = "standard"


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
day = 1
nodes, n_stage, parent_node, children_node, prob, sc_nodes = create_scenario_tree(stages, scenarios, single_prob)
readData_single.read_data(filepath, curPath, stages, n_stage, t_per_stage, day)
sc_headers = list(sc_nodes.keys())
max_iter = 100


# create blocks
m = b.create_model(n_stages, time_periods, t_per_stage, max_iter, formulation,readData_single)
fieldnames = ["repnday", "solution", "obj", "time"]
lines = ["Coastal_South", "Coastal_Northeast", "South_Northeast", "South_West", "West_Northeast", "West_Panhandle", "Northeast_Panhandle"]      
for t in m.t:
    for line in lines:
        fieldnames.append(line + "[" + str(t) + "]")
        fieldnames.append("cost_" + line + "[" + str(t) + "]")
    for (rn, r) in m.rn_r:
        if rn in m.rnew:
            fieldnames.append("ngb_rn[" + rn + "," + r + "," + str(t) + "]")  
            fieldnames.append("cost_ngb_rn[" + rn + "," + r + "," + str(t) + "]")  
        fieldnames.append("nge_rn[" + rn + "," + r + "," + str(t) + "]")  
        fieldnames.append("cost_nge_rn[" + rn + "," + r + "," + str(t) + "]")  
    for (th,r) in m.th_r:
        if th in m.tnew:
            fieldnames.append("ngb_th[" + th + "," + r + "," + str(t) + "]")
            fieldnames.append("cost_ngb_th[" + th + "," + r + "," + str(t) + "]")
        fieldnames.append("nge_th[" + th + "," + r + "," + str(t) + "]")
        fieldnames.append("cost_nge_th[" + th + "," + r + "," + str(t) + "]")
    for j in m.j:
        for r in m.r:
            fieldnames.append("nsb["+j + ","+r+"," +  str(t) +"]")
            fieldnames.append("cost_nsb["+j + ","+r+"," +  str(t) +"]")


day_start = 1
day_end = 366
with open('repn_results/5yearsinvestment_NETL_no_reserve' + str(day_start) + "-" + str(day_end) + '.csv', 'w', newline='') as results_file:      
    writer = csv.DictWriter(results_file, fieldnames=fieldnames)    
    writer.writeheader()

    for day in range(day_start, day_end):               
        # create scenarios and input data
        nodes, n_stage, parent_node, children_node, prob, sc_nodes = create_scenario_tree(stages, scenarios, single_prob)
        readData_single.read_data(filepath, curPath, stages, n_stage, t_per_stage, day)
        sc_headers = list(sc_nodes.keys())
        max_iter = 100


        # create blocks
        m = b.create_model(n_stages, time_periods, t_per_stage, max_iter, formulation, readData_single)
        start_time = time.time()



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
                for j in m.j:
                    for r in m.r:
                        m.Bl[stage].link_equal3.add(expr=(m.Bl[stage].nso_prev[j, r] ==
                                                         m.Bl[stage-1].nso[j, r, t_per_stage[stage-1][-1]]))

                for l in m.l_new:
                    m.Bl[stage].link_equal4.add(expr=(m.Bl[stage].nte_prev[l] ==
                                                         m.Bl[stage-1].nte[l, t_per_stage[stage-1][-1]]))
        m.obj = Objective(expr=0, sense=minimize)

        for stage in m.stages:
            m.Bl[stage].obj.deactivate()
            m.obj.expr += m.Bl[stage].obj.expr

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
        # import time
        a = TransformationFactory("core.relax_integrality")
        a.apply_to(m)
        # for t in m.t:
        #   m.Bl[t].ntb.domain = Binary
        # opt = SolverFactory("cplex_persistent")
        opt = SolverFactory("cplex")
        opt.options['threads'] = 6
        opt.options['mipgap'] = 0.005
        opt.options['LPMethod'] = 4
        opt.options['solutiontype'] =2 
# 0 Automatic
# 1 Primal Simplex
# 2 Dual Simplex
# 3 Network Simplex
# 4 Barrier
# 5 Sifting
# 6 Concurrent      
        results = opt.solve(m, tee=True)
        # opt.set_instance(m)
        # opt.set_benders_annotation()
        # opt.set_benders_strategy(1)
        # opt._solver_model.parameters.mip.tolerances.mipgap.set(0.005)
        # opt._solver_model.parameters.threads.set(1)
        # opt._solver_model.parameters.timelimit.set(3600*5)

        # #set master variables 
        # investment_vars = ["ntb","nte","nte_prev","ngr_rn","nge_rn","ngr_th","nge_th","ngo_rn","ngb_rn","ngo_th","ngb_th","ngo_rn_prev","ngo_th_prev","nsr","nsb","nso","nso_prev", "alphafut", "RES_def"]
        # for v in m.component_objects(Var):
        #     if v.getname() in investment_vars:
        #         for index in v:
        #             opt.set_master_variable(v[index])

        # #set subproblems
        # operating_vars = []
        # if formulation == "standard":
        #   operating_vars = ["L_shed", "theta", "P", "cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]
        # elif formulation == "hull":
        #   operating_vars = ["L_shed", "theta", "P", "d_theta_1", "d_theta_2","cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]
        # elif formulation == "improved":
        #   operating_vars = ["L_shed", "theta", "P", "d_theta_plus", "d_theta_minus", "d_P_flow_plus", "d_P_flow_minus", "cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]  
        # map_d = {'fall':3, 'summer':2, 'spring':1, 'winter':4}
        # for v in m.component_objects(Var):
        #     if v.getname() in operating_vars:
        #         for index in v:
        #             t = index[-3]
        #             opt.set_subproblem_variable(v[index], t)


        # opt.solve(m, tee=True)
        # print(results)
        # print(results['Problem'][0]['Lower bound'], opt.results['Problem'][0]['Upper bound'])
        # print(results.Solver[0]['Wall time'])
        # print(opt.options['LPMethod'])
        #b.nso ngo_th ngo_rn
        #get investment variable values in solution pool


        #if we only include the optimization results of one year
        # fieldnames = ["repnday", "solution", "obj", "Coastal_South", "Coastal_Northeast", "South_Northeast", "South_West", "West_Northeast", "West_Panhandle", "Northeast_Panhandle" ]
        # for (rn, r) in m.rn_r:
        #   fieldnames.append("ngo_rn[" + rn + "," + r + "]")  
        # for (th,r) in m.th_r:
        #   fieldnames.append("ngo_th[" + th + "," + r + "]")
        # for j in m.j:
        #   for r in m.r:
        #       fieldnames.append("nso["+j + ","+r+"]")

        # with open('repn_results/firstyear.csv', 'w', newline='') as results_file:      
        #   writer = csv.DictWriter(results_file, fieldnames=fieldnames) 
        #   writer.writeheader()
        #   for soln in opt._solver_model.solution.pool.get_names():
        #       if m.Bl[1].obj.expr() * 1.01 > opt._solver_model.solution.pool.get_objective_value(soln):
        #           new_row = {"repnday":1, "solution":soln, "obj":opt._solver_model.solution.pool.get_objective_value(soln), "Coastal_South":0, "Coastal_Northeast":0, "South_Northeast":0, "South_West":0,
        #                   "West_Northeast":0, "West_Panhandle":0, "Northeast_Panhandle":0} 
        #           for l in m.l_new:
        #               value = opt._solver_model.solution.pool.get_values(soln, opt._pyomo_var_to_solver_var_map[m.Bl[1].nte[l,1]])
        #               key = readData_single.tielines[l-1]['Near Area Name'] + "_" + readData_single.tielines[l-1]['Far Area Name']
        #               new_row[key] += value 
        #           for (rn, r) in m.rn_r:
        #               value = opt._solver_model.solution.pool.get_values(soln, opt._pyomo_var_to_solver_var_map[m.Bl[1].ngo_rn[rn, r, 1]])
        #               key = "ngo_rn[" + rn + "," + r + "]"
        #               new_row[key] = value 
        #           for (th, r) in m.th_r:
        #               value = opt._solver_model.solution.pool.get_values(soln, opt._pyomo_var_to_solver_var_map[m.Bl[1].ngo_th[th, r, 1]])
        #               key = "ngo_th[" + th + "," + r + "]"
        #               new_row[key] = value    
        #           for j in m.j:
        #               for r in m.r:
        #                   value = opt._solver_model.solution.pool.get_values(soln, opt._pyomo_var_to_solver_var_map[m.Bl[1].nso[j, r, 1]])
        #                   key = "nso[" + j + "," + r + "]"
        #                   new_row[key] = value 
        #           writer.writerow(new_row)    



        # with open('repn_results/firstyear.csv', 'w', newline='') as results_file:      
        #   writer = csv.DictWriter(results_file, fieldnames=fieldnames) 
        #   writer.writeheader()
        #   for soln in opt._solver_model.solution.pool.get_names():
        #       if m.obj.expr() * 1.01 > opt._solver_model.solution.pool.get_objective_value(soln):
        #           new_row = {"repnday":1, "solution":soln, "obj":opt._solver_model.solution.pool.get_objective_value(soln)}
        #           for t

        #            in m.t: 
        #               for line in lines:
        #                   new_row[line + "[" + str(t) + "]"] = 0
        #               for l in m.l_new:
        #                   value = opt._solver_model.solution.pool.get_values(soln, opt._pyomo_var_to_solver_var_map[m.Bl[t].nte[l,t]])
        #                   key = readData_single.tielines[l-1]['Near Area Name'] + "_" + readData_single.tielines[l-1]['Far Area Name'] + "[" + str(t) + "]"
        #                   new_row[key] += value 
        #               for (rn, r) in m.rn_r:
        #                   value = opt._solver_model.solution.pool.get_values(soln, opt._pyomo_var_to_solver_var_map[m.Bl[t].ngo_rn[rn, r, t]])
        #                   key = "ngo_rn[" + rn + "," + r + "," +  str(t) +"]"
        #                   new_row[key] = value 
        #               for (th, r) in m.th_r:
        #                   value = opt._solver_model.solution.pool.get_values(soln, opt._pyomo_var_to_solver_var_map[m.Bl[t].ngo_th[th, r, t]])
        #                   key = "ngo_th[" + th + "," + r + "," +  str(t) + "]"
        #                   new_row[key] = value  
        #               for j in m.j:
        #                   for r in m.r:
        #                       value = opt._solver_model.solution.pool.get_values(soln, opt._pyomo_var_to_solver_var_map[m.Bl[t].nso[j, r, t]])
        #                       key = "nso[" + j + "," + r + "," +  str(t) + "]"
        #                       new_row[key] = value 
        #           writer.writerow(new_row)  


        new_row = {"repnday":day, "solution":1, "obj":m.obj.expr(), "time":results['Solver'][0]['Time']}
        for t in m.t: 
            #investment related variables 
            for line in lines:
                new_row[line + "[" + str(t) + "]"] = 0
                new_row["cost_" + line + "[" + str(t) + "]"] = 0
            for l in m.l_new:
                value = m.Bl[t].ntb[l,t].value
                key = readData_single.tielines[l-1]['Near Area Name'] + "_" + readData_single.tielines[l-1]['Far Area Name'] + "[" + str(t) + "]"
                new_row[key] += value 
                value = m.Bl[t].ntb[l,t].value * m.TIC[l,t] * m.if_[t]  * 10 ** (-6)
                key = "cost_" + readData_single.tielines[l-1]['Near Area Name'] + "_" + readData_single.tielines[l-1]['Far Area Name'] + "[" + str(t) + "]"
                new_row[key] += value 
            for (rn, r) in m.rn_r:
                if rn in m.rnew:
                    value = m.Bl[t].ngb_rn[rn, r, t].value 
                    key = "ngb_rn[" + rn + "," + r + "," +  str(t) +"]"
                    new_row[key] = value 
                    value = m.Bl[t].ngb_rn[rn, r, t].value * m.DIC[rn, t] * m.CCm[rn] * m.Qg_np[rn, r] * m.if_[t]  * 10 ** (-6)
                    key = "cost_ngb_rn[" + rn + "," + r + "," +  str(t) +"]"
                    new_row[key] = value 
                value = m.Bl[t].nge_rn[rn, r, t].value 
                key = "nge_rn[" + rn + "," + r + "," +  str(t) +"]"
                new_row[key] = value 
                value = m.Bl[t].nge_rn[rn, r, t].value  * m.DIC[rn, t] * m.LEC[rn] * m.Qg_np[rn, r] * m.if_[t]  * 10 ** (-6)
                key = "cost_nge_rn[" + rn + "," + r + "," +  str(t) +"]"
                new_row[key] = value 
            for (th, r) in m.th_r:
                if th in m.tnew:
                    value = m.Bl[t].ngb_th[th, r, t].value 
                    key = "ngb_th[" + th + "," + r + "," +  str(t) + "]"
                    new_row[key] = value  
                    value = m.Bl[t].ngb_th[th, r, t].value * m.DIC[th, t] * m.CCm[th] * m.Qg_np[th, r] * m.if_[t]  * 10 ** (-6)
                    key = "cost_ngb_th[" + th + "," + r + "," +  str(t) + "]"
                    new_row[key] = value                    
                value = m.Bl[t].nge_th[th, r, t].value 
                key = "nge_th[" + th + "," + r + "," +  str(t) + "]"
                new_row[key] = value  
                value = m.Bl[t].nge_th[th, r, t].value * m.DIC[th, t] * m.LEC[th] * m.Qg_np[th, r] * m.if_[t]  * 10 ** (-6)
                key = "cost_nge_th[" + th + "," + r + "," +  str(t) + "]"
                new_row[key] = value                    
            for j in m.j:
                for r in m.r:
                    value =m.Bl[t].nsb[j, r, t].value 
                    key = "nsb[" + j + "," + r + "," +  str(t) + "]"
                    new_row[key] = value 
                    value = m.Bl[t].nsb[j, r, t].value * m.storage_inv_cost[j, t] * m.max_storage_cap[j] * m.if_[t]  * 10 ** (-6)
                    key = "cost_nsb[" + j + "," + r + "," +  str(t) + "]"
                    new_row[key] = value 
        writer.writerow(new_row)  


