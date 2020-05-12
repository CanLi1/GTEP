import os
import pandas as pd
import deterministic.readData_single as readData_single
import csv
import numpy as np 

from scenarioTree import create_scenario_tree


#preprocess
def load_cost_data(year=5):
	curPath = os.path.abspath(os.path.curdir)
	curPath = curPath.replace('/deterministic', '')
	filepath = 'data/GTEPdata_2020_2024.db'
	n_stages = 5  # number od stages in the scenario tree
	stages = range(1, n_stages + 1)
	t_per_stage = {}
	for i in range(1, n_stages+1):
		t_per_stage[i] = [i]
	stages = range(1, n_stages + 1)
	scenarios = ['M']
	single_prob = {'M': 1.0}	
	nodes, n_stage, parent_node, children_node, prob, sc_nodes = create_scenario_tree(stages, scenarios, single_prob)	
	readData_single.read_data(filepath, curPath, stages, n_stage, t_per_stage, 1)
	rnew = ['wind-new', 'pv-new', 'csp-new']
	tnew = ['coal-igcc-new', 'coal-igcc-ccs-new', 'ng-cc-new','ng-cc-ccs-new', 'ng-ct-new','nuc-st-new']
	region = ['Northeast', 'West', 'Coastal', 'South', 'Panhandle']
	storage = ['Li_ion', 'Lead_acid', 'Flow']
	lines = ["Coastal_South", "Coastal_Northeast", "South_Northeast", "South_West", "West_Northeast", "West_Panhandle", "Northeast_Panhandle"]    
	investment = pd.read_csv("repn_results/5yearsinvestment1-366.csv", index_col=0, header=0).iloc[:, :]

	#filter the data (domain reduction) && translate the data into cost domain
	data = investment.obj
	for line in lines:
		if investment.loc[:, line + "[5]"].sum()> 0.1:
			data = pd.concat([data, investment.loc[:, line + "[5]"].multiply(readData_single.lines_cost[line] * 10 ** (-9))], axis=1)

	for rn in rnew:
		for r in region:
			key = "ngo_rn[" + rn + "," + r + ",5]"
			if investment.loc[:, key].sum() > 0.1:
				data = pd.concat([data, investment.loc[:, key].multiply(readData_single.DIC[rn, 5] * readData_single.CCm[rn] * readData_single.Qg_np[rn, r]* 10 ** (-9))], axis=1)

	for th in tnew:
		for r in region:
			key = "ngo_th[" + th + "," + r + ",5]"
			if investment.loc[:,key].sum() > 0.1:
				data = pd.concat([data, investment.loc[:, key].multiply(readData_single.DIC[th, 5] * readData_single.CCm[th] * readData_single.Qg_np[th, r]* 10 ** (-9))], axis=1)			
	for j in storage:
		for r in region:
			key = "nso[" + j + "," + r + ",5]"
			if investment.loc[:,key].sum() > 0.1:
				data = pd.concat([data, investment.loc[:, key].multiply(readData_single.storage_inv_cost[j, 5] * readData_single.max_storage_cap[j] * 10 ** (-9))], axis=1)

	return data.drop(["obj"], axis=1).to_numpy(), data.obj.to_numpy()


def load_input_data():
	#load 
	L_NE = pd.read_csv('NSRDB_wind/for_cluster/L_Northeast_2012.csv', index_col=0, header=0).iloc[:, 1]
	L_W = pd.read_csv('NSRDB_wind/for_cluster/L_West_2012.csv', index_col=0, header=0).iloc[:, 1]
	L_C = pd.read_csv('NSRDB_wind/for_cluster/L_Coastal_2012.csv', index_col=0, header=0).iloc[:, 1]
	L_S = pd.read_csv('NSRDB_wind/for_cluster/L_South_2012.csv', index_col=0, header=0).iloc[:, 1]

	#solar CSP
	CF_CSP_NE = pd.read_csv('NSRDB_wind/for_cluster/CF_Northeast_CSP2012.csv', index_col=0, header=0
	                          ).iloc[:, 1]
	CF_CSP_W = pd.read_csv('NSRDB_wind/for_cluster/CF_West_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
	CF_CSP_C = pd.read_csv('NSRDB_wind/for_cluster/CF_Coastal_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
	CF_CSP_S = pd.read_csv('NSRDB_wind/for_cluster/CF_South_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
	CF_CSP_PH = pd.read_csv('NSRDB_wind/for_cluster/CF_Panhandle_CSP2012.csv', index_col=0, header=0
	                          ).iloc[:, 1]

	# -> solar PVSAT
	CF_PV_NE = pd.read_csv('NSRDB_wind/for_cluster/CF_Northeast_PV2012.csv', index_col=0, header=0
	                         ).iloc[:, 1]
	CF_PV_W = pd.read_csv('NSRDB_wind/for_cluster/CF_West_PV2012.csv', index_col=0, header=0).iloc[:, 1]
	CF_PV_C = pd.read_csv('NSRDB_wind/for_cluster/CF_Coastal_PV2012.csv', index_col=0, header=0).iloc[:, 1]
	CF_PV_S = pd.read_csv('NSRDB_wind/for_cluster/CF_South_PV2012.csv', index_col=0, header=0).iloc[:, 1]
	CF_PV_PH = pd.read_csv('NSRDB_wind/for_cluster/CF_Panhandle_PV2012.csv', index_col=0, header=0
	                         ).iloc[:, 1]
	# -> wind new (new turbines)
	CF_wind_new_NE = pd.read_csv('NSRDB_wind/for_cluster/CF_Northeast_wind2012.csv', index_col=0, header=0
	                               ).iloc[:, 1]
	CF_wind_new_W = pd.read_csv('NSRDB_wind/for_cluster/CF_West_wind2012.csv', index_col=0, header=0).iloc[:, 1]
	CF_wind_new_C = pd.read_csv('NSRDB_wind/for_cluster/CF_Coastal_wind2012.csv', index_col=0, header=0
	                              ).iloc[:, 1]
	CF_wind_new_S = pd.read_csv('NSRDB_wind/for_cluster/CF_South_wind2012.csv', index_col=0, header=0
	                              ).iloc[:, 1]
	CF_wind_new_PH = pd.read_csv('NSRDB_wind/for_cluster/CF_Panhandle_wind2012.csv', index_col=0, header=0
                                   ).iloc[:, 1]
	input_data = [L_NE, L_W, L_C, L_S, CF_CSP_NE, CF_CSP_W, CF_CSP_C, CF_CSP_S, 
	CF_CSP_PH, CF_PV_NE, CF_PV_W, CF_PV_C, CF_PV_S, CF_PV_PH, CF_wind_new_NE, CF_wind_new_W, CF_wind_new_C, CF_wind_new_S, CF_wind_new_PH]
	normalized_data = 0
	i = 0
	for series in input_data:
		if i == 0:
			normalized_data = (series - series.mean()).divide(np.sqrt(series.var()))
		else:
			normalized_data = pd.concat([normalized_data, (series - series.mean()).divide(np.sqrt(series.var()))], axis=1)
		i+= 1
	return normalized_data.to_numpy().reshape(365, 24*19)	


def run_cluster(data, method="kmedoid_exact", n_clusters=10):

	
	from sklearn.cluster import KMeans
	if method == "kmedoid_exact":
		from kmedoid_exact import kmedoid_mip 
		result = kmedoid_mip(data, n_clusters, 0.001)
		return result
	labels = []
	indices = []
	if method == "kmedoid":
		from sklearn_extra.cluster import KMedoids
		km = KMedoids(n_clusters=n_clusters, init='k-medoids++',max_iter=300000)
		km.fit_predict(data)
		labels = km.labels_
		indices = km.medoid_indices_
	# if method == "kmeans":
	count = [0] * n_clusters
	for s in labels:
		count[s] += 1
	temp_count = {}
	for i in range(n_clusters):
		temp_count[indices[i]] = count[i]
	indices.sort()
	sorted_count = [0] * n_clusters
	for i in range(n_clusters):
		sorted_count[i] = temp_count[indices[i]]

	return {"medoids":indices+1, "weights":sorted_count, "labels":labels+1}

def select_extreme_days_cost(obj, cluster_results, n=1, method="highest_cost"):
	if method == "highest_cost":
		days = obj.argsort()[-n:] + 1
		#adjust weight of the cluster where the representative days is in 
		for day in days:
			cluster_results['weights'][cluster_results['labels'][day-1]-1] -= 1
			cluster_results['medoids'].append(day)
			cluster_results['weights'].append(1)

		return cluster_results 



# km = KMedoids(n_clusters=10, init='k-medoids++',max_iter=300000)
# km = KMedoids(n_clusters=10, init='random',max_iter=300000,random_state=0)

# label_km = km.fit_predict(data.to_numpy())















