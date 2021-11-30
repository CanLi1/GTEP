__author__ = "Can Li"
# this class is the interface for running all gtep models and algorithms


import logging

from pyomo.common.config import ConfigBlock, ConfigValue, In, PositiveFloat, PositiveInt

from config_options import _get_GTEP_config, check_config
from representativeday.select_repn import select_repn_days
from dataloader.dataloader import load_db_data
from util import *
from copy import deepcopy
import dataloader.load_operational as SingleDayData
import models.gtep_optBlocks_det as b
from representativeday.cluster import select_extreme_days

logger = logging.getLogger("gtep")


class GTEP:
    """interface for generation and transmission expansion planning models and algorithms"""

    CONFIG = _get_GTEP_config()

    def __init__(self, **kwds):
        self.config = self.CONFIG(kwds.pop("options", {}))
        self.config.set_value(kwds)
        check_config(self.config)
        self.clustering_result = select_repn_days(self.config)
        self.InvestData, self.OperationalData = load_db_data(
            self.clustering_result, self.config
        )

    def solve_model(self):
        if self.config.algo == "benders":
            from algos.deterministic_benders import benders_solve

            self.m, self.opt, self.opt_results = benders_solve(
                self.config, self.InvestData, self.OperationalData
            )
            self.algo_walltime = round(self.opt_results["Solver"][0]["Wallclock time"])
        elif self.config.algo == "nested_benders":
            from algos.deterministic_nested import nested_benders_solve

            self.m, cost_LB, cost_UB, elapsed_time = nested_benders_solve(
                self.config, self.InvestData, self.OperationalData
            )
            self.algo_walltime = round(elapsed_time)
            self.opt_results = {
                "cost LB": cost_LB,
                "cost UB": cost_UB,
                "Wallclock time": elapsed_time,
            }
        elif self.config.algo == "fullspace":
            from algos.fullspace import fullspace_solve

            self.m, self.opt, self.opt_results = fullspace_solve(
                self.config, self.InvestData, self.OperationalData
            )
            self.algo_walltime = round(self.opt_results["Solver"][0]["Time"])

        self.config.logger.info(
            "GTEP problem of the %s region in %s formulation is solved with %s in %s seconds"
            % (
                self.config.region,
                self.config.formulation,
                self.config.algo,
                self.algo_walltime,
            )
        )

    def add_extremedays(self):
        method = self.config.repn_day_method
        extreme_day_method = self.config.extreme_day_method
        clustering_method = self.config.clustering_algorithm
        iter_ = 1
        best_ub = float("inf")
        initial_cluster_result = deepcopy(self.clustering_result)
        while True:
            if method == "cost":
                if extreme_day_method == "highest_cost":
                    cluster_results = deepcopy(
                        initial_cluster_result
                    )  # reselected n days as extreme days
                elif (
                    extreme_day_method == "highest_cost_infeasible"
                    or extreme_day_method == "load_shedding_cost"
                ) and iter_ == 1:
                    cluster_results = deepcopy(
                        initial_cluster_result
                    )  # only copy once and add 1 extreme days per iteration
                if iter_ > 1 and len(infeasible_days) > 0:
                    cluster_results = select_extreme_days(
                        cluster_results,
                        cluster_obj=cluster_obj,
                        n=1,
                        method=extreme_day_method,
                        infeasible_days=infeasible_days,
                        load_shedding_cost=load_shedding_cost,
                        clustering_method=clustering_method,
                    )

            if method == "input":
                if iter_ == 1:
                    cluster_results = deepcopy(initial_cluster_result)
                if iter_ > 1 and len(infeasible_days) > 0:
                    cluster_results = select_extreme_days(
                        cluster_results,
                        n=1,
                        method=extreme_day_method,
                        infeasible_days=infeasible_days,
                        load_shedding_cost=load_shedding_cost,
                        clustering_method=clustering_method,
                    )

            self.InvestData, self.OperationalData = load_db_data(
                cluster_results, self.config
            )
            self.solve_model()

            # write results
            if iter_ == 1:
                write_GTEP_results(
                    self.m, self.InvestData, self.config, self.opt_results
                )
            else:
                write_GTEP_results(
                    self.m, self.InvestData, self.config, self.opt_results, mode="a"
                )

            # #==============fix the investment decisions and evaluate them ========================
            # #create a new model with a single representative day per year
            SingleDayData.read_representative_days(self.config.time_horizon, [1], [365])
            n_stages = self.config.time_horizon
            formulation = self.config.formulation
            t_per_stage = {}
            for i in range(1, n_stages + 1):
                t_per_stage[i] = [i]
            new_model = b.create_model(
                n_stages, t_per_stage, formulation, self.InvestData, SingleDayData
            )
            new_model = fix_investment(self.m, new_model)
            investment_cost = 0.0
            for i in self.m.stages:
                investment_cost += self.m.Bl[i].total_investment_cost.expr()

            # import pymp
            # NumProcesses =3
            # operating_cost = pymp.shared.dict()
            # infeasible_days = pymp.shared.list()
            # load_shedding_cost = pymp.shared.list()
            # with pymp.Parallel(NumProcesses) as p:
            operating_cost = {}
            infeasible_days = []
            load_shedding_cost = []
            for day in range(1, 366):
                operating_cost[day] = eval_investment_single_day(
                    new_model, day, self.config
                )
                if operating_cost[day]["total_operating_cost"] >= 1e9:
                    infeasible_days.append(day)
                    load_shedding_cost.append(operating_cost[day]["load_shedding_cost"])

            write_repn_results(operating_cost, self.config, cluster_results)

            self.config.logger.info(
                "%s extreme days have been added there are still %s infeasible days"
                % (
                    iter_,
                    len(infeasible_days),
                )
            )
            # check termination criteria
            if iter_ >= self.config.max_extreme_day:
                break

            days = np.sort(list(operating_cost.keys()))
            totol_cost = investment_cost + sum(
                operating_cost[day]["total_operating_cost"] for day in days
            ) / len(operating_cost)

            if best_ub > totol_cost:
                best_ub = totol_cost

            if len(infeasible_days) == 0:
                break
            del new_model
            iter_ += 1

    def get_solver_time(self):
        return self.algo_walltime

    def write_gtep_results(self):
        write_GTEP_results(self.m, self.InvestData, self.config, self.opt_results)
