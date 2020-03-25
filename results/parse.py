import pandas as pd
import os 
import csv


name = "days_mediumtax_fullcostlines_improved.csv"
with open("sensitivity_repndays.csv", 'w', newline='') as results_file:
	fieldnames = ["day", "coal", "nuclear", "natural_gas", "wind", "solar", "transmission","obj"]
	writer = csv.DictWriter(results_file, fieldnames=fieldnames)
	writer.writeheader()	
	for d in range(4,16):
		result = pd.read_csv(str(d) + name, index_col=0, header=0).iloc[:, :]
		coal = result.coal_capacity[19]
		nuclear = result.nuclear_capacity[19]
		natural_gas = result.natural_gas_capacity[19]
		wind = result.wind_capacity[19]
		solar = result.solar_capacity[19]
		transmission = result.transmission_line_cost[0:20].sum()
		writer.writerow({"day":d, "coal":coal, "nuclear":nuclear, "natural_gas":natural_gas, "wind":wind, "solar":solar, "transmission":transmission, "obj":result.iat[-1,0]})	


