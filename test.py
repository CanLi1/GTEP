from gtep import *
import pyomo.common.unittest as unittest
import time as timemodule
import json
import pyomo.environ as pyo
import os.path

from algos.fullspace import create_model as create_fullspace_model

if not os.path.exists("test_data"):
    os.makedirs("test_data")


def write_json(data, fname):
    with open(fname, "w") as fp:
        json.dump(data, fp)


def read_json(fname):
    with open(fname, "r") as fp:
        data = json.load(fp)
    return data


def get_fname(n_days, horizon, component_string):
    return (
        "test_data/%sdays_%syears_" % (n_days, horizon)
        + component_string
        + ".json"
    )


class BasicTest(unittest.TestCase):

    def _make_small_model(self, n_days, horizon):
        newinstance = GTEP(
            repn_day_method="input",
            time_limit=100000,
            tee=True,
            algo="fullspace",
            clustering_algorithm="kmeans",
            num_repn_days=n_days,
            time_horizon=horizon, # Assume this is years
            formulation="improved",
            print_level=4,
        )
        return newinstance

    def _write_data(self, instance):
        """
        Writes the data stored in a model instance, presumably after
        it has been solved
        """
        n_days = instance.config.num_repn_days
        horizon = instance.config.time_horizon
        instance_name = "%sdays_%syears" % (n_days, horizon)
        model = instance.m

        var_data_dict = {}
        for var in model.component_data_objects(pyo.Var):
            name = str(pyo.ComponentUID(var))
            var_data_dict[name] = var.value

        con_data_dict = {}
        for con in model.component_data_objects(pyo.Constraint, active=True):
            name = str(pyo.ComponentUID(con))
            con_data_dict[name] = (
                pyo.value(con.lower), 
                pyo.value(con.body),
                pyo.value(con.upper),
            )

        param_data_dict = {}
        for param in model.component_data_objects(pyo.Param):
            if isinstance(param, pyo.Param):
                name = str(pyo.ComponentUID(param))
                param_data_dict[name] = pyo.value(param)

        obj_data_dict = {}
        for obj in model.component_data_objects(pyo.Objective, active=True):
            name = str(pyo.ComponentUID(obj))
            obj_data_dict[name] = pyo.value(obj)

        expr_data_dict = {}
        for expr in model.component_data_objects(pyo.Expression, active=True):
            name = str(pyo.ComponentUID(expr))
            expr_data_dict[name] = pyo.value(expr)

        var_fname = get_fname(n_days, horizon, "variables")
        con_fname = get_fname(n_days, horizon, "constraints")
        param_fname = get_fname(n_days, horizon, "parameters")
        obj_fname = get_fname(n_days, horizon, "objectives")
        expr_fname = get_fname(n_days, horizon, "expressions")
        write_json(var_data_dict, var_fname)
        write_json(con_data_dict, con_fname)
        write_json(param_data_dict, param_fname)
        write_json(obj_data_dict, obj_fname)
        write_json(expr_data_dict, expr_fname)

    def _write_solved_model_data(self, n_days, horizon):
        instance = self._make_small_model(n_days, horizon)
        instance.solve_model()
        self._write_data(instance)

    def _test_solve_model(self, n_days, horizon):
        """
        Here we solve the model, then look up var values and make
        sure they are what we expect from a previous solution.
        """
        instance = self._make_small_model(n_days, horizon)
        instance.solve_model()
        var_fname = get_fname(n_days, horizon, "variables")
        var_data = read_json(var_fname)
        for name, val in var_data.items():
            var = instance.m.find_component(name)
            self.assertAlmostEqual(val, var.value)

    def _test_constraints_and_objective_at_solution(self, n_days, horizon):
        """
        Here we do not solve the model, we simply load variable values from a
        previous solution and assert that constraints have the expression
        values we expect.
        """
        instance = self._make_small_model(n_days, horizon)
        model = create_fullspace_model(
            instance.config, instance.InvestData, instance.OperationalData
        )
        var_fname = get_fname(n_days, horizon, "variables")
        var_data = read_json(var_fname)
        for name, val in var_data.items():
            var = model.find_component(name)
            var.set_value(val, valid=True)

        con_fname = get_fname(n_days, horizon, "constraints")
        con_data = read_json(con_fname)
        for name, (lower, body, upper) in con_data.items():
            con = model.find_component(name)
            self.assertAlmostEqual(pyo.value(con.lower), lower)
            self.assertAlmostEqual(pyo.value(con.body), body)
            self.assertAlmostEqual(pyo.value(con.upper), upper)
        
        obj_fname = get_fname(n_days, horizon, "objectives")
        obj_data = read_json(obj_fname)
        for name, val in obj_data.items():
            obj = model.find_component(name)
            self.assertAlmostEqual(pyo.value(obj), val)

    def test_create_model_1day_1year_no_error(self):
        """
        We don't assert anything here, just create the model and
        hope we don't get an error.
        """
        instance = self._make_small_model(1, 1)
        model = create_fullspace_model(
            instance.config, instance.InvestData, instance.OperationalData
        )
        # We now have the Pyomo model. In theory we could go check all
        # sorts of things to make sure it looks like what we expect.

    def test_solve_model_1day_1year(self):
        self._test_solve_model(1, 1)

    def test_constraints_1day_1year(self):
        self._test_constraints_and_objective_at_solution(1, 1)

    def test_constraints_2day_2year(self):
        self._test_constraints_and_objective_at_solution(2, 2)


if __name__ == "__main__":
    unittest.main()
