__author__ = "Can Li"


import models.gtep_optBlocks_det as b
from pyomo.environ import *


def fullspace_solve(config, InvestData, OperationalData):
    n_stages = config.time_horizon
    formulation = config.formulation
    t_per_stage = {}
    for i in range(1, n_stages + 1):
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
                m.Bl[stage].link_equal1.add(
                    expr=(
                        m.Bl[stage].ngo_rn_prev[rn, r]
                        == m.Bl[stage - 1].ngo_rn[rn, r, t_per_stage[stage - 1][-1]]
                    )
                )
            for (th, r) in m.th_r:
                m.Bl[stage].link_equal2.add(
                    expr=(
                        m.Bl[stage].ngo_th_prev[th, r]
                        == m.Bl[stage - 1].ngo_th[th, r, t_per_stage[stage - 1][-1]]
                    )
                )
            for (j, r) in j_r:
                m.Bl[stage].link_equal3.add(
                    expr=(
                        m.Bl[stage].nso_prev[j, r]
                        == m.Bl[stage - 1].nso[j, r, t_per_stage[stage - 1][-1]]
                    )
                )

            for l in m.l_new:
                m.Bl[stage].link_equal4.add(
                    expr=(
                        m.Bl[stage].nte_prev[l]
                        == m.Bl[stage - 1].nte[l, t_per_stage[stage - 1][-1]]
                    )
                )
    m.obj = Objective(expr=0, sense=minimize)

    for stage in m.stages:
        m.Bl[stage].obj.deactivate()
        m.obj.expr += m.Bl[stage].obj.expr
    # a = TransformationFactory("core.relax_integrality")
    # a.apply_to(m)
    opt = SolverFactory(config.solver)
    opt.options["threads"] = config.threads
    opt.options["timelimit"] = config.time_limit
    opt.options["LPMethod"] = 4
    opt.options["solutiontype"] = 2
    opt_results = opt.solve(m, tee=config.tee)
    return m, opt, opt_results
