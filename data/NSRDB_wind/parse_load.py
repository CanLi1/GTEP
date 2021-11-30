import pandas as pd
import os
import csv

CSP = pd.read_csv("West/West_CSP2012.csv", index_col=0, header=0).iloc[:, :1]
load2012 = pd.read_csv("load/load_2012.csv", index_col=0, header=0).iloc[:, :5]
load2019 = pd.read_csv("load/load_2019.csv", index_col=0, header=0).iloc[:, :5]
fieldnames = ["time", "year", "ercot"]
regions = ["Northeast", "Coastal", "West", "South"]
for r in regions:
    scaled_load = load2012[r].multiply(load2019[r].sum() / load2012[r].sum())
    with open("for_cluster/" + "L_" + r + "_2012.csv", "w", newline="") as results_file:
        writer = csv.DictWriter(results_file, fieldnames=fieldnames)
        writer.writeheader()
        i = 0
        for row in CSP.index.values:
            writer.writerow({"time": row, "year": 2012, "ercot": scaled_load[i]})
            i += 1
