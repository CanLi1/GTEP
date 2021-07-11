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

    params = ['L_max', 'Qg_np', 'Ng_old', 'Ng_max', 'Qinst_UB', 'LT', 'Tremain', 'Ng_r', 'q_v',
              'Pg_min', 'Ru_max', 'Rd_max', 'f_start', 'C_start', 'frac_spin', 'frac_Qstart', 't_loss', 't_up', 'dist',
              'if_', 'ED', 'Rmin', 'hr', 'EF_CO2', 'FOC', 'VOC', 'CCm',  'LEC', 'PEN', 'tx_CO2', 'OCC'
              'RES_min', 'P_fuel']  


    for p in params:
        globals()[p] = process_param(p)

    conn.close()

    d_FOC = process_param("FOC")
    d_VOC = process_param("VOC")
    d_OCC = process_param("OCC")    
    LT = process_param("LT")
    if_ = process_param("if_")
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


    temp_dict = {}                        
    for key in storage_inv_cost:                   
        if key[1] <= time:
            temp_dict[key] = storage_inv_cost[key]
    storage_inv_cost = temp_dict
    globals()["storage_inv_cost"] = storage_inv_cost


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
            for t in range(1, len(n_stage)+1):
                ACC = temp_line['Cost'] * ir / (1 - (1/(1+ir)) ** LT_t) 
                T_remain = len(n_stage) - t + 1
                TIC[(j,t)] = ACC * sum(if_[tt] for tt in range(1, len(n_stage) + 1) if (tt <= T_remain and tt <= LT[g]))
            all_tielines.append(temp_line)
            j += 1
    tielines = all_tielines
    globals()["tielines"] = tielines    
    globals()["TIC"] = TIC   




