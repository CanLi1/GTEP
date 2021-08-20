from gtep import *
newinstance = GTEP(repn_day_method="cost", time_limit=30, tee=True, algo="fullspace", clustering_algorithm = "kmedoid", num_repn_days=1, time_horizon=1)
newinstance.add_extremedays()
# newinstance.write_gtep_results()
