__author__ = "Cristiana L. Lara"


from pyomo.environ import *
from pyomo.opt import SolverStatus, TerminationCondition

def forward_pass(bl, rn_r, th_r, j_r, l_new, time_period_stage, relax):

    # Solve the model
    mipsolver = SolverFactory('cplex')
    mipsolver.options['mipgap'] = 0.001
    mipsolver.options['relax_integrality'] = relax
    mipsolver.options['timelimit'] = 10000
    mipsolver.options['threads'] = 1
    results = mipsolver.solve(bl, tee=False)
    print("termination condition")
    print(results.solver.termination_condition)
    if results.solver.termination_condition != TerminationCondition.optimal:
        results = mipsolver.solve(bl, tee=True, keepfiles=True)
        raise NameError('forward_pass nonoptimal')

    ngo_rn_par = {}
    ngo_th_par = {}
    nso_par = {}
    nte_par = {}

    # Fix the linking variable as parameter for next
    for t in time_period_stage:
        for (rn, r) in rn_r:
            ngo_rn_par[rn, r, t] = bl.ngo_rn[rn, r, t].value

        for (th, r) in th_r:
            ngo_th_par[th, r, t] = bl.ngo_th[th, r, t].value
        for (j, r) in j_r:
            nso_par[j, r, t] = bl.nso[j, r, t].value
        for l in l_new:
            nte_par[l, t] = bl.nte[l, t].value

    # Store obj value to compute UB
    cost = bl.obj() - bl.alphafut.value

    return ngo_rn_par, ngo_th_par, nso_par, nte_par, cost
