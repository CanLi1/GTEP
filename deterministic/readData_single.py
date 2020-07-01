import sqlite3 as sql
import os
import pandas as pd


def read_data(database_file, curPath, stages, n_stage, t_per_stage, day):
    print(os.path.exists(database_file))
    print(database_file)
    conn = sql.connect(database_file)
    c = conn.cursor()

    def process_param(sql_param):
        d = dict()
        for row in c.execute("SELECT * FROM {}".format(sql_param)):
            p_len = len(row)
            if p_len == 2:
                try:
                    d[int(row[0])] = row[1]
                except ValueError:
                    d[str(row[0])] = row[1]
            elif p_len == 3:
                try:
                    d[str(row[0]), int(row[1])] = row[2]
                except ValueError:
                    d[str(row[0]), str(row[1])] = row[2]
            elif p_len == 4:
                try:
                    d[str(row[0]), str(row[1]), int(row[2])] = row[3]
                except ValueError:
                    d[str(row[0]), str(row[1]), str(row[2])] = row[3]
            elif p_len == 5:
                try:
                    d[str(row[0]), int(row[1]), str(row[2]), str(row[3])] = row[4]
                except ValueError:
                    d[str(row[0]), str(row[1]), str(row[2]), str(row[3])] = row[4]
            elif p_len == 6:
                try:
                    d[str(row[0]), str(row[1]), int(row[2]), str(row[3]), str(row[4])] = row[5]
                except ValueError:
                    d[str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4])] = row[5]
        return d

    params = ['L_max', 'Qg_np', 'Ng_old', 'Ng_max', 'Qinst_UB', 'LT', 'Tremain', 'Ng_r', 'q_v',
              'Pg_min', 'Ru_max', 'Rd_max', 'f_start', 'C_start', 'frac_spin', 'frac_Qstart', 't_loss', 't_up', 'dist',
              'if_', 'ED', 'Rmin', 'hr', 'EF_CO2', 'FOC', 'VOC', 'CCm', 'DIC', 'LEC', 'PEN', 'tx_CO2',
              'RES_min', 'P_fuel']  


    for p in params:
        if p not in ["FOC", "VOC", "DIC"]:
            globals()[p] = process_param(p)

    FOC = process_param("FOC")
    VOC = process_param("VOC")
    DIC = process_param("DIC")
    LT = process_param("LT")
    if_ = process_param("if_")
    conn.close()

    time = len(t_per_stage)

    #change investment cost, variable operating cost and fixed operating cost of future generators
    # m.FOC: 􏰄fixed operating cost of generator cluster i ($/MW)
    # m.VOC: variable O&M cost of generator cluster i ($/MWh)
    # m.DIC: discounted investment cost of generator cluster i in year t ($/MW)
    new_gen = ['wind-new', 'pv-new', 'csp-new', 'coal-igcc-new', 'coal-igcc-ccs-new', 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new','nuc-st-new']    

    d_FOC = pd.read_csv(os.path.join(curPath, 'generator/fixOM.csv'), index_col=0, header=0).iloc[:, :]
    d_OCC = pd.read_csv(os.path.join(curPath, 'generator/overnightcost.csv'), index_col=0, header=0).iloc[:, :]
    d_VOC = pd.read_csv(os.path.join(curPath, 'generator/variableOM.csv'), index_col=0, header=0).iloc[:, :]
    #ir nomimal interest rate 
    ir = 0.057
    for t in range(1, len(n_stage)+1):
        for g in new_gen:
            FOC[(g,t)] = float(d_FOC[g][t])
            OCC = float(d_OCC[g][t])
            ACC = OCC * ir / (1 - (1/(1+ir)) ** LT[g]) 
            T_remain = len(n_stage) - t + 1
            DIC[(g,t)] = ACC * sum(if_[tt] for tt in range(1, len(n_stage) + 1) if (tt <= T_remain and tt <= LT[g]))
            VOC[(g,t)] = float(d_VOC[g][t])
    globals()['FOC'] = FOC 
    globals()['DIC'] = DIC
    globals()['VOC'] = VOC 

    globals()['hs'] = 1
    globals()['ir'] = 0.057
    globals()['PENc'] = 5000
    t_up['West', 'Coastal'] = 0
    t_up['Coastal', 'West'] = 0
    t_up['Coastal', 'Panhandle'] = 0
    t_up['South', 'Panhandle'] = 0
    t_up['Panhandle', 'Coastal'] = 0
    t_up['Panhandle', 'South'] = 0

    ####################################################################################################################
    # Storage data (Lithium-ion battery (utility) -> c-rate 1/1.2 h;
    #               Lead-acid battery (residency) -> c-rate 1/3 h;
    #               Redox-Flow battery (residency) -> c-rate 1/3 h
    # source: https://www.nature.com/articles/nenergy2017110.pdf

    # Storage Investment Cost in $/MW
    storage_inv_cost = {('Li_ion', 1): 1637618.014, 
                        ('Li_ion', 2): 1350671.054, ('Li_ion', 3): 1203144.473,
                        ('Li_ion', 4): 1099390.353, ('Li_ion', 5): 1017197.661,
                         ('Li_ion', 6): 948004.5483,
                         ('Li_ion', 7): 887689.7192, ('Li_ion', 8): 834006.1087, ('Li_ion', 9): 785632.3346,
                         ('Li_ion', 10): 741754.6519,
                         ('Li_ion', 11): 701857.294, ('Li_ion', 12): 665604.5808,
                         ('Li_ion', 13): 632766.397, ('Li_ion', 14): 603165.7101, ('Li_ion', 15): 576639.6204,
                        ('Li_ion', 16): 553012.1704, ('Li_ion', 17): 532079.791, ('Li_ion', 18): 513609.5149,
                        ('Li_ion', 19): 497347.4123, ('Li_ion', 20): 483032.4302,
                        ('Lead_acid', 1): 4346125.294, 
                        ('Lead_acid', 2): 3857990.578, ('Lead_acid', 3): 3458901.946,
                        ('Lead_acid', 4): 3117666.824, ('Lead_acid', 5): 2818863.27,
                         ('Lead_acid', 6): 2553828.021,
                         ('Lead_acid', 7): 2317228.867, ('Lead_acid', 8): 2105569.661, ('Lead_acid', 9): 1916483.132,
                         ('Lead_acid', 10): 1748369.467,
                         ('Lead_acid', 11): 1600168.567, ('Lead_acid', 12): 1471137.002,
                         ('Lead_acid', 13): 1360557.098, ('Lead_acid', 14): 1267402.114, ('Lead_acid', 15): 1190102.412,
                        ('Lead_acid', 16): 1126569.481, ('Lead_acid', 17): 1074464.42, ('Lead_acid', 18): 1031526.418,
                        ('Lead_acid', 19): 995794.3254, ('Lead_acid', 20): 965683.7645,
                        ('Flow', 1): 4706872.908, 
                        ('Flow', 2): 3218220.336, ('Flow', 3): 2810526.973,
                        ('Flow', 4): 2555010.035, ('Flow', 5): 2362062.488,
                         ('Flow', 6): 2203531.648,
                         ('Flow', 7): 2067165.77, ('Flow', 8): 1946678.078, ('Flow', 9): 1838520.24,
                         ('Flow', 10): 1740573.662
         , ('Flow', 11): 1651531.463, ('Flow', 12): 1570567.635,
                         ('Flow', 13): 1497136.957, ('Flow', 14): 1430839.31, ('Flow', 15): 1371321.436,
                        ('Flow', 16): 1318208.673, ('Flow', 17): 1271067.144, ('Flow', 18): 1229396.193,
                        ('Flow', 19): 1192645.164, ('Flow', 20): 1160243.518
                        }
    temp_dict = {}                        
    for key in storage_inv_cost:                   
        if key[1] <= time:
            temp_dict[key] = storage_inv_cost[key]
    storage_inv_cost = temp_dict
    globals()["storage_inv_cost"] = storage_inv_cost

    # Power rating [MW]
    P_min_charge = {'Li_ion': 0, 'Lead_acid': 0, 'Flow': 0}
    globals()["P_min_charge"] = P_min_charge
    P_max_charge = {'Li_ion': 40, 'Lead_acid': 36, 'Flow': 2}
    globals()["P_max_charge"] = P_max_charge
    P_min_discharge = {'Li_ion': 0, 'Lead_acid': 0, 'Flow': 0}
    globals()["P_min_discharge"] = P_min_discharge
    P_max_discharge = {'Li_ion': 40, 'Lead_acid': 36, 'Flow': 2}
    globals()["P_max_discharge"] = P_max_discharge

    # Rated energy capacity [MWh]
    min_storage_cap = {'Li_ion': 0, 'Lead_acid': 0, 'Flow': 0}
    globals()["min_storage_cap"] = min_storage_cap
    max_storage_cap = {'Li_ion': 20, 'Lead_acid': 24, 'Flow': 12}
    globals()["max_storage_cap"] = max_storage_cap

    # Charge efficiency (fraction)
    eff_rate_charge = {'Li_ion': 0.95, 'Lead_acid': 0.85, 'Flow': 0.75}
    globals()["eff_rate_charge"] = eff_rate_charge
    eff_rate_discharge = {'Li_ion': 0.85, 'Lead_acid': 0.85, 'Flow': 0.75}
    globals()["eff_rate_discharge"] = eff_rate_discharge

    # Storage lifetime (years)
    storage_lifetime = {'Li_ion': 15, 'Lead_acid': 15, 'Flow': 20}
    globals()["storage_lifetime"] = storage_lifetime

    ####################################################################################################################
    # Operational uncertainty data
    globals()['num_days'] = 1
    list_of_repr_days_per_scenario = list(range(1,(1+1)))
    n_ss = {}
    n_ss[1] = 365
    globals()['n_ss'] = n_ss
    # Misleading (seasons not used) but used because of structure of old data
    # ############ LOAD ############
    L_NE_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/L_Northeast_2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    L_NE_1.columns = list_of_repr_days_per_scenario
    L_W_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/L_West_2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    L_W_1.columns = list_of_repr_days_per_scenario
    L_C_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/L_Coastal_2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    L_C_1.columns = list_of_repr_days_per_scenario
    L_S_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/L_South_2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    L_S_1.columns = list_of_repr_days_per_scenario
    L_PH_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/L_South_2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1].multiply(0)
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

    L_max = {}
    for t in range(1, len(n_stage)+1):
        L_max[t] = 0 
        for d in list_of_repr_days_per_scenario:
            s_idx = 0
            for ss in range(24):
                s = ss + 1
                L_max[t] =max(L_max[t],  L_1['Northeast', t, d, s] + L_1['West', t, d, s] + L_1['Coastal', t, d, s] + L_1['South', t, d, s] )
                           

    L_by_scenario = [L_1]
    # print(L_by_scenario)
    globals()["L_by_scenario"] = L_by_scenario
    globals()["L_max"] = L_max
    L_by_scenario = [L_1]
    # print(L_by_scenario)
    globals()["L_by_scenario"] = L_by_scenario

    # ############ CAPACITY FACTOR ############
    # -> solar CSP
    CF_CSP_NE_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Northeast_CSP2012.csv'), index_col=0, header=0
                              ).iloc[(day*24-24):(day*24), 1]
    CF_CSP_NE_1.columns = list_of_repr_days_per_scenario
    CF_CSP_W_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_West_CSP2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_CSP_W_1.columns = list_of_repr_days_per_scenario
    CF_CSP_C_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Coastal_CSP2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_CSP_C_1.columns = list_of_repr_days_per_scenario
    CF_CSP_S_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_South_CSP2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_CSP_S_1.columns = list_of_repr_days_per_scenario
    CF_CSP_PH_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Panhandle_CSP2012.csv'), index_col=0, header=0
                              ).iloc[(day*24-24):(day*24), 1]
    CF_CSP_PH_1.columns = list_of_repr_days_per_scenario

    # -> solar PVSAT
    CF_PV_NE_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Northeast_PV2012.csv'), index_col=0, header=0
                             ).iloc[(day*24-24):(day*24), 1]
    CF_PV_NE_1.columns = list_of_repr_days_per_scenario
    CF_PV_W_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_West_PV2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_PV_W_1.columns = list_of_repr_days_per_scenario
    CF_PV_C_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Coastal_PV2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_PV_C_1.columns = list_of_repr_days_per_scenario
    CF_PV_S_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_South_PV2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_PV_S_1.columns = list_of_repr_days_per_scenario
    CF_PV_PH_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Panhandle_PV2012.csv'), index_col=0, header=0
                             ).iloc[(day*24-24):(day*24), 1]
    CF_PV_PH_1.columns = list_of_repr_days_per_scenario

    # -> wind (old turbines)
    CF_wind_NE_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Northeast_wind2012.csv'), index_col=0, header=0
                               ).iloc[(day*24-24):(day*24), 1]
    CF_wind_NE_1.columns = list_of_repr_days_per_scenario
    CF_wind_W_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_West_wind2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_wind_W_1.columns = list_of_repr_days_per_scenario
    CF_wind_C_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Coastal_wind2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_wind_C_1.columns = list_of_repr_days_per_scenario
    CF_wind_S_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_South_wind2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_wind_S_1.columns = list_of_repr_days_per_scenario
    CF_wind_PH_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Panhandle_wind2012.csv'), index_col=0, header=0
                               ).iloc[(day*24-24):(day*24), 1]
    CF_wind_PH_1.columns = list_of_repr_days_per_scenario

    # -> wind new (new turbines)
    CF_wind_new_NE_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Northeast_wind2012.csv'), index_col=0, header=0
                                   ).iloc[(day*24-24):(day*24), 1]
    CF_wind_new_NE_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_W_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_West_wind2012.csv'), index_col=0, header=0).iloc[(day*24-24):(day*24), 1]
    CF_wind_new_W_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_C_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Coastal_wind2012.csv'), index_col=0, header=0
                                  ).iloc[(day*24-24):(day*24), 1]
    CF_wind_new_C_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_S_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_South_wind2012.csv'), index_col=0, header=0
                                  ).iloc[(day*24-24):(day*24), 1]
    CF_wind_new_S_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_PH_1 = pd.read_csv(os.path.join(curPath, 'NSRDB_wind/for_cluster/CF_Panhandle_wind2012.csv'), index_col=0, header=0
                                   ).iloc[(day*24-24):(day*24), 1]
    CF_wind_new_PH_1.columns = list_of_repr_days_per_scenario


    cf_1 = {}
    for t in range(1, len(n_stage)+1):
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

    # print(cf_by_scenario)
    globals()["cf_by_scenario"] = cf_by_scenario


    ###################################################################################################################

    # Strategic uncertainty data

    # Different scenarios for PEAK LOAD:
    L_max_scenario = {'L': L_max, 'M': {t: 1.05 * L_max[t] for t in L_max}, 'H': {t: 1.2 * L_max[t] for t in L_max}}
    # print(L_max_scenario)
    
    L_max_s = {}
    for stage in stages:
        for n in n_stage[stage]:
            for t in t_per_stage[stage]:
                if stage == 1:
                    L_max_s[t, stage, n] = L_max_scenario['M'][t]
                else:
                    m = n[-1]
                    if m == 'L':
                        L_max_s[t, stage, n] = L_max_scenario['L'][t]
                    elif m == 'M':
                        L_max_s[t, stage, n] = L_max_scenario['M'][t]
                    elif m == 'H':
                        L_max_s[t, stage, n] = L_max_scenario['H'][t]
    globals()["L_max_s"] = L_max_s
    print(L_max_s)

    # Different scenarios for CARBON TAX:
#the data in the original file does not seem correct we have changed it the the data in readData.py
    # tx_CO2_scenario = {(1, 'M'): 0,
    #           (2, 'M'): 0.50,
    #           (3, 'M'): 0.65,
    #           (4, 'M'): 0.81,
    #           (5, 'M'): 0.96,
    #           (6, 'M'): 0.112,
    #           (7, 'M'): 0.127,
    #           (8, 'M'): 0.142,
    #           (9, 'M'): 0.158,
    #           (10, 'M'): 0.173,
    #           (11, 'M'): 0.188,
    #           (12, 'M'): 0.204,
    #           (13, 'M'): 0.219,
    #           (14, 'M'): 0.235,
    #           (15, 'M'): 0.250}

    # tx_CO2 = {}
    # for stage in stages:
    #     for t in t_per_stage[stage]:
    #         if stage == 1:
    #             tx_CO2[t, stage, 'O'] = 0
    #         else:
    #             for n in ['M']:
    #                 tx_CO2[t, stage, n] = tx_CO2_scenario[t, 'M']

    # globals()["tx_CO2"] = tx_CO2

    # # Different scenarios for NG PRICE:
    # ng_price_scenarios = {(1, 'M'): 4.20823445,
    #                       (2, 'M'): 4.12045385,
    #                       (3, 'M'): 4.1614488,
    #                       (4, 'M'): 4.33768595,
    #                       (5, 'M'): 4.6312679,
    #                       (6, 'M'): 4.9058309,
    #                       (7, 'M'): 5.1202266,
    #                       (8, 'M'): 5.2027597,
    #                       (9, 'M'): 5.3456442,
    #                       (10, 'M'): 5.3456442,
    #                       (11, 'M'): 5.4251275,
    #                       (12, 'M'): 5.45180595,
    #                       (13, 'M'): 5.5881823,
    #                       (14, 'M'): 5.65757295,
    #                       (15, 'M'): 5.75265282
    #                       }

    # min, median and max values from the scenarios of EIA outlook for NG price for electricity
    # https://www.eia.gov/outlooks/aeo/data/browser/#/?id=3-AEO2019&cases=ref2019&sourcekey=0
    # Strategic uncertainty data

    # Different scenarios for CARBON TAX:
    tx_CO2_scenario = {(2, 'L'): 0, (2, 'M'): 0.050, (2, 'H'): 0.100,
                       (3, 'L'): 0, (3, 'M'): 0.065, (3, 'H'): 0.131,
                       (4, 'L'): 0, (4, 'M'): 0.081, (4, 'H'): 0.162,
                       (5, 'L'): 0, (5, 'M'): 0.096, (5, 'H'): 0.192,
                       (6, 'L'): 0, (6, 'M'): 0.112, (6, 'H'): 0.223,
                       (7, 'L'): 0, (7, 'M'): 0.127, (7, 'H'): 0.254,
                       (8, 'L'): 0, (8, 'M'): 0.142, (8, 'H'): 0.285,
                       (9, 'L'): 0, (9, 'M'): 0.158, (9, 'H'): 0.315,
                       (10, 'L'): 0, (10, 'M'): 0.173, (10, 'H'): 0.346,
                       (11, 'L'): 0, (11, 'M'): 0.188, (11, 'H'): 0.377,
                       (12, 'L'): 0, (12, 'M'): 0.204, (12, 'H'): 0.408,
                       (13, 'L'): 0, (13, 'M'): 0.219, (13, 'H'): 0.438,
                       (14, 'L'): 0, (14, 'M'): 0.235, (14, 'H'): 0.469,
                       (15, 'L'): 0, (15, 'M'): 0.250, (15, 'H'): 0.500,
                       (16, 'L'): 0, (16, 'M'): 0.265, (16, 'H'): 0.500,
                       (17, 'L'): 0, (17, 'M'): 0.280, (17, 'H'): 0.500,
                       (18, 'L'): 0, (18, 'M'): 0.295, (18, 'H'): 0.500,
                       (19, 'L'): 0, (19, 'M'): 0.310, (19, 'H'): 0.500,
                       (20, 'L'): 0, (20, 'M'): 0.325, (20, 'H'): 0.500
                       }
    temp_dict = {}
    for key in tx_CO2_scenario:
        if key[0] <= time:
            temp_dict[key] = tx_CO2_scenario[key]
    tx_CO2_scenario = temp_dict

    tx_CO2 = {}
    for stage in stages:
        for t in t_per_stage[stage]:
            if stage == 1:
                tx_CO2[t, stage, 'O'] = 0
            else:
                for n in ['L', 'M', 'H']:
                    tx_CO2[t, stage, n] = tx_CO2_scenario[t, n]
    globals()["tx_CO2"] = tx_CO2

    # Different scenarios for NG PRICE:
    # ng_price_scenarios = {(1, 'L'): 3.117563, (1, 'M'): 3.4014395, (1, 'H'): 4.249755,
    #                       (2, 'L'): 2.976701, (2, 'M'): 3.357056, (2, 'H'): 4.188047,
    #                       (3, 'L'): 2.974117, (3, 'M'): 3.4164015, (3, 'H'): 4.228118,
    #                       (4, 'L'): 3.082466, (4, 'M'): 3.578708, (4, 'H'): 4.403251,
    #                       (5, 'L'): 3.236482, (5, 'M'): 3.8122265, (5, 'H'): 4.745406,
    #                       (6, 'L'): 3.394663, (6, 'M'): 3.9940535, (6, 'H'): 5.088468,
    #                       (7, 'L'): 3.479183, (7, 'M'): 4.0682835, (7, 'H'): 5.442574,
    #                       (8, 'L'): 3.504514, (8, 'M'): 4.117297, (8, 'H'): 5.565526,
    #                       (9, 'L'): 3.498631, (9, 'M'): 4.188261, (9, 'H'): 5.82389,
    #                       (10, 'L'): 3.490988, (10, 'M'): 4.219348, (10, 'H'): 5.905959,
    #                       (11, 'L'): 3.483505, (11, 'M'): 4.250815, (11, 'H'): 5.955,
    #                       (12, 'L'): 3.496959, (12, 'M'): 4.2411075, (12, 'H'): 6.013945,
    #                       (13, 'L'): 3.534126, (13, 'M'): 4.3724575, (13, 'H'): 6.17547,
    #                       (14, 'L'): 3.57645, (14, 'M'): 4.4414835, (14, 'H'): 6.240099,
    #                       (15, 'L'): 3.585003, (15, 'M'): 4.47585855, (15, 'H'): 6.41513
    #                       }
    # for t in range(1, 16):
    #     ng_price_scenarios[t, 'H'] = 1.5 * ng_price_scenarios[t, 'H']
        
    # th_generators = ['coal-st-old1', 'coal-igcc-new', 'coal-igcc-ccs-new', 'ng-ct-old',
    #                  'ng-cc-old', 'ng-st-old', 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new']
    # ng_generators = ['ng-ct-old', 'ng-cc-old', 'ng-st-old', 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new']
    # # 'nuc-st-old', 'nuc-st-new',
    
    # P_fuel_scenarios = {}
    # for stage in stages:
    #     for t in t_per_stage[stage]:
    #         for i in th_generators:
    #             if stage == 1:
    #                 P_fuel_scenarios[i, t, stage, 'O'] = P_fuel[i, t]
    #             else:
    #                 for n in ['M']:
    #                     if i in ng_generators:
    #                         P_fuel_scenarios[i, t, stage, n] = ng_price_scenarios[t, n]
    #                     else:
    #                         P_fuel_scenarios[i, t, stage, n] = P_fuel[i, t]
    # globals()["P_fuel_scenarios"] = P_fuel_scenarios
    # print(P_fuel_scenarios)


####################################read tie lines data
    tielines_df = pd.read_csv(os.path.join(curPath, 'data/tielines.csv'), index_col=0, header=0).iloc[:, :]
    all_tielines = []
    #"Far West" "West" are both "West", "South" and "South Central" are both "South"
    #"North Central" and "East" are both "Northeast"
    areaMap = {'Coast':'Coastal', 'South':'South', 'South Central':'South', 'East':'Northeast', \
                'West':'West', 'Far West':'West', 'North':'Northeast', 'North Central':'Northeast'}
    CostPerMile = {115:500000, 161:600000, 230:959700, 500:1919450}
    TIC = {}
    # j= 1
    # for i in range(tielines_df.shape[0]):
    #     if areaMap[tielines_df.iat[i,0]] == areaMap[tielines_df.iat[i,1]]:
    #         continue
    #     temp_line = {}
    #     temp_line['Near Area Name'] = areaMap[tielines_df.iat[i,0]]
    #     temp_line['Far Area Name'] = areaMap[tielines_df.iat[i,1]]
    #     temp_line['Capacity'] = float(tielines_df.iat[i,2])
    #     temp_line['X'] = float(tielines_df.iat[i,3])
    #     temp_line['R'] = float(tielines_df.iat[i,4])
    #     temp_line['Voltage'] = tielines_df.iat[i,5]
    #     temp_line['B'] = - temp_line['X'] / (temp_line['X'] * temp_line['X'] + temp_line['R'] *  temp_line['R']) * 100
    #     temp_line['Distance'] = dist[temp_line['Near Area Name'], temp_line['Far Area Name']]
    #     temp_line['Cost'] = CostPerMile[temp_line['Voltage']] * temp_line['Distance']
    #     if temp_line['Voltage'] > 300:
    #         TIC[j] = temp_line['Cost']
    #         all_tielines.append(temp_line)
    #         j += 1
    
    # #try to aggregate the tie lines 
    # for i in range(len(temp_line)):
    #make each area have lines with same properties
    line = {'Capacity': 2020.0,  'B': 8467.24770417039}
    lines_cost = {}
    lines_two_end = [('Coastal', 'South'), ('Coastal', 'Northeast'), ('South', 'Northeast'), ('South', 'West'),
        ('West', 'Northeast'), ('West', 'Panhandle'), ('Northeast', 'Panhandle') ]
    for two_ends in lines_two_end:
        key = two_ends[0] + "_" + two_ends[1]
        lines_cost[key] = dist[two_ends[0], two_ends[1]] *  CostPerMile[500]
    globals()["lines_cost"] = lines_cost
          
    j = 1
    for ends in lines_two_end:
        for i in range(10):
            temp_line = {}
            temp_line['Near Area Name'] = ends[0]
            temp_line['Far Area Name'] = ends[1]
            temp_line['Capacity'] = float(line['Capacity'])
            temp_line['B'] = line['B']
            temp_line['Distance'] = dist[temp_line['Near Area Name'], temp_line['Far Area Name']]
            temp_line['Cost'] = CostPerMile[500] * temp_line['Distance'] 
            TIC[j] = temp_line['Cost']# * 0.3
            all_tielines.append(temp_line)
            j += 1


    tielines = all_tielines
    globals()["tielines"] = tielines    
    globals()["TIC"] = TIC   

    print('finished loading data')

























