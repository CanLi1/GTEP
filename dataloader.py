__author__ = "Can Li"
# this class is the interface for running all gtep models and algorithms

# data = CSVDataLoader('path/to/instance.csv')
# model = GTEPModel()
# model.create_model(data)
# solver = SDDP_Solver()

# solver.solve(model, options= {...})
# pyutilib/misc/config.py
from pyomo.common.config import ConfigBlock, CondigList, ConfigValue
class DataLoader:
	"""load gtep data in different formats"""
	def __init__(self):
		pass

	def load_db_data(self, path):
		import os.path
		import deterministic.readData_det as readData_det
		curPath = os.path.abspath(os.path.curdir)
		curPath = curPath.replace('/deterministic', '')		
		filepath = os.path.join(curPath, path)
		n_stages = 20  # number od stages in the scenario tree
		formulation = "improved"
		num_days =12
		stages = range(1, n_stages + 1)
		t_per_stage = {}
		for i in range(1, n_stages+1):
		  t_per_stage[i] = [i]
		readData_det.read_data(filepath, curPath, stages, n_stage, t_per_stage, num_days)
		return readData_det




