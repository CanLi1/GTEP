__author__ = "Can Li"
# this class is the interface for running all gtep models and algorithms

import time
import math
import random
from copy import deepcopy
import os.path
from pyomo.environ import *
import csv

import logging

from pyomo.common.config import (
    ConfigBlock, ConfigValue, In, PositiveFloat, PositiveInt
)

from scenarioTree import create_scenario_tree

class GTEP:
    """interface for generation and transmission expansion planning models and algorithms
    """	

    CONFIG = ConfigBlock("GTEP")
    CONFIG.declare("print_level", ConfigValue(
        default=0,
        domain=In([0, 1, 2, 3, 4]),
        description="print level of log",
        doc="Determine how verbose the solution process is printed to the screen"
    ))
    CONFIG.declare("solver", ConfigValue(
        default="cplex",
        domain=In(["cplex", "gurobi", "cbc"]),
        description="solver",
        doc="the solver used to solve the fullspace problem or the subproblems in the decomposition algorithms"
    ))    

    CONFIG.declare("time_limit", ConfigValue(
        default=36000,
        domain=PositiveFloat,
        description="Time limit (seconds, default=36000)",
        doc="Seconds allowed until the algorithm terminated. Note that the time limit "
        "is for the time of the whole algorithm. you may want to set the time limit of the solvers"
        "for each subproblem involved in the algorithm through solver options"
    ))    

#just use solver options at this level and leave the detailed config to different algorithms
    CONFIG.declare("solver_options", ConfigBlock(
        default=100,
        domain=PositiveInt,

        description="iteration limit for nested Benders",
        doc="Maximum number of iteration for the nested Benders iteration algorithm"
        "The algorithm will be forced terminate at this iteration limit"
    )) 

    CONFIG.declare("max_nested_benders_iteration", ConfigValue(
        default=100,
        domain=PositiveInt,
        description="iteration limit for nested Benders",
        doc="Maximum number of iteration for the nested Benders iteration algorithm"
        "The algorithm will be forced terminate at this iteration limit"
    )) 

    CONFIG.declare("nested_benders_rel_gap", ConfigValue(
        default=0.01,
        domain=PositiveFloat,
        description="relative optimality gap for nested Benders",
        doc="Since the nested Benders decomposition algorithm does not have optimality guarantee"
        ", a threshold for optimality gap need to be set. The algorithm will terminate"
        "after it has reached the optimality gap tolerance"
    ))        

    CONFIG.declare("solver_options", ConfigBlock(
        implicit=True,
        description="options passed to the solver",
        doc="options passed to the solver while executing the decomposition algorithms"
    ))     

	def __init__(self, data):
		self.gtep_data = data 



	def create_model(self, data, model_type):
		if model_type == "GTEP":
			import model.gtep_optBlocks_det as b
			self.gtep_model = b.create_model(self.gtep_data)
		elif model_type == "GEP":
			import model.gep_optBlocks_det as b
			self.gtep_model = b.create_model(self.gtep_data)

		self.model_type = model_type
		return self.gep_model

	def solve_model(self, **kwds):
		self.config = self.CONFIG(kwds.pop('options', {}))
		self.config.set_value(kwds)

		if algorithm == "benders" and self.model_type == "GTEP":
			import algos.benders_cplex_gtep as benders
			self.results = benders.solve(self.gtep_model, self.config)
		elif algorithm == "benders" and self.model_type == "GEP":
			import algos.benders_cplex_gep as benders
			self.results = benders.solve(self.gtep_model, self.config)		
		elif algorithm == "nested_benders" and self.model_type == "GTEP":
			import algos.nested_benders_gtep as nested
			self.results = nested.solve(self.gtep_model, self.config)
		elif algorithm == "nested_benders" and self.model_type == "GEP":
			import algos.nested_benders_gep as nested
			self.results = nested.solve(self.gtep_model, self.config)		


	def get_solver_time(self):
		pass  

	def get_algorithm_log(self):
		pass 

	def write_all_results_to_csv(self):
		pass

	def write_generation_expansion_results_to_csv(self):
		pass

	def write_transmission_expansion_results_to_csv(self):
		pass 

	def write_cost_breakdown_to_csv(self):
		pass 

	def write_algorithm_log_to_csv(self):
		pass 


