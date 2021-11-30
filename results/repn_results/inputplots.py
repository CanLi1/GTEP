import os
import pandas as pd
import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import spline
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from cluster import *

plt.rcParams["font.weight"] = "bold"
plt.rcParams["axes.labelweight"] = "bold"
plt.rcParams["figure.titleweight"] = "bold"
plt.rcParams["axes.titleweight"] = "bold"


# L_NE = pd.read_csv('../NSRDB_wind/for_cluster/L_Northeast_2012.csv', index_col=0, header=0).iloc[:, 1]
# L_W = pd.read_csv('../NSRDB_wind/for_cluster/L_West_2012.csv', index_col=0, header=0).iloc[:, 1]
L_C = pd.read_csv(
    "../NSRDB_wind/for_cluster/L_Coastal_2012.csv", index_col=0, header=0
).iloc[:, 1]
# L_S = pd.read_csv('../NSRDB_wind/for_cluster/L_South_2012.csv', index_col=0, header=0).iloc[:, 1]

# solar CSP
# CF_CSP_NE = pd.read_csv('../NSRDB_wind/for_cluster/CF_Northeast_CSP2012.csv', index_col=0, header=0
#                           ).iloc[:, 1]
# CF_CSP_W = pd.read_csv('../NSRDB_wind/for_cluster/CF_West_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
# CF_CSP_C = pd.read_csv('../NSRDB_wind/for_cluster/CF_Coastal_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
# CF_CSP_S = pd.read_csv('../NSRDB_wind/for_cluster/CF_South_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
# CF_CSP_PH = pd.read_csv('../NSRDB_wind/for_cluster/CF_Panhandle_CSP2012.csv', index_col=0, header=0
#                           ).iloc[:, 1]

# -> solar PVSAT
# CF_PV_NE = pd.read_csv('../NSRDB_wind/for_cluster/CF_Northeast_PV2012.csv', index_col=0, header=0
#                          ).iloc[:, 1]
# CF_PV_W = pd.read_csv('../NSRDB_wind/for_cluster/CF_West_PV2012.csv', index_col=0, header=0).iloc[:, 1]
CF_PV_C = pd.read_csv(
    "../NSRDB_wind/for_cluster/CF_Coastal_PV2012.csv", index_col=0, header=0
).iloc[:, 1]
# CF_PV_S = pd.read_csv('../NSRDB_wind/for_cluster/CF_South_PV2012.csv', index_col=0, header=0).iloc[:, 1]
# CF_PV_PH = pd.read_csv('../NSRDB_wind/for_cluster/CF_Panhandle_PV2012.csv', index_col=0, header=0
#                          ).iloc[:, 1]
# -> wind new (new turbines)
# CF_wind_new_NE = pd.read_csv('../NSRDB_wind/for_cluster/CF_Northeast_wind2012.csv', index_col=0, header=0
#                                ).iloc[:, 1]
# CF_wind_new_W = pd.read_csv('../NSRDB_wind/for_cluster/CF_West_wind2012.csv', index_col=0, header=0).iloc[:, 1]
CF_wind_new_C = pd.read_csv(
    "../NSRDB_wind/for_cluster/CF_Coastal_wind2012.csv", index_col=0, header=0
).iloc[:, 1]
# CF_wind_new_S = pd.read_csv('../NSRDB_wind/for_cluster/CF_South_wind2012.csv', index_col=0, header=0
#                               ).iloc[:, 1]
# CF_wind_new_PH = pd.read_csv('../NSRDB_wind/for_cluster/CF_Panhandle_wind2012.csv', index_col=0, header=0
#                                ).iloc[:, 1]


# =========plot input data =================
# PV
PV_C = CF_PV_C.to_numpy().reshape(365, 24)
x = np.array(range(1, 25))
fig, ax = plt.subplots()
for i in range(365):
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, PV_C[i], xnew)
    plt.plot(xnew, smooth, color="darkgray", linewidth=0.00001)
plt.xlim([1, 24])
plt.ylim([0, 1])
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(20)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(20)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_title("Solar PV capacity factor", fontsize=24)
# ax.set_xlabel('Time (hr)',fontsize=24)
plt.savefig("PV_raw.pdf", format="pdf", dpi=300)
# wind
wind_C = CF_wind_new_C.to_numpy().reshape(365, 24)
x = np.array(range(1, 25))
fig, ax = plt.subplots()
for i in range(365):
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, wind_C[i], xnew)
    plt.plot(xnew, smooth, color="darkgray", linewidth=0.00001)
plt.xlim([1, 24])
plt.ylim([0, 1])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(20)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(20)
ax.set_title("Wind capacity factor", fontsize=24)
# ax.set_xlabel('Time (hr)',fontsize=24)
plt.savefig("wind_raw.pdf", format="pdf", dpi=300)

# load
Load_C = L_C.multiply(0.001).to_numpy().reshape(365, 24)
x = np.array(range(1, 25))
fig, ax = plt.subplots()
for i in range(365):
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, Load_C[i], xnew)
    plt.plot(xnew, smooth, color="darkgray", linewidth=0.00001)
plt.xlim([1, 24])
# plt.ylim([0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(20)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(20)
ax.set_title("Load (GW)", fontsize=24)
# ax.set_xlabel('Time (hr)',fontsize=24)
plt.savefig("load_raw.pdf", format="pdf", dpi=300)

# ===============plot normalized data ========================
# PV (series - series.mean()).divide(np.sqrt(series.var()))
PV_C = (
    (CF_PV_C - CF_PV_C.mean())
    .divide(np.sqrt(CF_PV_C.var()))
    .to_numpy()
    .reshape(365, 24)
)
x = np.array(range(1, 25))
fig, ax = plt.subplots()
for i in range(365):
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, PV_C[i], xnew)
    plt.plot(xnew, smooth, color="darkgray", linewidth=0.00001)
plt.xlim([1, 24])

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_title("Normalized PV", fontsize=24)
# ax.set_xlabel('Time (hr)',fontsize=24)
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(20)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(20)
plt.savefig("PV_norm.pdf", format="pdf", dpi=300)
# wind
wind_C = (
    (CF_wind_new_C - CF_wind_new_C.mean())
    .divide(np.sqrt(CF_wind_new_C.var()))
    .to_numpy()
    .reshape(365, 24)
)
x = np.array(range(1, 25))
fig, ax = plt.subplots()
for i in range(365):
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, wind_C[i], xnew)
    plt.plot(xnew, smooth, color="darkgray", linewidth=0.00001)
plt.xlim([1, 24])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_title("Normalized wind", fontsize=24)
# ax.set_xlabel('Time (hr)',fontsize=24)
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(20)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(20)
plt.savefig("wind_norm.pdf", format="pdf", dpi=300)

# load
Load_C = (L_C - L_C.mean()).divide(np.sqrt(L_C.var())).to_numpy().reshape(365, 24)
x = np.array(range(1, 25))
fig, ax = plt.subplots()
for i in range(365):
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, Load_C[i], xnew)
    plt.plot(xnew, smooth, color="darkgray", linewidth=0.00001)
plt.xlim([1, 24])
# plt.ylim([0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_title("Normalized load", fontsize=24)
# ax.set_xlabel('Time (hr)',fontsize=24)
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(20)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(20)
plt.savefig("load_norm.pdf", format="pdf", dpi=300)

# perform clustering
# input_data = [L_NE, L_W, L_C, L_S, CF_CSP_NE, CF_CSP_W, CF_CSP_C, CF_CSP_S,
# CF_CSP_PH, CF_PV_NE, CF_PV_W, CF_PV_C, CF_PV_S, CF_PV_PH, CF_wind_new_NE, CF_wind_new_W, CF_wind_new_C, CF_wind_new_S, CF_wind_new_PH]
input_data = [CF_PV_C, CF_wind_new_C, L_C]
normalized_data = 0
i = 0
# =============plot clustering results=========================
for series in input_data:
    if i == 0:
        normalized_data = (series - series.mean()).divide(np.sqrt(series.var()))
    else:
        normalized_data = pd.concat(
            [normalized_data, (series - series.mean()).divide(np.sqrt(series.var()))],
            axis=1,
        )
    i += 1

for_cluster = normalized_data.to_numpy().reshape(365, 24 * 3)

# cluster_result = run_cluster(data=for_cluster, method="kmedoid_exact", n_clusters=3)
cluster_result = {
    "medoids": [267, 313, 333],
    "labels": [
        2,
        2,
        3,
        3,
        3,
        2,
        3,
        3,
        3,
        2,
        3,
        2,
        3,
        3,
        3,
        2,
        3,
        3,
        3,
        2,
        3,
        2,
        3,
        3,
        2,
        3,
        3,
        2,
        3,
        3,
        2,
        3,
        3,
        3,
        3,
        2,
        3,
        3,
        3,
        3,
        3,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        2,
        3,
        3,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        2,
        2,
        2,
        3,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        1,
        2,
        2,
        3,
        1,
        3,
        3,
        3,
        1,
        1,
        1,
        3,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        2,
        3,
        2,
        3,
        2,
        2,
        2,
        2,
        2,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        3,
        2,
        3,
        3,
        1,
        3,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        3,
        3,
        1,
        1,
        1,
        1,
        1,
        1,
        3,
        1,
        3,
        3,
        3,
        3,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        1,
        1,
        2,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        3,
        2,
        2,
        3,
        1,
        1,
        1,
        1,
        2,
        3,
        3,
        1,
        1,
        1,
        2,
        2,
        3,
        3,
        2,
        2,
        3,
        3,
        2,
        2,
        1,
        1,
        1,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        2,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        2,
        3,
        3,
        3,
        2,
        2,
        3,
        3,
        3,
        2,
        2,
        3,
        3,
        2,
        3,
        2,
        2,
        3,
        2,
        2,
        3,
        2,
    ],
    "weights": [149, 72, 144],
}
colors = ["darkorchid", "darkorange", "limegreen"]

for j in range(3):
    PV_C = (
        (CF_PV_C - CF_PV_C.mean())
        .divide(np.sqrt(CF_PV_C.var()))
        .to_numpy()
        .reshape(365, 24)
    )
    x = np.array(range(1, 25))
    fig, ax = plt.subplots()
    for i in range(365):
        if cluster_result["labels"][i] == j + 1:
            xnew = np.linspace(x.min(), x.max(), 3000)
            smooth = spline(x, PV_C[i], xnew)
            plt.plot(xnew, smooth, color=colors[j], linewidth=0.05)
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, PV_C[cluster_result["medoids"][j] - 1], xnew)
    plt.plot(xnew, smooth, color="black", linewidth=3)

    plt.xlim([1, 24])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("PV", fontsize=24)
    # ax.set_xlabel('Time (hr)',fontsize=24)
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(20)
    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(20)
    plt.savefig("PV_cluster" + str(j + 1) + ".pdf", format="pdf", dpi=300)
    # wind
    wind_C = (
        (CF_wind_new_C - CF_wind_new_C.mean())
        .divide(np.sqrt(CF_wind_new_C.var()))
        .to_numpy()
        .reshape(365, 24)
    )
    x = np.array(range(1, 25))
    fig, ax = plt.subplots()
    for i in range(365):
        if cluster_result["labels"][i] == j + 1:
            xnew = np.linspace(x.min(), x.max(), 3000)
            smooth = spline(x, wind_C[i], xnew)
            plt.plot(xnew, smooth, color=colors[j], linewidth=0.05)
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, wind_C[cluster_result["medoids"][j] - 1], xnew)
    plt.plot(xnew, smooth, color="black", linewidth=3)
    plt.xlim([1, 24])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("Wind", fontsize=24)
    # ax.set_xlabel('Time (hr)',fontsize=24)
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(20)
    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(20)
    plt.savefig("wind_cluster" + str(j + 1) + ".pdf", format="pdf", dpi=300)

    # load
    Load_C = (L_C - L_C.mean()).divide(np.sqrt(L_C.var())).to_numpy().reshape(365, 24)
    x = np.array(range(1, 25))
    fig, ax = plt.subplots()
    for i in range(365):
        if cluster_result["labels"][i] == j + 1:
            xnew = np.linspace(x.min(), x.max(), 3000)
            smooth = spline(x, Load_C[i], xnew)
            plt.plot(xnew, smooth, color=colors[j], linewidth=0.05)
    xnew = np.linspace(x.min(), x.max(), 3000)
    smooth = spline(x, Load_C[cluster_result["medoids"][j] - 1], xnew)
    plt.plot(xnew, smooth, color="black", linewidth=3)
    plt.xlim([1, 24])
    # plt.ylim([0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("Load", fontsize=24)
    # ax.set_xlabel('Time (hr)',fontsize=24)
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(20)
    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(20)
    plt.savefig("load_cluster" + str(j + 1) + ".pdf", format="pdf", dpi=300)
