# author: Can Li 
#utils for representative days selection
import numpy as np 
from pyomo.environ import *
import pandas as pd
import csv
import dataloader.load_operational as SingleDayData


#fix investment decisions
def fix_investment(ref_model, new_model):
	investment_vars = ["ntb","nte","nte_prev","ngr_rn","nge_rn","ngr_th","nge_th","ngo_rn","ngb_rn","ngo_th","ngb_th","ngo_rn_prev","ngo_th_prev","nsr","nsb","nso","nso_prev", "RES_def"]	
	for i in ref_model.stages:
		for v1 in ref_model.Bl[i].component_objects(Var):
			for v2 in new_model.Bl[i].component_objects(Var):
				if v1.getname() in investment_vars and v2.getname() in investment_vars and v1.getname() == v2.getname():
					for index in v1:
						if v1[index].value != None:
							v2[index].fix(v1[index].value)
	return new_model

def eval_investment_single_day(new_model, day, config, load_shedding=True):
	n_stages = config.time_horizon	
	t_per_stage = {}
	for i in range(1, n_stages+1):
		t_per_stage[i] = [i]	
	new_model.n_d._initialize_from({1:365})
	SingleDayData.read_representative_days(config.time_horizon, [day], [365])
	new_model.cf._initialize_from(SingleDayData.cf_by_scenario[0])						
	new_model.L._initialize_from(SingleDayData.L_by_scenario[0])

	opt = SolverFactory(config.solver)
	opt.options['threads'] = config.threads  

	total_operating_cost = 0.0

	for i in range(1, n_stages+1):
		results = opt.solve(new_model.Bl[i])
		if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
			total_operating_cost += new_model.Bl[i].total_operating_cost.expr()
		elif results.solver.termination_condition == TerminationCondition.infeasible:
			total_operating_cost += 1e10
			break
		else:
			raise Exception("the problem at a given time is not solved to optimality termination_condition is ", results.solver.termination_condition)    
	operating_related_cost = {}
	operating_related_cost["total_operating_cost"] = total_operating_cost      
	operating_related_cost["load_shedding_cost"] = 0.0      
	if total_operating_cost >= 1e9:
		operating_related_cost["variable_operating_cost" ] = 1e10
		operating_related_cost["fixed_operating_cost"] = 1e10
		operating_related_cost["startup_cost"] = 1e10
		operating_related_cost["penalty_cost"] = 1e10
		lines = ["Coastal_South", "Coastal_Northeast", "South_Northeast", "South_West", "West_Northeast", "West_Panhandle", "Northeast_Panhandle"] 
		for line in lines:
			operating_related_cost[line] = 0
		operating_related_cost["solar_energy_generated"] = 0
		operating_related_cost["wind_energy_generated" ] = 0
		operating_related_cost["nuclear_energy_generated"] = 0
		operating_related_cost["coal_energy_generated" ] = 0
		operating_related_cost["natural_gas_energy_generated"] = 0
		operating_related_cost["total_energy_generated"] = 0
#calculate load shedding cost when the problem is infeasible
		if load_shedding:
			for stage in new_model.stages:
				for r in new_model.r:
					for t in t_per_stage[stage]:
						for d in new_model.d:
							for s in new_model.hours:
								new_model.Bl[t].L_shed[r, t, d, s].unfix()
			for i in range(1, n_stages+1):
				new_model.Bl[i].obj.deactivate()
				new_model.Bl[i].lobj.activate()
				results = opt.solve(new_model.Bl[i], tee=True)
				operating_related_cost["load_shedding_cost"] += new_model.Bl[i].load_shedding_cost.expr()    
			for stage in new_model.stages:
				for r in new_model.r:
					for t in t_per_stage[stage]:
						for d in new_model.d:
							for s in new_model.hours:
								new_model.Bl[t].L_shed[r, t, d, s].fix(0)     
			for i in range(1, n_stages+1):
				new_model.Bl[i].obj.activate()
				new_model.Bl[i].lobj.deactivate()                                               
		return operating_related_cost
	variable_operating_cost = []
	fixed_operating_cost =[]
	startup_cost = []    
	penalty_cost = []
	total_power_flow = {}
	solar_energy_generated = []
	wind_energy_generated = []
	nuclear_energy_generated = []
	coal_energy_generated = []
	natural_gas_energy_generated = []
	total_energy_generated = []
	lines = ["Coastal_South", "Coastal_Northeast", "South_Northeast", "South_West", "West_Northeast", "West_Panhandle", "Northeast_Panhandle"] 
	for line in lines:
		total_power_flow[line] = 0.0 
	for stage in new_model.stages:
		variable_operating_cost.append(new_model.Bl[stage].variable_operating_cost.expr())
		fixed_operating_cost.append(new_model.Bl[stage].fixed_operating_cost.expr())
		startup_cost.append(new_model.Bl[stage].startup_cost.expr())                
		total_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for (i,r)
		 in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours))
		coal_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for 
			(i,r) in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours if i in new_model.co))
		natural_gas_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for
		 (i,r) in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours if i in new_model.ng))
		nuclear_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for 
			(i,r) in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours if i in new_model.nu))
		solar_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for
		 (i,r) in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours if (i in new_model.pv or i in new_model.csp)))
		wind_energy_generated.append(sum(new_model.Bl[stage].P[i,r,t,d,s].value * new_model.n_d[d].value * pow(10,-6) for 
			(i,r) in new_model.i_r for t in t_per_stage[stage] for d in new_model.d for s in new_model.hours if i in new_model.wi ))
		for l in new_model.l:
			for t in t_per_stage[stage]:
				for d in new_model.d:
					for s in new_model.hours:
						er = new_model.l_er[l][1]
						sr = new_model.l_sr[l][1]
						if new_model.Bl[stage].P_flow[l,t,d,s].value > 0.001:
							total_power_flow[sr+ "_" + er] += new_model.Bl[stage].P_flow[l,t,d,s].value * new_model.n_d[d].value * pow(10,-6)
	operating_related_cost["variable_operating_cost" ] = np.sum(variable_operating_cost )
	operating_related_cost["fixed_operating_cost"] = np.sum(fixed_operating_cost)
	operating_related_cost["startup_cost"] = np.sum(startup_cost )
	operating_related_cost["penalty_cost"] = np.sum(penalty_cost)
	for line in lines:
		operating_related_cost[line] = total_power_flow[line]
	operating_related_cost["solar_energy_generated"] = np.sum(solar_energy_generated)
	operating_related_cost["wind_energy_generated" ] = np.sum(wind_energy_generated )
	operating_related_cost["nuclear_energy_generated"] = np.sum(nuclear_energy_generated)
	operating_related_cost["coal_energy_generated" ] = np.sum(coal_energy_generated )
	operating_related_cost["natural_gas_energy_generated"] = np.sum(natural_gas_energy_generated)
	operating_related_cost["total_energy_generated"] = np.sum(total_energy_generated)
	
	
	return operating_related_cost


def write_GTEP_results(m,  InvestData, config, results = [], ub_problem={}, mode="w"):
	t_per_stage = {}
	for i in range(1, len(m.t)+1):
		t_per_stage[i] = [i]
	outputfile = config.region + "_" + str(config.time_horizon) + "_" + config.formulation + "_" + config.algo + ".csv"
	total_investment_cost = []
	variable_operating_cost = []
	fixed_operating_cost =[]
	startup_cost = []
	thermal_generator_cost = []
	extending_thermal_generator_cost = []
	renewable_generator_cost = []
	extending_renewable_generator_cost = []
	storage_investment_cost = []
	penalty_cost = []
	renewable_capacity = []
	thermal_capacity = []
	total_capacity = []
	transmission_line_cost = []
	solar_capacity = []
	wind_capacity = []
	nuclear_capacity = []
	coal_capacity = []
	natural_gas_capacity = []
	solar_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
	wind_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
	nuclear_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
	coal_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
	natural_gas_capacity_region = {'Northeast':[], 'West':[], 'Coastal':[], 'South':[], 'Panhandle':[]}
	power_flow = []
	solar_energy_generated = []
	wind_energy_generated = []
	nuclear_energy_generated = []
	coal_energy_generated = []
	natural_gas_energy_generated = []
	total_energy_generated = []

	for stage in m.stages:
		total_investment_cost.append(m.Bl[stage].total_investment_cost.expr())
		variable_operating_cost.append(m.Bl[stage].variable_operating_cost.expr())
		fixed_operating_cost.append(m.Bl[stage].fixed_operating_cost.expr())
		startup_cost.append(m.Bl[stage].startup_cost.expr())
		thermal_generator_cost.append(m.Bl[stage].thermal_generator_cost.expr())
		extending_thermal_generator_cost.append(m.Bl[stage].extending_thermal_generator_cost.expr())
		renewable_generator_cost.append(m.Bl[stage].renewable_generator_cost.expr())
		extending_renewable_generator_cost.append(m.Bl[stage].extending_renewable_generator_cost.expr())
		storage_investment_cost.append(m.Bl[stage].storage_investment_cost.expr())
		penalty_cost.append(m.Bl[stage].penalty_cost.expr())
		renewable_capacity.append(m.Bl[stage].renewable_capacity.expr())
		thermal_capacity.append(m.Bl[stage].thermal_capacity.expr())
		total_capacity.append(m.Bl[stage].total_capacity.expr())
		transmission_line_cost.append(m.Bl[stage].transmission_line_cost.expr())
		coal_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.co) )
		natural_gas_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.ng) )
		nuclear_capacity.append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, r in m.i_r if th in m.nu) )
		solar_capacity.append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, r in m.i_r if (rn in m.pv or rn in m.csp)) )
		wind_capacity.append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, r in m.i_r if rn in m.wi) )
		for r in m.r:
			coal_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for  th, rr in m.i_r if (rr==r and th in m.co) ))
			natural_gas_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, rr in m.i_r if (rr==r and th in m.ng) ))
			nuclear_capacity_region[r].append(sum(m.Qg_np[th, r] * m.Bl[stage].ngo_th[th, r, stage].value for th, rr in m.i_r if (rr==r  and th in m.nu) ))
			solar_capacity_region[r].append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, rr in m.i_r if (rr == r and (rn in m.pv or rn in m.csp))) )
			wind_capacity_region[r].append(sum(m.Qg_np[rn, r] * m.Bl[stage].ngo_rn[rn, r, stage].value  for rn, rr in m.i_r if( rr==r and rn in m.wi) ))
		total_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for (i,r)
		 in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours))
		coal_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for 
			(i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.co))
		natural_gas_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for
		 (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.ng))
		nuclear_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for 
			(i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.nu))
		solar_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for
		 (i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if (i in m.pv or i in m.csp)))
		wind_energy_generated.append(sum(m.Bl[stage].P[i,r,t,d,s].value * m.n_d[d].value * pow(10,-6) for 
			(i,r) in m.i_r for t in t_per_stage[stage] for d in m.d for s in m.hours if i in m.wi ))
		temp_power_flow = {}
		for r in m.r:
			temp_power_flow[r] = {}
			for rr in m.r:
				temp_power_flow[r][rr] = 0
		for l in m.l:
			for t in t_per_stage[stage]:
				for d in m.d:
					for s in m.hours:
						er = m.l_er[l][1]
						sr = m.l_sr[l][1]
						if m.Bl[stage].P_flow[l,t,d,s].value > 0:
							temp_power_flow[sr][er] += m.Bl[stage].P_flow[l,t,d,s].value * m.n_d[d].value * pow(10,-6)
						else:
							temp_power_flow[er][sr] -= m.Bl[stage].P_flow[l,t,d,s].value * m.n_d[d].value * pow(10,-6)
		power_flow.append(temp_power_flow)
	
	energy_region_dict ={"solar":solar_capacity_region,
	"nuc":nuclear_capacity_region, 
	"coal":coal_capacity_region,
	"natural gas": natural_gas_capacity_region,
	"wind":wind_capacity_region}
	with open(outputfile, mode, newline='') as results_file:
				fieldnames = ["Time", "total_investment_cost", "variable_operating_cost",
							"fixed_operating_cost",
							"startup_cost",
							"thermal_generator_cost",
							"extending_thermal_generator_cost",
							"renewable_generator_cost",
							"extending_renewable_generator_cost",
							"storage_investment_cost",
							"penalty_cost",
							"renewable_capacity",
							"thermal_capacity",                        
							"transmission_line_cost",
							"coal_capacity",
							"natural_gas_capacity",
							"nuclear_capacity",
							"solar_capacity",
							"wind_capacity",
							"total_capacity",
							"power_flow",
							"solar_energy_generated",
							"wind_energy_generated",
							"nuclear_energy_generated",
							"coal_energy_generated",
							"natural_gas_energy_generated",
							"total_energy_generated"
							]
				for r in m.r:
					for gen in ["coal", "natural gas", "nuc", "solar", "wind"]:
						fieldnames.append(r+ " " + gen)
				writer = csv.DictWriter(results_file, fieldnames=fieldnames)
				writer.writeheader()
				for i in range(len(m.stages)):
					new_row = {"Time":i + 1,
						"total_investment_cost":total_investment_cost[i],
						"variable_operating_cost":variable_operating_cost[i],
						"fixed_operating_cost":fixed_operating_cost[i],
						"startup_cost":startup_cost[i],
						"thermal_generator_cost":thermal_generator_cost[i],
						"extending_thermal_generator_cost":extending_thermal_generator_cost[i],
						"renewable_generator_cost":renewable_generator_cost[i],
						"extending_renewable_generator_cost":extending_renewable_generator_cost[i],
						"storage_investment_cost":storage_investment_cost[i],
						"penalty_cost":penalty_cost[i],
						"renewable_capacity":renewable_capacity[i],
						"thermal_capacity":thermal_capacity[i],
						"total_capacity":total_capacity[i],
						"transmission_line_cost":transmission_line_cost[i],
						"coal_capacity":coal_capacity[i],
						"natural_gas_capacity":natural_gas_capacity[i],
						"nuclear_capacity":nuclear_capacity[i],
						"solar_capacity":solar_capacity[i],
						"wind_capacity":wind_capacity[i],
						"power_flow":power_flow[i],
						"solar_energy_generated":solar_energy_generated[i],
						"wind_energy_generated":wind_energy_generated[i],
						"nuclear_energy_generated":nuclear_energy_generated[i],
						"coal_energy_generated":coal_energy_generated[i],
						"natural_gas_energy_generated":natural_gas_energy_generated[i],
						"total_energy_generated":total_energy_generated[i]}
					for r in m.r:
						for gen in ["coal", "natural gas", "nuc", "solar", "wind"]:
							key = r+ " " + gen
							new_row[key] = energy_region_dict[gen][r][i]
					writer.writerow(new_row)                    
				results_writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
				#get the transmission line expansion 
				for stage in m.stages:                
					for l in m.l_new:
						if m.Bl[stage].ntb[l,stage].value > 0.1:
							temp_row = [stage, InvestData.tielines[l-1]["Near Area Name"], InvestData.tielines[l-1]["Far Area Name"]]
							results_writer.writerow(temp_row)
					 #get the peak demand network structure in the last year  
				last_stage = len(m.stages)                          
				largest_d, largest_s =  0, 0
				largest_load = 0.0
				for r in m.r:
					for d in m.d:
						for s in m.hours:
							if m.L[r, last_stage,d,s].value > largest_load:
								largest_load = m.L[r, last_stage,d,s].value
								largest_d = d 
								largest_s = s 
				#write down the load of each region 
				results_writer.writerow([" at last year ",  d, s])
				results_writer.writerow([" ", 'Northeast', 'West', 'Coastal', 'South', 'Panhandle'])
				results_writer.writerow(["load ", m.L["Northeast", last_stage, largest_d, largest_s].value, 
					m.L["West", last_stage, largest_d, largest_s].value,m.L["Coastal", last_stage, largest_d, largest_s].value,
					m.L["South", last_stage, largest_d, largest_s].value,m.L["Panhandle", last_stage, largest_d, largest_s].value])
				new_row = ["power generation"]
				for r in m.r:
					new_row.append(sum(m.Bl[last_stage].P[i, r, last_stage, largest_d, largest_s].value for i,rr in m.i_r if rr==r))
				results_writer.writerow(new_row)
				new_row = ["power charged"]
				for r in m.r:
					new_row.append(sum(m.Bl[last_stage].p_charged[j, r, last_stage, largest_d, largest_s].value for j in m.j)) 
				results_writer.writerow(new_row)
				new_row = ["power discharged"]    
				for r in m.r:
					new_row.append(sum(m.Bl[last_stage].p_discharged[j, r, last_stage, largest_d, largest_s].value for j in m.j))     
				results_writer.writerow(new_row)
				new_row = ["transmission power "]
				for r in m.r:
					temp_P = 0
					for l in m.l:
						er = m.l_er[l][1]
						sr = m.l_sr[l][1]
						if er == r:
							temp_P += m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value
						if sr == r:
							temp_P -= m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value
					new_row.append(temp_P)
				results_writer.writerow(new_row)
				new_row = ["curtailment "]
				for r in m.r:
					new_row.append(m.Bl[last_stage].cu[r, last_stage, largest_d, largest_s].value)
				results_writer.writerow(new_row)
				   #power transmission of each line 
				results_writer.writerow([])
				results_writer.writerow(["transmission at peak load "])
				for l in m.l:
					if abs(m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value) > 0.1:
						results_writer.writerow([InvestData.tielines[l-1]["Near Area Name"], InvestData.tielines[l-1]["Far Area Name"], m.Bl[last_stage].P_flow[l, last_stage, largest_d, largest_s].value ])
				results_writer.writerow([])        
				results_writer.writerow(["total_investment_cost", sum(total_investment_cost[:])])
				if results != []:
					if 'Solver' in results:
						if 'Time' in results['Solver'][0]:
							results_writer.writerow(["solver fullspace time", results['Solver'][0]['Time']])
						elif 'Wallclock time' in results['Solver'][0]:
							 results_writer.writerow(["solver fullspace time", results['Solver'][0]['Wallclock time']])
						if 'Lower bound' in results['Problem'][0]:
							results_writer.writerow(["lb", results['Problem'][0]['Lower bound']])
						if 'Upper bound' in results['Problem'][0]:
							results_writer.writerow(["ub", results['Problem'][0]['Upper bound']])
					if 'cost LB' in results:
						results_writer.writerow(["nested benders LB", results['cost LB']])
					if 'cost UB' in results:
						results_writer.writerow(["nested benders UB", results['cost UB']]) 
					if 'Wallclock time' in results:
						results_writer.writerow(["nested benders walltime", results['Wallclock time']]) 
	#{"ub time":ub_time, "upper_bound_obj":upper_bound_obj}                    
					if "ub time" in ub_problem:
						results_writer.writerow(["ub_time", ub_problem["ub time"]])
					if "upper_bound_obj" in ub_problem:
						results_writer.writerow(["upper_bound_obj", ub_problem["upper_bound_obj"]])

def write_repn_results(operating_cost, config, cluster_results={}):
	outputfile = config.region + "_" + str(config.time_horizon) + "_" + config.formulation + "_" + config.algo + ".csv"
	with open(outputfile, 'a', newline='') as results_file:
		results_writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		results_writer.writerow([])
		results_writer.writerow(["testing over all the repn days results"])
		results_writer.writerow(["aggregated results for whole year "])        
		fieldnames = ["day_number"] + list(operating_cost[list(operating_cost.keys())[0]].keys())
		writer = csv.DictWriter(results_file, fieldnames=fieldnames)
		
		days = np.sort(list(operating_cost.keys()))
		#first write down the average 
		average = {key:(sum(operating_cost[day][key] for day in days)/len(operating_cost)) for key in fieldnames if key != "day_number"}
		average["day_number"] = "average"
		num_infeasible_days = average["total_operating_cost"] * 365/1e10
		results_writer.writerow(["number of infeasible days", num_infeasible_days])
		for key in cluster_results:
			results_writer.writerow([key, list(cluster_results[key])])
		writer.writeheader()
		writer.writerow(average)
		for day in days:
			new_row = {key:operating_cost[day][key] for key in fieldnames  if key != "day_number"}
			new_row["day_number"] = day 
			writer.writerow(new_row) 




















