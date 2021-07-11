from pyomo.environ import *
import numpy as np 
#the formulation is taken from page 19 of Papageorgiou, D. J., & Trespalacios, F. (2018). 
#Pseudo basic steps: bound improvement guarantees from Lagrangian decomposition in convex disjunctive programming. EURO Journal on Computational Optimization, 6(1), 55-83.
def kmeans_miqcp(X, ncluster, gap):
	num_points = len(X)
	ndim = len(X[0])
	m = ConcreteModel()
	m.I = RangeSet(num_points)
	m.J = RangeSet(ndim)
	m.K = RangeSet(ncluster)
	m.M = Param(m.I, initialize=0, mutable=True)
	for i in range(1, num_points+1):
		m.M[i] = max([np.linalg.norm(X[i-1] - X[j]) ** 2 for j in range(num_points)])
	m.p = Param(m.I, m.J, mutable = True)
	for i in m.I:
		for j in m.J:
			m.p[i,j] = X[i-1][j-1]
	m.y = Var(m.I, m.K, within=Binary)
	m.d = Var(m.I, within=NonNegativeReals)
	m.c = Var(m.K, m.J)

	def c1(m, i, k):
		return m.d[i] >= sum((m.p[i,j] - m.c[k,j]) * (m.p[i,j] - m.c[k,j]) for j in m.J) - m.M[i] * (1-m.y[i,k])
	m.c1 = Constraint(m.I, m.K, rule=c1)

	def c2(m, i):
		return sum(m.y[i,k] for k in m.K) == 1
	m.c2 = Constraint(m.I, rule=c2)

	def c3(m, k):
		if k != 1:
			return m.c[k-1,1] <= m.c[k,1]
		else:
			return Constraint.Skip 
	m.c3 = Constraint(m.K, rule=c3)			
	def c4(m,k):
		return sum(m.y[i,k] for i in m.I) >= 1
	m.c4 = Constraint(m.K, rule=c4)


	def obj(m):
		return sum(m.d[i] for i in m.I)
	m.obj = Objective(rule=obj, sense=minimize)
	opt = SolverFactory("cplex")
	opt.options['mipgap'] = gap
	opt.options['threads'] = 8
	opt.solve(m, tee=True)

	labels = []
	for i in m.I:
		for k in m.K:
			if m.y[i,k].value > 0.5:
				labels.append(i-1)

	return labels



