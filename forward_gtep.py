__author__ = "Cristiana L. Lara"


from pyomo.environ import *


def forward_pass(bl, rn_r, th_r, j_r, l_new, time_period_stage):

    # Solve the model
    mipsolver = SolverFactory('gurobi')
    mipsolver.options['mipgap'] = 0.001
    mipsolver.options['timelimit'] = 300
    mipsolver.options['threads'] = 6
    mipsolver.solve(bl, tee=True)

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
