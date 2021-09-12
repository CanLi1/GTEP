from gtep import *
newinstance = GTEP(repn_day_method="input", time_limit=100000, tee=True, algo="fullspace", clustering_algorithm = "kmeans", num_repn_days=15, time_horizon=5, formulation="improved")
newinstance.solve_model()
# newinstance.add_extremedays()
# newinstance.write_gtep_results()
