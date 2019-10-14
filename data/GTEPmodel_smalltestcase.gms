* Generation and Transmission Expansion model for ERCOT region
* Author: C.L. Lara and I.E. Grossmann
* Last revision: 09/26/2016

********************************************************************************
************************************ Data **************************************
********************************************************************************

SET      r       load node (ERCOT regions)
;

SETS     i         generation clusters
         th(i)     thermal clusters
         rn(i)     renewable clusters
         co(th)     coal clusters
         ng(th)     NG clusters
         nu(th)     nuclear clusters
         PV(rn)     solar PV clusters
         CSP(rn)    solar CSP clusters
         wi(rn)     wind clusters
         old(i)    existing clusters
         new(i)    potential clusters
         rold(old) rn existing clusters
         rnew(new) rn potential clusters
         told(old) th existing clusters
         tnew(new) th potential clusters
;

SETS     i_r(i,r)  mapping set between regions and clusters;

ALIAS (i,ii);

SETS
         t       time periods (years) /1*15/
         ss      season
         s       subperiods
;

ALIAS (t,tt,ttt)
      (s,s_)
      (r,r_);

PARAMETERS
                 L(r,t,ss,s)      load demand per region for subperiod s in season ss of year t(MW)
                 n_ss(ss)         days per season
                 L_max(t)         peak load in year t (MW)
                 cf(i,r,t,ss,s)   capacity factor
                 Qg_np(i,r)       nameplate capacity per generator in cluster i of region r (MW)
                 Ng_old(i,r)      number of existing generators in each cluster per region r
                 Ng_max(i,r)      maximum number generators in each new cluster
                 Qinst_UB(i,t)    'upper bound on yearly installation based on energy (MW/year)'
                 LT(i)            expected lifetime of a generator in cluster i (years)
                 Tremain(t)       remaining time in years
                 Ng_r(old,r,t)    # of generators to retire at year in cluster i in region r
                 q_v(i)           capacity value
                 Pg_min(i)        Minimum operating output of a generator in cluster i (% nameplate)
                 Ru_max(i)        'maximum up-ramp rate (% Qg_np/h)'
                 Rd_max(i)        'maximum down-ramp rate (% QG_np/h)'
                 f_start(i)       'fuel usage at startup (MMBtu/MW)'
                 C_start(i)       'fixed startup cost ($/MW)'
                 frac_spin(i)     maximum fraction of each cluster that can contribute to spinning reserves
                 frac_Qstart(i)   maximum fraction of each cluster that can contribute to quick-start reserves
                 t_loss(r,r_)     'transmission loss metric between region r and region r_(%/miles)'
                 t_up(r,r_)       transmission limit (MW)
                 dist(r,r_)       'distance from region z to region z_ (miles)'
                 if_(t)           interest factor for year t
                 ED(t)            energy demand during year t (MWh)
                 Rmin(t)          system minimum reserve margin for year t (fraction)
                 hr(i,r)          'heat rate of cluster i in region r (MMBtu/MWh)'
                 P_fuel(i,t)      'price of fuel for cluster i in year t ($/MMBtu)'
                 EF_CO2(i)        'full lifecycle emission factor (kg CO2/MMBtu)'
                 FOC(i,t)         'fixed operating cost ($/MW)'
                 VOC(i,t)         'variable operating cost ($/MWh)'
                 CCm(i)           capital cost multiplier (unitless)
                 DIC(i,t)         'discounted investment cost ($/MW)'
                 LEC(i)           'life extension cost (% DIC(i,y) of corresponding new generator)'
                 PEN(t)           'penalty for not meeting the RES quota target during year t ($/MWh)'
                 PENc             'penalty for curtailment'
                 tx_CO2(t)        'carbon tax in year t ($/kg CO2)'
                 RES_min(t)       minimum RES production requirement during year t (per unit of annual demand)
;
         SCALARS
                 hs     duration of the subperiod s of year y (hr)
                 ir     nominal interest rate;

$GDXin GTEP_data
$LOAD i, th, rn, co, ng, nu, PV, CSP, wi, old, new, rold, rnew, told, tnew, r, ss, s
$LOAD L, n_ss, L_max, cf, Qg_np, Ng_old, Ng_max, Qinst_UB, LT, Tremain, Ng_r, q_v, Pg_min, Ru_max, Rd_max
$LOAD f_start, C_start, frac_spin, frac_Qstart, t_loss, t_up, dist, if_, ED, Rmin, hr, P_fuel, EF_CO2
$LOAD FOC, VOC, CCm, DIC, LEC, PEN, PENc, tx_CO2, RES_min
$LOAD hs, ir
$GDXin

i_r(old,r)$(Ng_old(old,r) NE 0) = yes;
i_r(new,r)=yes;
display i_r;

Execute_unload 'GTEP_data.gdx';

Execute "gdx2sqlite -i GTEP_data.gdx -o GTEP_data_15years.db";













