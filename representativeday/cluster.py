import pandas as pd 
import csv 
import numpy as np 
#preprocess
def load_cost_data(config):
    n_stages = config.time_horizon
    stages = range(1, n_stages + 1)
    rnew = ['wind-new', 'pv-new', 'csp-new']
    rn_r = [('pv-old', 'West'), ('pv-old', 'South'), ('pv-new', 'Northeast'), ('pv-new', 'West'), ('pv-new', 'Coastal'), ('pv-new', 'South'), ('pv-new', 'Panhandle'), ('csp-new', 'Northeast'), ('csp-new', 'West'), ('csp-new', 'Coastal'), ('csp-new', 'South'), ('csp-new', 'Panhandle'), ('wind-old', 'Northeast'), ('wind-old', 'West'), ('wind-old', 'Coastal'), ('wind-old', 'South'), ('wind-old', 'Panhandle'), ('wind-new', 'Northeast'), ('wind-new', 'West'), ('wind-new', 'Coastal'), ('wind-new', 'South'), ('wind-new', 'Panhandle')]
    th_r = [('coal-st-old1', 'Northeast'), ('coal-st-old1', 'West'), ('coal-st-old1', 'Coastal'), ('coal-st-old1', 'South'), ('coal-igcc-new', 'Northeast'), ('coal-igcc-new', 'West'), ('coal-igcc-new', 'Coastal'), ('coal-igcc-new', 'South'), ('coal-igcc-new', 'Panhandle'), ('coal-igcc-ccs-new', 'Northeast'), ('coal-igcc-ccs-new', 'West'), ('coal-igcc-ccs-new', 'Coastal'), ('coal-igcc-ccs-new', 'South'), ('coal-igcc-ccs-new', 'Panhandle'), ('ng-ct-old', 'Northeast'), ('ng-ct-old', 'West'), ('ng-ct-old', 'Coastal'), ('ng-ct-old', 'South'), ('ng-ct-old', 'Panhandle'), ('ng-cc-old', 'Northeast'), ('ng-cc-old', 'West'), ('ng-cc-old', 'Coastal'), ('ng-cc-old', 'South'), ('ng-st-old', 'Northeast'), ('ng-st-old', 'West'), ('ng-st-old', 'South'), ('ng-cc-new', 'Northeast'), ('ng-cc-new', 'West'), ('ng-cc-new', 'Coastal'), ('ng-cc-new', 'South'), ('ng-cc-new', 'Panhandle'), ('ng-cc-ccs-new', 'Northeast'), ('ng-cc-ccs-new', 'West'), ('ng-cc-ccs-new', 'Coastal'), ('ng-cc-ccs-new', 'South'), ('ng-cc-ccs-new', 'Panhandle'), ('ng-ct-new', 'Northeast'), ('ng-ct-new', 'West'), ('ng-ct-new', 'Coastal'), ('ng-ct-new', 'South'), ('ng-ct-new', 'Panhandle'), ('nuc-st-old', 'Northeast'), ('nuc-st-old', 'Coastal'), ('nuc-st-new', 'Northeast'), ('nuc-st-new', 'West'), ('nuc-st-new', 'Coastal'), ('nuc-st-new', 'South'), ('nuc-st-new', 'Panhandle')]
    tnew = ['coal-igcc-new', 'coal-igcc-ccs-new', 'ng-cc-new','ng-cc-ccs-new', 'ng-ct-new','nuc-st-new']
    region = ['Northeast', 'West', 'Coastal', 'South', 'Panhandle']
    storage = ['Li_ion', 'Lead_acid', 'Flow']
    lines = ["Coastal_South", "Coastal_Northeast", "South_Northeast", "South_West", "West_Northeast", "West_Panhandle", "Northeast_Panhandle"]    
    investment = pd.read_csv("5yearsinvestment_NETL_no_reserve1-366_MIP.csv", index_col=0, header=0).iloc[:, :]
    data = investment.obj 
    #filter the data (domain reduction) && translate the data into cost domain
    for line in lines:
        if sum( investment.loc[:, "cost_" + line + "[" + str(t) + "]"].sum() for t in stages) > 0.1:
            new_col = sum( investment.loc[:, "cost_" + line + "[" + str(t) + "]"] for t in stages)
            new_col.name = "tcost_" +  line 
            data = pd.concat([data, new_col], axis=1)

    for (rn, r) in rn_r:
        if rn in rnew:
            if sum(investment.loc[:, "cost_ngb_rn[" + rn + "," + r + "," +  str(t) +"]"].sum() for t in stages) > 0.1:
                new_col = sum(investment.loc[:, "cost_ngb_rn[" + rn + "," + r + "," +  str(t) +"]"] for t in stages)
                new_col.name = "tcost_ngb_rn[" + rn + "," + r + "]"
                data = pd.concat([data, new_col], axis=1)
        if sum(investment.loc[:, "cost_nge_rn[" + rn + "," + r + "," +  str(t) +"]"].sum() for t in stages) > 0.1:
            new_col = sum(investment.loc[:, "cost_nge_rn[" + rn + "," + r + "," +  str(t) +"]"] for t in stages)
            new_col.name = "tcost_nge_rn[" + rn + "," + r + "]"
            data = pd.concat([data, new_col], axis=1)               

    for (th, r) in th_r:
        if th in tnew:
            if sum(investment.loc[:, "cost_ngb_th[" + th + "," + r + "," +  str(t) +"]"].sum() for t in stages) > 0.1:
                new_col = sum(investment.loc[:, "cost_ngb_th[" + th + "," + r + "," +  str(t) +"]"] for t in stages)
                new_col.name = "tcost_ngb_th[" + th + "," + r + "]"
                data = pd.concat([data, new_col], axis=1)
        if sum(investment.loc[:, "cost_nge_th[" + th + "," + r + "," +  str(t) + "]"].sum() for t in stages) > 0.1:
            new_col = sum(investment.loc[:, "cost_nge_th[" + th + "," + r + "," +  str(t) + "]"] for t in stages)
            new_col.name = "tcost_nge_th[" + th + "," + r + "]"
            data = pd.concat([data, new_col], axis=1)   

    for j in storage:
        for r in region:
            if sum(investment.loc[:,"cost_nsb[" + j + "," + r + "," + str(t) + "]"].sum() for t in stages) > 0.1:
                new_col = sum(investment.loc[:,"cost_nsb[" + j + "," + r + "," + str(t) + "]"] for t in stages)
                new_col.name = "cost_nsb[" + j + "," + r + "," + str(t) + "]"
                data = pd.concat([data, new_col], axis=1)

    return data.drop(["obj"], axis=1).to_numpy(), data.obj.to_numpy()


def load_input_data(config):
    #load 
    L_NE = pd.read_csv('data/NSRDB_wind/for_cluster/L_Northeast_2012.csv', index_col=0, header=0).iloc[:, 1]
    L_W = pd.read_csv('data/NSRDB_wind/for_cluster/L_West_2012.csv', index_col=0, header=0).iloc[:, 1]
    L_C = pd.read_csv('data/NSRDB_wind/for_cluster/L_Coastal_2012.csv', index_col=0, header=0).iloc[:, 1]
    L_S = pd.read_csv('data/NSRDB_wind/for_cluster/L_South_2012.csv', index_col=0, header=0).iloc[:, 1]

    #solar CSP
    CF_CSP_NE = pd.read_csv('data/NSRDB_wind/for_cluster/CF_Northeast_CSP2012.csv', index_col=0, header=0
                              ).iloc[:, 1]
    CF_CSP_W = pd.read_csv('data/NSRDB_wind/for_cluster/CF_West_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
    CF_CSP_C = pd.read_csv('data/NSRDB_wind/for_cluster/CF_Coastal_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
    CF_CSP_S = pd.read_csv('data/NSRDB_wind/for_cluster/CF_South_CSP2012.csv', index_col=0, header=0).iloc[:, 1]
    CF_CSP_PH = pd.read_csv('data/NSRDB_wind/for_cluster/CF_Panhandle_CSP2012.csv', index_col=0, header=0
                              ).iloc[:, 1]

    # -> solar PVSAT
    CF_PV_NE = pd.read_csv('data/NSRDB_wind/for_cluster/CF_Northeast_PV2012.csv', index_col=0, header=0
                             ).iloc[:, 1]
    CF_PV_W = pd.read_csv('data/NSRDB_wind/for_cluster/CF_West_PV2012.csv', index_col=0, header=0).iloc[:, 1]
    CF_PV_C = pd.read_csv('data/NSRDB_wind/for_cluster/CF_Coastal_PV2012.csv', index_col=0, header=0).iloc[:, 1]
    CF_PV_S = pd.read_csv('data/NSRDB_wind/for_cluster/CF_South_PV2012.csv', index_col=0, header=0).iloc[:, 1]
    CF_PV_PH = pd.read_csv('data/NSRDB_wind/for_cluster/CF_Panhandle_PV2012.csv', index_col=0, header=0
                             ).iloc[:, 1]
    # -> wind new (new turbines)
    CF_wind_new_NE = pd.read_csv('data/NSRDB_wind/for_cluster/CF_Northeast_wind2012.csv', index_col=0, header=0
                                   ).iloc[:, 1]
    CF_wind_new_W = pd.read_csv('data/NSRDB_wind/for_cluster/CF_West_wind2012.csv', index_col=0, header=0).iloc[:, 1]
    CF_wind_new_C = pd.read_csv('data/NSRDB_wind/for_cluster/CF_Coastal_wind2012.csv', index_col=0, header=0
                                  ).iloc[:, 1]
    CF_wind_new_S = pd.read_csv('data/NSRDB_wind/for_cluster/CF_South_wind2012.csv', index_col=0, header=0
                                  ).iloc[:, 1]
    CF_wind_new_PH = pd.read_csv('data/NSRDB_wind/for_cluster/CF_Panhandle_wind2012.csv', index_col=0, header=0
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


def run_cluster(data, config, method="kmedoid_exact", n_clusters=10):  
    
    from sklearn.cluster import KMeans
    if method == "kmedoid_exact":
        from representativeday.kmedoid_exact import kmedoid_mip 
        result = kmedoid_mip(data, n_clusters, 0.001, config)
        return result
    labels = []
    indices = []
    if method == "kmedoid":
        from sklearn_extra.cluster import KMedoids
        km = KMedoids(n_clusters=n_clusters, init='k-medoids++',max_iter=300000)
        km.fit_predict(data)
        labels = km.labels_
        indices = km.medoid_indices_
    if method == "kmeans":
        km = KMeans(n_clusters=n_clusters, max_iter=300000, n_init=100, random_state=0)
        km.fit_predict(data)
        labels = km.labels_
        return {"labels":list(labels+1)}     
    if method == "kmeans_exact":
        from representativeday.kmeans_exact import kmeans_miqcp
        labels = kmeans_miqcp(data, n_clusters, 0.001, config)
        return {"labels":labels+1}     
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

    return {"medoids":list(indices+1), "weights":list(sorted_count), "labels":list(labels+1)}

def select_extreme_days(cluster_results, cluster_obj=[], n=1, method="highest_cost", infeasible_days=[], load_shedding_cost=[], clustering_method="kmedoid"):
    if method == "highest_cost":
        days = cluster_obj.argsort()[-n:] + 1
        #adjust weight of the cluster where the representative days is in 
    if method == "highest_cost_infeasible":
        days =  []#days selected
        if len(infeasible_days) <= n:
            days = infeasible_days
        else:
            days_obj = []#the cost of infeasible days
            for day in infeasible_days:
                days_obj.append(cluster_obj[day-1])         
            days_obj = np.array(days_obj)
            for index in days_obj.argsort()[-n:]:
                days.append(infeasible_days[index])

    if method == "load_shedding_cost": #select the infeasible days with largest load shedding cost 
        days =  []#days selected
        if len(infeasible_days) <= n:
            days = infeasible_days
        else:       
            load_shedding_cost = np.array(load_shedding_cost)
            for index in load_shedding_cost.argsort()[-n:]:
                days.append(infeasible_days[index])
                                
    num_days = len(np.unique(cluster_results["labels"]))
    i = 1
    for day in days:
        day_label = cluster_results["labels"][day-1]
        if len(np.where(cluster_results["labels"] == day_label)[0]) == 1:
            raise NameError('the' + method + ' day already has weight 1')        
        if clustering_method == "kmedoid" or clustering_method == "kmedoid_exact":
            cluster_results['weights'][cluster_results['labels'][day-1]-1] -= 1
            cluster_results['medoids'].append(day)
            cluster_results['weights'].append(1)
        cluster_results["labels"][day-1] = num_days + i 
        i += 1

    return cluster_results 

