* Generation and Transmission Expansion model for ERCOT region
* Author: C.L. Lara and I.E. Grossmann
* Last revision: 05/17/2016


********************************************************************************
*************************** Capacity-related data ******************************
********************************************************************************

PARAMETER        Qg_np(i,r)    nameplate capacity per generator in cluster i of region r (MW)
                 Ng_old(i,r)   number of existing generators in each cluster per region r;
$onecho > task.txt
par=Qg_np            rng=GenData!j86:o102         rdim=1         cdim=1
par=Ng_old           rng=GenData!c86:h102         rdim=1         cdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  Qg_np
$LOADDC  Ng_old
$GDXIN
DISPLAY Qg_np, Ng_old;


PARAMETER       I_max(i)               Installation upper bound (MW)
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=I_max rng=GenData!h63:i78   rdim=1
$GDXIN GTEPdata_rev.gdx
$LOAD I_max
$GDXIN
DISPLAY I_max;

PARAMETER       Ng_max(i,r)             maximum number generators in each new cluster;
Ng_max(i,r)=floor(I_max(i)/Qg_np(i,r))$(Qg_np(i,r) NE 0) + 0;
DISPLAY Ng_max;

PARAMETER        Qinst_UB(i,t)         'upper bound on yearly installation based on energy (MW/year)';
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=Qinst_UB rng=GenData!ac26:bg42   rdim=1 cdim=1
$GDXIN GTEPdata_rev.gdx
$LOAD Qinst_UB
$GDXIN
Display Qinst_UB;

PARAMETER        LT(i)           expected lifetime of a generator in cluster i (years);
$onecho > task.txt
par=LT               rng=GenData!k45:l60          rdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  LT
$GDXIN

DISPLAY LT;

PARAMETER        Tremain(t)      remaining time in years;
Tremain(t)= CARD(t)-ORD(t)+1;

DISPLAY Tremain;


PARAMETER        Ng_r_NE(t,old)          # of generators to retire at year in cluster i in the Northeast region
                 Ng_r_W(t,old)           # of generators to retire at year in cluster i in the West region
                 Ng_r_C(t,old)           # of generators to retire at year in cluster i in the Coastal region
                 Ng_r_S(t,old)           # of generators to retire at year in cluster i in the South region
                 Ng_r_PH(t,old)          # of generators to retire at year in cluster i in the Panhandle region
                 Ng_r(old,r,t)           # of generators to retire at year in cluster i in region r
;
$onecho > task.txt
par=Ng_r_NE               rng=GenRetirement!i2:p32          rdim=1      cdim=1
par=Ng_r_W                rng=GenRetirement!i36:p66         rdim=1      cdim=1
par=Ng_r_C                rng=GenRetirement!i69:p99         rdim=1      cdim=1
par=Ng_r_S                rng=GenRetirement!i102:p132       rdim=1      cdim=1
par=Ng_r_PH               rng=GenRetirement!i135:p165       rdim=1      cdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  Ng_r_NE, Ng_r_W, Ng_r_C, Ng_r_S, Ng_r_PH
$GDXIN

Ng_r(old,'Northeast',t)=Ng_r_NE(t,old);
Ng_r(old,'West',t)=Ng_r_W(t,old);
Ng_r(old,'Coastal',t)=Ng_r_C(t,old);
Ng_r(old,'South',t)=Ng_r_S(t,old);
Ng_r(old,'Panhandle',t)=Ng_r_PH(t,old);

DISPLAY Ng_r;

PARAMETER        q_v(i)      capacity value;
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=q_v rng=GenData!e63:f78   rdim=1
$GDXIN GTEPdata_rev.gdx
$LOAD q_v
$GDXIN
Display q_v;

********************************************************************************
******************************* Operational data *******************************
********************************************************************************

PARAMETER Pg_min(i)       Minimum operating output of a generator in cluster i (% nameplate);
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=Pg_min rng=GenData!q45:r60   rdim=1
$GDXIN GTEPdata_rev.gdx
$LOAD Pg_min
$GDXIN
Display Pg_min;

PARAMETER Ru_max(i)      'maximum up-ramp rate (% Qg_np/h)'
          Rd_max(i)      'maximum down-ramp rate (% QG_np/h)';
$onecho > task.txt
par=Ru_max            rng=GenData!w45:x60          rdim=1
par=Rd_max            rng=GenData!t45:u60          rdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  Ru_max
$LOADDC  Rd_max
$GDXIN
DISPLAY Ru_max, Rd_max;


PARAMETER f_start(i)      'fuel usage at startup (MMBtu/MW)';
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=f_start rng=GenData!b63:c78   rdim=1
$GDXIN GTEPdata_rev.gdx
$LOAD f_start
$GDXIN
Display f_start;

PARAMETER C_start(i)      'fixed startup cost ($/MW)';
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=C_start rng=GenData!k63:l78   rdim=1
$GDXIN GTEPdata_rev.gdx
$LOAD C_start
$GDXIN
Display C_start;

PARAMETER frac_spin(i)   maximum fraction of each cluster that can contribute to spinning reserves
          frac_Qstart(i) maximum fraction of each cluster that can contribute to quick-start reserves;
$onecho > task.txt
par=frac_spin            rng=GenData!t63:u78          rdim=1
par=frac_Qstart          rng=GenData!w63:x78          rdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  frac_spin
$LOADDC  frac_Qstart
$GDXIN

DISPLAY frac_spin, frac_Qstart;

********************************************************************************
******************************* Transmission data ******************************
********************************************************************************

PARAMETER t_loss(r,r_) 'transmission loss metric between region r and region r_(%/miles)'
;
t_loss(r,r_)=0.0001;
display t_loss;
* 1%/100 miles as it was assumed in ReEDS model

PARAMETER dist(r,r_)   'distance from region z to region z_ (miles)'
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=dist rng=Transm!a4:f9   rdim=1 cdim=1
$GDXIN GTEPdata_rev.gdx
$LOAD dist
$GDXIN
DISPLAY dist;

PARAMETER t_up(r,r_)   transmission limit (MW)
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=t_up rng=Transm!a17:f22   rdim=1 cdim=1
$GDXIN GTEPdata_rev.gdx
$LOAD t_up
$GDXIN
DISPLAY t_up;

PARAMETER t_cost        'transmission cost in $/mile';
t_cost=2000000;

********************************************************************************
*************************** Cost-related data **********************************
********************************************************************************


SCALAR
         ir              nominal interest rate   /0.057/
;
display ir;

PARAMETER
         if_(t)          discount factor for year t
         ED(t)           energy demand during year t (MWh)
         Rmin(t)         system minimum reserve margin for year t (fraction)
;

*Interest factor
if_(t) = 1/((1+ir)**(ORD(t)-1));


*Energy demand
ED(t)=sum((r,ss,s),(n_ss(ss)*hs*L(r,t,ss,s)));

*Minimum reserve margin
Rmin(t)=0.1375;
display if_, ED, Rmin;

PARAMETER
         hr(i,r)         'heat rate of cluster i in region r (MMBtu/MWh)'
         P_fuel_NG(t)    'price of NG in year t ($/MMBtu)'
         P_fuel_coal(t)  'price of coal in year t ($/MMBtu)'
         P_fuel(i,t)     'price of fuel for cluster i in year t ($/MMBtu)'
         EF_CO2(i)       'full lifecycle emission factor (kg CO2/MMBtu)'
;


*Heat Rate
$onecho > task.txt
par=hr            rng=GenData!c106:h122          rdim=1    cdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  hr
$GDXIN
display hr;

*Price of fuel (source US Energy Information Administration)
$onecho > task.txt
par=P_fuel_NG            rng=FuelPrice!t36:u65    rdim=1
par=P_fuel_coal          rng=FuelPrice!w36:x65    rdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  P_fuel_NG, P_fuel_coal
$GDXIN

P_fuel(ng,t)=P_fuel_NG(t);
P_fuel(co,t)=P_fuel_coal(t);
P_fuel(nu,t)=0.72;
P_fuel(rn,t)=0;

DISPLAY P_fuel;


*CO2 emission factor in (kg CO2/MWh)
$onecho > task.txt
par=EF_CO2            rng=GenData!e27:f42          rdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  EF_CO2
$GDXIN

DISPLAY EF_CO2;


PARAMETER        FOC(i,t)         'fixed operating cost ($/MW)';
$onecho > task.txt
par=FOC            rng=FixOM!a2:ae18          rdim=1 cdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  FOC
$GDXIN

Display FOC;


PARAMETER        VOC(i,t)          'variable operating cost ($/MWh)';
$onecho > task.txt
par=VOC            rng=VarOM!a2:ae18          rdim=1 cdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  VOC
$GDXIN

Display VOC;

PARAMETER        ACC(i,t)          'annualized capital cost ($/MW)'
                 CCm(i)            capital cost multiplier (unitless)
;

*Overnight capital cost
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=ACC rng=CapCost!A23:AE39   rdim=1 cdim=1
$GDXIN GTEPdata_rev.gdx
$LOADDC ACC
$GDXIN
*Display ACC;

*Capital Cost multiplier
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=CCm rng=CapCost!G43:H58   rdim=1
$GDXIN GTEPdata_rev.gdx
$LOADDC CCm
$GDXIN
*Display CCm;


PARAMETER        DIC(i,t)        'discounted investment cost ($/MW)';
DIC(new,t) = ACC(new,t)*sum((tt)$(ORD(tt) LE min(LT(new),Tremain(t))), if_(tt));

*DIC for existing plants is used in the calculation of extended lifetime cost
*It is the same as for the new clusters that have the same or similar generation technology
DIC('coal-st-old1',t) = DIC('coal-igcc-new',t);
DIC('ng-ct-old',t) = DIC('ng-ct-new',t);
DIC('ng-st-old',t) = DIC('coal-igcc-new',t);
DIC('ng-cc-old',t) = DIC('ng-cc-new',t);
DIC('nuc-st-old',t) = DIC('nuc-st-new',t);
DIC('pv-old',t) = DIC('pv-new',t);
DIC('wind-old',t) = DIC('wind-new',t);
DISPLAY DIC;

PARAMETER        LEC(i)          'life extension cost (% DIC(i,y) of corresponding new generator)';
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=LEC rng=GenData!Q63:R78   rdim=1
$GDXIN GTEPdata_rev.gdx
$LOADDC LEC
$GDXIN

DISPLAY LEC;



