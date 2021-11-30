import os
import pandas as pd
import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import spline
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from cluster import *
from scenarioTree import create_scenario_tree

plt.rcParams["font.weight"] = "bold"
plt.rcParams["axes.labelweight"] = "bold"
plt.rcParams["figure.titleweight"] = "bold"
plt.rcParams["axes.titleweight"] = "bold"

curPath = os.path.abspath(os.path.curdir)
curPath = curPath.replace("../deterministic", "")
filepath = "../data/GTEPdata_2020_2024.db"
n_stages = 5  # number od stages in the scenario tree
stages = range(1, n_stages + 1)
t_per_stage = {}
for i in range(1, n_stages + 1):
    t_per_stage[i] = [i]
scenarios = ["M"]
single_prob = {"M": 1.0}
nodes, n_stage, parent_node, children_node, prob, sc_nodes = create_scenario_tree(
    stages, scenarios, single_prob
)
rnew = ["wind-new", "pv-new", "csp-new"]
rn_r = [
    ("pv-old", "West"),
    ("pv-old", "South"),
    ("pv-new", "Northeast"),
    ("pv-new", "West"),
    ("pv-new", "Coastal"),
    ("pv-new", "South"),
    ("pv-new", "Panhandle"),
    ("csp-new", "Northeast"),
    ("csp-new", "West"),
    ("csp-new", "Coastal"),
    ("csp-new", "South"),
    ("csp-new", "Panhandle"),
    ("wind-old", "Northeast"),
    ("wind-old", "West"),
    ("wind-old", "Coastal"),
    ("wind-old", "South"),
    ("wind-old", "Panhandle"),
    ("wind-new", "Northeast"),
    ("wind-new", "West"),
    ("wind-new", "Coastal"),
    ("wind-new", "South"),
    ("wind-new", "Panhandle"),
]
th_r = [
    ("coal-st-old1", "Northeast"),
    ("coal-st-old1", "West"),
    ("coal-st-old1", "Coastal"),
    ("coal-st-old1", "South"),
    ("coal-igcc-new", "Northeast"),
    ("coal-igcc-new", "West"),
    ("coal-igcc-new", "Coastal"),
    ("coal-igcc-new", "South"),
    ("coal-igcc-new", "Panhandle"),
    ("coal-igcc-ccs-new", "Northeast"),
    ("coal-igcc-ccs-new", "West"),
    ("coal-igcc-ccs-new", "Coastal"),
    ("coal-igcc-ccs-new", "South"),
    ("coal-igcc-ccs-new", "Panhandle"),
    ("ng-ct-old", "Northeast"),
    ("ng-ct-old", "West"),
    ("ng-ct-old", "Coastal"),
    ("ng-ct-old", "South"),
    ("ng-ct-old", "Panhandle"),
    ("ng-cc-old", "Northeast"),
    ("ng-cc-old", "West"),
    ("ng-cc-old", "Coastal"),
    ("ng-cc-old", "South"),
    ("ng-st-old", "Northeast"),
    ("ng-st-old", "West"),
    ("ng-st-old", "South"),
    ("ng-cc-new", "Northeast"),
    ("ng-cc-new", "West"),
    ("ng-cc-new", "Coastal"),
    ("ng-cc-new", "South"),
    ("ng-cc-new", "Panhandle"),
    ("ng-cc-ccs-new", "Northeast"),
    ("ng-cc-ccs-new", "West"),
    ("ng-cc-ccs-new", "Coastal"),
    ("ng-cc-ccs-new", "South"),
    ("ng-cc-ccs-new", "Panhandle"),
    ("ng-ct-new", "Northeast"),
    ("ng-ct-new", "West"),
    ("ng-ct-new", "Coastal"),
    ("ng-ct-new", "South"),
    ("ng-ct-new", "Panhandle"),
    ("nuc-st-old", "Northeast"),
    ("nuc-st-old", "Coastal"),
    ("nuc-st-new", "Northeast"),
    ("nuc-st-new", "West"),
    ("nuc-st-new", "Coastal"),
    ("nuc-st-new", "South"),
    ("nuc-st-new", "Panhandle"),
]
tnew = [
    "coal-igcc-new",
    "coal-igcc-ccs-new",
    "ng-cc-new",
    "ng-cc-ccs-new",
    "ng-ct-new",
    "nuc-st-new",
]
region = ["Northeast", "West", "Coastal", "South", "Panhandle"]
storage = ["Li_ion", "Lead_acid", "Flow"]
lines = [
    "Coastal_South",
    "Coastal_Northeast",
    "South_Northeast",
    "South_West",
    "West_Northeast",
    "West_Panhandle",
    "Northeast_Panhandle",
]
investment = pd.read_csv(
    "investmentdata/5yearsinvestment_NETL_no_reserve1-366_MIP.csv",
    index_col=0,
    header=0,
).iloc[:, :]

data = investment.obj
# filter the data (domain reduction) && translate the data into cost domain
for line in lines:
    # if sum( investment.loc[:, "cost_" + line + "[" + str(t) + "]"].sum() for t in stages) > 0.1:
    new_col = sum(
        investment.loc[:, "cost_" + line + "[" + str(t) + "]"] for t in stages
    )
    new_col.name = "tcost_" + line
    data = pd.concat([data, new_col], axis=1)

for (rn, r) in rn_r:
    if rn in rnew:
        # if sum(investment.loc[:, "cost_ngb_rn[" + rn + "," + r + "," +  str(t) +"]"].sum() for t in stages) > 0.1:
        new_col = sum(
            investment.loc[:, "cost_ngb_rn[" + rn + "," + r + "," + str(t) + "]"]
            for t in stages
        )
        new_col.name = "tcost_ngb_rn[" + rn + "," + r + "]"
        data = pd.concat([data, new_col], axis=1)
    # if sum(investment.loc[:, "cost_nge_rn[" + rn + "," + r + "," +  str(t) +"]"].sum() for t in stages) > 0.1:
    new_col = sum(
        investment.loc[:, "cost_nge_rn[" + rn + "," + r + "," + str(t) + "]"]
        for t in stages
    )
    new_col.name = "tcost_nge_rn[" + rn + "," + r + "]"
    data = pd.concat([data, new_col], axis=1)

for (th, r) in th_r:
    if th in tnew:
        # if sum(investment.loc[:, "cost_ngb_th[" + th + "," + r + "," +  str(t) +"]"].sum() for t in stages) > 0.1:
        new_col = sum(
            investment.loc[:, "cost_ngb_th[" + th + "," + r + "," + str(t) + "]"]
            for t in stages
        )
        new_col.name = "tcost_ngb_th[" + th + "," + r + "]"
        data = pd.concat([data, new_col], axis=1)
    # if sum(investment.loc[:, "cost_nge_th[" + th + "," + r + "," +  str(t) + "]"].sum() for t in stages) > 0.1:
    new_col = sum(
        investment.loc[:, "cost_nge_th[" + th + "," + r + "," + str(t) + "]"]
        for t in stages
    )
    new_col.name = "tcost_nge_th[" + th + "," + r + "]"
    data = pd.concat([data, new_col], axis=1)

for j in storage:
    for r in region:
        for t in stages:
            # if sum(investment.loc[:,"cost_nsb[" + j + "," + r + "," + str(t) + "]"].sum() for t in stages) > 0.1:
            new_col = sum(
                investment.loc[:, "cost_nsb[" + j + "," + r + "," + str(t) + "]"]
                for t in stages
            )
            new_col.name = "cost_nsb[" + j + "," + r + "," + str(t) + "]"
            data = pd.concat([data, new_col], axis=1)
new_col = (
    data["tcost_ngb_th[ng-cc-ccs-new,Coastal]"]
    + data["tcost_ngb_th[ng-ct-new,Coastal]"]
    + data["tcost_ngb_th[ng-cc-new,Coastal]"]
)
new_col.name = "ng"
data = pd.concat([data, new_col], axis=1)
# plot solar, wind, natural gas, coal, storage, transmission
entries = [
    "tcost_Coastal_Northeast",
    "tcost_ngb_rn[pv-new,Coastal]",
    "tcost_ngb_rn[wind-new,Coastal]",
    "tcost_ngb_th[coal-igcc-new,Coastal]",
    "ng",
    "cost_nsb[Li_ion,Coastal,1]",
]
titles = ["Transmission lines", "PV", "Wind", "Coal", "Natural gas", "Battery"]


def makecostplot(entry, title):
    x = data[entry].to_numpy()
    fig, ax = plt.subplots(figsize=(13, 14))

    plt.scatter(np.array(range(1, 366)), x, s=100)
    if x.max() < 100:
        plt.ylim([0, 100])
    plt.xlim([1, 380])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title(title, fontsize=56)
    plt.xticks(np.arange(1, 366, 364))
    ax.set_xlabel("Days", fontsize=56)
    # ax.set_ylabel('million dollars',fontsize=)
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(40)
    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(40)
    # ax.set_aspect(aspect=0.5)
    # plt.show()
    plt.savefig(title + ".pdf", format="pdf", dpi=100)

    return 0


# for i in range(len(entries)):
#     makecostplot(entries[i], titles[i])

# perform clustering
ventries = [
    "tcost_Coastal_Northeast",
    "tcost_ngb_rn[pv-new,Coastal]",
    "tcost_ngb_rn[wind-new,Coastal]",
    "ng",
]
vtitles = ["Transmission lines", "PV", "Wind", "Natural gas"]
for_cluster = data[ventries].to_numpy()
# cluster_result = run_cluster(data=for_cluster, method="kmedoid_exact", n_clusters=3)
cluster_result = {
    "medoids": [30, 157, 284],
    "labels": [
        1,
        1,
        3,
        3,
        3,
        1,
        1,
        1,
        3,
        3,
        3,
        1,
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
        3,
        1,
        1,
        1,
        1,
        1,
        3,
        1,
        1,
        3,
        1,
        1,
        1,
        1,
        3,
        3,
        3,
        3,
        3,
        1,
        3,
        3,
        3,
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
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        3,
        1,
        1,
        1,
        1,
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
        3,
        1,
        1,
        3,
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
        3,
        1,
        3,
        1,
        1,
        3,
        1,
        3,
        3,
        1,
        3,
        1,
        1,
        3,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        3,
        1,
        1,
        1,
        3,
        3,
        1,
        3,
        3,
        3,
        3,
        1,
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
        1,
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
        3,
        3,
        2,
        2,
        2,
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
        2,
        2,
        3,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
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
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        3,
        2,
        2,
        3,
        3,
        3,
        3,
        2,
        2,
        3,
        3,
        2,
        2,
        3,
        2,
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
        3,
        3,
        3,
        3,
        3,
        3,
        2,
        3,
        2,
        3,
        3,
        3,
        3,
        1,
        3,
        3,
        3,
        3,
        1,
        1,
        3,
        3,
        3,
        1,
        1,
        3,
        1,
        1,
        3,
        3,
        1,
        1,
        3,
        3,
        3,
        1,
        1,
        1,
        1,
        1,
        3,
        3,
        3,
        1,
        1,
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
        3,
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
        3,
        1,
        1,
        3,
        1,
        3,
        3,
        3,
        3,
        3,
        1,
    ],
    "weights": [141, 65, 159],
}
colors = ["darkorchid", "darkorange", "limegreen"]


def makecostplot_cluster(entry, title, j):
    x = data[entry].to_numpy()
    fig, ax = plt.subplots(figsize=(13, 14))
    first_point = True

    x_value = []
    y_value = []
    p_color = []
    p_size = []
    p_marker = []
    for i in range(1, 366):
        if cluster_result["labels"][i - 1] == j + 1:
            x_value.append(i)
            y_value.append(x[i - 1])
            if i == cluster_result["medoids"][j]:
                p_color.append("black")
                p_marker.append("*")
                p_size.append(2000)
            else:
                p_color.append(colors[j])
                p_marker.append("o")
                p_size.append(100)

    print(x_value, y_value)
    plt.scatter(x_value, y_value, s=p_size, c=p_color)
    # plt.scatter(cluster_result['medoids'][j], x[cluster_result['medoids'][j]-1], s=1000, c='black', marker='*')
    if x.max() < 100:
        plt.ylim([0, 100])
    plt.xlim([1, 380])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title(title, fontsize=56)
    plt.xticks(np.arange(1, 366, 364))
    ax.set_xlabel("Days", fontsize=56)
    # ax.set_ylabel('million dollars',fontsize=)
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(40)
    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(40)
    # ax.set_aspect(aspect=0.5)
    # plt.show()
    plt.savefig(title + "_cluster" + str(j + 1) + ".pdf", format="pdf", dpi=100)

    return 0


for a in range(3):
    for b in range(4):
        makecostplot_cluster(ventries[b], vtitles[b], a)
