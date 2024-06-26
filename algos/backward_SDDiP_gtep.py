__author__ = "Cristiana L. Lara"

from pyomo.environ import *
from pyomo.opt import SolverStatus, TerminationCondition


def backward_pass(stage, bl, n_stages, rn_r, th_r, j_r, l_new, config):
    if stage == n_stages:
        bl.alphafut.fix(0)
    else:
        bl.alphafut.unfix()

    # Solve the model
    opt = SolverFactory(config.solver)
    opt.options['relax_integrality'] = 1
    opt.options['timelimit'] = 6000
    opt.options['threads'] = config.threads
    results = opt.solve(bl, tee=config.tee)
    if results.solver.termination_condition != TerminationCondition.optimal:
        results = opt.solve(bl, tee=True, keepfiles=True)
        config.logger.error("backward_pass nonoptimal")
        raise NameError('backward_pass nonoptimal')

    mltp_o_rn = {}
    mltp_o_th = {}
    mltp_so = {}
    mltp_te = {}

    if stage != 1:
        # Get Lagrange multiplier from linking equality
        for rn_r_index in range(len(rn_r)):
            i = rn_r[rn_r_index][0]
            j = rn_r[rn_r_index][1]
            mltp_o_rn[i, j] = - bl.dual[bl.link_equal1[rn_r_index + 1]]

        for th_r_index in range(len(th_r)):
            i = th_r[th_r_index][0]
            j = th_r[th_r_index][1]
            mltp_o_th[i, j] = - bl.dual[bl.link_equal2[th_r_index + 1]]
        for j_r_index in range(len(j_r)):
            i = j_r[j_r_index][0]
            j = j_r[j_r_index][1]
            mltp_so[i, j] = - bl.dual[bl.link_equal3[j_r_index + 1]]
        for l_index in range(len(l_new)):
            l = l_new[l_index]
            mltp_te[l] = - bl.dual[bl.link_equal4[l_index + 1]]            

    # Get optimal value
    cost = bl.obj()

    return mltp_o_rn, mltp_o_th, mltp_so, mltp_te, cost
