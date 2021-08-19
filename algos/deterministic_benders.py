__author__ = "Can Li"


import models.gtep_optBlocks_det as b
from pyomo.environ import *
def benders_solve(config, InvestData, OperationalData):
	n_stages = config.time_horizon
	formulation = config.formulation
	t_per_stage = {}
	for i in range(1, n_stages+1):
		t_per_stage[i] = [i]
	m = b.create_model(n_stages, t_per_stage, formulation, InvestData, OperationalData)

	# # # converting sets to lists:
	rn_r = list(m.rn_r)
	th_r = list(m.th_r)
	j_r = [(j, r) for j in m.j for r in m.r]
	l_new = list(m.l_new)


	# # Add equality constraints (solve the full space)
	for stage in m.stages:
		if stage != 1:
			for (rn, r) in m.rn_r:
				m.Bl[stage].link_equal1.add(expr=(m.Bl[stage].ngo_rn_prev[rn, r] ==
												  m.Bl[stage-1].ngo_rn[rn, r, t_per_stage[stage-1][-1]] ))
			for (th, r) in m.th_r:
				m.Bl[stage].link_equal2.add(expr=(m.Bl[stage].ngo_th_prev[th, r] ==
													m.Bl[stage-1].ngo_th[th, r, t_per_stage[stage-1][-1]]  ))
			for (j, r) in j_r:
				m.Bl[stage].link_equal3.add(expr=(m.Bl[stage].nso_prev[j, r] ==
													 m.Bl[stage-1].nso[j, r, t_per_stage[stage-1][-1]]))

			for l in m.l_new:
				m.Bl[stage].link_equal4.add(expr=(m.Bl[stage].nte_prev[l] ==
													 m.Bl[stage-1].nte[l, t_per_stage[stage-1][-1]]))
	m.obj = Objective(expr=0, sense=minimize)

	for stage in m.stages:
		m.Bl[stage].obj.deactivate()
		m.obj.expr += m.Bl[stage].obj.expr


	#relax integer variables in the Benders subproblem
	operating_integer_vars = ["u", "su", "sd"]
	for stage in m.stages:
		for t in t_per_stage[stage]:
			for d in m.d:
				for s in m.hours:
					for (th, r) in m.th_r:
						lb, ub = m.Bl[stage].u[th, r, t, d, s].bounds
						m.Bl[stage].u[th, r, t, d, s].domain = Reals
						m.Bl[stage].u[th, r, t, d, s].setlb(lb)
						m.Bl[stage].u[th, r, t, d, s].setub(ub)     
						lb, ub = m.Bl[stage].su[th, r, t, d, s].bounds
						m.Bl[stage].su[th, r, t, d, s].domain = Reals
						m.Bl[stage].su[th, r, t, d, s].setlb(lb)
						m.Bl[stage].su[th, r, t, d, s].setub(ub)  
						lb, ub = m.Bl[stage].sd[th, r, t, d, s].bounds
						m.Bl[stage].sd[th, r, t, d, s].domain = Reals
						m.Bl[stage].sd[th, r, t, d, s].setlb(lb)
						m.Bl[stage].sd[th, r, t, d, s].setub(ub)                                                     
	import time

	opt = SolverFactory("cplex_persistent")
	 
	opt.options['threads'] = config.threads
	opt.options['timelimit'] = config.time_limit
	opt.set_instance(m)
	opt.set_benders_annotation()
	opt.set_benders_strategy(1)
	opt.set_mip_rel_gap(config.benders_mip_gap)

	#set master variables 
	investment_vars = ["ntb","nte","nte_prev","ngr_rn","nge_rn","ngr_th","nge_th","ngo_rn","ngb_rn","ngo_th","ngb_th","ngo_rn_prev","ngo_th_prev","nsr","nsb","nso","nso_prev", "alphafut", "RES_def"]
	for v in m.component_objects(Var):
		if v.getname() in investment_vars:
			for index in v:
				opt.set_master_variable(v[index])

	#set subproblems
	operating_vars = []
	if formulation == "standard":
	  operating_vars = ["L_shed", "theta", "P", "cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]
	elif formulation == "hull":
	  operating_vars = ["L_shed", "theta", "P", "d_theta_1", "d_theta_2","cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]
	elif formulation == "improved":
	  operating_vars = ["L_shed", "theta", "P", "d_theta_plus", "d_theta_minus", "d_P_flow_plus", "d_P_flow_minus", "cu",  "P_flow", "P_Panhandle", "Q_spin", "Q_Qstart", "u", "su", "sd",  "p_charged", "p_discharged", "p_storage_level", "p_storage_level_end_hour"]  
	map_d = {'fall':3, 'summer':2, 'spring':1, 'winter':4}
	for v in m.component_objects(Var):
		if v.getname() in operating_vars:
			for index in v:
				t = index[-3]
				opt.set_subproblem_variable(v[index], t)

	opt_results = opt.solve(m, tee=config.tee)
	return m, opt, opt_results 


