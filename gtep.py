__author__ = "Can Li"
# this class is the interface for running all gtep models and algorithms


import logging

from pyomo.common.config import (
	ConfigBlock, ConfigValue, In, PositiveFloat, PositiveInt
)

from config_options import _get_GTEP_config, check_config
from representativeday.select_repn import select_repn_days
from dataloader.dataloader import load_db_data
from util import write_GTEP_results

logger = logging.getLogger('gtep')

class GTEP:
	"""interface for generation and transmission expansion planning models and algorithms
	"""	
	CONFIG = _get_GTEP_config()
	 

	def __init__(self, **kwds):
		self.config = self.CONFIG(kwds.pop('options', {}))
		self.config.set_value(kwds)
		check_config(self.config)


	def solve_model(self):
		clustering_result = select_repn_days(self.config)
		self.InvestData, self.OperationalData = load_db_data(clustering_result, self.config)
		if self.config.algo == "benders":
			from algos.deterministic_benders import benders_solve
			self.m, self.opt, self.opt_results = benders_solve(self.config, self.InvestData, self.OperationalData)
			self.algo_walltime = round(self.opt_results['Solver'][0]['Wallclock time'])		
		elif self.config.algo == "nested_benders":
			from algos.deterministic_nested import nested_benders_solve
			self.m, cost_LB, cost_UB, elapsed_time = nested_benders_solve(self.config, self.InvestData, self.OperationalData)
			self.algo_walltime = round(elapsed_time)
			self.opt_results = {'cost LB': cost_LB, 'cost UB':cost_UB, 'Wallclock time': elapsed_time}
		elif self.config.algo == "fullspace":
			from algos.fullspace import fullspace_solve
			self.m, self.opt, self.opt_results = fullspace_solve(self.config, self.InvestData, self.OperationalData)
			self.algo_walltime = round(self.opt_results['Solver'][0]['Time'])					

		self.config.logger.info("GTEP problem of the %s region in %s formulation is solved with %s in %s seconds" % (self.config.region, self.config.formulation, self.config.algo, self.algo_walltime))



	def get_solver_time(self):
		pass  

	def get_algorithm_log(self):
		pass 

	def write_gtep_results(self):
		write_GTEP_results(self.m, self.InvestData, self.config, self.opt_results)

newinstance = GTEP(repn_day_method="cost", time_limit=20, algo="fullspace", clustering_algorithm = "kmedoid", num_repn_days=1, time_horizon=3, tee=False)
newinstance.solve_model()
newinstance.write_gtep_results()