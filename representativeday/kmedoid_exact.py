from pyomo.environ import *
import numpy as np 
def kmedoid_mip(X, ncluster, gap):
	num_points = len(X)
	dist_matrix = {}
	for i in range(num_points):
		for j in range(num_points):
			dist_matrix[(i+1, j+1)] = np.linalg.norm(X[i] - X[j])

	m = ConcreteModel()
	m.I = RangeSet(num_points)
	m.Dist = Param(m.I, m.I, initialize=dist_matrix)
	m.z = Var(m.I, m.I, within=Binary)
	m.y = Var(m.I, within=Binary)

	def c1(m, i):
		return sum(m.z[i,j] for j in m.I) == 1
	m.c1 = Constraint(m.I, rule=c1)

	def c2(m, i, j):
		return m.z[i,j] <= m.y[j]
	m.c2 = Constraint(m.I, m.I, rule=c2)

	def c3(m):
		return sum(m.y[i] for i in m.I) == ncluster
	m.c3 = Constraint(rule=c3)


	def obj(m):
		return sum(m.z[i,j] * m.Dist[i,j] for i in m.I for j in m.I)
	m.obj = Objective(rule=obj, sense=minimize)
	opt = SolverFactory("cplex")
	opt.options['mipgap'] = gap
	opt.options['threads'] = 8
	opt.solve(m, tee=True)

	results = {'medoids':[], 'labels':[], 'weights':[]}
	for i in range(num_points):
		if m.y[i+1].value > 0.5:
			results['medoids'].append(i+1)
			results['weights'].append(0)
	for i in range(num_points):
		for j in range(num_points):
			if m.z[i+1,j+1].value > 0.5:
				results['labels'].append(results['medoids'].index(j+1)+1)
				results['weights'][results['medoids'].index(j+1)] += 1

	return results 



