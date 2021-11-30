import sqlite3 as sql
import os
import pandas as pd
import numpy as np


def read_representative_days(len_t, days, weights):

    ####################################################################################################################
    # Operational uncertainty data
    globals()["num_days"] = len(days)
    list_of_repr_days_per_scenario = list(range(1, len(days) + 1))
    n_ss = {}

    # Misleading (seasons not used) but used because of structure of old data
    # ############ LOAD ############
    selected_hours = []
    i = 1
    for day in days:
        selected_hours += list(range((day * 24 - 24), (day * 24)))
        n_ss[i] = weights[i - 1]
        i += 1
    globals()["n_ss"] = n_ss

    L_NE_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/L_Northeast_2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    L_NE_1.columns = list_of_repr_days_per_scenario
    L_W_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/L_West_2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    L_W_1.columns = list_of_repr_days_per_scenario
    L_C_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/L_Coastal_2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    L_C_1.columns = list_of_repr_days_per_scenario
    L_S_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/L_South_2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    L_S_1.columns = list_of_repr_days_per_scenario
    L_PH_1 = (
        pd.read_csv(
            "data/NSRDB_wind/for_cluster/L_South_2012.csv", index_col=0, header=0
        )
        .iloc[selected_hours, 1]
        .multiply(0)
    )
    L_PH_1.columns = list_of_repr_days_per_scenario

    L_1 = {}
    # growth_rate = 0.014
    growth_rate_high = 0.014
    growth_rate_medium = 0.014
    growth_rate_low = 0.014
    for t in range(1, len_t + 1):
        d_idx = 0
        for d in list_of_repr_days_per_scenario:
            s_idx = 0
            for ss in range(24):
                s = ss + 1
                if t >= 15:
                    L_1["Northeast", t, d, s] = L_NE_1.iat[s_idx + 24 * d_idx] * (
                        1 + growth_rate_medium * (t - 1)
                    )
                    L_1["West", t, d, s] = L_W_1.iat[s_idx + 24 * d_idx] * (
                        1 + growth_rate_low * (t - 1)
                    )
                    L_1["Coastal", t, d, s] = L_C_1.iat[s_idx + 24 * d_idx] * (
                        1 + growth_rate_high * (t - 1)
                    )
                    L_1["South", t, d, s] = L_S_1.iat[s_idx + 24 * d_idx] * (
                        1 + growth_rate_high * (t - 1)
                    )
                    L_1["Panhandle", t, d, s] = L_PH_1.iat[s_idx + 24 * d_idx] * (
                        1 + growth_rate_low * (t - 1)
                    )
                else:
                    L_1["Northeast", t, d, s] = L_NE_1.iat[s_idx + 24 * d_idx] * (
                        1 + growth_rate_medium * (t - 1)
                    )
                    L_1["West", t, d, s] = L_W_1.iat[s_idx + 24 * d_idx] * (
                        1 + growth_rate_low * (t - 1)
                    )
                    L_1["Coastal", t, d, s] = L_C_1.iat[s_idx + 24 * d_idx] * (
                        1 + growth_rate_high * (t - 1)
                    )
                    L_1["South", t, d, s] = L_S_1.iat[s_idx + 24 * d_idx] * (
                        1 + growth_rate_high * (t - 1)
                    )
                    L_1["Panhandle", t, d, s] = L_PH_1.iat[s_idx + 24 * d_idx] * (
                        1 + growth_rate_low * (t - 1)
                    )

                s_idx += 1
            d_idx += 1

    L_max = {}
    for t in range(1, len_t + 1):
        L_max[t] = 0
        for d in list_of_repr_days_per_scenario:
            s_idx = 0
            for ss in range(24):
                s = ss + 1
                L_max[t] = max(
                    L_max[t],
                    L_1["Northeast", t, d, s]
                    + L_1["West", t, d, s]
                    + L_1["Coastal", t, d, s]
                    + L_1["South", t, d, s],
                )

    L_by_scenario = [L_1]
    # print(L_by_scenario)
    globals()["L_by_scenario"] = L_by_scenario
    globals()["L_max"] = L_max

    # ############ CAPACITY FACTOR ############
    # -> solar CSP
    CF_CSP_NE_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Northeast_CSP2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_CSP_NE_1.columns = list_of_repr_days_per_scenario
    CF_CSP_W_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_West_CSP2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_CSP_W_1.columns = list_of_repr_days_per_scenario
    CF_CSP_C_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Coastal_CSP2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_CSP_C_1.columns = list_of_repr_days_per_scenario
    CF_CSP_S_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_South_CSP2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_CSP_S_1.columns = list_of_repr_days_per_scenario
    CF_CSP_PH_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Panhandle_CSP2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_CSP_PH_1.columns = list_of_repr_days_per_scenario

    # -> solar PVSAT
    CF_PV_NE_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Northeast_PV2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_PV_NE_1.columns = list_of_repr_days_per_scenario
    CF_PV_W_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_West_PV2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_PV_W_1.columns = list_of_repr_days_per_scenario
    CF_PV_C_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Coastal_PV2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_PV_C_1.columns = list_of_repr_days_per_scenario
    CF_PV_S_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_South_PV2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_PV_S_1.columns = list_of_repr_days_per_scenario
    CF_PV_PH_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Panhandle_PV2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_PV_PH_1.columns = list_of_repr_days_per_scenario

    # -> wind (old turbines)
    CF_wind_NE_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Northeast_wind2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_wind_NE_1.columns = list_of_repr_days_per_scenario
    CF_wind_W_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_West_wind2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_wind_W_1.columns = list_of_repr_days_per_scenario
    CF_wind_C_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Coastal_wind2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_wind_C_1.columns = list_of_repr_days_per_scenario
    CF_wind_S_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_South_wind2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_wind_S_1.columns = list_of_repr_days_per_scenario
    CF_wind_PH_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Panhandle_wind2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_wind_PH_1.columns = list_of_repr_days_per_scenario

    # -> wind new (new turbines)
    CF_wind_new_NE_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Northeast_wind2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_wind_new_NE_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_W_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_West_wind2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_wind_new_W_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_C_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Coastal_wind2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_wind_new_C_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_S_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_South_wind2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_wind_new_S_1.columns = list_of_repr_days_per_scenario
    CF_wind_new_PH_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Panhandle_wind2012.csv", index_col=0, header=0
    ).iloc[selected_hours, 1]
    CF_wind_new_PH_1.columns = list_of_repr_days_per_scenario

    cf_1 = {}
    for t in range(1, len_t + 1):
        d_idx = 0
        for d in list_of_repr_days_per_scenario:
            s_idx = 0
            for ss in range(24):
                s = ss + 1
                for i in ["csp-new"]:
                    cf_1[i, "Northeast", t, d, s] = CF_CSP_NE_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "West", t, d, s] = CF_CSP_W_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "Coastal", t, d, s] = CF_CSP_C_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "South", t, d, s] = CF_CSP_S_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "Panhandle", t, d, s] = CF_CSP_PH_1.iat[s_idx + 24 * d_idx]
                for i in ["pv-old", "pv-new"]:
                    cf_1[i, "Northeast", t, d, s] = CF_PV_NE_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "West", t, d, s] = CF_PV_W_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "Coastal", t, d, s] = CF_PV_C_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "South", t, d, s] = CF_PV_S_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "Panhandle", t, d, s] = CF_PV_PH_1.iat[s_idx + 24 * d_idx]
                for i in ["wind-old"]:
                    cf_1[i, "Northeast", t, d, s] = CF_wind_NE_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "West", t, d, s] = CF_wind_W_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "Coastal", t, d, s] = CF_wind_C_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "South", t, d, s] = CF_wind_S_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "Panhandle", t, d, s] = CF_wind_PH_1.iat[s_idx + 24 * d_idx]
                for i in ["wind-new"]:
                    cf_1[i, "Northeast", t, d, s] = CF_wind_new_NE_1.iat[
                        s_idx + 24 * d_idx
                    ]
                    cf_1[i, "West", t, d, s] = CF_wind_new_W_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "Coastal", t, d, s] = CF_wind_new_C_1.iat[
                        s_idx + 24 * d_idx
                    ]
                    cf_1[i, "South", t, d, s] = CF_wind_new_S_1.iat[s_idx + 24 * d_idx]
                    cf_1[i, "Panhandle", t, d, s] = CF_wind_new_PH_1.iat[
                        s_idx + 24 * d_idx
                    ]
                s_idx += 1
            d_idx += 1
    cf_by_scenario = [cf_1]

    # print(cf_by_scenario)
    globals()["cf_by_scenario"] = cf_by_scenario


def read_representative_days_mean(len_t, labels):
    # Operational uncertainty data
    globals()["num_days"] = len(np.unique(labels))
    list_of_repr_days_per_scenario = list(range(1, num_days + 1))
    n_ss = {}

    # Misleading (seasons not used) but used because of structure of old data
    # ############ LOAD ############
    selected_hours = []
    for i in range(1, num_days + 1):
        n_ss[i] = len(np.where(labels == i)[0])

    globals()["n_ss"] = n_ss

    L_NE_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/L_Northeast_2012.csv", index_col=0, header=0
    )
    L_W_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/L_West_2012.csv", index_col=0, header=0
    )
    L_C_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/L_Coastal_2012.csv", index_col=0, header=0
    )
    L_S_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/L_South_2012.csv", index_col=0, header=0
    )

    L_1 = {}
    # growth_rate = 0.014
    growth_rate_high = 0.014
    growth_rate_medium = 0.014
    growth_rate_low = 0.014
    for t in range(1, len_t + 1):
        for d in range(1, num_days + 1):
            selected_days = np.where(labels == d)[0]
            for ss in range(24):
                s = ss + 1
                selected_hours = selected_days * 24 + ss
                if t >= 15:
                    L_1["Northeast", t, d, s] = L_NE_1.iloc[
                        selected_hours, 1
                    ].mean() * (1 + growth_rate_medium * (t - 1))
                    L_1["West", t, d, s] = L_W_1.iloc[selected_hours, 1].mean() * (
                        1 + growth_rate_low * (t - 1)
                    )
                    L_1["Coastal", t, d, s] = L_C_1.iloc[selected_hours, 1].mean() * (
                        1 + growth_rate_high * (t - 1)
                    )
                    L_1["South", t, d, s] = L_S_1.iloc[selected_hours, 1].mean() * (
                        1 + growth_rate_high * (t - 1)
                    )
                    L_1["Panhandle", t, d, s] = 0.0
                else:
                    L_1["Northeast", t, d, s] = L_NE_1.iloc[
                        selected_hours, 1
                    ].mean() * (1 + growth_rate_medium * (t - 1))
                    L_1["West", t, d, s] = L_W_1.iloc[selected_hours, 1].mean() * (
                        1 + growth_rate_low * (t - 1)
                    )
                    L_1["Coastal", t, d, s] = L_C_1.iloc[selected_hours, 1].mean() * (
                        1 + growth_rate_high * (t - 1)
                    )
                    L_1["South", t, d, s] = L_S_1.iloc[selected_hours, 1].mean() * (
                        1 + growth_rate_high * (t - 1)
                    )
                    L_1["Panhandle", t, d, s] = 0.0

    L_max = {}
    for t in range(1, len_t + 1):
        L_max[t] = 0
        for d in range(1, num_days + 1):
            s_idx = 0
            for ss in range(24):
                s = ss + 1
                L_max[t] = max(
                    L_max[t],
                    L_1["Northeast", t, d, s]
                    + L_1["West", t, d, s]
                    + L_1["Coastal", t, d, s]
                    + L_1["South", t, d, s],
                )

    L_by_scenario = [L_1]
    # print(L_by_scenario)
    globals()["L_by_scenario"] = L_by_scenario
    globals()["L_max"] = L_max

    # ############ CAPACITY FACTOR ############
    # -> solar CSP
    CF_CSP_NE_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Northeast_CSP2012.csv", index_col=0, header=0
    )
    CF_CSP_W_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_West_CSP2012.csv", index_col=0, header=0
    )
    CF_CSP_C_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Coastal_CSP2012.csv", index_col=0, header=0
    )
    CF_CSP_S_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_South_CSP2012.csv", index_col=0, header=0
    )
    CF_CSP_PH_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Panhandle_CSP2012.csv", index_col=0, header=0
    )

    # -> solar PVSAT
    CF_PV_NE_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Northeast_PV2012.csv", index_col=0, header=0
    )
    CF_PV_W_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_West_PV2012.csv", index_col=0, header=0
    )
    CF_PV_C_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Coastal_PV2012.csv", index_col=0, header=0
    )
    CF_PV_S_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_South_PV2012.csv", index_col=0, header=0
    )
    CF_PV_PH_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Panhandle_PV2012.csv", index_col=0, header=0
    )

    # -> wind (old and new turbines)
    CF_wind_NE_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Northeast_wind2012.csv", index_col=0, header=0
    )
    CF_wind_W_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_West_wind2012.csv", index_col=0, header=0
    )
    CF_wind_C_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Coastal_wind2012.csv", index_col=0, header=0
    )
    CF_wind_S_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_South_wind2012.csv", index_col=0, header=0
    )
    CF_wind_PH_1 = pd.read_csv(
        "data/NSRDB_wind/for_cluster/CF_Panhandle_wind2012.csv", index_col=0, header=0
    )

    cf_1 = {}
    for t in range(1, len_t + 1):
        for d in range(1, num_days + 1):
            selected_days = np.where(labels == d)[0]
            for ss in range(24):
                selected_hours = selected_days * 24 + ss
                s = ss + 1
                for i in ["csp-new"]:
                    cf_1[i, "Northeast", t, d, s] = CF_CSP_NE_1.iloc[
                        selected_hours, 1
                    ].mean()
                    cf_1[i, "West", t, d, s] = CF_CSP_W_1.iloc[selected_hours, 1].mean()
                    cf_1[i, "Coastal", t, d, s] = CF_CSP_C_1.iloc[
                        selected_hours, 1
                    ].mean()
                    cf_1[i, "South", t, d, s] = CF_CSP_S_1.iloc[
                        selected_hours, 1
                    ].mean()
                    cf_1[i, "Panhandle", t, d, s] = CF_CSP_PH_1.iloc[
                        selected_hours, 1
                    ].mean()
                for i in ["pv-old", "pv-new"]:
                    cf_1[i, "Northeast", t, d, s] = CF_PV_NE_1.iloc[
                        selected_hours, 1
                    ].mean()
                    cf_1[i, "West", t, d, s] = CF_PV_W_1.iloc[selected_hours, 1].mean()
                    cf_1[i, "Coastal", t, d, s] = CF_PV_C_1.iloc[
                        selected_hours, 1
                    ].mean()
                    cf_1[i, "South", t, d, s] = CF_PV_S_1.iloc[selected_hours, 1].mean()
                    cf_1[i, "Panhandle", t, d, s] = CF_PV_PH_1.iloc[
                        selected_hours, 1
                    ].mean()
                for i in ["wind-old", "wind-new"]:
                    cf_1[i, "Northeast", t, d, s] = CF_wind_NE_1.iloc[
                        selected_hours, 1
                    ].mean()
                    cf_1[i, "West", t, d, s] = CF_wind_W_1.iloc[
                        selected_hours, 1
                    ].mean()
                    cf_1[i, "Coastal", t, d, s] = CF_wind_C_1.iloc[
                        selected_hours, 1
                    ].mean()
                    cf_1[i, "South", t, d, s] = CF_wind_S_1.iloc[
                        selected_hours, 1
                    ].mean()
                    cf_1[i, "Panhandle", t, d, s] = CF_wind_PH_1.iloc[
                        selected_hours, 1
                    ].mean()

    cf_by_scenario = [cf_1]

    # print(cf_by_scenario)
    globals()["cf_by_scenario"] = cf_by_scenario

    # Strategic uncertainty data


def read_strategic_uncertainty(len_t, peak_load="L", tax="M"):
    # Different scenarios for PEAK LOAD:
    L_max_scenario = {
        "L": L_max,
        "M": {t: 1.05 * L_max[t] for t in L_max},
        "H": {t: 1.2 * L_max[t] for t in L_max},
    }
    # print(L_max_scenario)

    L_max_s = L_max_scenario[peak_load]
    # for stage in stages:
    #     for n in n_stage[stage]:
    #         for t in t_per_stage[stage]:
    #             if stage == 1:
    #                 L_max_s[t, stage, n] = L_max_scenario['M'][t]
    #             else:
    #                 m = n[-1]
    #                 if m == 'L':
    #                     L_max_s[t, stage, n] = L_max_scenario['L'][t]
    #                 elif m == 'M':
    #                     L_max_s[t, stage, n] = L_max_scenario['M'][t]
    #                 elif m == 'H':
    #                     L_max_s[t, stage, n] = L_max_scenario['H'][t]
    globals()["L_max_s"] = L_max_s

    # Different scenarios for CARBON TAX:
    tx_CO2_scenario = {
        (2, "L"): 0,
        (2, "M"): 0.050,
        (2, "H"): 0.100,
        (3, "L"): 0,
        (3, "M"): 0.065,
        (3, "H"): 0.131,
        (4, "L"): 0,
        (4, "M"): 0.081,
        (4, "H"): 0.162,
        (5, "L"): 0,
        (5, "M"): 0.096,
        (5, "H"): 0.192,
        (6, "L"): 0,
        (6, "M"): 0.112,
        (6, "H"): 0.223,
        (7, "L"): 0,
        (7, "M"): 0.127,
        (7, "H"): 0.254,
        (8, "L"): 0,
        (8, "M"): 0.142,
        (8, "H"): 0.285,
        (9, "L"): 0,
        (9, "M"): 0.158,
        (9, "H"): 0.315,
        (10, "L"): 0,
        (10, "M"): 0.173,
        (10, "H"): 0.346,
        (11, "L"): 0,
        (11, "M"): 0.188,
        (11, "H"): 0.377,
        (12, "L"): 0,
        (12, "M"): 0.204,
        (12, "H"): 0.408,
        (13, "L"): 0,
        (13, "M"): 0.219,
        (13, "H"): 0.438,
        (14, "L"): 0,
        (14, "M"): 0.235,
        (14, "H"): 0.469,
        (15, "L"): 0,
        (15, "M"): 0.250,
        (15, "H"): 0.500,
        (16, "L"): 0,
        (16, "M"): 0.265,
        (16, "H"): 0.500,
        (17, "L"): 0,
        (17, "M"): 0.280,
        (17, "H"): 0.500,
        (18, "L"): 0,
        (18, "M"): 0.295,
        (18, "H"): 0.500,
        (19, "L"): 0,
        (19, "M"): 0.310,
        (19, "H"): 0.500,
        (20, "L"): 0,
        (20, "M"): 0.325,
        (20, "H"): 0.500,
    }
    tx_CO2 = {}
    for key in tx_CO2_scenario:
        if key[0] <= len_t and key[1] == tax:
            tx_CO2[key[0]] = tx_CO2_scenario[key]

    globals()["tx_CO2"] = tx_CO2

    # # Different scenarios for NG PRICE:
    # ng_price_scenarios = {(1, 'L'): 3.117563, (1, 'M'): 3.4014395, (1, 'H'): 4.249755,
    #                       (2, 'L'): 2.976701, (2, 'M'): 3.357056, (2, 'H'): 4.188047,
    #                       (3, 'L'): 2.974117, (3, 'M'): 3.4164015, (3, 'H'): 4.228118,
    #                       (4, 'L'): 3.082466, (4, 'M'): 3.578708, (4, 'H'): 4.403251,
    #                       (5, 'L'): 3.236482, (5, 'M'): 3.8122265, (5, 'H'): 4.745406,
    #                       (6, 'L'): 3.394663, (6, 'M'): 3.9940535, (6, 'H'): 5.088468,
    #                       (7, 'L'): 3.479183, (7, 'M'): 4.0682835, (7, 'H'): 5.442574,
    #                       (8, 'L'): 3.504514, (8, 'M'): 4.117297, (8, 'H'): 5.565526,
    #                       (9, 'L'): 3.498631, (9, 'M'): 4.188261, (9, 'H'): 5.82389,
    #                       (10, 'L'): 3.490988, (10, 'M'): 4.219348, (10, 'H'): 5.905959,
    #                       (11, 'L'): 3.483505, (11, 'M'): 4.250815, (11, 'H'): 5.955,
    #                       (12, 'L'): 3.496959, (12, 'M'): 4.2411075, (12, 'H'): 6.013945,
    #                       (13, 'L'): 3.534126, (13, 'M'): 4.3724575, (13, 'H'): 6.17547,
    #                       (14, 'L'): 3.57645, (14, 'M'): 4.4414835, (14, 'H'): 6.240099,
    #                       (15, 'L'): 3.585003, (15, 'M'): 4.47585855, (15, 'H'): 6.41513
    #                       }
    # for t in range(1, 16):
    #     ng_price_scenarios[t, 'H'] = 1.5 * ng_price_scenarios[t, 'H']

    # th_generators = ['coal-st-old1', 'coal-igcc-new', 'coal-igcc-ccs-new', 'ng-ct-old',
    #                  'ng-cc-old', 'ng-st-old', 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new']
    # ng_generators = ['ng-ct-old', 'ng-cc-old', 'ng-st-old', 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new']
    # # 'nuc-st-old', 'nuc-st-new',

    # P_fuel_scenarios = {}
    # for stage in stages:
    #     for t in t_per_stage[stage]:
    #         for i in th_generators:
    #             if stage == 1:
    #                 P_fuel_scenarios[i, t, stage, 'O'] = P_fuel[i, t]
    #             else:
    #                 for n in ['M']:
    #                     if i in ng_generators:
    #                         P_fuel_scenarios[i, t, stage, n] = ng_price_scenarios[t, n]
    #                     else:
    #                         P_fuel_scenarios[i, t, stage, n] = P_fuel[i, t]
    # globals()["P_fuel_scenarios"] = P_fuel_scenarios
