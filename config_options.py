from pyomo.common.config import (
    ConfigBlock,
    ConfigValue,
    In,
    PositiveFloat,
    PositiveInt,
    NonNegativeInt,
)
import idaes.logger as idaeslog


def _get_GTEP_config():
    CONFIG = ConfigBlock("GTEP")
    CONFIG.declare(
        "region",
        ConfigValue(
            default="ERCOT",
            domain=In(["ERCOT"]),
            description="The region where the GTEP model is solved, currently only support ERCOT",
            doc="The region where the GTEP model is solved, currently only support ERCOT",
        ),
    )

    CONFIG.declare(
        "time_horizon",
        ConfigValue(
            default=5,
            domain=In(list(range(1, 21))),
            description="planning horizon of the GTEP model (from 1 to 20)",
            doc="planning horizon of the GTEP model (from 1 to 20)",
        ),
    )

    CONFIG.declare(
        "num_repn_days",
        ConfigValue(
            default=10,
            domain=PositiveInt,
            description="The number of representative days to be used for the GTEP model",
            doc="The number of representative days to be used for the GTEP model",
        ),
    )

    CONFIG.declare(
        "formulation",
        ConfigValue(
            default="improved",
            domain=In(["improved", "hull", "standard"]),
            description="formulation for the transmission expansion",
            doc="formulation for the transmission expansion (standard->big M, improved->improved big M, hull->hull",
        ),
    )

    CONFIG.declare(
        "algo",
        ConfigValue(
            default="benders",
            domain=In(["benders", "nested_benders", "fullspace"]),
            description="solution algorithm",
            doc="solution algorithm for the gtep model",
        ),
    )

    CONFIG.declare(
        "clustering_algorithm",
        ConfigValue(
            default="kmeans",
            domain=In(["kmeans", "kmedoid", "kmeans_exact", "kmedoid_exact"]),
            description="cluster algorithm",
            doc="cluster algorithm used by the representative day selection",
        ),
    )

    CONFIG.declare(
        "max_extreme_day",
        ConfigValue(
            default=8,
            domain=PositiveInt,
            description="max number of extreme days added",
            doc="max number of extreme days added",
        ),
    )

    CONFIG.declare(
        "extreme_day_method",
        ConfigValue(
            default="load_shedding_cost",
            domain=In(
                [
                    "highest_cost_infeasible",
                    "highest_cost",
                    "load_shedding_cost",
                    "kmedoid_exact",
                ]
            ),
            description="extreme day selection method",
            doc="extreme day selection method in case there are infeasible days",
        ),
    )

    CONFIG.declare(
        "repn_day_method",
        ConfigValue(
            default="input",
            domain=In(["input", "cost"]),
            description="representative day selection method",
            doc="representative day selection method",
        ),
    )

    CONFIG.declare(
        "print_level",
        ConfigValue(
            default=3,
            domain=In([0, 1, 2, 3, 4]),
            description="print level of log",
            doc="Determine how verbose the solution process is printed to the screen",
        ),
    )
    CONFIG.declare(
        "solver",
        ConfigValue(
            default="cplex",
            domain=In(["cplex", "gurobi", "cbc"]),
            description="solver",
            doc="the solver used to solve the fullspace problem or the subproblems in the decomposition algorithms",
        ),
    )

    CONFIG.declare(
        "time_limit",
        ConfigValue(
            default=36000,
            domain=PositiveFloat,
            description="Time limit (seconds, default=36000)",
            doc="Seconds allowed until the algorithm terminated. Note that the time limit "
            "is for the time of the whole algorithm. you may want to set the time limit of the solvers"
            "for each subproblem involved in the algorithm through solver options",
        ),
    )

    CONFIG.declare(
        "benders_mip_gap",
        ConfigValue(
            default=5e-3,
            domain=PositiveFloat,
            description="relative optimality gap for benders decomposition",
            doc="relative optimality gap for benders decomposition default is 5e-3",
        ),
    )

    CONFIG.declare(
        "nested_benders_iter_limit",
        ConfigValue(
            default=100,
            domain=PositiveInt,
            description="iteration limit for nested Benders",
            doc="Maximum number of iteration for the nested Benders iteration algorithm"
            "The algorithm will be forced terminate at this iteration limit",
        ),
    )

    CONFIG.declare(
        "nested_benders_relax_integrality_forward",
        ConfigValue(
            default=1,
            domain=In([0, 1]),
            description="whether to relax integrality in the nested bender forward pass",
            doc="If equals to 1, the nested Benders decomposition algorithm solves the LP relaxation of the problem until the LP relaxation is solved to optimality ",
        ),
    )

    CONFIG.declare(
        "nested_benders_rel_gap",
        ConfigValue(
            default=0.01,
            domain=PositiveFloat,
            description="relative optimality gap for nested Benders",
            doc="Since the nested Benders decomposition algorithm does not have optimality guarantee"
            ", a threshold for optimality gap need to be set. The algorithm will terminate"
            "after it has reached the optimality gap tolerance",
        ),
    )

    CONFIG.declare(
        "threads",
        ConfigValue(
            default=1,
            domain=PositiveInt,
            description="number of threads",
            doc="number of threads used by the algorithms",
        ),
    )

    CONFIG.declare(
        "solver_options",
        ConfigBlock(
            implicit=True,
            description="options passed to the solver",
            doc="options passed to the solver while executing the decomposition algorithms",
        ),
    )

    CONFIG.declare(
        "tee",
        ConfigValue(
            default=False, description="Stream solver output to terminal.", domain=bool
        ),
    )

    CONFIG.declare(
        "write_gtep_results",
        ConfigValue(
            default=True,
            description="Boolean varaible whether to write gtep results to a csv file",
            domain=bool,
        ),
    )

    CONFIG.declare(
        "logger",
        ConfigValue(
            default=idaeslog.getLogger(__name__),
            description="The logger object or name to use for reporting.",
        ),
    )

    return CONFIG


def check_config(config):
    if config.print_level == 0:
        config.logger.setLevel(idaeslog.CRITICAL)
    elif config.print_level == 1:
        config.logger.setLevel(idaeslog.ERROR)
    elif config.print_level == 2:
        config.logger.setLevel(idaeslog.WARNING)
    elif config.print_level == 3:
        config.logger.setLevel(idaeslog.INFO)
    elif config.print_level == 4:
        config.logger.setLevel(idaeslog.DEBUG)
    if (
        config.repn_day_method == "cost"
        or config.extreme_day_method != "load_shedding_cost"
    ) and config.time_horizon != 5:
        config.logger.error(
            "investment cost for %s years has not been calculated. switch to input-based clustering"
            % (config.time_horizon,)
        )
        config.repn_day_method = "input"
        config.extreme_day_method = "load_shedding_cost"
    if config.region != "ERCOT":
        config.logger.error(
            "we do not support %s region, switch to ERCOT" % (config.region,)
        )
