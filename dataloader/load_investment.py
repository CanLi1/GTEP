import sqlite3 as sql
import os
import pandas as pd


def read_data(database_file, len_t):
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

    params = ['Qg_np', 'Ng_old', 'Ng_max', 'Qinst_UB', 'LT', 'Tremain', 'Ng_r', 'q_v',
              'Pg_min', 'Ru_max', 'Rd_max', 'f_start', 'C_start', 'frac_spin', 'frac_Qstart', 't_loss', 't_up', 'dist',
              'if_', 'ED', 'Rmin', 'hr', 'EF_CO2', 'FOC', 'VOC', 'CCm',  'LEC', 'PEN', 'tx_CO2', 'OCC',
              'RES_min', 'P_fuel', 'P_min_charge', 'P_max_charge', 'P_min_discharge', 'P_max_discharge',
              'min_storage_cap', 'max_storage_cap', 'eff_rate_charge', 'eff_rate_discharge', 'storage_lifetime']  


    for p in params:
        globals()[p] = process_param(p)


    #trim the parameters to within len_t
    d_FOC = process_param("FOC")
    d_VOC = process_param("VOC")
    d_OCC = process_param("OCC")  
    d_Qinst_UB = process_param("Qinst_UB") 
    d_Ng_r = process_param("Ng_r") 
    LT = process_param("LT")
    if_ = process_param("if_")
    d_ED = process_param("ED")
    d_Rmin = process_param("Rmin")
    d_P_fuel = process_param("P_fuel")
    d_PEN = process_param("PEN")

    storage_inv_cost = process_param("storage_inv_cost")
    conn.close()    
    FOC = {}
    DIC = {}
    VOC = {}

    #change investment cost, variable operating cost and fixed operating cost of future generators to be less than year t
    # m.FOC: 􏰄fixed operating cost of generator cluster i ($/MW)
    # m.VOC: variable O&M cost of generator cluster i ($/MWh)
    # m.DIC: discounted investment cost of generator cluster i in year t ($/MW)
    new_gen = ['wind-new', 'pv-new', 'csp-new', 'coal-igcc-new', 'coal-igcc-ccs-new', 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new','nuc-st-new']    
    ir = 0.057
    for t in range(1, len_t +1):
        for g in new_gen:
            FOC[(g,t)] = float(d_FOC[g,t])
            OCC = float(d_OCC[g,t])
            ACC = OCC * ir / (1 - (1/(1+ir)) ** LT[g]) 
            T_remain = len_t - t + 1
            DIC[(g,t)] = ACC * sum(if_[tt] for tt in range(1, len_t + 1) if (tt <= T_remain and tt <= LT[g]))
            VOC[(g,t)] = float(d_VOC[g,t])
    globals()['FOC'] = FOC 
    globals()['DIC'] = DIC
    globals()['VOC'] = VOC 

    temp_dict = {}                        
    for key in storage_inv_cost:                   
        if key[1] <= len_t:
            temp_dict[key] = storage_inv_cost[key]
    storage_inv_cost = temp_dict
    globals()["storage_inv_cost"] = storage_inv_cost

    Qinst_UB = {}
    for key in d_Qinst_UB:
        if key[1] <= len_t:
            Qinst_UB[key] = d_Qinst_UB[key]
    globals()["Qinst_UB"] = Qinst_UB

    Ng_r = {}
    for key in d_Ng_r:
        if key[2] <= len_t:
            Ng_r[key] = d_Ng_r[key]
    globals()["Ng_r"] = Ng_r

    if__ = {}
    ED = {}
    Rmin = {}
    PEN = {}
    for key in if_:
        if key <= len_t:
            if__[key] = if_[key]
            ED[key] = d_ED[key]
            Rmin[key] = d_Rmin[key]
            PEN[key] = d_PEN[key]
    globals()["if_"] = if__
    globals()["ED"] = ED 
    globals()["Rmin"] = Rmin
    globals()["PEN"] = PEN 


    P_fuel = {}
    for key in P_fuel:
        if key[1] <= len_t:
            P_fuel[key] = d_P_fuel[key]
    globals()["P_fuel"] = P_fuel


    globals()['hs'] = 1
    globals()['ir'] = 0.057
    globals()['PENc'] = 5000
    t_up['West', 'Coastal'] = 0
    t_up['Coastal', 'West'] = 0
    t_up['Coastal', 'Panhandle'] = 0
    t_up['South', 'Panhandle'] = 0
    t_up['Panhandle', 'Coastal'] = 0
    t_up['Panhandle', 'South'] = 0

    all_tielines = []

    areaMap = {'Coast':'Coastal', 'South':'South', 'South Central':'South', 'East':'Northeast', \
                'West':'West', 'Far West':'West', 'North':'Northeast', 'North Central':'Northeast'}
    CostPerMile = {115:500000, 161:600000, 230:959700, 500:1919450}
    TIC = {}
    line = {'Capacity': 2020.0,  'B': 8467.24770417039}
    lines_two_end = [('Coastal', 'South'), ('Coastal', 'Northeast'), ('South', 'Northeast'), ('South', 'West'),
        ('West', 'Northeast'), ('West', 'Panhandle'), ('Northeast', 'Panhandle') ]
    j = 1
    #life expectancy of transmission lines 
    LT_t = 80
    for ends in lines_two_end:
        for i in range(10):
            temp_line = {}
            temp_line['Near Area Name'] = ends[0]
            temp_line['Far Area Name'] = ends[1]
            temp_line['Capacity'] = float(line['Capacity'])
            temp_line['B'] = line['B']
            temp_line['Distance'] = dist[temp_line['Near Area Name'], temp_line['Far Area Name']]
            temp_line['Cost'] = CostPerMile[500] * temp_line['Distance'] 
            for t in range(1, len_t+1):
                ACC = temp_line['Cost'] * ir / (1 - (1/(1+ir)) ** LT_t) 
                T_remain = len_t - t + 1
                TIC[(j,t)] = ACC * sum(if_[tt] for tt in range(1, len_t + 1) if (tt <= T_remain and tt <= LT[g]))
            all_tielines.append(temp_line)
            j += 1
    tielines = all_tielines
    globals()["tielines"] = tielines    
    globals()["TIC"] = TIC   




