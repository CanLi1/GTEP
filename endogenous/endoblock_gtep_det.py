# Generation and Transmission Expansion Planning 
# IDAES project
# author: Can Li 
# date: 10/09/2017
# Model available at http://www.optimization-online.org/DB_FILE/2017/08/6162.pdf

from pyomo.environ import *
import math



def create_model(time_periods, formulation, readData_det, num_scenario):
    m = ConcreteModel()

    # ################################## Declare of sets ##################################
    '''
        Set Notation:
        m.r: regions
        m.i: generators
        m.th: thermal generators
        m.rn: renewable generators
        m.co: coal-based generators
            coal-st-old1: cluster of existing coal steam turbine generators
            coal-igcc-new: cluster of potential coal IGCC generators
            coal-igcc-ccs-new: cluster of potential coal IGCC generators with carbon capture
        m.ng: natural gas (NG) generators
            ng-ct-old: cluster of existing NG combustion-fired turbine generators
            ng-cc-old: cluster of existing NG combined-cycle generators
            ng-st-old: cluster of existing NG steam-turbine generators
            ng-cc-new: cluster of potential NG combined-cycle generators
            ng-cc-ccs-new: cluster of potential NG combined-cycle generators with carbon capture
            ng-ct-new: cluster of potential NG combustion-fired turbine generators
        m.nu: nuclear generators
            nuc-st-old: cluster of existing nuclear steam turbine generators
            nuc-st-new: cluster of potential nuclear steam turbine generators
        m.pv: solar photovoltaic generators
            pv-old: cluster of existing solar photovoltaic generators
            pv-new: cluster of potential solar photovoltaic generators
        m.csp: concentrated solar panels
            csp-new: cluster of potential concentrated solar panels
        m.wi: wind turbines
            wind-old: cluster of existing wind turbines
            wind-new: cluster of potential wind turbines
        m.old: subset of existing generators
        m.new: subset of potential generators
        m.rold: subset of existing renewable generators
        m.rnew: subset of potential renewable generators
        m.told: subset of existing thermal generators
        m.tnew: subset of potential thermal generators

        m.j: clusters of potential storage unit

        m.d: set of representative days

        m.hours: set of subperiods within the days

        m.t: set of time periods

        m.l: set of transmission lines
        m.l_old: set of existing transmission lines
        m.l_new: set of prospective transmission lines

        m.stage: set of stages in the scenario tree
    '''
    m.r = Set(initialize=['Northeast', 'West', 'Coastal', 'South', 'Panhandle'], ordered=True)
    m.i = Set(initialize=['coal-st-old1', 'ng-ct-old', 'ng-cc-old', 'ng-st-old', 'pv-old', 'wind-old',
                          'wind-new', 'pv-new', 'csp-new', 'coal-igcc-new', 'coal-igcc-ccs-new',
                          'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new','nuc-st-old','nuc-st-new','coal-first-new'], ordered=True)
    # 'nuc-st-old', 'nuc-st-new',
    m.th = Set(within=m.i, initialize=['coal-st-old1', 'coal-igcc-new', 'coal-igcc-ccs-new',
                                       'ng-ct-old', 'ng-cc-old', 'ng-st-old', 'ng-cc-new', 'ng-cc-ccs-new',
                                       'ng-ct-new','nuc-st-old', 'nuc-st-new', 'coal-first-new'], ordered=True)
    # 'nuc-st-old', 'nuc-st-new',
    m.rn = Set(within=m.i, initialize=['pv-old', 'pv-new', 'csp-new', 'wind-old', 'wind-new'], ordered=True)
    m.co = Set(within=m.th, initialize=['coal-st-old1', 'coal-igcc-new', 'coal-igcc-ccs-new', 'coal-first-new'], ordered=True)
    m.ng = Set(within=m.th, initialize=['ng-ct-old', 'ng-cc-old', 'ng-st-old', 'ng-cc-new', 'ng-cc-ccs-new',
                                        'ng-ct-new'], ordered=True)
    m.nu = Set(within=m.th, initialize=['nuc-st-old', 'nuc-st-new'], ordered=True)
    m.pv = Set(within=m.rn, initialize=['pv-old', 'pv-new'], ordered=True)
    m.csp = Set(within=m.rn, initialize=['csp-new'], ordered=True)
    m.wi = Set(within=m.rn, initialize=['wind-old', 'wind-new'], ordered=True)
    m.old = Set(within=m.i, initialize=['coal-st-old1', 'ng-ct-old', 'ng-cc-old', 'ng-st-old', 'pv-old',
                                        'wind-old','nuc-st-old'], ordered=True)
    m.new = Set(within=m.i, initialize=['wind-new', 'pv-new', 'csp-new', 'coal-igcc-new',
                                        'coal-igcc-ccs-new', 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new','nuc-st-new', 'coal-first-new'], ordered=True)
    m.rold = Set(within=m.old, initialize=['pv-old', 'wind-old'], ordered=True)
    m.rnew = Set(within=m.new, initialize=['wind-new', 'pv-new', 'csp-new'], ordered=True)
    m.told = Set(within=m.old, initialize=['coal-st-old1', 'ng-ct-old', 'ng-cc-old', 'ng-st-old','nuc-st-old'],
                 ordered=True)

    m.tnew = Set(within=m.new, initialize=['coal-igcc-new', 'coal-igcc-ccs-new', 'ng-cc-new',
                                           'ng-cc-ccs-new', 'ng-ct-new','nuc-st-new', 'coal-first-new'], ordered=True)
    m.j = Set(initialize=['Li_ion', 'Lead_acid', 'Flow'], ordered=True)

    m.d = RangeSet(readData_det.num_days)
    #  Misleading (seasons not used) but used because of structure of old data

    m.hours = RangeSet(24)

    m.t = RangeSet(time_periods)
    m.scenarios = RangeSet(num_scenario)
    nlines = len(readData_det.tielines)
    m.l = RangeSet(nlines)
    
    m.l_old = Set(within=m.l)
    m.l_new = RangeSet(nlines)


    # ################################## Import parameters ############################################
    m.Ng_old = Param(m.i, m.r, default=0, initialize=readData_det.Ng_old)

    def i_r_filter(m, i, r):
        return (i in m.new ) or (i in m.old and m.Ng_old[i, r] != 0)

    m.i_r = Set(initialize=m.i * m.r, filter=i_r_filter, ordered=True)

    def rn_r_filter(m, rn, r):
        return rn in m.rnew or (rn in m.rold and m.Ng_old[rn, r] != 0)

    m.rn_r = Set(initialize=m.rn * m.r, filter=rn_r_filter, ordered=True)

    def th_r_filter(m, th, r):
        return th in m.tnew or (th in m.told and m.Ng_old[th, r] != 0)

    m.th_r = Set(initialize=m.th * m.r, filter=th_r_filter, ordered=True)

    #if there is a transmission line between region 
    def l_rr_filter(m, l, r, rr):
        return (r == readData_det.tielines[l-1]['Near Area Name']) and (rr == readData_det.tielines[l-1]['Far Area Name'])
    m.l_rr = Set(initialize=m.l * m.r * m.r, filter=l_rr_filter, ordered=True)    

    def l_er_filter(m, l, r):
        return r == readData_det.tielines[l-1]['Far Area Name']
    m.l_er = Set(initialize=m.l*m.r, filter=l_er_filter, ordered=True)

    def l_sr_filter(m, l, r):
        return r == readData_det.tielines[l-1]['Near Area Name']
    m.l_sr = Set(initialize=m.l*m.r, filter=l_sr_filter, ordered=True)    
    '''
    Parameter notation

    m.L: load demand in region r in sub-period s of representative day d of year t (MW)
    m.n_d: weight of representative day d
    m.L_max: peak load in year t (MW)
    m.cf: capacity factor of renewable generation cluster i in region r at sub-period s, of representative day d of r
        year t (fraction of the nameplate capacity)
    m.Qg_np: generator nameplate capacity (MW)
    m.Ng_max: max number of generators in cluster i of region r
    m.Qinst_UB: Yearly upper bound on installation capacity by generator type
    m.LT: expected lifetime of generation cluster i (years)
    m.Tremain: remaining time until the end of the time horizon at year t (years)
    m.Ng_r: number of generators in cluster i of region r that achieved their expected lifetime
    m.q_v: capacity value of generation cluster i (fraction of the nameplate capacity)
    m.Pg_min: minimum operating output of a generator in cluster i ∈ ITH (fraction of the nameplate capacity)
    m.Ru_max: maximum ramp-up rate for cluster i ∈ ITH (fraction of nameplate capacity)
    m.Rd_max: maximum ramp-down rate for cluster i ∈ ITH (fraction of nameplate capacity)
    m.f_start: fuel usage at startup (MMbtu/MW)
    m.C_start: 􏰄xed startup cost for generator cluster i ($/MW)
    m.frac_spin: maximum fraction of nameplate capacity of each generator that can contribute to spinning reserves
        (fraction of nameplate capacity)
    m.frac_Qstart: maximum fraction of nameplate capacity of each generator that can contribute to quick-start reserves
        (fraction of nameplate capacity)
    m.t_loss: transmission loss factor between region r and region r ̸= r (%/miles)
    m.t_up: transmission line capacity
    m.dist: distance between region r and region r′ ̸= r (miles)
    m.if_: discount factor for year t
    m.ED: energy demand during year t (MWh)
    m.Rmin: system's minimum reserve margin for year t (fraction of the peak load)
    m.hr: heat rate of generator cluster i (MMBtu/MWh)
    m.P_fuel: price of fuel for generator cluster i in year t ($/MMBtu)
    m.EF_CO2: full lifecycle CO2 emission factor for generator cluster i (kgCO2/MMBtu)
    m.FOC: 􏰄fixed operating cost of generator cluster i ($/MW)
    m.VOC: variable O&M cost of generator cluster i ($/MWh)
    m.CCm: capital cost multiplier of generator cluster i (unitless)
    m.DIC: discounted investment cost of generator cluster i in year t ($/MW)
    m.TIC: investment cost of tranmission line l ($)
    m.LEC: life extension cost for generator cluster i (fraction of the investment cost of corresponding new generator)
    m.PEN: penalty for not meeting renewable energy quota target during year t ($/MWh)
    m.PENc: penalty for curtailment during year t ($/MWh)
    m.tx_CO2: carbon tax in year t ($/kg CO2)
    m.susceptance susceptance of transmission line l [Siemenns]
    m.line_capacity capacity of transmission line l (MW)
    m.RES_min: minimum renewable energy production requirement during year t (fraction of annual energy demand)
    m.hs: duration of sub-period s (hours)
    m.ir: interest rate
    m.storage_inv_cost: investment cost of storage unit of type j in year t [$/MW]
    m.P_min_charge: min power storage charge for unit j [MW]
    m.P_max_charge: max power storage charge for unit j [MW]
    m.P_min_discharge: min power storage discharge for unit j [MW]
    m.P_max_discharge: max power storage discharge for unit j [MW]
    m.min_storage_cap: min storage capacity for unit j [MWh]
    m.max_storage_cap: max storage capacity for unit j [MWh]
    m.eff_rate_charge: efficiency rate to charge energy in storage unit j
    m.eff_rate_discharge: efficiency rate to discharge energy in storage unit j
    m.storage_lifetime: storage lifetime (years)

    '''

# m.L = Param(m.r, m.t, m.d, m.hours, default=0, mutable=True)  # initialize=readData_det.L)
    m.L = Param(m.r, m.t, m.d, m.hours, default=0, initialize=readData_det.L_by_scenario[0], mutable=True) 
    m.n_d = Param(m.d, default=0, mutable=True, initialize=readData_det.n_ss)
    # m.L_max = Param(m.t_stage, default=0, mutable=True)
    m.L_max = Param(m.t, default=0, initialize=readData_det.L_max)
    # m.cf = Param(m.i, m.r, m.t, m.d, m.hours, default=0, mutable=True)  # initialize=readData_det.cf)
    m.cf = Param(m.i, m.r, m.t, m.d, m.hours, mutable=True, initialize=readData_det.cf_by_scenario[0])
    m.Qg_np = Param(m.i_r, default=0, initialize=readData_det.Qg_np)
    m.Ng_max = Param(m.i_r, default=0, initialize=readData_det.Ng_max, mutable=True)
    m.Qinst_UB = Param(m.i, m.t, default=0, initialize=readData_det.Qinst_UB)
    m.LT = Param(m.i, initialize=readData_det.LT, default=0)
    m.Tremain = Param(m.t, default=0, initialize=readData_det.Tremain)
    m.Ng_r = Param(m.old, m.r, m.t, default=0, initialize=readData_det.Ng_r)
    m.q_v = Param(m.i, default=0, initialize=readData_det.q_v)
    m.Pg_min = Param(m.i, default=0, initialize=readData_det.Pg_min)
    m.Ru_max = Param(m.i, default=0, initialize=readData_det.Ru_max)
    m.Rd_max = Param(m.i, default=0, initialize=readData_det.Rd_max)
    m.f_start = Param(m.i, default=0, initialize=readData_det.f_start)
    m.C_start = Param(m.i, default=0, initialize=readData_det.C_start)
    m.frac_spin = Param(m.i, default=0, initialize=readData_det.frac_spin)
    m.frac_Qstart = Param(m.i, default=0, initialize=readData_det.frac_Qstart)
    m.t_loss = Param(m.r, m.r, default=0, initialize=readData_det.t_loss)
    m.t_up = Param(m.r, m.r, default=0, initialize=readData_det.t_up)
    m.dist = Param(m.r, m.r, default=0, initialize=readData_det.dist)
    m.if_ = Param(m.t, default=0, initialize=readData_det.if_)
    m.ED = Param(m.t, default=0, initialize=readData_det.ED)
    m.Rmin = Param(m.t, default=0, initialize=readData_det.Rmin)
    m.hr = Param(m.i_r, default=0, initialize=readData_det.hr)
    m.P_fuel = Param(m.i, m.t, default=0, initialize=readData_det.P_fuel)
    # m.P_fuel = Param(m.i, m.t_stage, default=0, mutable=True)
    m.EF_CO2 = Param(m.i, default=0, initialize=readData_det.EF_CO2)
    m.FOC = Param(m.i, m.t, default=0, initialize=readData_det.FOC)
    m.VOC = Param(m.i, m.t, default=0, initialize=readData_det.VOC)
    m.CCm = Param(m.i, default=0, initialize=readData_det.CCm)
    # m.DIC = Param(m.i, m.t, default=0, initialize=readData_det.DIC)
    m.DIC = Param(m.i, m.t, m.scenarios, default = 0, mutable = True)
    m.TIC = Param(m.l, m.t, default=0, initialize=readData_det.TIC)
    m.LEC = Param(m.i, default=0, initialize=readData_det.LEC)
    m.PEN = Param(m.t, default=0, initialize=readData_det.PEN)
    m.PENc = Param(default=0, initialize=readData_det.PENc)
    m.tx_CO2 = Param(m.t, m.t, default=0, mutable=True)   
    for t in m.t:
        if t == 1:
            m.tx_CO2[t,t] = readData_det.tx_CO2[t, t, 'O']
        else:
            m.tx_CO2[t,t] = readData_det.tx_CO2[t, t, 'M']
    m.RES_min = Param(m.t, default=0, initialize=readData_det.RES_min)
    m.hs = Param(initialize=readData_det.hs, default=1)
    m.ir = Param(initialize=readData_det.ir, default=0)

    #transmission
    m.suceptance = Param(m.l, initialize=0, mutable=True)
    for i in range(len(readData_det.tielines)):
        m.suceptance[i+1] = readData_det.tielines[i]['B']

    m.line_capacity = Param(m.l, initialize=0, mutable=True)
    for i in range(len(readData_det.tielines)):
        m.line_capacity[i+1] = readData_det.tielines[i]['Capacity']    


    # Storage
    m.storage_inv_cost = Param(m.j, m.t, default=0, initialize=readData_det.storage_inv_cost)
    m.P_min_charge = Param(m.j, default=0, initialize=readData_det.P_min_charge)
    m.P_max_charge = Param(m.j, default=0, initialize=readData_det.P_max_charge)
    m.P_min_discharge = Param(m.j, default=0, initialize=readData_det.P_min_discharge)
    m.P_max_discharge = Param(m.j, default=0, initialize=readData_det.P_max_discharge)
    m.min_storage_cap = Param(m.j, default=0, initialize=readData_det.min_storage_cap)
    m.max_storage_cap = Param(m.j, default=0, initialize=readData_det.max_storage_cap)
    m.eff_rate_charge = Param(m.j, default=0, initialize=readData_det.eff_rate_charge)
    m.eff_rate_discharge = Param(m.j, default=0, initialize=readData_det.eff_rate_discharge)
    m.storage_lifetime = Param(m.j, default=0, initialize=readData_det.storage_lifetime)

    #probability 
    m.probability = Param(m.scenarios, default=1, mutable=True)

    # Block of Equations per time period
    def time_block_rule(b, tt, scenario):
        def bound_P(_b, scenario, i, r, t, d, s):
            if i in m.old:
                return 0, m.Qg_np[i, r] * m.Ng_old[i, r]
            else:
                return 0, m.Qg_np[i, r] * m.Ng_max[i, r]

        def bound_Pflow(_b, scenario, l, t, d, s):
             return -m.line_capacity[l], m.line_capacity[l]
        
        def bound_Pflow_plus(_b, scenario, l, t, d, s):
             return 0, m.line_capacity[l]             

        def bound_Pflow_minus(_b, scenario, l, t, d, s):
             return 0, m.line_capacity[l]


        def bound_o_rn(_b, scenario, rn, r, t):
            if rn in m.rold:
                return 0, m.Ng_old[rn, r]
            else:
                return 0, m.Ng_max[rn, r]

        def bound_o_rn_prev(_b, scenario, rn, r):
            if rn in m.rold:
                return 0, m.Ng_old[rn, r]
            else:
                return 0, m.Ng_max[rn, r]

        def bound_b_rn(_b, scenario, rn, r, t):
            if rn in m.rold:
                return 0, 0
            else:
                return 0, math.floor(m.Qinst_UB[rn, t] / m.Qg_np[rn, r])

        def bound_r_rn(_b, scenario, rn, r, t):
            if rn in m.rold:
                return 0, m.Ng_old[rn, r]
            else:
                return 0, m.Ng_max[rn, r]

        def bound_e_rn(_b, scenario, rn, r, t):
            if rn in m.rold:
                return 0, m.Ng_r[rn, r, t]
            else:
                return 0, m.Ng_max[rn, r]

        def bound_o_th(_b, scenario, th, r, t):
            if th in m.told:
                return 0, m.Ng_old[th, r]
            else:
                return 0, m.Ng_max[th, r]

        def bound_o_th_prev(_b, scenario, th, r):
            if th in m.told:
                return 0, m.Ng_old[th, r]
            else:
                return 0, m.Ng_max[th, r]


        def bound_b_th(_b, scenario, th, r, t):
            if th in m.told:
                return 0, 0
            else:
                return 0, math.floor(m.Qinst_UB[th, t] / m.Qg_np[th, r])

        def bound_r_th(_b, scenario, th, r, t):
            if th in m.told:
                return 0, m.Ng_old[th, r]
            else:
                return 0, m.Ng_max[th, r]

        def bound_e_th(_b, scenario, th, r, t):
            if th in m.told:
                return 0, m.Ng_r[th, r, t]
            else:
                return 0, m.Ng_max[th, r]

        def bound_UC(_b, scenario, th, r, t, d, s):
            if th in m.told:
                return 0, m.Ng_old[th, r]
            else:
                return 0, m.Ng_max[th, r]

        def bound_theta(_b, scenario, r, t, d, s):
            if r == "Northeast":
                return 0, 0
            else:
                return -3.14159, 3.14159

        def bound_cu(_b, scenario, r, t, d, s):
            return 0, m.L_max[t]

        def bound_RES_def(_b, scenario, t):
            return 0, m.RES_min[t] * m.ED[t]

        def bound_Q_spin(_b, scenario, th, r, t, d, s):
            return 0, 0.075 * m.L[r, t, d, s]

        def bound_Q_start(_b, scenario, th, r, t, d, s):
            return 0, 0.075 * m.L[r, t, d, s]

        def bound_ngb_rn(_b, scenario, rn, r, t):
            if rn in m.rnew:
                return 0, m.Qinst_UB[rnew, t] / sum(m.Qg_np[rnew, r] / len(m.r) for r in m.r)
            else:
                return 0,0

        def bound_ngb_th(_b, scenario, th, r, t):
            if th in m.tnew:
                return 0, m.Qinst_UB[tnew, t] / sum(m.Qg_np[tnew, r] / len(m.r) for r in m.r)
            else:
                return 0,0

        def bound_p_charged(_b, scenario, j, r, t, d, s):
            return 0, m.P_max_charge[j] * 1e3 

        def bound_p_discharged(_b, scenario, j, r, t, d, s):
            return 0, m.P_max_discharge[j] * 1e3

        def bound_p_storage_level(_b, scenario, j, r, t, d, s):
            return 0, m.max_storage_cap[j] * 1e3

        def bound_p_storage_level_end_hour(_b, scenario, j, r, t, d, s):
            return 0, m.max_storage_cap[j] * 1e3






    


        '''
        Variscenario, ables notation:
        b.P: power output of generation cluster i in region r during sub-period s of representative day d of year t (MW)
        b.cu: curtailment slack generation in region r during sub-period s of representative day d of year t (MW)
        b.RES_def: de􏰂cit from renewable energy quota target during year t (MWh)
        b.P_flow: power transfer from region r to region r̸=r during sub-period s of representative day d of year t (MW)
        b.d_P_flow_plus: nonnegative variable, power flow from the sending end of transmission line l, s(l), to the receiving end of line l, r(l) during sub-period s of representative day d of year t (MW)
        b.d_P_flow_minus: nonnegative variable, power flow from the receiving end of transmission line l, r(l), to the sending end of line l, s(l) during sub-period s of representative day d of year t (MW)        
        b.Q_spin:spinning reserve capacity of generation cluster i in region r during sub-period s of representative day 
            d of year t (MW)
        b.Q_Qstart: quick-start capacity reserve of generation cluster i in region r during sub-period s of 
            representative day d of year t (MW)
        b.ngr_rn: number of generators that retire in cluster i ∈ IRN of region r in year t (continuous relaxation)
        b.nge_rn: number of generators that had their life extended in cluster i ∈ IRN of region r in year t 
            (continuous relaxation)
        b.ngb_rn: number of generators that are built in cluster i ∈ IRN of region r in year t (continuous relaxation)
        b.ngo_rn: number of generators that are operational in cluster i ∈ IRN of region r in year t (continuous r
            relaxation)
        b.ngr_th: number of generators that retire in cluster i ∈ ITH of region r in year t (integer variable)
        b.nge_th: number of generators that had their life extended in cluster i ∈ ITH of region r in year t (integer r
            variable)
        b.ngb_th: number of generators that are built in cluster i ∈ ITH of region r in year t (integer variable) r
        b.ngo_th: number of generators that are operational in cluster i ∈ ITH of region r in year t (integer variable)
        b.u: number of thermal generators ON in cluster i ∈ Ir of region r during sub-period s of representative day 
            d of year t (integer variable)
        b.su: number of generators starting up in cluster i during sub-period s of representative day d in year t 
            (integer variable)
        b.sd: number of generators shutting down in cluster i during sub-period s of representative day d in year t 
            (integer variable)
        b.p_charged: power charged into storage in region r, day d, hour h, year t [MW]
        b.p_discharged : power discharged into storage in region r, day d, hour h, year t [MW]
        b.p_storage_level: ending state of charge of storage in region r, day d, hour h, year t [MWh]
        b.p_storage_level_end_hour: ending state of charge of storage in region r, day d, hour h, year t [MWh]
        b.nsb: Number of storage units of type j installed in region r, year t (relaxed to continuous)
        b.nso: Number of storage units of type j operational in region r, year t (relaxed to continuous)
        b.nsr: Number of storage units of type j retired in region r, year t (relaxed to continuous)
        b.ntb: Whether new transmission line l is built in time period t
        b.nte: whether transmission line l exist in time period t 
        b.theta: voltage angle at region r during sub-period s of representative day d of year t
        b.d_theta_plus: nonnegative variable, angle difference between the angles at sending end and receiving end of transmission line l during sub-period s of representative day d of year t (MW)
        b.d_theta_minus: nonnegative variable, angle difference between the angles at receiving end and sending end of transmission line l during sub-period s of representative day d of year t (MW)
        b.d_theta_1: disaggregated variable in the hull formulation, angle difference between the angles at sending end and receiving end of transmission line l during sub-period s of representative day d of year t (MW) if the transmission line l exists in year t
        b.d_theta_2: disaggregated variable in the hull formulation, angle difference between the angles at sending end and receiving end of transmission line l during sub-period s of representative day d of year t (MW) if the transmission line l does not exist in year t
        '''

        b.ntb = Var([scenario], m.l_new, [tt], within=Binary)
        b.nte = Var([scenario], m.l_new, [tt], within=Binary)
        b.nte_prev = Var([scenario], m.l_new, bounds=(0,1), domain=NonNegativeReals)
        #variables for different formulation of transmission 
        if formulation == "standard":
            b.theta = Var([scenario], m.r, [tt], m.d, m.hours, within=Reals, bounds=bound_theta)        
            b.P_flow = Var([scenario], m.l, [tt], m.d, m.hours, bounds=bound_Pflow)
        elif formulation == "improved":
            b.d_theta_plus = Var([scenario], m.l, [tt], m.d, m.hours, bounds=(0, 3.14159))
            b.d_theta_minus = Var([scenario], m.l, [tt], m.d, m.hours, bounds=(0, 3.14159))
            b.theta = Var([scenario], m.r, [tt], m.d, m.hours, within=Reals, bounds=bound_theta) 
            b.d_P_flow_plus = Var([scenario], m.l, [tt], m.d, m.hours, bounds=bound_Pflow_plus)
            b.d_P_flow_minus = Var([scenario], m.l, [tt], m.d, m.hours, bounds=bound_Pflow_minus)
            b.P_flow = Var([scenario], m.l, [tt], m.d, m.hours, bounds=bound_Pflow)
        elif formulation == "hull":
            b.theta = Var([scenario], m.r, [tt], m.d, m.hours, within=Reals, bounds=bound_theta)        
            b.P_flow = Var([scenario], m.l, [tt], m.d, m.hours, bounds=bound_Pflow)            
            b.d_theta_1 = Var([scenario], m.l_new, [tt], m.d, m.hours, within=Reals, bounds=bound_theta)        
            b.d_theta_2 = Var([scenario], m.l_new, [tt], m.d, m.hours, within=Reals, bounds=bound_theta)                   
        b.P = Var([scenario], m.i_r, [tt], m.d, m.hours, within=NonNegativeReals, bounds=bound_P)
        b.cu = Var([scenario], m.r, [tt], m.d, m.hours,within=NonNegativeReals, bounds=bound_cu)
        b.RES_def = Var([scenario], [tt], within=NonNegativeReals, bounds=bound_RES_def)
        b.Q_spin = Var([scenario], m.th_r, [tt], m.d, m.hours, within=NonNegativeReals, bounds=bound_Q_spin)
        b.Q_Qstart = Var([scenario], m.th_r, [tt], m.d, m.hours, within=NonNegativeReals, bounds=bound_Q_start)
        b.ngr_rn = Var([scenario], m.rn_r, [tt], bounds=bound_r_rn, domain=NonNegativeReals)


        #rnew does not occur in the logic constraints
        for t in [tt]:
            for rnew, r in m.rn_r:
                if rnew in m.rnew:
                    b.ngr_rn[scenario, rnew, r, t].fix(0.0)
      

        b.nge_rn = Var([scenario], m.rn_r, [tt], bounds=bound_e_rn, domain=NonNegativeReals)

        for t in [tt]:
            for rnew, r in m.rn_r:
                if rnew in m.rnew:
                    b.nge_rn[scenario, rnew, r, t].fix(0.0)

        b.ngr_th = Var([scenario], m.th_r, [tt], bounds=bound_r_th, domain=NonNegativeIntegers)

        for t in [tt]:
            for tnew, r in m.th_r:
                if tnew in m.tnew:
                    b.ngr_th[scenario, tnew, r, t].fix(0.0)
      

        b.nge_th = Var([scenario], m.th_r, [tt], bounds=bound_e_th, domain=NonNegativeIntegers)

        for t in [tt]:
            for tnew, r in m.th_r:
                if tnew in m.tnew:
                    b.nge_th[scenario, tnew, r, t].fix(0.0)

        b.u = Var([scenario], m.th_r, [tt], m.d, m.hours, bounds=bound_UC, domain=NonNegativeIntegers)
        b.su = Var([scenario], m.th_r, [tt], m.d, m.hours, bounds=bound_UC, domain=NonNegativeIntegers)
        b.sd = Var([scenario], m.th_r, [tt], m.d, m.hours, bounds=bound_UC, domain=NonNegativeIntegers)
        for th, r, t, d, s in m.th_r * [tt] * m.d * m.hours:
            if s == 1:
                b.sd[scenario, th, r, t, d, s].fix(0.0)
            else:
                b.sd[scenario, th, r, t, d, s].unfix()


        b.ngo_rn = Var([scenario], m.rn_r, [tt], bounds=bound_o_rn, domain=NonNegativeReals)
        b.ngb_rn = Var([scenario], m.rn_r, [tt],  bounds=bound_ngb_rn, domain=NonNegativeReals)

        for t in [tt]:
            for rold, r in m.rn_r:
                if rold in m.rold:
                    b.ngb_rn[scenario, rold, r, t].fix(0.0)

        b.ngo_th = Var([scenario], m.th_r, [tt], bounds=bound_o_th, domain=NonNegativeIntegers)
        b.ngb_th = Var([scenario], m.th_r, [tt],  bounds=bound_ngb_th, domain=NonNegativeIntegers)     
        for t in [tt]:
            for th, r in m.th_r: 
                if th in m.told:
                    b.ngb_th[scenario, th, r, t].fix(0.0)           

        b.ngo_rn_prev = Var([scenario], m.rn_r, bounds=bound_o_rn_prev, domain=NonNegativeReals)
        b.ngo_th_prev = Var([scenario], m.th_r, bounds=bound_o_th_prev, domain=NonNegativeReals)

        # Storage related Variables
        b.p_charged = Var([scenario], m.j, m.r, [tt], m.d, m.hours, within=NonNegativeReals, bounds=bound_p_charged)
        b.p_discharged = Var([scenario], m.j, m.r, [tt], m.d, m.hours, within=NonNegativeReals, bounds=bound_p_discharged)
        b.p_storage_level = Var([scenario], m.j, m.r, [tt], m.d, m.hours, within=NonNegativeReals, bounds=bound_p_storage_level)
        b.p_storage_level_end_hour = Var([scenario], m.j,m.r, [tt], m.d, m.hours, within=NonNegativeReals, bounds=bound_p_storage_level_end_hour)
        b.nsr = Var([scenario], m.j, m.r, [tt], within=NonNegativeReals, bounds=(0,1e3))
        b.nsb = Var([scenario], m.j, m.r, [tt], within=NonNegativeReals, bounds=(0,1e3))
        b.nso = Var([scenario], m.j, m.r, [tt], within=NonNegativeReals, bounds=(0,1e3))

        b.nso_prev = Var([scenario], m.j, m.r, within=NonNegativeReals, bounds=(0,1e3))

        ####################### add constraints related to transmission ####################### 
        if formulation == "standard":
            def dc_power_flow_old(_b, l, t, d, s):
                return _b.P_flow[scenario, l, t, d, s] == m.suceptance[l] * (_b.theta[scenario, readData_det.tielines[l-1]['Near Area Name'], t, d, s] - _b.theta[scenario, readData_det.tielines[l-1]['Far Area Name'], t, d, s])
            b.dc_power_flow_old = Constraint(m.l_old,  [tt], m.d, m.hours, rule=dc_power_flow_old)

            def dc_power_flow_new_lo(_b, l, t, d, s):
                return _b.P_flow[scenario, l, t, d, s] - m.suceptance[l] * \
                (_b.theta[scenario, readData_det.tielines[l-1]['Near Area Name'], t, d, s] - _b.theta[scenario, readData_det.tielines[l-1]['Far Area Name'], t, d, s])\
                >= -(1- _b.nte[scenario, l, t]) * 5 * m.line_capacity[l]
            b.dc_power_flow_new_lo = Constraint(m.l_new, [tt], m.d, m.hours, rule=dc_power_flow_new_lo)

            def dc_power_flow_new_up(_b, l, t, d, s):
                return _b.P_flow[scenario, l, t, d, s] - m.suceptance[l] * \
                (_b.theta[scenario, readData_det.tielines[l-1]['Near Area Name'], t, d, s] - _b.theta[scenario, readData_det.tielines[l-1]['Far Area Name'], t, d, s])\
                <= (1- _b.nte[scenario, l, t]) * 5 * m.line_capacity[l]
            b.dc_power_flow_new_up = Constraint(m.l_new, [tt], m.d, m.hours, rule=dc_power_flow_new_up)        

            def power_flow_bounds_new_lo(_b, l, t, d, s):
                return _b.P_flow[scenario, l, t, d, s] >= - m.line_capacity[l] * _b.nte[scenario, l, t]
            b.power_flow_bounds_new_lo = Constraint(m.l_new, [tt], m.d, m.hours, rule=power_flow_bounds_new_lo)

            def power_flow_bounds_new_up(_b, l, t, d, s):
                return _b.P_flow[scenario, l, t, d, s] <=  m.line_capacity[l] * _b.nte[scenario, l, t]
            b.power_flow_bounds_new_up = Constraint(m.l_new, [tt], m.d, m.hours, rule=power_flow_bounds_new_up)
        elif formulation == "improved":
            def dc_power_flow_old(_b, l, t, d, s):
                return _b.P_flow[scenario, l, t, d, s] == m.suceptance[l] * (_b.theta[scenario, readData_det.tielines[l-1]['Near Area Name'], t, d, s] - _b.theta[scenario, readData_det.tielines[l-1]['Far Area Name'], t, d, s])
            b.dc_power_flow_old = Constraint(m.l_old,  [tt], m.d, m.hours, rule=dc_power_flow_old)

            def dc_power_flow_new_lb1(_b, l, t, d, s):
                return _b.d_P_flow_plus[scenario, l, t, d, s] - m.suceptance[l] * \
                _b.d_theta_plus[scenario, l, t, d, s]\
                >= -(1- _b.nte[scenario, l, t]) * 5 * m.line_capacity[l]             
            b.dc_power_flow_new_lb1 = Constraint(m.l_new, [tt], m.d, m.hours, rule=dc_power_flow_new_lb1)
            
            def dc_power_flow_new_ub1(_b, l, t, d, s):
                return _b.d_P_flow_plus[scenario, l, t, d, s] - m.suceptance[l] * \
                _b.d_theta_plus[scenario, l, t, d, s]\
                <= 0 
            b.dc_power_flow_new_ub1 = Constraint(m.l_new, [tt], m.d, m.hours, rule=dc_power_flow_new_ub1)

            def dc_power_flow_new_lb2(_b, l, t, d, s):
                return _b.d_P_flow_minus[scenario, l, t, d, s] - m.suceptance[l] * \
                _b.d_theta_minus[scenario, l, t, d, s]\
                >= -(1- _b.nte[scenario, l, t]) * 5 * m.line_capacity[l]             
            b.dc_power_flow_new_lb2 = Constraint(m.l_new, [tt], m.d, m.hours, rule=dc_power_flow_new_lb2)
            
            def dc_power_flow_new_ub2(_b, l, t, d, s):
                return _b.d_P_flow_minus[scenario, l, t, d, s] - m.suceptance[l] * \
                _b.d_theta_minus[scenario, l, t, d, s]\
                <= 0 
            b.dc_power_flow_new_ub2 = Constraint(m.l_new, [tt], m.d, m.hours, rule=dc_power_flow_new_ub2)    

            def P_flow_def(_b, l, t, d, s):
                return _b.P_flow[scenario, l, t, d, s] == _b.d_P_flow_plus[scenario, l, t, d, s] - _b.d_P_flow_minus[scenario, l, t, d, s]
            b.P_flow_def = Constraint(m.l_new, [tt], m.d, m.hours, rule=P_flow_def)

            def d_theta_def(_b, l, t, d, s):
                return _b.theta[scenario, readData_det.tielines[l-1]['Near Area Name'], t, d, s] - \
                _b.theta[scenario, readData_det.tielines[l-1]['Far Area Name'], t, d, s] == _b.d_theta_plus[scenario, l, t, d, s] - _b.d_theta_minus[scenario, l, t, d, s]
            b.d_theta_def = Constraint(m.l_new, [tt], m.d, m.hours, rule=d_theta_def)                

            def d_power_flow_bounds_new_plus(_b, l, t, d, s):
                return _b.d_P_flow_plus[scenario, l, t, d, s] <=  m.line_capacity[l] * _b.nte[scenario, l, t]
            b.d_power_flow_bounds_new_plus = Constraint(m.l_new, [tt], m.d, m.hours, rule=d_power_flow_bounds_new_plus)

            def d_power_flow_bounds_new_minus(_b, l, t, d, s):
                return _b.d_P_flow_minus[scenario, l, t, d, s] <=  m.line_capacity[l] * _b.nte[scenario, l, t]
            b.d_power_flow_bounds_new_minus = Constraint(m.l_new, [tt], m.d, m.hours, rule=d_power_flow_bounds_new_minus)                     
        elif formulation == "hull":
            def dc_power_flow_old(_b, l, t, d, s):
                return _b.P_flow[scenario, l, t, d, s] == m.suceptance[l] * (_b.theta[scenario, readData_det.tielines[l-1]['Near Area Name'], t, d, s] - _b.theta[scenario, readData_det.tielines[l-1]['Far Area Name'], t, d, s])
            b.dc_power_flow_old = Constraint(m.l_old,  [tt], m.d, m.hours, rule=dc_power_flow_old)

            def dc_power_flow_new(_b, l, t, d, s):
                return _b.P_flow[scenario, l, t, d, s] - m.suceptance[l] * \
                _b.d_theta_1[l, t, d, s]\
                == 0 
            b.dc_power_flow_new = Constraint(m.l_new, [tt], m.d, m.hours, rule=dc_power_flow_new)

            def d_theta_1_bound_ub(_b, l, t, d, s):
                return _b.d_theta_1[l, t, d, s] <= _b.nte[scenario, l, t] * 3.14159
            b.d_theta_1_bound_ub = Constraint(m.l, [tt], m.d, m.hours, rule=d_theta_1_bound_ub)       

            def d_theta_1_bound_lb(_b, l, t, d, s):
                return _b.d_theta_1[l, t, d, s] >= - _b.nte[scenario, l, t] * 3.14159
            b.d_theta_1_bound_lb = Constraint(m.l_new, [tt], m.d, m.hours, rule=d_theta_1_bound_lb)   

            def d_theta_2_bound_ub(_b, l, t, d, s):
                return _b.d_theta_2[l, t, d, s] <= (1-_b.nte[scenario, l, t]) * 3.14159
            b.d_theta_2_bound_ub = Constraint(m.l_new, [tt], m.d, m.hours, rule=d_theta_2_bound_ub)       

            def d_theta_2_bound_lb(_b, l, t, d, s):
                return _b.d_theta_2[l, t, d, s] >= - (1- _b.nte[scenario, l, t]) * 3.14159
            b.d_theta_2_bound_lb = Constraint(m.l_new, [tt], m.d, m.hours, rule=d_theta_2_bound_lb)  

            def d_theta_aggregate(_b, l, t, d, s):
                return _b.theta[scenario, readData_det.tielines[l-1]['Near Area Name'], t, d, s] - \
                _b.theta[scenario, readData_det.tielines[l-1]['Far Area Name'], t, d, s] ==   _b.d_theta_1[l, t, d, s] +  _b.d_theta_2[l, t, d, s]       
            b.d_theta_aggregate = Constraint(m.l_new, [tt], m.d, m.hours, rule=d_theta_aggregate)         

            def power_flow_bounds_new_lo(_b, l, t, d, s):
                return _b.P_flow[scenario, l, t, d, s] >= - m.line_capacity[l] * _b.nte[scenario, l, t]
            b.power_flow_bounds_new_lo = Constraint(m.l_new, [tt], m.d, m.hours, rule=power_flow_bounds_new_lo)

            def power_flow_bounds_new_up(_b, l, t, d, s):
                return _b.P_flow[scenario, l, t, d, s] <=  m.line_capacity[l] * _b.nte[scenario, l, t]
            b.power_flow_bounds_new_up = Constraint(m.l_new, [tt], m.d, m.hours, rule=power_flow_bounds_new_up)               

        def transmission_line_balance(_b, l, t):
            if t == 1:
                return _b.nte[scenario, l, t] == _b.ntb[scenario, l, t]
            else:
                return _b.nte[scenario, l,t] ==  _b.nte_prev[scenario, l] + _b.ntb[scenario, l, t]
        b.transmission_line_balance = Constraint(m.l_new, [tt], rule=transmission_line_balance)     

        # def symmetrybreaking_line(_b, l, t):
        #     if l%10 != 1:
        #         return _b.nte[scenario, l,t] >= _b.nte[scenario, l-1,t]
        #     else:
        #         return Constraint.Skip
        # b.symmetrybreaking_line = Constraint(m.l_new, [tt], rule=symmetrybreaking_line)

        ####################### end constraints related to transmission ####################### 
        #show costs breakdown 
      
        def variable_operating_cost(_b):
            return sum(m.if_[t] * (sum(m.n_d[d] * 1.0000000 * sum((m.VOC[i, t] + m.hr[i, r] * m.P_fuel[i, t]
                                                              + m.EF_CO2[i] * m.tx_CO2[t, t] * m.hr[i, r]) * _b.P[scenario, 
                                                                 i, r, t, d, s]
                                                             for i, r in m.i_r)
                                       for d in m.d for s in m.hours) )   for t in [tt])* 10 ** (-9)
        b.variable_operating_cost = Expression(rule=variable_operating_cost)


        def fixed_operating_cost(_b):
            return sum(m.if_[t] * (sum(m.FOC[rn, t] * m.Qg_np[rn, r] *
                                                                            _b.ngo_rn[scenario, rn, r, t] for rn, r in m.rn_r)
                                   + sum(m.FOC[th, t] * m.Qg_np[th, r] * _b.ngo_th[scenario, th, r, t]
                                         for th, r in m.th_r))   for t in [tt])* 10 ** (-9)
        b.fixed_operating_cost = Expression(rule=fixed_operating_cost)


        def startup_cost(_b):
            return sum(m.if_[t] * (sum(m.n_d[d] * 1.0000000 * _b.su[scenario, th, r, t, d, s] * m.Qg_np[th, r]
                                         * (m.f_start[th] * m.P_fuel[th, t]
                                            + m.f_start[th] * m.EF_CO2[th] * m.tx_CO2[t, t] + m.C_start[th])
                                   for th, r in m.th_r for d in m.d for s in m.hours))   for t in [tt])* 10 ** (-9)
        b.startup_cost = Expression(rule=startup_cost)

        def renewable_generator_cost(_b):
            return sum(m.if_[t] * (sum(m.DIC[rnew, t, scenario] * m.CCm[rnew] * m.Qg_np[rnew, r] * _b.ngb_rn[scenario, rnew, r, t]
                                         for rnew, r in m.rn_r if rnew in m.rnew))   for t in [tt])* 10 ** (-9)
        b.renewable_generator_cost = Expression(rule=renewable_generator_cost)



        def thermal_generator_cost(_b):
            return sum(m.if_[t] * (sum(m.DIC[tnew, t, scenario] * m.CCm[tnew] * m.Qg_np[tnew, r] * _b.ngb_th[scenario, tnew, r, t]
                                         for tnew, r in m.th_r if tnew in m.tnew))   for t in [tt])* 10 ** (-9)
        b.thermal_generator_cost = Expression(rule=thermal_generator_cost)

        def extending_renewable_generator_cost(_b):
            return sum(m.if_[t] * (sum(m.DIC[rn, t, scenario] * m.LEC[rn] * m.Qg_np[rn, r] * _b.nge_rn[scenario, rn, r, t]
                                         for rn, r in m.rn_r))   for t in [tt])* 10 ** (-9)
        b.extending_renewable_generator_cost = Expression(rule=extending_renewable_generator_cost)


        def extending_thermal_generator_cost(_b):
            return sum(m.if_[t] * (sum(m.DIC[th, t, scenario] * m.LEC[th] * m.Qg_np[th, r] * _b.nge_th[scenario, th, r, t]
                                         for th, r in m.th_r))   for t in [tt])* 10 ** (-9)
        b.extending_thermal_generator_cost = Expression(rule=extending_thermal_generator_cost)

        def transmission_line_cost(_b):
            return sum(m.if_[t] * sum(m.TIC[l,t] * _b.ntb[scenario, l,t] for l in m.l) for t in [tt])* 10 ** (-9)
        b.transmission_line_cost = Expression(rule=transmission_line_cost)

        def storage_investment_cost(_b):
            return sum(m.if_[t] * (sum(m.storage_inv_cost[j, t] * m.max_storage_cap[j] * _b.nsb[scenario, j, r, t]
                                         for j in m.j for r in m.r))   for t in [tt])* 10 ** (-9)  
        b.storage_investment_cost = Expression(rule=storage_investment_cost)       
        
        def penalty_cost(_b):
            return sum(m.if_[t] * (m.PEN[t] * _b.RES_def[scenario, t]
                                   + m.PENc * sum(_b.cu[scenario, r, t, d, s]
                                                  for r in m.r for d in m.d for s in m.hours))   for t in [tt])  * 10 ** (-9)
        b.penalty_cost = Expression(rule=penalty_cost)   

        def renewable_capacity(_b):
            return sum(m.Qg_np[rn, r] * _b.ngo_rn[scenario, rn, r, t] * m.q_v[rn] for rn, r in m.i_r if rn in m.rn) 
        b.renewable_capacity = Expression(rule=renewable_capacity)

        def thermal_capacity(_b):
            return sum(m.Qg_np[th, r] * _b.ngo_th[scenario, th, r, t] for th, r in m.i_r if th in m.th)   
        b.thermal_capacity = Expression(rule=thermal_capacity)

        def total_capacity(_b):
            return sum(m.Qg_np[rn, r] * _b.ngo_rn[scenario, rn, r, t] * m.q_v[rn] for rn, r in m.i_r if rn in m.rn) \
                   + sum(m.Qg_np[th, r] * _b.ngo_th[scenario, th, r, t] for th, r in m.i_r if th in m.th)
        b.total_capacity = Expression(rule=total_capacity)   

        def total_investment_cost(_b):
            return   sum(m.if_[t] * ( sum(m.DIC[rnew, t, scenario] * m.CCm[rnew] * m.Qg_np[rnew, r] * _b.ngb_rn[scenario, rnew, r, t]
                                         for rnew, r in m.rn_r if rnew in m.rnew)
                                   + sum(m.DIC[tnew, t, scenario] * m.CCm[tnew] * m.Qg_np[tnew, r] * _b.ngb_th[scenario, tnew, r, t]
                                         for tnew, r in m.th_r if tnew in m.tnew)
                                   + sum(m.DIC[rn, t, scenario] * m.LEC[rn] * m.Qg_np[rn, r] * _b.nge_rn[scenario, rn, r, t]
                                         for rn, r in m.rn_r)
                                   + sum(m.DIC[th, t, scenario] * m.LEC[th] * m.Qg_np[th, r] * _b.nge_th[scenario, th, r, t]
                                         for th, r in m.th_r)
                                  + sum(m.TIC[l,t] * _b.ntb[scenario, l, t] for l in m.l_new)
                                   + sum(m.storage_inv_cost[j, t] * m.max_storage_cap[j] * _b.nsb[scenario, j, r, t]
                                         for j in m.j for r in m.r)
                                   + m.PEN[t] * _b.RES_def[scenario, t] )
                      for t in [tt]) \
                   * 10 ** (-9)
        b.total_investment_cost = Expression(rule=total_investment_cost)

        def total_operating_cost(_b):
             return sum(m.if_[t] * (sum(m.n_d[d] * 1.0000000 * sum((m.VOC[i, t] + m.hr[i, r] * m.P_fuel[i, t]
                                                              + m.EF_CO2[i] * m.tx_CO2[t, t] * m.hr[i, r]) * _b.P[scenario, 
                                                                 i, r, t, d, s]
                                                             for i, r in m.i_r)
                                       for d in m.d for s in m.hours) 
                                   + sum(m.n_d[d] * 1.0000000 * _b.su[scenario, th, r, t, d, s] * m.Qg_np[th, r]
                                         * (m.f_start[th] * m.P_fuel[th, t]
                                            + m.f_start[th] * m.EF_CO2[th] * m.tx_CO2[t, t] + m.C_start[th])
                                         for th, r in m.th_r for d in m.d for s in m.hours)                                   
                                   + m.PENc * sum(_b.cu[scenario, r, t, d, s]
                                                  for r in m.r for d in m.d for s in m.hours) )
                      for t in [tt]) \
                   * 10 ** (-9)                                                                                                                       
        b.total_operating_cost = Expression(rule=total_operating_cost)
        b.vobj = Objective(rule=total_operating_cost, sense=minimize)
        b.vobj.deactivate()


        def obj_rule(_b):
            return m.probability[scenario] * sum(m.if_[t] * (sum(m.n_d[d] * 1.0000000 * sum((m.VOC[i, t] + m.hr[i, r] * m.P_fuel[i, t]
                                                              + m.EF_CO2[i] * m.tx_CO2[t, t] * m.hr[i, r]) * _b.P[scenario, 
                                                                 i, r, t, d, s]
                                                             for i, r in m.i_r)
                                       for d in m.d for s in m.hours) + sum(m.FOC[rn, t] * m.Qg_np[rn, r] *
                                                                            _b.ngo_rn[scenario, rn, r, t] for rn, r in m.rn_r)
                                   + sum(m.FOC[th, t] * m.Qg_np[th, r] * _b.ngo_th[scenario, th, r, t]
                                         for th, r in m.th_r)
                                   + sum(m.n_d[d] * 1.0000000 * _b.su[scenario, th, r, t, d, s] * m.Qg_np[th, r]
                                         * (m.f_start[th] * m.P_fuel[th, t]
                                            + m.f_start[th] * m.EF_CO2[th] * m.tx_CO2[t, t] + m.C_start[th])
                                         for th, r in m.th_r for d in m.d for s in m.hours)
                                   + sum(m.DIC[rnew, t, scenario] * m.CCm[rnew] * m.Qg_np[rnew, r] * _b.ngb_rn[scenario, rnew, r, t]
                                         for rnew, r in m.rn_r if rnew in m.rnew)
                                   + sum(m.DIC[tnew, t, scenario] * m.CCm[tnew] * m.Qg_np[tnew, r] * _b.ngb_th[scenario, tnew, r, t]
                                         for tnew, r in m.th_r if tnew in m.tnew)
                                   + sum(m.DIC[rn, t, scenario] * m.LEC[rn] * m.Qg_np[rn, r] * _b.nge_rn[scenario, rn, r, t]
                                         for rn, r in m.rn_r)
                                   + sum(m.DIC[th, t, scenario] * m.LEC[th] * m.Qg_np[th, r] * _b.nge_th[scenario, th, r, t]
                                         for th, r in m.th_r)
                                  + sum(m.TIC[l,t] * _b.ntb[scenario, l, t] for l in m.l_new)
                                   + sum(m.storage_inv_cost[j, t] * m.max_storage_cap[j] * _b.nsb[scenario, j, r, t]
                                         for j in m.j for r in m.r)
                                   + m.PEN[t] * _b.RES_def[scenario, t]
                                   + m.PENc * sum(_b.cu[scenario, r, t, d, s]
                                                  for r in m.r for d in m.d for s in m.hours) )
                      for t in [tt]) \
                   * 10 ** (-9) \
                   

        b.obj = Objective(rule=obj_rule, sense=minimize)

        # def min_RN_req(_b, t):
        #     return sum(m.n_d[d] * 1.0000000 * ( sum(_b.P[scenario, rn, r, t, d, s] for rn, r in m.i_r if rn in m.rn) - sum(_b.cu[scenario, r, t, d, s] for r in m.r)) \
        #                for d in m.d for s in m.hours) \
        #            + _b.RES_def[scenario, t] >= m.RES_min[t] * m.ED[t]

        # b.min_RN_req = Constraint([tt], rule=min_RN_req)

        def min_reserve(_b, t):
            return sum(m.Qg_np[rn, r] * _b.ngo_rn[scenario, rn, r, t] * m.q_v[rn] for rn, r in m.i_r if rn in m.rn) \
                   + sum(m.Qg_np[th, r] * _b.ngo_th[scenario, th, r, t] for th, r in m.i_r if th in m.th) \
                   >= (1 + m.Rmin[t]) * m.L_max[t]

        b.min_reserve = Constraint([tt], rule=min_reserve)

        def inst_RN_UB(_b, rnew, t):
            return sum(_b.ngb_rn[scenario, rnew, r, t] for r in m.r) \
                   <= m.Qinst_UB[rnew, t] / sum(m.Qg_np[rnew, r] / len(m.r) for r in m.r)

        b.inst_RN_UB = Constraint(m.rnew, [tt], rule=inst_RN_UB)

        def inst_TH_UB(_b, tnew, t):
            return sum(_b.ngb_th[scenario, tnew, r, t] for r in m.r) \
                   <= m.Qinst_UB[tnew, t] / sum(m.Qg_np[tnew, r] / len(m.r) for r in m.r)

        b.inst_TH_UB = Constraint(m.tnew, [tt], rule=inst_TH_UB)

        def en_bal(_b, r, t, d, s):
            return sum(_b.P[scenario, i, r, t, d, s] for i in m.i if (i, r) in m.i_r) \
                   + sum(_b.P_flow[scenario, l, t, d, s] for l in m.l if (l,r) in m.l_er) -\
                         sum(_b.P_flow[scenario, l, t, d, s] for l in m.l if (l,r) in m.l_sr ) \
                   + sum(_b.p_discharged[scenario, j, r, t, d, s] for j in m.j) \
                   == m.L[r, t, d, s] + sum(_b.p_charged[scenario, j, r, t, d, s] for j in m.j) + _b.cu[scenario, r, t, d, s]        

        b.en_bal = Constraint(m.r, [tt], m.d, m.hours, rule=en_bal)

        def capfactor(_b, rn, r, t, d, s):
            return _b.P[scenario, rn, r, t, d, s] == m.Qg_np[rn, r] * m.cf[rn, r, t, d, s] \
                   * _b.ngo_rn[scenario, rn, r, t]

        b.capfactor = Constraint(m.rn_r, [tt], m.d, m.hours, rule=capfactor)

        def min_output(_b, th, r, t, d, s):
            return _b.u[scenario, th, r, t, d, s] * m.Pg_min[th] * m.Qg_np[th, r] <= _b.P[scenario, th, r, t, d, s]

        b.min_output = Constraint(m.th_r, [tt], m.d, m.hours, rule=min_output)

        def max_output(_b, th, r, t, d, s):
            return _b.u[scenario, th, r, t, d, s] * m.Qg_np[th, r] >= _b.P[scenario, th, r, t, d, s] \
                   + _b.Q_spin[scenario, th, r, t, d, s]

        b.max_output = Constraint(m.th_r, [tt], m.d, m.hours, rule=max_output)

        def unit_commit1(_b, th, r, t, d, s, s_):
            if s_ == s - 1:
                return _b.u[scenario, th, r, t, d, s] == _b.u[scenario, th, r, t, d, s_] + _b.su[scenario, th, r, t, d, s] \
                       - _b.sd[scenario, th, r, t, d, s]
            return Constraint.Skip

        b.unit_commit1 = Constraint(m.th_r, [tt], m.d, m.hours, m.hours, rule=unit_commit1)

        def ramp_up(_b, th, r, t, d, s, s_):
            if (th, r) in m.i_r and th in m.th and (s_ == s - 1):
                return _b.P[scenario, th, r, t, d, s] - _b.P[scenario, th, r, t, d, s_] <= m.Ru_max[th] * 1.0000000 * \
                       m.Qg_np[th, r] * (_b.u[scenario, th, r, t, d, s] - _b.su[scenario, th, r, t, d, s]) + \
                       max(m.Pg_min[th], m.Ru_max[th] * 1.0000000) * m.Qg_np[th, r] * _b.su[scenario, th, r, t, d, s]
            return Constraint.Skip

        b.ramp_up = Constraint(m.th, m.r, [tt], m.d, m.hours, m.hours, rule=ramp_up)

        def ramp_down(_b, th, r, t, d, s, s_):
            if s_ == s - 1:
                return _b.P[scenario, th, r, t, d, s_] - _b.P[scenario, th, r, t, d, s] <= m.Rd_max[th] * 1.0000000 * \
                       m.Qg_np[th, r] * (_b.u[scenario, th, r, t, d, s] - _b.su[scenario, th, r, t, d, s]) + \
                       max(m.Pg_min[th], m.Rd_max[th] * 1.0000000) * m.Qg_np[th, r] * _b.sd[scenario, th, r, t, d, s]
            return Constraint.Skip

        b.ramp_down = Constraint(m.th_r, [tt], m.d, m.hours, m.hours, rule=ramp_down)

        def total_op_reserve(_b, r, t, d, s):
            return sum(_b.Q_spin[scenario, th, r, t, d, s] + _b.Q_Qstart[scenario, th, r, t, d, s] for th in m.th if (th, r) in m.th_r) \
                   >= 0.075 * m.L[r, t, d, s]

        b.total_op_reserve = Constraint(m.r, [tt], m.d, m.hours, rule=total_op_reserve)

        def total_spin_reserve(_b, r, t, d, s):
            return sum(_b.Q_spin[scenario, th, r, t, d, s] for th in m.th if (th, r) in m.th_r) >= 0.015 * m.L[r, t, d, s]

        b.total_spin_reserve = Constraint(m.r, [tt], m.d, m.hours, rule=total_spin_reserve)

        def reserve_cap_1(_b, th, r, t, d, s):
            return _b.Q_spin[scenario, th, r, t, d, s] <= m.Qg_np[th, r] * m.frac_spin[th] * _b.u[scenario, th, r, t, d, s]

        b.reserve_cap_1 = Constraint(m.th_r, [tt], m.d, m.hours, rule=reserve_cap_1)

        def reserve_cap_2(_b, th, r, t, d, s):
            return _b.Q_Qstart[scenario, th, r, t, d, s] <= m.Qg_np[th, r] * m.frac_Qstart[th] * \
                   (_b.ngo_th[scenario, th, r, t] - _b.u[scenario, th, r, t, d, s])

        b.reserve_cap_2 = Constraint(m.th_r, [tt], m.d, m.hours, rule=reserve_cap_2)

        def logic_RN_1(_b, rn, r, t):
            if t == 1:
                return _b.ngb_rn[scenario, rn, r, t] - _b.ngr_rn[scenario, rn, r, t] == _b.ngo_rn[scenario, rn, r, t] - \
                       m.Ng_old[rn, r]
            else:
                return _b.ngb_rn[scenario, rn, r, t] - _b.ngr_rn[scenario, rn, r, t] == _b.ngo_rn[scenario, rn, r, t] - \
                       _b.ngo_rn_prev[scenario, rn, r]

        b.logic_RN_1 = Constraint(m.rn_r, [tt], rule=logic_RN_1)

        def logic_TH_1(_b, th, r, t):
            if t == 1:
                return _b.ngb_th[scenario, th, r, t] - _b.ngr_th[scenario, th, r, t] == _b.ngo_th[scenario, th, r, t] - \
                       m.Ng_old[th, r]
            else:
                return _b.ngb_th[scenario, th, r, t] - _b.ngr_th[scenario, th, r, t] == _b.ngo_th[scenario, th, r, t] - \
                       _b.ngo_th_prev[scenario, th, r]

        b.logic_TH_1 = Constraint(m.th_r, [tt], rule=logic_TH_1)

        def logic_ROld_2(_b, rold, r, t):
            if rold in m.rold:
                return _b.ngr_rn[scenario, rold, r, t] + _b.nge_rn[scenario, rold, r, t] == m.Ng_r[rold, r, t]
            return Constraint.Skip

        b.logic_ROld_2 = Constraint(m.rn_r, [tt], rule=logic_ROld_2)

        def logic_TOld_2(_b, told, r, t):
            if told in m.told:
                return _b.ngr_th[scenario, told, r, t] + _b.nge_th[scenario, told, r, t] == m.Ng_r[told, r, t]
            return Constraint.Skip

        b.logic_TOld_2 = Constraint(m.th_r, [tt], rule=logic_TOld_2)

        def logic_3(_b, th, r, t, d, s):
            return _b.u[scenario, th, r, t, d, s] <= _b.ngo_th[scenario, th, r, t]

        b.logic_3 = Constraint(m.th_r, [tt], m.d, m.hours, rule=logic_3)

        # Storage constraints
        def storage_units_balance(_b, j, r, t):
            if t == 1:
                return _b.nsb[scenario, j, r, t] - _b.nsr[scenario, j, r, t] == _b.nso[scenario, j, r, t]
            else:
                return _b.nsb[scenario, j, r, t] - _b.nsr[scenario, j, r, t] == _b.nso[scenario, j, r, t] - _b.nso_prev[scenario, j, r]

        b.storage_units_balance = Constraint(m.j, m.r, [tt], rule=storage_units_balance)

        def min_charge(_b, j, r, t, d, s):
            return m.P_min_charge[j] * _b.nso[scenario, j, r, t] <= _b.p_charged[scenario, j, r, t, d, s]

        b.min_charge = Constraint(m.j, m.r, [tt], m.d, m.hours, rule=min_charge)

        def max_charge(_b, j, r, t, d, s):
            return _b.p_charged[scenario, j, r, t, d, s] <= m.P_max_charge[j] * _b.nso[scenario, j, r, t]

        b.max_charge = Constraint(m.j, m.r, [tt], m.d, m.hours, rule=max_charge)

        def min_discharge(_b, j, r, t, d, s):
            return m.P_min_discharge[j] * _b.nso[scenario, j, r, t] <= _b.p_discharged[scenario, j, r, t, d, s]

        b.min_discharge = Constraint(m.j, m.r, [tt], m.d, m.hours, rule=min_discharge)

        def max_discharge(_b, j, r, t, d, s):
            return _b.p_discharged[scenario, j, r, t, d, s] <= m.P_max_discharge[j] * _b.nso[scenario, j, r, t]

        b.max_discharge = Constraint(m.j, m.r, [tt], m.d, m.hours, rule=max_discharge)

        def min_storage_level(_b, j, r, t, d, s):
            return m.min_storage_cap[j] * _b.nso[scenario, j, r, t] <= _b.p_storage_level[scenario, j, r, t, d, s]

        b.min_storage_level = Constraint(m.j, m.r, [tt], m.d, m.hours, rule=min_storage_level)

        def max_storage_level(_b, j, r, t, d, s):
            return _b.p_storage_level[scenario, j, r, t, d, s] <= m.max_storage_cap[j] * _b.nso[scenario, j, r, t]

        b.max_storage_level = Constraint(m.j, m.r, [tt], m.d, m.hours, rule=max_storage_level)

        def storage_balance(_b, j, r, t, d, s, s_):
            if s_ == s - 1 and s > 1:
                return _b.p_storage_level[scenario, j, r, t, d, s] == _b.p_storage_level[scenario, j, r, t, d, s_] \
                       + m.eff_rate_charge[j] * _b.p_charged[scenario, j, r, t, d, s] \
                       - (1 / m.eff_rate_discharge[j]) * _b.p_discharged[scenario, j, r, t, d, s]
            return Constraint.Skip

        b.storage_balance = Constraint(m.j, m.r, [tt], m.d, m.hours, m.hours, rule=storage_balance)

        def storage_balance_1HR(_b, j, r, t, d, s):
            if s == 1:
                return _b.p_storage_level[scenario, j, r, t, d, s] == 0.5 * m.max_storage_cap[j] * _b.nso[scenario, j, r, t] \
                       + m.eff_rate_charge[j] * _b.p_charged[scenario, j, r, t, d, s] \
                       - (1 / m.eff_rate_discharge[j]) * _b.p_discharged[scenario, j, r, t, d, s]
            return Constraint.Skip

        b.storage_balance_1HR = Constraint(m.j, m.r, [tt], m.d, m.hours, rule=storage_balance_1HR)

        def storage_heuristic(_b, j, r, t, d, s):
            if s == m.hours.last():
                return _b.p_storage_level[scenario, j, r, t, d, s] == 0.5 * m.max_storage_cap[j] * _b.nso[scenario, j, r, t]
            return Constraint.Skip

        b.storage_heuristic = Constraint(m.j, m.r, [tt], m.d, m.hours, rule=storage_heuristic)

        b.link_equal1 = ConstraintList()

        b.link_equal2 = ConstraintList()

        b.link_equal3 = ConstraintList()

        b.link_equal4 = ConstraintList()

        b.fut_cost = ConstraintList()

    def scenario_block_rule(_b, scenario):
        _b.time_block = Block(m.t, [scenario], rule=time_block_rule)

    m.scenario_block = Block(m.scenarios, rule=scenario_block_rule)

    return m
