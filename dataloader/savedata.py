import os
import pandas as pd
import sqlite3 as sql 
conn = sql.connect("../data/test.db")
c = conn.cursor()
def process_param(sql_param):
    d = dict()
    for row in c.execute("SELECT * FROM {}".format(sql_param)):
        p_len = len(row)
        if p_len == 1:
            d = row[0]
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
dist = process_param("dist")    
new_gen = ['wind-new', 'pv-new', 'csp-new', 'coal-igcc-new', 'coal-igcc-ccs-new', 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new','nuc-st-new']    

d_FOC = pd.read_csv('../data/generator/fixOM.csv', index_col=0, header=0).iloc[:, :]
d_OCC = pd.read_csv('../data/generator/overnightcost.csv', index_col=0, header=0).iloc[:, :]
d_VOC = pd.read_csv('../data/generator/variableOM.csv', index_col=0, header=0).iloc[:, :]
FOC = {}
OCC = {}
VOC = {}
#ir nomimal interest rate 
ir = 0.057
n_stage = 20 
for t in range(1, 20+1):
    for g in new_gen:
        FOC[(g,t)] = float(d_FOC[g][t])
        OCC[(g,t)] = float(d_OCC[g][t])
        VOC[(g,t)] = float(d_VOC[g][t])


c.execute('''CREATE TABLE FOC(
   g CHAR(20) NOT NULL, 
   year INT,
   value FLOAT
)''')
for k in FOC:
    c.execute("""INSERT INTO  FOC (g, year, value)
                    VALUES (?, ?, ?)""",
                    (k[0], k[1], FOC[k])) 

c.execute('''CREATE TABLE VOC(
   g CHAR(20) NOT NULL, 
   year INT,
   value FLOAT
)''')
for k in VOC:
    c.execute("""INSERT INTO  VOC (g, year, value)
                    VALUES (?, ?, ?)""",
                    (k[0], k[1], VOC[k])) 

c.execute('''CREATE TABLE OCC(
   g CHAR(20) NOT NULL, 
   year INT,
   value FLOAT
)''')
for k in OCC:
    c.execute("""INSERT INTO  OCC (g, year, value)
                    VALUES (?, ?, ?)""",
                    (k[0], k[1], OCC[k])) 



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

c.execute('''CREATE TABLE storage_inv_cost(
   battery CHAR(20) NOT NULL,
   year INT,
   value FLOAT
)''')
for k in storage_inv_cost:
    c.execute("""INSERT INTO  storage_inv_cost (battery, year, value)
                    VALUES (?, ?, ?)""",
                    (k[0], k[1], storage_inv_cost[k]))                    


    # Power rating [MW]
P_min_charge = {'Li_ion': 0, 'Lead_acid': 0, 'Flow': 0}
c.execute('''CREATE TABLE P_min_charge(
   battery CHAR(20) NOT NULL,
   value FLOAT
)''')
for k in P_min_charge:
    c.execute("""INSERT INTO  P_min_charge (battery, value)
                    VALUES (?, ?)""",
                    (k[0], P_min_charge[k]))    


P_max_charge = {'Li_ion': 40, 'Lead_acid': 36, 'Flow': 2}
c.execute('''CREATE TABLE P_max_charge(
   battery CHAR(20) NOT NULL,
   value FLOAT
)''')
for k in P_max_charge:
    c.execute("""INSERT INTO  P_max_charge (battery, value)
                    VALUES (?, ?)""",
                       (k[0], P_max_charge[k])) 

P_min_discharge = {'Li_ion': 0, 'Lead_acid': 0, 'Flow': 0}
c.execute('''CREATE TABLE P_min_discharge(
   battery CHAR(20) NOT NULL,
   value FLOAT
)''')
for k in P_min_discharge:
    c.execute("""INSERT INTO  P_min_discharge (battery, value)
                    VALUES (?, ?)""",
                       (k[0], P_min_discharge[k])) 



P_max_discharge = {'Li_ion': 40, 'Lead_acid': 36, 'Flow': 2}
c.execute('''CREATE TABLE P_max_discharge(
   battery CHAR(20) NOT NULL,
   value FLOAT
)''')
for k in P_max_discharge:
    c.execute("""INSERT INTO  P_max_discharge (battery, value)
                    VALUES (?, ?)""",
                       (k[0], P_max_discharge[k])) 

# Rated energy capacity [MWh]
min_storage_cap = {'Li_ion': 0, 'Lead_acid': 0, 'Flow': 0}
c.execute('''CREATE TABLE min_storage_cap(
   battery CHAR(20) NOT NULL,
   value FLOAT
)''')
for k in min_storage_cap:
    c.execute("""INSERT INTO  min_storage_cap (battery, value)
                    VALUES (?, ?)""",
                       (k[0], min_storage_cap[k])) 



max_storage_cap = {'Li_ion': 20, 'Lead_acid': 24, 'Flow': 12}
c.execute('''CREATE TABLE max_storage_cap(
   battery CHAR(20) NOT NULL,
   value FLOAT
)''')
for k in max_storage_cap:
    c.execute("""INSERT INTO  max_storage_cap (battery, value)
                    VALUES (?, ?)""",
                       (k[0], max_storage_cap[k])) 

# Charge efficiency (fraction)
eff_rate_charge = {'Li_ion': 0.95, 'Lead_acid': 0.85, 'Flow': 0.75}
c.execute('''CREATE TABLE eff_rate_charge(
   battery CHAR(20) NOT NULL,
   value FLOAT
)''')
for k in eff_rate_charge:
    c.execute("""INSERT INTO  eff_rate_charge (battery, value)
                    VALUES (?, ?)""",
                       (k[0], eff_rate_charge[k])) 



eff_rate_discharge = {'Li_ion': 0.85, 'Lead_acid': 0.85, 'Flow': 0.75}
c.execute('''CREATE TABLE eff_rate_discharge(
   battery CHAR(20) NOT NULL,
   value FLOAT
)''')
for k in eff_rate_discharge:
    c.execute("""INSERT INTO  eff_rate_discharge (battery, value)
                    VALUES (?, ?)""",
                       (k[0], eff_rate_discharge[k])) 

# Storage lifetime (years)
storage_lifetime = {'Li_ion': 15, 'Lead_acid': 15, 'Flow': 20}
c.execute('''CREATE TABLE storage_lifetime(
   battery CHAR(20) NOT NULL,
   value FLOAT
)''')
for k in storage_lifetime:
    c.execute("""INSERT INTO  storage_lifetime (battery, value)
                    VALUES (?, ?)""",
                       (k[0], storage_lifetime[k])) 



# tielines_df = pd.read_csv('../data/tielines.csv', index_col=0, header=0).iloc[:, :]
all_tielines = []
#"Far West" "West" are both "West", "South" and "South Central" are both "South"
#"North Central" and "East" are both "Northeast"
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
B = {}
Far_end = {}
Near_end = {}
T_OCC = {}
for ends in lines_two_end:
    for i in range(10):
        temp_line = {}
        temp_line['Near Area Name'] = ends[0]
        temp_line['Far Area Name'] = ends[1]
        temp_line['Capacity'] = float(line['Capacity'])
        temp_line['B'] = line['B']
        temp_line['Distance'] = dist[temp_line['Near Area Name'], temp_line['Far Area Name']]
        temp_line['Cost'] = CostPerMile[500] * temp_line['Distance'] 
        B[j] = line['B']
        Far_end[j] = ends[1]
        Near_end[j] = ends[0]
        T_OCC[j] = temp_line['Cost'] 
        j += 1

# c.execute('''CREATE TABLE Far_end(
#    j INT,
#    value CHAR(20) NOT NULL
# )''')
# for k in Far_end:
#     c.execute("""INSERT INTO  Far_end (j value)
#                     VALUES (?, ?)""",
#                     (k, Far_end[k])) 

# c.execute('''CREATE TABLE Near_end(
#    j INT,
#    value CHAR(20) NOT NULL
# )''')
# for k in Near_end:
#     c.execute("""INSERT INTO  Near_end (j value)
#                     VALUES (?, ?)""",
#                     (k, Near_end[k])) 


# c.execute('''CREATE TABLE T_OCC(
#    j INT,
#    value CHAR(20) NOT NULL
# )''')
# for k in T_OCC:
#     c.execute("""INSERT INTO  T_OCC (j value)
#                     VALUES (?, ?)""",
#                     (k, T_OCC[k])) 











conn.commit()