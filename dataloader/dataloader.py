__author__ = "Can Li"

import dataloader.load_investment as InvestData
import dataloader.load_operational as OperationalData

# from pyomo.common.config import ConfigBlock, CondigList, ConfigValue
# class DataLoader:
# 	"""load gtep data in different formats"""
# 	def __init__(self):
# 		pass


def load_db_data(clustering_result, config):
    if (
        config.clustering_algorithm == "kmeans"
        or config.clustering_algorithm == "kmeans_exact"
    ):
        OperationalData.read_representative_days_mean(
            config.time_horizon, clustering_result["labels"]
        )
    else:
        OperationalData.read_representative_days(
            config.time_horizon,
            clustering_result["medoids"],
            clustering_result["weights"],
        )
    if config.region == "ERCOT":
        InvestData.read_data("data/ERCOT.db", config.time_horizon)
    OperationalData.read_strategic_uncertainty(config.time_horizon)
    return InvestData, OperationalData
