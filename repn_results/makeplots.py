import os
import pandas as pd
import csv
import numpy as np 
import matplotlib.pyplot as plt
from scipy.interpolate import spline

L_NE = pd.read_csv('../NSRDB_wind/for_cluster/L_Northeast_2012.csv', index_col=0, header=0).iloc[:, 1]
L_W = pd.read_csv('../NSRDB_wind/for_cluster/L_West_2012.csv', index_col=0, header=0).iloc[:, 1]
L_C = pd.read_csv('../NSRDB_wind/for_cluster/L_Coastal_2012.csv', index_col=0, header=0).iloc[:, 1]
L_S = pd.read_csv('../NSRDB_wind/for_cluster/L_South_2012.csv', index_col=0, header=0).iloc[:, 1]

#solar CSP
CF_CSP_NE = pd.read_csv('../NSRDB_wind/for_cluster/CF_Northeast_CSP2012.csv', index_col=0, header=0
                          ).iloc[:, 1]
CF_CSP_W = pd.read_csv('../NSRDB_wind/for_cluster/CF_West_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
CF_CSP_C = pd.read_csv('../NSRDB_wind/for_cluster/CF_Coastal_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
CF_CSP_S = pd.read_csv('../NSRDB_wind/for_cluster/CF_South_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
CF_CSP_PH = pd.read_csv('../NSRDB_wind/for_cluster/CF_Panhandle_CSP2012.csv', index_col=0, header=0
                          ).iloc[:, 1]

# -> solar PVSAT
CF_PV_NE = pd.read_csv('../NSRDB_wind/for_cluster/CF_Northeast_PV2012.csv', index_col=0, header=0
                         ).iloc[:, 1]
CF_PV_W = pd.read_csv('../NSRDB_wind/for_cluster/CF_West_PV2012.csv', index_col=0, header=0).iloc[:, 1]
CF_PV_C = pd.read_csv('../NSRDB_wind/for_cluster/CF_Coastal_PV2012.csv', index_col=0, header=0).iloc[:, 1]
CF_PV_S = pd.read_csv('../NSRDB_wind/for_cluster/CF_South_PV2012.csv', index_col=0, header=0).iloc[:, 1]
CF_PV_PH = pd.read_csv('../NSRDB_wind/for_cluster/CF_Panhandle_PV2012.csv', index_col=0, header=0
                         ).iloc[:, 1]
# -> wind new (new turbines)
CF_wind_new_NE = pd.read_csv('../NSRDB_wind/for_cluster/CF_Northeast_wind2012.csv', index_col=0, header=0
                               ).iloc[:, 1]
CF_wind_new_W = pd.read_csv('../NSRDB_wind/for_cluster/CF_West_wind2012.csv', index_col=0, header=0).iloc[:, 1]
CF_wind_new_C = pd.read_csv('../NSRDB_wind/for_cluster/CF_Coastal_wind2012.csv', index_col=0, header=0
                              ).iloc[:, 1]
CF_wind_new_S = pd.read_csv('../NSRDB_wind/for_cluster/CF_South_wind2012.csv', index_col=0, header=0
                              ).iloc[:, 1]
CF_wind_new_PH = pd.read_csv('../NSRDB_wind/for_cluster/CF_Panhandle_wind2012.csv', index_col=0, header=0
                               ).iloc[:, 1]


input_data = [L_NE, L_W, L_C, L_S, CF_CSP_NE, CF_CSP_W, CF_CSP_C, CF_CSP_S, 
CF_CSP_PH, CF_PV_NE, CF_PV_W, CF_PV_C, CF_PV_S, CF_PV_PH, CF_wind_new_NE, CF_wind_new_W, CF_wind_new_C, CF_wind_new_S, CF_wind_new_PH]
normalized_data = 0

#=========plot input data =================
#PV
PV_C = CF_PV_C.to_numpy().reshape(365,24)
x = np.array(range(1,25))
fig, ax = plt.subplots()
for i in range(365):
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, PV_C[i], xnew)
    plt.plot(xnew, smooth, color="darkgray", linewidth=0.1)
plt.xlim([1, 24])
plt.ylim([0,1])
ax.set_ylabel('Solar PV capacity factor',fontsize=20)
ax.set_xlabel('Time (hr)',fontsize=20)
plt.savefig("PV_raw.pdf", dpi=150)
#wind
wind_C = CF_wind_new_C.to_numpy().reshape(365,24)
x = np.array(range(1,25))
fig, ax = plt.subplots()
for i in range(365):
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, wind_C[i], xnew)
    plt.plot(xnew, smooth, color="darkgray", linewidth=0.1)
plt.xlim([1, 24])
plt.ylim([0,1])
ax.set_ylabel('Wind capacity factor',fontsize=20)
ax.set_xlabel('Time (hr)',fontsize=20)
plt.savefig("wind_raw.pdf", dpi=150)

#load
Load_C = L_C.multiply(0.001).to_numpy().reshape(365,24)
x = np.array(range(1,25))
fig, ax = plt.subplots()
for i in range(365):
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, Load_C[i], xnew)
    plt.plot(xnew, smooth, color="darkgray", linewidth=0.1)
plt.xlim([1, 24])
# plt.ylim([0)
ax.set_ylabel('Load (GW)',fontsize=20)
ax.set_xlabel('Time (hr)',fontsize=20)
plt.savefig("load_raw.pdf", dpi=150)

#===============plot normalized data ========================
# i = 0
# for series in input_data:
#     if i == 0:
#         normalized_data = (series - series.mean()).divide(np.sqrt(series.var()))
#     else:
#         normalized_data = pd.concat([normalized_data, (series - series.mean()).divide(np.sqrt(series.var()))], axis=1)
#     i+= 1


