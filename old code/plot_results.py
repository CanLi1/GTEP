import matplotlib.pyplot as plt
import numpy as np

# cases = ['Reference case\nwith NG price\nuncertainty', '"No nuclear" case\nwith NG price\nuncertainty',
#          '"No nuclear" case\nwith carbon tax\nuncertainty', '"No nuclear" case\nwith HIGH carbon tax\nuncertainty']
# coal = np.array([17.4, 17.40, 17.40, 17.40])
# natural_gas = np.array([55.63, 60.64, 60.64, 60.60])
# nuclear = np.array([5.16, 0, 0, 0])
# solar = np.array([0.71, 0.66, 0.66, 1.41])
# wind = np.array([20.54, 20.54, 20.54, 20.58])
# storage = np.array([0, 0, 0, 0])
# ind = [x for x, _ in enumerate(cases)]
#
# plt.bar(ind, storage, width=0.7, label='storage', color='black', bottom=nuclear+coal+natural_gas+wind+solar)
# plt.bar(ind, solar, width=0.7, label='solar', color='red', bottom=nuclear+coal+natural_gas+wind)
# plt.bar(ind, wind, width=0.7, label='wind', color='limegreen', hatch="//", bottom=nuclear+coal+natural_gas)
# plt.bar(ind, natural_gas, width=0.7, label='natural gas', color='darkorange', hatch="*", bottom=nuclear+coal)
# plt.bar(ind, coal, width=0.7, label='coal', color='dodgerblue', hatch="+", bottom=nuclear)
# plt.bar(ind, nuclear, width=0.7, color='darkorchid', hatch="o", label='nuclear')
#
# plt.xticks(ind, cases)
# plt.ylabel("Generation capacity in the first year\nof the planning horizon [GW]")
# # plt.xlabel("Number of stages in the scenario tree")
# plt.subplots_adjust(right=0.7)
#
# plt.legend(bbox_to_anchor=(1.04, 0.5), loc="center left", borderaxespad=0)
# # plt.figure(figsize=(20, 10))
#
# plt.ylim(0, 120)
# plt.show()

cases = ['"No nuclear" case\nwith HIGH carbon tax\nuncertainty', 'Deterministic "No nuclear" case\nusing average '
                                                                 'of\nHIGH carbon tax realizations']
coal_st = np.array([17.4, 17.40])
ng_cc = np.array([44.43, 40.73])
ng_cc_ccs = np.array([0, 5.44])
ng_ct = np.array([9.79, 8.11])
ng_st = np.array([5.54, 5.54])
pv = np.array([1.41, 1.41])
wind = np.array([20.58, 22.11])
ind = [x for x, _ in enumerate(cases)]

plt.bar(ind, pv, width=0.7, label='pv', color='red', bottom=coal_st+ng_st+ng_ct+ng_cc+ng_cc_ccs+wind)
plt.bar(ind, wind, width=0.7, label='wind', color='limegreen', hatch="//", bottom=coal_st+ng_st+ng_ct+ng_cc+ng_cc_ccs)
plt.bar(ind, ng_cc_ccs, width=0.7, label='ng-ccs', color='pink', hatch="o", bottom=coal_st+ng_st+ng_ct+ng_cc)
plt.bar(ind, ng_cc, width=0.7, label='ng-cc', color='mediumvioletred', hatch="*", bottom=coal_st+ng_st+ng_ct)
plt.bar(ind, ng_ct, width=0.7, label='ng-ct', color='yellow', hatch="O", bottom=coal_st+ng_st)
plt.bar(ind, ng_st, width=0.7, label='ng-st', color='darkorange', hatch=".", bottom=coal_st)
plt.bar(ind, coal_st, width=0.7, label='coal-st', color='dodgerblue', hatch="+")

plt.xticks(ind, cases)
plt.ylabel("Generation capacity in the first year\nof the planning horizon [GW]")
# plt.xlabel("Number of stages in the scenario tree")
plt.subplots_adjust(right=0.7)

plt.legend(bbox_to_anchor=(1.04, 0.5), loc="center left", borderaxespad=0)
# plt.figure(figsize=(20, 10))

plt.ylim(0, 120)
plt.show()

