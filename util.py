# author: Can Li 
#utils for representative days selection
import numpy as np 
from pyomo.environ import *
import pandas as pd
import csv

#pick solution from solution pool
def pick_soln(opt):
    best_thermal_capacity = 0 
    best_soln = 0
    m = opt._pyomo_model
    print("number of solutions in solution pool", len(opt._solver_model.solution.pool.get_names()))
    for soln in opt._solver_model.solution.pool.get_names():
        if opt.results['Problem'][0]['Upper bound'] * 1.01 < opt._solver_model.solution.pool.get_objective_value(soln):
            continue 
        print(soln)
        def get_var_value(var, opt=opt, soln=soln):
            return opt._solver_model.solution.pool.get_values(soln, opt._pyomo_var_to_solver_var_map[var])
        temp_thermal_capacity = sum(sum(m.Qg_np[th, r]* get_var_value(m.Bl[t].ngo_th[th, r, t]) for th, r in m.i_r if th in m.th) for t in m.stages)
        if temp_thermal_capacity > best_thermal_capacity:
            best_thermal_capacity = temp_thermal_capacity
            best_soln = soln
    #fix the variables in m to the values in best_soln
    for i in m.stages:
        for v1 in m.Bl[i].component_objects(Var):
            for index in v1:
                if v1[index].value != None:
                    new_value = opt._solver_model.solution.pool.get_values(best_soln, opt._pyomo_var_to_solver_var_map[v1[index]])
                    v1[index].fix(new_value)


#fix investment decisions
def fix_investment(ref_model, new_model):
    investment_vars = ["ntb","nte","nte_prev","ngr_rn","nge_rn","ngr_th","nge_th","ngo_rn","ngb_rn","ngo_th","ngb_th","ngo_rn_prev","ngo_th_prev","nsr","nsb","nso","nso_prev", "RES_def"]	
    for i in ref_model.stages:
        for v1 in ref_model.Bl[i].component_objects(Var):
            for v2 in new_model.Bl[i].component_objects(Var):
                if v1.getname() in investment_vars and v2.getname() in investment_vars and v1.getname() == v2.getname():
                    for index in v1:
                        if v1[index].value != None:
                            v2[index].fix(v1[index].value)
    return new_model

def eval_investment_single_day(new_model, day, n_stages, readData_det, t_per_stage):
    new_model.n_d._initialize_from({1:365})
    list_of_repr_days_per_scenario = list(range(1,(1+1)))
    L_NE_1 = pd.read_csv('NSRDB_wind/for_cluster/L_Northeast_2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    L_NE_1.columns = list_of_repr_days_per_scenario
    L_W_1 = pd.read_csv('NSRDB_wind/for_cluster/L_West_2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    L_W_1.columns = list_of_repr_days_per_scenario
    L_C_1 = pd.read_csv('NSRDB_wind/for_cluster/L_Coastal_2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    L_C_1.columns = list_of_repr_days_per_scenario
    L_S_1 = pd.read_csv('NSRDB_wind/for_cluster/L_South_2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    L_S_1.columns = list_of_repr_days_per_scenario
    L_PH_1 = pd.read_csv('NSRDB_wind/for_cluster/L_South_2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1].multiply(0)
    L_PH_1.columns = list_of_repr_days_per_scenario


    L_1 = {}
    # growth_rate = 0.014
    growth_rate_high = 0.014
    growth_rate_medium = 0.014
    growth_rate_low = 0.014
    for t in range(1, n_stages+1):
        d_idx = 0
        for d in list_of_repr_days_per_scenario:
            s_idx = 0
            for ss in range(24):
                s = ss + 1
                if t >= 15:
                    L_1['Northeast', t, d, s] = L_NE_1.iat[s_idx] * (1 + growth_rate_medium * (t-1))
                    L_1['West', t, d, s] = L_W_1.iat[s_idx] * (1 + growth_rate_low * (t-1))
                    L_1['Coastal', t, d, s] = L_C_1.iat[s_idx]* (1 + growth_rate_high * (t-1))
                    L_1['South', t, d, s] = L_S_1.iat[s_idx]* (1 + growth_rate_high * (t-1))
                    L_1['Panhandle', t, d, s] = L_PH_1.iat[s_idx]* (1 + growth_rate_low * (t-1))
                else:
                    L_1['Northeast', t, d, s] = L_NE_1.iat[s_idx] * (1 + growth_rate_medium * (t-1))
                    L_1['West', t, d, s] = L_W_1.iat[s_idx] * (1 + growth_rate_low * (t-1))
                    L_1['Coastal', t, d, s] = L_C_1.iat[s_idx]* (1 + growth_rate_high * (t-1))
                    L_1['South', t, d, s] = L_S_1.iat[s_idx]* (1 + growth_rate_high * (t-1))
                    L_1['Panhandle', t, d, s] = L_PH_1.iat[s_idx]* (1 + growth_rate_low * (t-1))                                 

                s_idx += 1
            d_idx += 1

                           

    L_by_scenario = [L_1]
    # print(L_by_scenario)
    globals()["L_by_scenario"] = L_by_scenario
    L_by_scenario = [L_1]
    # print(L_by_scenario)
    globals()["L_by_scenario"] = L_by_scenario

    # ############ CAPACITY FACTOR ############
    # -> solar CSP
    CF_CSP_NE_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Northeast_CSP2012.csv', index_col=0, header=0
                              ).iloc[(day*24-24):(day*24), 1]
    CF_CSP_NE_1.columns = list_of_repr_days_per_scenario
    CF_CSP_W_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_West_CSP2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_CSP_W_1.columns = list_of_repr_days_per_scenario
    CF_CSP_C_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Coastal_CSP2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_CSP_C_1.columns = list_of_repr_days_per_scenario
    CF_CSP_S_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_South_CSP2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_CSP_S_1.columns = list_of_repr_days_per_scenario
    CF_CSP_PH_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Panhandle_CSP2012.csv', index_col=0, header=0
                              ).iloc[(day*24-24):(day*24), 1]
    CF_CSP_PH_1.columns = list_of_repr_days_per_scenario

    # -> solar PVSAT
    CF_PV_NE_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Northeast_PV2012.csv', index_col=0, header=0
                             ).iloc[(day*24-24):(day*24), 1]
    CF_PV_NE_1.columns = list_of_repr_days_per_scenario
    CF_PV_W_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_West_PV2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_PV_W_1.columns = list_of_repr_days_per_scenario
    CF_PV_C_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Coastal_PV2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_PV_C_1.columns = list_of_repr_days_per_scenario
    CF_PV_S_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_South_PV2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_PV_S_1.columns = list_of_repr_days_per_scenario
    CF_PV_PH_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Panhandle_PV2012.csv', index_col=0, header=0
                             ).iloc[(day*24-24):(day*24), 1]
    CF_PV_PH_1.columns = list_of_repr_days_per_scenario

    # -> wind (old turbines)
    CF_wind_NE_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Northeast_wind2012.csv', index_col=0, header=0
                               ).iloc[(day*24-24):(day*24), 1]
    CF_wind_NE_1.columns = list_of_repr_days_per_scenario
    CF_wind_W_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_West_wind2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_wind_W_1.columns = list_of_repr_days_per_scenario
    CF_wind_C_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Coastal_wind2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_wind_C_1.columns = list_of_repr_days_per_scenario
    CF_wind_S_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_South_wind2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_wind_S_1.columns = list_of_repr_days_per_scenario
    CF_wind_PH_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Panhandle_wind2012.csv', index_col=0, header=0
                               ).iloc[(day*24-24):(day*24), 1]
    CF_wind_PH_1.columns = list_of_repr_days_per_scenario

    # -> wind new (new turbines)
    CF_wind_new_NE_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Northeast_wind2012.csv', index_col=0, header=0
                                   ).iloc[(day*24-24):(day*24), 1]
    CF_wind_new_NE_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_W_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_West_wind2012.csv', index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_wind_new_W_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_C_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Coastal_wind2012.csv', index_col=0, header=0
                                  ).iloc[(day*24-24):(day*24), 1]
    CF_wind_new_C_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_S_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_South_wind2012.csv', index_col=0, header=0
                                  ).iloc[(day*24-24):(day*24), 1]
    CF_wind_new_S_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_PH_1 = pd.read_csv('NSRDB_wind/for_cluster/CF_Panhandle_wind2012.csv', index_col=0, header=0
                                   ).iloc[(day*24-24):(day*24), 1]
    CF_wind_new_PH_1.columns = list_of_repr_days_per_scenario


    cf_1 = {}
    for t in range(1, n_stages+1):
        d_idx = 0
        for d in list_of_repr_days_per_scenario:
            s_idx = 0
            for ss in range(24):
                s = ss + 1
                for i in ['csp-new']:
                    cf_1[i, 'Northeast', t, d, s] = CF_CSP_NE_1.iat[s_idx]
                    cf_1[i, 'West', t, d, s] = CF_CSP_W_1.iat[s_idx]
                    cf_1[i, 'Coastal', t, d, s] = CF_CSP_C_1.iat[s_idx]
                    cf_1[i, 'South', t, d, s] = CF_CSP_S_1.iat[s_idx]
                    cf_1[i, 'Panhandle', t, d, s] = CF_CSP_PH_1.iat[s_idx]
                for i in ['pv-old', 'pv-new']:
                    cf_1[i, 'Northeast', t, d, s] = CF_PV_NE_1.iat[s_idx]
                    cf_1[i, 'West', t, d, s] = CF_PV_W_1.iat[s_idx]
                    cf_1[i, 'Coastal', t, d, s] = CF_PV_C_1.iat[s_idx]
                    cf_1[i, 'South', t, d, s] = CF_PV_S_1.iat[s_idx]
                    cf_1[i, 'Panhandle', t, d, s] = CF_PV_PH_1.iat[s_idx]
                for i in ['wind-old']:
                    cf_1[i, 'Northeast', t, d, s] = CF_wind_NE_1.iat[s_idx]
                    cf_1[i, 'West', t, d, s] = CF_wind_W_1.iat[s_idx]
                    cf_1[i, 'Coastal', t, d, s] = CF_wind_C_1.iat[s_idx]
                    cf_1[i, 'South', t, d, s] = CF_wind_S_1.iat[s_idx]
                    cf_1[i, 'Panhandle', t, d, s] = CF_wind_PH_1.iat[s_idx]
                for i in ['wind-new']:
                    cf_1[i, 'Northeast', t, d, s] = CF_wind_new_NE_1.iat[s_idx]
                    cf_1[i, 'West', t, d, s] = CF_wind_new_W_1.iat[s_idx]
                    cf_1[i, 'Coastal', t, d, s] = CF_wind_new_C_1.iat[s_idx]
                    cf_1[i, 'South', t, d, s] = CF_wind_new_S_1.iat[s_idx]
                    cf_1[i, 'Panhandle', t, d, s] = CF_wind_new_PH_1.iat[s_idx]
                s_idx += 1
            d_idx += 1
    cf_by_scenario = [cf_1]	

    new_model.cf._initialize_from(cf_by_scenario[0])						
    new_model.L._initialize_from(L_by_scenario[0])
    # opt = SolverFactory("gurobi")
    opt = SolverFactory("cplex")
    # opt.options['mipgap'] = 0.001
    # opt.options['TimeLimit'] = 36000
    opt.options['threads'] = 1
    # opt.options['emphasis numerical'] = 'y'
    # opt.options['simplex tolerances feasibility'] = 0.01
    # opt.options['feasibility'] = 1e-4
    # opt.options['LPMethod'] = 4
    # opt.options['solutiontype'] =2     

    total_operating_cost = 0.0

    for i in range(1, n_stages+1):
        results = opt.solve(new_model.Bl[i])
        if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
            total_operating_cost += new_model.Bl[i].total_operating_cost.expr()
        elif results.solver.termination_condition == TerminationCondition.infeasible:
            total_operating_cost += 1e10
            # opt.solve(new_model.Bl[i], tee=True, keepfiles=True)
            break
        else:
            # opt.solve(new_model.Bl[i], tee=True, keepfiles=True)
            raise Exception("the problem at a given time is not solved to optimality termination_condition is ", results.solver.termination_condition)    
    operating_related_cost = {}
    operating_related_cost["total_operating_cost"] = total_operating_cost            
    if total_operating_cost >= 1e9:
        operating_related_cost["variable_operating_cost" ] = 1e10
        operating_related_cost["fixed_operating_cost"] = 1e10
        operating_related_cost["startup_cost"] = 1e10
        operating_related_cost["penalty_cost"] = 1e10
        lines = ["Coastal_South", "Coastal_Northeast", "South_Northeast", "South_West", "West_Northeast", "West_Panhandle", "Northeast_Panhandle"] 
        for line in lines:
            operating_related_cost[line] = 0
        operating_related_cost["solar_energy_generated"] = 0
        operating_related_cost["wind_energy_generated" ] = 0
        operating_related_cost["nuclear_energy_generated"] = 0
        operating_related_cost["coal_energy_generated" ] = 0
        operating_related_cost["natural_gas_energy_generated"] = 0
        operating_related_cost["total_energy_generated"] = 0
        return operating_related_cost
    variable_operating_cost = []
    fixed_operating_cost =[]
    startup_cost = []    
    penalty_cost = []
    total_power_flow = {}
    solar_energy_generated = []
    wind_energy_generated = []
    nuclear_energy_generated = []
    coal_energy_generated = []
    natural_gas_energy_generated = []
    total_energy_generated = []
    lines = ["Coastal_South", "Coastal_Northeast", "South_Northeast", "South_West", "West_Northeast", "West_Panhandle", "Northeast_Panhandle"] 
    for line in lines:
        total_power_flow[line] = 0.0 
    for stage in new_model.stages:
        variable_operating_cost.append(new_model.Bl[stage].variable_operating_cost.expr())
        fixed_operating_cost.append(new_model.Bl[stage].fixed_operating_cost.expr())
        startup_cost.append(new_model.Bl[stage].startup_cost.expr())                
        total_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for (i,r)
         in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours))
        coal_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for 
            (i,r) in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours if i in new_model.co))
        natural_gas_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for
         (i,r) in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours if i in new_model.ng))
        nuclear_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for 
            (i,r) in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours if i in new_model.nu))
        solar_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for
         (i,r) in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours if (i in new_model.pv or i in new_model.csp)))
        wind_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for 
            (i,r) in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours if i in new_model.wi ))
        for l in new_model.l:
            for t in t_per_stage[stage]:
                for d in new_model.d:
                    for s in new_model.hours:
                        er = new_model.l_er[l][1]
                        sr = new_model.l_sr[l][1]
                        if new_model.Bl[stage].P_flow[l,t,d,s].value > 0.001:
                            total_power_flow[sr+ "_" + er] += new_model.Bl[stage].P_flow[l,t,d,s].value * new_model.n_d[d].value * pow(10,-6)
    operating_related_cost["variable_operating_cost" ] = np.sum(variable_operating_cost )
    operating_related_cost["fixed_operating_cost"] = np.sum(fixed_operating_cost)
    operating_related_cost["startup_cost"] = np.sum(startup_cost )
    operating_related_cost["penalty_cost"] = np.sum(penalty_cost)
    for line in lines:
        operating_related_cost[line] = total_power_flow[line]
    operating_related_cost["solar_energy_generated"] = np.sum(solar_energy_generated)
    operating_related_cost["wind_energy_generated" ] = np.sum(wind_energy_generated )
    operating_related_cost["nuclear_energy_generated"] = np.sum(nuclear_energy_generated)
    operating_related_cost["coal_energy_generated" ] = np.sum(coal_energy_generated )
    operating_related_cost["natural_gas_energy_generated"] = np.sum(natural_gas_energy_generated)
    operating_related_cost["total_energy_generated"] = np.sum(total_energy_generated)
    return operating_related_cost


def write_GTEP_results(m, outputfile, opt, readData_det, t_per_stage, results=[], ub_problem={}, mode="w"):
    total_investment_cost = []
    variable_operating_cost = []
    fixed_operating_cost =[]
    startup_cost = []
    thermal_generator_cost = []
    extending_thermal_generator_cost = []
    renewable_generator_cost = []
    extending_renewable_generator_cost = []
    storage_investment_cost = []
    penalty_cost = []
    renewable_capacity = []
    thermal_capacity = []
    total_capacity = []
    transmission_line_cost = []
    solar_capacity = []
    wind_capacity = []
    nuclear_capacity = []
    coal_capacity = []
    natural_gas_capacity = []
    solar_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
    wind_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
    nuclear_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
    coal_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
    natural_gas_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
    power_flow = []
    solar_energy_generated = []
    wind_energy_generated = []
    nuclear_energy_generated = []
    coal_energy_generated = []
    natural_gas_energy_generated = []
    total_energy_generated = []

    for stage in m.stages:
        total_investment_cost.append(m.Bl[stage].total_investment_cost.expr())
        variable_operating_cost.append(m.Bl[stage].variable_operating_cost.expr())
        fixed_operating_cost.append(m.Bl[stage].fixed_operating_cost.expr())
        startup_cost.append(m.Bl[stage].startup_cost.expr())
        thermal_generator_cost.append(m.Bl[stage].thermal_generator_cost.expr())
        extending_thermal_generator_cost.append(m.Bl[stage].extending_thermal_generator_cost.expr())
        renewable_generator_cost.append(m.Bl[stage].renewable_generator_cost.expr())
        extending_renewable_generator_cost.append(m.Bl[stage].extending_renewable_generator_cost.expr())
        storage_investment_cost.append(m.Bl[stage].storage_investment_cost.expr())
        penalty_cost.append(m.Bl[stage].penalty_cost.expr())
        renewable_capacity.append(m.Bl[stage].renewable_capacity.expr())
        thermal_capacity.append(m.Bl[stage].thermal_capacity.expr())
        total_capacity.append(m.Bl[stage].total_capacity.expr())
        transmission_line_cost.append(m.Bl[stage].transmission_line_cost.expr())
        coal_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.co) )
        natural_gas_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.ng) )
        nuclear_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.nu) )
        solar_capacity.append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, r in m.i_r if (rn in m.pv or rn in m.csp)) )
        wind_capacity.append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, r in m.i_r if rn in m.wi) )
        for r in m.r:
            coal_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for  th, rr in m.i_r if (rr==r and th in m.co) ))
            natural_gas_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, rr in m.i_r if (rr==r and th in m.ng) ))
            nuclear_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, rr in m.i_r if (rr==r  and th in m.nu) ))
            solar_capacity_region[r].append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, rr in m.i_r if (rr == r and (rn in m.pv or rn in m.csp))) )
            wind_capacity_region[r].append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, rr in m.i_r if( rr==r and rn in m.wi) ))
        total_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for (i,r)
         in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours))
        coal_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for 
            (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.co))
        natural_gas_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for
         (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.ng))
        nuclear_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for 
            (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.nu))
        solar_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for
         (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if (i in m.pv or i in m.csp)))
        wind_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for 
            (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.wi ))
        temp_power_flow = {}
        for r in m.r:
            temp_power_flow[r] = {}
            for rr in m.r:
                temp_power_flow[r][rr] = 0
        for l in m.l:
            for t in t_per_stage[stage]:
                for d in m.d:
                    for s in m.hours:
                        er = m.l_er[l][1]
                        sr = m.l_sr[l][1]
                        if m.Bl[stage].P_flow[l,t,d,s].value > 0:
                            temp_power_flow[sr][er] += m.Bl[stage].P_flow[l,t,d,s].value * m.n_d[d].value * pow(10,-6)
                        else:
                            temp_power_flow[er][sr] -= m.Bl[stage].P_flow[l,t,d,s].value * m.n_d[d].value * pow(10,-6)
        power_flow.append(temp_power_flow)
    
    energy_region_dict ={"solar":solar_capacity_region,
    "nuc":nuclear_capacity_region, 
    "coal":coal_capacity_region,
    "natural gas": natural_gas_capacity_region,
    "wind":wind_capacity_region}
    with open(outputfile, mode, newline='') as results_file:
                fieldnames = ["Time", "total_investment_cost", "variable_operating_cost",
                            "fixed_operating_cost",
                            "startup_cost",
                            "thermal_generator_cost",
                            "extending_thermal_generator_cost",
                            "renewable_generator_cost",
                            "extending_renewable_generator_cost",
                            "storage_investment_cost",
                            "penalty_cost",
                            "renewable_capacity",
                            "thermal_capacity",                        
                            "transmission_line_cost",
                            "coal_capacity",
                            "natural_gas_capacity",
                            "nuclear_capacity",
                            "solar_capacity",
                            "wind_capacity",
                            "total_capacity",
                            "power_flow",
                            "solar_energy_generated",
                            "wind_energy_generated",
                            "nuclear_energy_generated",
                            "coal_energy_generated",
                            "natural_gas_energy_generated",
                            "total_energy_generated"
                            ]
                for r in m.r:
                    for gen in ["coal", "natural gas", "nuc", "solar", "wind"]:
                        fieldnames.append(r+ " " + gen)
                writer = csv.DictWriter(results_file, fieldnames=fieldnames)
                writer.writeheader()
                for i in range(len(m.stages)):
                    new_row = {"Time":i + 1,
                        "total_investment_cost":total_investment_cost[i],
                        "variable_operating_cost":variable_operating_cost[i],
                        "fixed_operating_cost":fixed_operating_cost[i],
                        "startup_cost":startup_cost[i],
                        "thermal_generator_cost":thermal_generator_cost[i],
                        "extending_thermal_generator_cost":extending_thermal_generator_cost[i],
                        "renewable_generator_cost":renewable_generator_cost[i],
                        "extending_renewable_generator_cost":extending_renewable_generator_cost[i],
                        "storage_investment_cost":storage_investment_cost[i],
                        "penalty_cost":penalty_cost[i],
                        "renewable_capacity":renewable_capacity[i],
                        "thermal_capacity":thermal_capacity[i],
                        "total_capacity":total_capacity[i],
                        "transmission_line_cost":transmission_line_cost[i],
                        "coal_capacity":coal_capacity[i],
                        "natural_gas_capacity":natural_gas_capacity[i],
                        "nuclear_capacity":nuclear_capacity[i],
                        "solar_capacity":solar_capacity[i],
                        "wind_capacity":wind_capacity[i],
                        "power_flow":power_flow[i],
                        "solar_energy_generated":solar_energy_generated[i],
                        "wind_energy_generated":wind_energy_generated[i],
                        "nuclear_energy_generated":nuclear_energy_generated[i],
                        "coal_energy_generated":coal_energy_generated[i],
                        "natural_gas_energy_generated":natural_gas_energy_generated[i],
                        "total_energy_generated":total_energy_generated[i]}
                    for r in m.r:
                        for gen in ["coal", "natural gas", "nuc", "solar", "wind"]:
                            key = r+ " " + gen
                            new_row[key] = energy_region_dict[gen][r][i]
                    writer.writerow(new_row)                    
                results_writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                #get the transmission line expansion 
                for stage in m.stages:                
                    for l in m.l_new:
                        if m.Bl[stage].ntb[l,stage].value > 0.1:
                            temp_row = [stage, readData_det.tielines[l-1]["Near Area Name"], readData_det.tielines[l-1]["Far Area Name"]]
                            results_writer.writerow(temp_row)
                     #get the peak demand network structure in the last year  
                last_stage = len(m.stages)                          
                largest_d, largest_s =  0, 0
                largest_load = 0.0
                for r in m.r:
                    for d in m.d:
                        for s in m.hours:
                            if m.L[r, last_stage,d,s].value > largest_load:
                                largest_load = m.L[r, last_stage,d,s].value
                                largest_d = d 
                                largest_s = s 
                #write down the load of each region 
                results_writer.writerow([" at last year ",  d, s])
                results_writer.writerow([" ", 'Northeast', 'West', 'Coastal', 'South', 'Panhandle'])
                results_writer.writerow(["load ", m.L["Northeast", last_stage, largest_d, largest_s].value, 
                    m.L["West", last_stage, largest_d, largest_s].value,m.L["Coastal", last_stage, largest_d, largest_s].value,
                    m.L["South", last_stage, largest_d, largest_s].value,m.L["Panhandle", last_stage, largest_d, largest_s].value])
                new_row = ["power generation"]
                for r in m.r:
                    new_row.append(sum(m.Bl[last_stage].P[i, r, last_stage, largest_d, largest_s].value for i,rr in m.i_r if rr==r))
                results_writer.writerow(new_row)
                new_row = ["power charged"]
                for r in m.r:
                    new_row.append(sum(m.Bl[last_stage].p_charged[j, r, last_stage, largest_d, largest_s].value for j in m.j)) 
                results_writer.writerow(new_row)
                new_row = ["power discharged"]    
                for r in m.r:
                    new_row.append(sum(m.Bl[last_stage].p_discharged[j, r, last_stage, largest_d, largest_s].value for j in m.j))     
                results_writer.writerow(new_row)
                new_row = ["transmission power "]
                for r in m.r:
                    temp_P = 0
                    for l in m.l:
                        er = m.l_er[l][1]
                        sr = m.l_sr[l][1]
                        if er == r:
                            temp_P += m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value
                        if sr == r:
                            temp_P -= m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value
                    new_row.append(temp_P)
                results_writer.writerow(new_row)
                new_row = ["curtailment "]
                for r in m.r:
                    new_row.append(m.Bl[last_stage].cu[r, last_stage, largest_d, largest_s].value)
                results_writer.writerow(new_row)
                   #power transmission of each line 
                results_writer.writerow([])
                results_writer.writerow(["transmission at peak load "])
                for l in m.l:
                    if abs(m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value) > 0.1:
                        results_writer.writerow([readData_det.tielines[l-1]["Near Area Name"], readData_det.tielines[l-1]["Far Area Name"], m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value ])
                results_writer.writerow([])        
                results_writer.writerow(["total_investment_cost", sum(total_investment_cost[:])])
                if results != []:
                    if 'Time' in results['Solver'][0]:
                        results_writer.writerow(["cplex fullspace time", results['Solver'][0]['Time']])
                    elif 'Wallclock time' in results['Solver'][0]:
                         results_writer.writerow(["cplex fullspace time", results['Solver'][0]['Wallclock time']])
                    if 'Lower bound' in results['Problem'][0]:
                        results_writer.writerow(["lb", results['Problem'][0]['Lower bound']])
                    if 'Upper bound' in results['Problem'][0]:
                        results_writer.writerow(["ub", results['Problem'][0]['Upper bound']])
    #{"ub time":ub_time, "upper_bound_obj":upper_bound_obj}                    
                    if "ub time" in ub_problem:
                        results_writer.writerow(["ub_time", ub_problem["ub time"]])
                    if "upper_bound_obj" in ub_problem:
                        results_writer.writerow(["upper_bound_obj", ub_problem["upper_bound_obj"]])

def write_repn_results(operating_cost, outputfile):
    with open(outputfile, 'a', newline='') as results_file:
        results_writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        results_writer.writerow([])
        results_writer.writerow(["testing over all the repn days results"])
        results_writer.writerow(["aggregated results for whole year "])        
        fieldnames = ["day_number"] + list(operating_cost[list(operating_cost.keys())[0]].keys())
        writer = csv.DictWriter(results_file, fieldnames=fieldnames)
        writer.writeheader()
        days = np.sort(list(operating_cost.keys()))
        #first write down the average 
        average = {key:(sum(operating_cost[day][key] for day in days)/len(operating_cost)) for key in fieldnames if key != "day_number"}
        average["day_number"] = "average"
        writer.writerow(average)
        for day in days:
            new_row = {key:operating_cost[day][key] for key in fieldnames  if key != "day_number"}
            new_row["day_number"] = day 
            writer.writerow(new_row) 




















