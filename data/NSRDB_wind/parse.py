import pandas as pd
import os 
import csv

regions = ['Northeast', 'West', 'Coastal', 'South', 'Panhandle']
np_CSP = 103.5
np_PV = 4.693
np_wind = 1500 
fieldnames = ["time", "year", "ercot"]
power_curve =[0,0,0,0,0,0,0,0,0,0,0,0,0,0,13.98,45.74,114.19,145.94,177.69,211.89,248.54,285.18,324.28,363.37,409.81,463.58,522.24,588.24,659.14,727.58,800.94,876.73,947.62,1060,1130,1200,1260,1310,1350,1390,1420,1450,1470,1490,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500]
for r in regions:
	PV = pd.read_csv(r + "/" + r + "_PV2012.csv", index_col=0, header=0).iloc[:, :1]
	with open('for_cluster/' + "CF_" + r + "_PV2012.csv", 'w', newline='') as results_file:
		writer = csv.DictWriter(results_file, fieldnames=fieldnames)
		writer.writeheader()
		i = 0
		for row in PV.index.values:
			if ':30' not in row:
				writer.writerow({"time":row, "year":2012, "ercot":max(0,min(1,PV.iat[i,0]/np_PV))})
			i +=1
		 
	CSP = pd.read_csv(r + "/" + r + "_CSP2012.csv", index_col=0, header=0).iloc[:, :1]
	with open('for_cluster/' + "CF_" + r + "_CSP2012.csv", 'w', newline='') as results_file:
		writer = csv.DictWriter(results_file, fieldnames=fieldnames)
		writer.writeheader()
		i = 0
		for row in CSP.index.values:
			writer.writerow({"time":row, "year":2012, "ercot":max(0,min(1, CSP.iat[i,0]/np_CSP))})
			i +=1	

	wind = pd.read_csv(r + "/" + r + "_windspeed2012.csv", index_col=0, header=0).iloc[:, :7]
	with open('for_cluster/' + "CF_" + r + "_wind2012.csv", 'w', newline='') as results_file:
		writer = csv.DictWriter(results_file, fieldnames=fieldnames)
		writer.writeheader()
		i = 0
		for row in CSP.index.values:
			pos = round(wind.iat[i*12,6]/0.25)
			pos = int(pos)
			if pos >= len(power_curve) - 1:
				pos = len(power_curve) - 1
			writer.writerow({"time":row, "year":2012, "ercot":max(0,min(1, power_curve[pos]/np_wind))})
			i +=1	


