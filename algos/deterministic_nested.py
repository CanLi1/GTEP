__author__ = "Cristiana L. Lara"
# Stochastic Dual Dynamic Integer Programming (SDDiP) description at:
# https://link.springer.com/content/pdf/10.1007%2Fs10107-018-1249-5.pdf

# This algorithm scenario tree satisfies stage-wise independence

import time
import models.gtep_optBlocks_det as b
from pyomo.environ import *
from algos.forward_gtep import forward_pass
from algos.backward_SDDiP_gtep import backward_pass
from algos.scenarioTree import create_scenario_tree


def nested_benders_solve(config, InvestData, OperationalData):
    n_stages = config.time_horizon
    formulation = config.formulation

    stages = range(1, n_stages + 1)
    scenarios = ["M"]
    single_prob = {"M": 1.0}

    time_periods = n_stages
    t_per_stage = {}
    for i in range(1, n_stages + 1):
        t_per_stage[i] = [i]

    # create blocks
    m = b.create_model(n_stages, t_per_stage, formulation, InvestData, OperationalData)

    start_time = time.time()

    # Define parameters of the decomposition
    max_iter = config.nested_benders_iter_limit
    max_time = config.time_limit
    opt_tol = config.nested_benders_rel_gap

    # Shared data among processes
    ngo_rn_par_k = {}
    ngo_th_par_k = {}
    nso_par_k = {}
    nsb_par_k = {}
    nte_par_k = {}
    cost_forward = {}
    cost_scenario_forward = {}
    mltp_o_rn = {}
    mltp_o_th = {}
    mltp_so = {}
    mltp_te = {}
    cost_backward = {}
    if_converged = {}

    # Decomposition Parameters
    m.ngo_rn_par = Param(m.rn_r, m.stages, default=0, initialize=0, mutable=True)
    m.ngo_th_par = Param(m.th_r, m.stages, default=0, initialize=0, mutable=True)
    m.nso_par = Param(m.j, m.r, m.stages, default=0, initialize=0, mutable=True)
    m.nte_par = Param(m.l_new, m.stages, default=0, initialize=0, mutable=True)

    # Parameters to compute upper and lower bounds
    cost_UB = {}
    cost_LB = {}
    gap = {}

    # create scenarios
    nodes, n_stage, parent_node, children_node, prob, sc_nodes = create_scenario_tree(
        stages, scenarios, single_prob
    )
    sc_headers = list(sc_nodes.keys())

    # converting sets to lists:
    rn_r = list(m.rn_r)
    th_r = list(m.th_r)
    j_r = [(j, r) for j in m.j for r in m.r]
    l_new = list(m.l_new)

    # request the dual variables for all (locally) defined blocks
    for bb in m.Bl.values():
        bb.dual = Suffix(direction=Suffix.IMPORT)

    # solve with nested benders
    for stage in m.stages:
        if stage != 1:
            # config.logger.info('stage', stage, 't_prev', t_prev)
            for (rn, r) in m.rn_r:
                m.Bl[stage].link_equal1.add(
                    expr=(m.Bl[stage].ngo_rn_prev[rn, r] == m.ngo_rn_par[rn, r, stage])
                )
            for (th, r) in m.th_r:
                m.Bl[stage].link_equal2.add(
                    expr=(m.Bl[stage].ngo_th_prev[th, r] == m.ngo_th_par[th, r, stage])
                )
            for (j, r) in j_r:
                m.Bl[stage].link_equal3.add(
                    expr=(m.Bl[stage].nso_prev[j, r] == m.nso_par[j, r, stage])
                )
            for l in m.l_new:
                m.Bl[stage].link_equal4.add(
                    expr=(m.Bl[stage].nte_prev[l] == m.nte_par[l, stage])
                )

    # Nested Benders decomposition
    relax_integrality = config.nested_benders_relax_integrality_forward
    for iter_ in range(1, max_iter + 1):
        # ####### Forward Pass ############################################################
        # solve ORIGIN node:
        stage = 1
        n = "O"
        config.logger.info(
            "Forward Pass: Stage %s Current Node %s"
            % (
                stage,
                n,
            )
        )
        op = 0

        ngo_rn, ngo_th, nso, nte, cost = forward_pass(
            m.Bl[stage],
            rn_r,
            th_r,
            j_r,
            l_new,
            t_per_stage[stage],
            relax_integrality,
            config,
        )

        for t in t_per_stage[stage]:
            for (rn, r) in rn_r:
                ngo_rn_par_k[rn, r, t, n, iter_] = ngo_rn[rn, r, t]
            for (th, r) in th_r:
                ngo_th_par_k[th, r, t, n, iter_] = ngo_th[th, r, t]
            for (j, r) in j_r:
                nso_par_k[j, r, t, n, iter_] = nso[j, r, t]
            for l in l_new:
                nte_par_k[l, t, n, iter_] = nte[l, t]
        cost_forward[stage, n, iter_] = cost
        config.logger.info("cost %s" % (cost_forward[stage, n, iter_],))

        for stage in m.stages:
            if stage != 1:
                for n in n_stage[stage]:
                    config.logger.info(
                        "Forward Pass: Stage %s Current Node %s"
                        % (
                            stage,
                            n,
                        )
                    )

                    # randomly select which operating data profile to solve and populate uncertainty parameters:
                    op = 0
                    config.logger.info("operating scenario %s" % (op,))

                    # populate current state from parent node
                    for (rn, r) in rn_r:
                        t_prev = t_per_stage[stage - 1][-1]
                        m.ngo_rn_par[rn, r, stage] = ngo_rn_par_k[
                            rn, r, t_prev, parent_node[n], iter_
                        ]
                    for (th, r) in th_r:
                        t_prev = t_per_stage[stage - 1][-1]
                        m.ngo_th_par[th, r, stage] = ngo_th_par_k[
                            th, r, t_prev, parent_node[n], iter_
                        ]
                    for (j, r) in j_r:
                        t_prev = t_per_stage[stage - 1][-1]
                        m.nso_par[j, r, stage] = nso_par_k[
                            j, r, t_prev, parent_node[n], iter_
                        ]
                    for l in l_new:
                        t_prev = t_per_stage[stage - 1][-1]
                        m.nte_par[l, stage] = nte_par_k[
                            l, t_prev, parent_node[n], iter_
                        ]

                    ngo_rn, ngo_th, nso, nte, cost = forward_pass(
                        m.Bl[stage],
                        rn_r,
                        th_r,
                        j_r,
                        l_new,
                        t_per_stage[stage],
                        relax_integrality,
                        config,
                    )

                    for t in t_per_stage[stage]:
                        for (rn, r) in rn_r:
                            ngo_rn_par_k[rn, r, t, n, iter_] = ngo_rn[rn, r, t]
                        for (th, r) in th_r:
                            ngo_th_par_k[th, r, t, n, iter_] = ngo_th[th, r, t]
                        for (j, r) in j_r:
                            nso_par_k[j, r, t, n, iter_] = nso[j, r, t]
                        for l in l_new:
                            nte_par_k[l, t, n, iter_] = nte[l, t]
                    cost_forward[stage, n, iter_] = cost
                    config.logger.info("cost %s" % (cost_forward[stage, n, iter_],))

        # Compute cost per scenario solved inside of a process
        cost_forward[iter_] = sum(
            prob[n] * cost_forward[stage, n, iter_]
            for stage in m.stages
            for n in n_stage[stage]
        )
        # config.logger.info(cost_scenario_forward)

        config.logger.info("finished forward pass")

        cost_UB[iter_] = min(
            cost_forward[kk] for kk in range(1, max_iter + 1) if kk <= iter_
        )
        config.logger.info(cost_UB)
        elapsed_time = time.time() - start_time
        config.logger.info("CPU Time (s) %s" % (elapsed_time,))

        # ####### Backward Pass ############################################################

        for stage in reversed(list(m.stages)):
            if stage != n_stages:
                for n in n_stage[stage]:
                    for cn in children_node[n]:
                        for op in [0]:
                            config.logger.info(
                                "Children Node %s of stage %s op scenario %s"
                                % (
                                    cn,
                                    stage + 1,
                                    op,
                                )
                            )

                            # populate current state from parent node
                            for (rn, r) in rn_r:
                                t_prev = t_per_stage[stage][-1]
                                m.ngo_rn_par[rn, r, stage + 1] = ngo_rn_par_k[
                                    rn, r, t_prev, n, iter_
                                ]

                            for (th, r) in th_r:
                                t_prev = t_per_stage[stage][-1]
                                m.ngo_th_par[th, r, stage + 1] = ngo_th_par_k[
                                    th, r, t_prev, n, iter_
                                ]

                            for (j, r) in j_r:
                                t_prev = t_per_stage[stage][-1]
                                m.nso_par[j, r, stage + 1] = nso_par_k[
                                    j, r, t_prev, n, iter_
                                ]

                            for l in l_new:
                                t_prev = t_per_stage[stage][-1]
                                m.nte_par[l, stage + 1] = nte_par_k[l, t_prev, n, iter_]

                            mltp_rn, mltp_th, mltp_s, mltp_t, cost = backward_pass(
                                stage + 1,
                                m.Bl[stage + 1],
                                n_stages,
                                rn_r,
                                th_r,
                                j_r,
                                l_new,
                                config,
                            )

                            cost_backward[stage + 1, cn, op, iter_] = cost
                            config.logger.info(
                                "cost %s %s %s %s"
                                % (
                                    stage + 1,
                                    cn,
                                    op,
                                    cost_backward[stage + 1, cn, op, iter_],
                                )
                            )

                            for (rn, r) in rn_r:
                                mltp_o_rn[rn, r, stage + 1, cn, op, iter_] = mltp_rn[
                                    rn, r
                                ]
                            for (th, r) in th_r:
                                mltp_o_th[th, r, stage + 1, cn, op, iter_] = mltp_th[
                                    th, r
                                ]
                            for (j, r) in j_r:
                                mltp_so[j, r, stage + 1, cn, op, iter_] = mltp_s[j, r]
                            for l in l_new:
                                mltp_te[l, stage + 1, cn, op, iter_] = mltp_t[l]

                # add Benders cut for current iteration
                t = t_per_stage[stage][-1]
                op = 0
                m.Bl[stage].fut_cost.add(
                    expr=(
                        m.Bl[stage].alphafut
                        >= sum(
                            (prob[cn] / prob[n])
                            * (
                                cost_backward[stage + 1, cn, op, iter_]
                                + sum(
                                    mltp_o_rn[rn, r, stage + 1, cn, op, iter_]
                                    * (
                                        ngo_rn_par_k[rn, r, t, n, iter_]
                                        - m.Bl[stage].ngo_rn[rn, r, t]
                                    )
                                    for rn, r in m.rn_r
                                )
                                + sum(
                                    mltp_o_th[th, r, stage + 1, cn, op, iter_]
                                    * (
                                        ngo_th_par_k[th, r, t, n, iter_]
                                        - m.Bl[stage].ngo_th[th, r, t]
                                    )
                                    for th, r in m.th_r
                                )
                                + sum(
                                    mltp_so[j, r, stage + 1, cn, op, iter_]
                                    * (
                                        nso_par_k[j, r, t, n, iter_]
                                        - m.Bl[stage].nso[j, r, t]
                                    )
                                    for j in m.j
                                    for r in m.r
                                )
                                + sum(
                                    mltp_te[l, stage + 1, cn, op, iter_]
                                    * (
                                        nte_par_k[l, t, n, iter_]
                                        - m.Bl[stage].nte[l, t]
                                    )
                                    for l in m.l_new
                                )
                            )
                            for cn in children_node[n]
                        )
                    )
                )

            # solve node in first stage
        op = 0
        stage = 1
        n = "O"

        opt = SolverFactory(config.solver)
        opt.options["timelimit"] = 1000
        opt.options["mipgap"] = 0.0001
        opt.options["threads"] = config.threads
        opt.options["relax_integrality"] = relax_integrality
        results = opt.solve(m.Bl[stage], tee=config.tee)
        cost_backward[stage, n, iter_] = m.Bl[stage].obj()

        # Compute lower bound
        cost_LB[iter_] = cost_backward[stage, n, iter_]
        config.logger.info(cost_LB)
        # Compute optimality gap
        gap[iter_] = (cost_UB[iter_] - cost_LB[iter_]) / cost_UB[iter_] * 100
        config.logger.info("gap: %s" % (gap[iter_],))

        if gap[iter_] <= opt_tol:
            if_converged[iter_] = True
        else:
            if_converged[iter_] = False

        elapsed_time = time.time() - start_time
        config.logger.info("CPU Time (s) %s" % (elapsed_time,))
        config.logger.info(cost_UB)
        config.logger.info(cost_LB)
        if (
            if_converged[iter_] or iter_ == max_iter - 1 or elapsed_time > max_time
        ) and relax_integrality == 0:
            last_iter = iter_
            break
        if if_converged[iter_] or iter_ == max_iter - 2 or elapsed_time > max_time:
            relax_integrality = 0

    elapsed_time = time.time() - start_time

    return m, cost_LB, cost_UB, elapsed_time
