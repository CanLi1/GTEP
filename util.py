# author: Can Li 
#utils for representative days selection
from pyomo.environ import *
import pandas as pd
#fix investment decisions
def fix_investment(ref_model, new_model):
	investment_vars = ["ntb","nte","nte_prev","ngr_rn","nge_rn","ngr_th","nge_th","ngo_rn","ngb_rn","ngo_th","ngb_th","ngo_rn_prev","ngo_th_prev","nsr","nsb","nso","nso_prev", "RES_def"]	
	for v1 in ref_model.component_objects(Var):
		for v2 in new_model.component_objects(Var):
			if v1.getname() in investment_vars and v2.getname() == investment_vars and v1.getname() == v2.getname:
				for index in v1:
					if v1[index].value != None:
						v2[index].fix(v1[index].value)
	return 0

def eval_investment_single_day(new_model, day, n_stages):
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
    opt = SolverFactory("cplex")
    opt.options['mipgap'] = 0.001
    opt.options['TimeLimit'] = 36000
    opt.options['threads'] = 1

    total_operating_cost = 0.0

    for i in range(1, n_stages+1):
        opt.solve(new_model.Bl[i], tee=False)
        total_operating_cost += new_model.Bl[i].total_operating_cost.expr()
    return total_operating_cost
























