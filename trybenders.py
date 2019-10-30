import cplex

c = cplex.Cplex("temp.lp")
idx = c.long_annotations.add('cpxBendersPartition', 0)
objtype = c.long_annotations.object_type.variable

for i in range(c.variables.get_num()):
	if i >=16:
		c.long_annotations.set_values(idx, objtype,i,1)
	else:
		c.long_annotations.set_values(idx, objtype,i,0)
c.parameters.benders.strategy.set(1)
c.solve()		