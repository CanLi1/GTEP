from ModelGeneration3_block import *
from pyomo.repn.standard_repn import generate_standard_repn
import time
import logging
import networkx as nx
import statistics
import random
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.DEBUG)


def add_weight_terms(contrlist):
    """Add weight terms to the objective function of each scenario block

    Arguments:
        contrlist {constraint_list()} -- The constraint list that need to be relaxed
    """
    for index, c in contrlist.iteritems():
        repn = generate_standard_repn(c.body)
        for var, coef in zip(repn.linear_vars, repn.linear_coefs):
            obj = next(var.parent_block().component_data_objects(
                ctype=Objective, active=True))
            obj.expr += model.lambd[index] * var * coef


def bound_calculate(model, scenarios, opt):
    # heuristic 1: y_drill fix
    '''
    for w, p in model.wp_tuple:
        for f in model.f:
            v = 0
            for s in model.s:
                v += model.prob[s] * \
                    model.scenario_block[s].y_drill[w, p, f, 1].value
            # print(v)
            v = round(v)
            # print(v)
            for s in bound_model.s:
                bound_model.scenario_block[s].y_drill[w, p, f, 1].fix(v)
    '''
    # heuristic 2: pick the largest 4 decisions
    '''
    average_value = []
    for w, p in model.wp_tuple:
        for f in model.f:
            v = 0
            for s in model.s:
                v += model.prob[s] * \
                    model.scenario_block[s].y_drill[w, p, f, 1].value
            average_value.append([v, (w, p, f)])
    average_value.sort(key=lambda x: x[0], reverse=True)
    chace = []
    picked_set = []
    for i in average_value:
        if i[1][1] not in chace and (i[1][0], i[1][2]) not in chace:
            chace.append(i[1][1])
            chace.append((i[1][0], i[1][2]))
            picked_set.append(i)
        if len(picked_set) >= 4:
            break
    for s in bound_model.s:
        bound_model.scenario_block[s].y_drill[:, :, :, 1].fix(0)
        for i in picked_set:
            bound_model.scenario_block[s].y_drill[i[1], 1].fix(1)
    '''
    # heuristic 3: select one scenario
    '''
    for w, p in bound_model.wp_tuple:
        for f in bound_model.f:
            for t in bound_model.t:
                for s in bound_model.s:
                    bound_model.scenario_block[s].y_drill[w, p, f, t].fix(round(
                        model.scenario_block[model.s.last()].y_drill[w, p, f, t].value))
    '''

    # heurstic 4:
    '''
    ss = list(model.ss_tuple.data())
    G = nx.Graph()
    G.add_edges_from(ss)
    removed_pairs = []
    drilled_well = {s: [] for s in model.s}  # 这个是根据picked_s fix的解
    original_drilled_well = {s: [] for s in model.s}  # 这个是原本每个subproblem的解

    # 每一个t分别来判断
    for t in model.t:
        if model.s.__len__() == nx.number_connected_components(G):
            break
        connected_set_list = list(nx.connected_components(G))
        original_drilled_well_t = {s: [] for s in model.s}

        # 先存下每个scenario原本的解至original_drilled_well和original_drilled_well_t中
        for s in model.s:
            for w, p in model.wp_tuple:
                for f in model.f:
                    if round(model.scenario_block[s].y_drill[w, p, f, t].value) == 1:
                        original_drilled_well_t[s].append([w, p, f])
                        # original_drilled_well_t[s].append((w, f))
                        # original_drilled_well不应该在这里更新，应该在后面
                        # original_drilled_well[s].append((w, p, f))
                        # original_drilled_well[s].append((w, f))

        # 开始按照connected_set遍历每一个scenario
        for connected_set in connected_set_list:
            connected_set = list(connected_set)
            print('connected_set', connected_set)
            drilled_well_t = []
            if len(connected_set) == 1:
                continue
            else:
                # 选取picked_s
                picked_s = connected_set[0]
                print('picked_s', picked_s)
                # picked_s这个周期drill的well可能跟它之前的重复了，所以需要进一步判断
                temp = original_drilled_well_t[picked_s].copy()
                print('temp: ', temp)
                drilled_well_picked_s_2d = [[w, f]
                                            for w, _, f in drilled_well[picked_s]]
                temp_p = [p for _, p, _ in drilled_well[picked_s]]
                for index, i in enumerate(temp):
                    if [i[0], i[2]] in drilled_well_picked_s_2d:
                        choices = [[w, p, f] for w, p, f in original_drilled_well[picked_s] if [
                            w, f] not in drilled_well_picked_s_2d and p not in temp_p]
                        temp[index] = random.sample(choices, 1)[0]
                print('final temp: ', temp)
                # fix the according to the picked_s
                for s in connected_set:
                    # 初始化，将所有的y_drill全部fix为0
                    bound_model.scenario_block[s].y_drill[:, :, :, t].fix(0)
                    for w, p, f in temp:
                        bound_model.scenario_block[s].y_drill[w, p, f, t].fix(
                            1)
                        # append final temp to drilled_well
                        drilled_well[s].append([w, p, f])
                for w, _, _ in temp:
                    drilled_well_t.append(w)
            drilled_well_t = list(dict.fromkeys(drilled_well_t))
            print('drilled_well_t', drilled_well_t)
            # update the graph, remove some edges
            removing_pairs = []
            for w in drilled_well_t:
                for (s1, s2) in ss:
                    if w in model.w_ss[s1, s2] and s1 in connected_set and s2 in connected_set:
                        removing_pairs.append((s1, s2))
            removing_pairs = list(dict.fromkeys(removing_pairs))
            removing_pairs = [
                i for i in removing_pairs if i not in removed_pairs]
            removed_pairs += removing_pairs
            for s1, s2 in removing_pairs:
                G.remove_edge(s1, s2)
                ss.remove((s1, s2))
        for s in model.s:
            original_drilled_well[s] += original_drilled_well_t[s]
    print(drilled_well)
    '''

    # heurstic 5:与heurstic 4不同，heurstic 5一直选定一个scenario来进行fix

    ss = list(model.ss_tuple.data())
    G = nx.Graph()
    G.add_edges_from(ss)
    removed_pairs = []
    # 选取picked_s
    picked_s = model.s.last()
    # print('picked_s', picked_s)

    # 每一个t分别来判断
    for t in model.t:
        # nx.draw(G, with_labels=True, label='t='+str(t))
        # plt.show()
        # plt.savefig('t'+str(t)+'.png')

        if model.s.__len__() == nx.number_connected_components(G):
            break

        connected_set_list = list(nx.connected_components(G))
        # print('t = ', t, ', connected_set_list = ', connected_set_list)
        drilled_well_t = []

        # 先存下每个scenario原本的解至original_drilled_well和original_drilled_well_t中
        for w, p in model.wp_tuple:
            for f in model.f:
                if round(model.scenario_block[picked_s].y_drill[w, p, f, t].value) == 1:
                    drilled_well_t.append(w)

        # 开始按照connected_set遍历每一个scenario
        for connected_set in connected_set_list:
            connected_set = list(connected_set)
            # print('connected_set', connected_set)

            if len(connected_set) == 1:
                continue
            else:
                # fix the according to the picked_s
                for s in connected_set:
                    for w, p in model.wp_tuple:
                        for f in model.f:
                            model.scenario_block[s].y_drill[w, p, f, t].fix(round(
                                model.scenario_block[picked_s].y_drill[w, p, f, t].value))
                    for r in model.r:
                        for p in model.p:
                            model.scenario_block[s].y_rig[r, p, t].fix(
                                round(model.scenario_block[picked_s].y_rig[r, p, t].value))
                    for n1, n2 in model.m_n_tuple_fixed:
                        for d in model.d:
                            model.scenario_block[s].z_pipe[n1, n2, d, t].fix(
                                round(model.scenario_block[picked_s].z_pipe[n1, n2, d, t].value))

            drilled_well_t = list(dict.fromkeys(drilled_well_t))
            # print('drilled_well_t', drilled_well_t)
            # update the graph, remove some edges
            removing_pairs = []
            for w in drilled_well_t:
                for (s1, s2) in ss:
                    if w in model.w_ss[s1, s2] and s1 in connected_set and s2 in connected_set:
                        removing_pairs.append((s1, s2))
            removing_pairs = list(dict.fromkeys(removing_pairs))
            removing_pairs = [
                i for i in removing_pairs if i not in removed_pairs]
            removed_pairs += removing_pairs
            for s1, s2 in removing_pairs:
                G.remove_edge(s1, s2)
                ss.remove((s1, s2))

    for s in model.s.data():
        # print('solve bound subproblem', s)
        result = opt.solve(model.scenario_block[s])  # , tee=True)
    print('result of subproblem: ', value(model.total_npv))

    for s in model.s.data():
        model.scenario_block[s].unfix_all_vars()
    return value(model.total_npv)


# Get the model
case = 4
model = ModelGeneration(case_flag=case, shutin_flag=False, pipeline_flag=False,
                        aggregated_flag=True, shutin_formulation_flag=True, pipeline_state_action_flag=False)
print('model build')

# Options for mip solvers
mipsolver_time = [600, 200, 50, 50]
boundsolver_time = [1800, 1800, 600, 600]
mipsolver = SolverFactory('cplex')
mipsolver.options['mipgap'] = 0.0001
mipsolver.options['threads'] = 1
mipsolver.options['timelimit'] = mipsolver_time[case - 1]
# boundsolver = SolverFactory('cplex')
# boundsolver.options['mipgap'] = 0.01
# boundsolver.options['threads'] = 1
# boundsolver.options['timelimit'] = boundsolver_time[case - 1]

# get the upper bound for multiplier update

# temp_model = model.clone()
# for s in temp_model.s.data():
#     next(temp_model.scenario_block[s].component_data_objects(
#         ctype=Objective, active=True)).deactivate()
#     # model.Bl[s].Cost_Objective.deactivate()
# TransformationFactory('gdp.bigm').apply_to(temp_model)
# result = mipsolver.solve(temp_model)  # , tee=True)
# ub = result.Problem.upper_bound
# print('optimal solution is: ', ub)
# print(result)

model.cnac_disjunction.deactivate()
model.cnac_disjunct.deactivate()
model.logic_rule21.deactivate()
model.logic_rule23.deactivate()


# Define and initialize lagrangean multipliers
model.num_nac = RangeSet(model.inac.__len__())
model.lambd = Param(model.num_nac, initialize=0, mutable=True)


# a = model.find_component('Bl')
# a = model.component('DevotedAcreage')
# print(a)
# print(type(a))
# help(model.Bl)

# help(model)
for s in model.s.data():
    model.scenario_block[s].unfix_all_vars()
# model.unfix_all_vars()

# Add weight_terms to objective functions
add_weight_terms(model.inac)

# Parameters for Lagrangean decomposition
alpha = 1
best_obj = -1E12
count = 0
startime = time.time()
print('iteration begins')
# Iteration begins
for k in range(5):
    # Solve subrproblems
    logging.info('Solve subrproblems')
    time_list = []
    for s in model.s.data():
        # print(s)
        result = mipsolver.solve(model.scenario_block[s])  # , tee=True)
        time_list.append(result.Solver.user_time)
    print('Average subproblem solving time: %.2f',
          statistics.mean(time_list))

    # Calculate subgradient
    logging.info('Calculate subgradient')
    subg = []
    for i in model.num_nac.data():
        subg.append(value(model.inac[i].body))
    # print('subg: ', subg)

    # Calculate the lower bound
    lb = sum(value(model.scenario_block[s].npv) for s in model.s.data())
    if best_obj <= lb:
        best_obj = lb

        # best_lambd = []
        # for i in model.num_nac.data():
        #     best_lambd.append(model.lambd[i].value)
        # print(best_lambd)
        count = 0
    else:
        count += 1

    if count > 5:
        alpha = alpha / 2
        count = 0
        print('alpha half cutted, alpha=', alpha)

        # for i in model.num_nac.data():
        #     model.lambd[i] = best_lambd[i-1]
        # print(best_lambd)

    # Calculate upper bound
    print('caculate bound')
    ub = bound_calculate(model, model.s.data(), mipsolver)
    # logging.info('Iteration %d, lb %.2f, ub %.2f, time %.2f',
    #              k + 1, lb, ub, time.time() - startime)
    print('Iteration', k + 1, 'lb: ', round(lb, 2), 'ub: ',
          round(ub, 2), 'time:', round(time.time() - startime, 2))

    # Calculate stepsize
    stepsize = alpha * (ub - lb) / sum(i * i for i in subg)

    # Update Lagrangean multipliers
    for i in model.num_nac.data():
        model.lambd[i] = model.lambd[i].value + abs(stepsize) * subg[i-1]
    # model.lambd.pprint()
print('best obj found = ', best_obj)
