__author__ = "Can Li"
# Representative days selction algorithm

from representativeday.cluster import *
def select_repn_days(config):
    if config.repn_day_method == "cost":
        data, cluster_obj = load_cost_data(config)
        clustering_result = run_cluster(data=data, config = config, method=config.clustering_algorithm, n_clusters=config.num_repn_days)
    elif config.repn_day_method == "input":
        data = load_input_data(config)
        clustering_result = run_cluster(data=data, config = config, method=config.clustering_algorithm, n_clusters=config.num_repn_days)
    config.logger.info("Perform %s to select %s representative days based on %s data" % (config.clustering_algorithm, config.num_repn_days, config.repn_day_method,))
    return clustering_result
