* Generation and Transmission Expansion model for ERCOT region
* Author: C.L. Lara and I.E. Grossmann
* Last revision: 05/17/2016

********************************************************************************
**************************** HOURLY LEVEL PROBLEM ******************************
********************************************************************************

SETS     i         generation clusters     /coal-st-old1, ng-ct-old, ng-cc-old, ng-st-old,
                                            nuc-st-old, pv-old, wind-old, nuc-st-new, wind-new, pv-new, csp-new
                                            coal-igcc-new, coal-igcc-ccs-new, ng-cc-new, ng-cc-ccs-new, ng-ct-new/
         th(i)     thermal clusters        /nuc-st-old, nuc-st-new, coal-st-old1,  coal-igcc-new,
                                            coal-igcc-ccs-new, ng-ct-old, ng-cc-old, ng-st-old, ng-cc-new,
                                            ng-cc-ccs-new, ng-ct-new/
         rn(i)     renewable clusters      /pv-old, pv-new, csp-new, wind-old, wind-new/

         co(th)     coal clusters           /coal-st-old1, coal-igcc-new, coal-igcc-ccs-new/
         ng(th)     NG clusters             /ng-ct-old, ng-cc-old, ng-st-old, ng-cc-new, ng-cc-ccs-new, ng-ct-new/
         nu(th)     nuclear clusters        /nuc-st-old, nuc-st-new/
         PV(rn)     solar PV clusters       /pv-old, pv-new/
         CSP(rn)    solar CSP clusters      /csp-new/
         wi(rn)     wind clusters           /wind-old, wind-new/

         old(i)    existing clusters       /coal-st-old1, ng-ct-old, ng-cc-old, ng-st-old,
                                            nuc-st-old, pv-old, wind-old/
         new(i)    potential clusters      /nuc-st-new, wind-new, pv-new, csp-new, coal-igcc-new, coal-igcc-ccs-new,
                                            ng-cc-new, ng-cc-ccs-new, ng-ct-new/
         rold(old) rn existing clusters   /pv-old, wind-old/
         rnew(new) rn potential clusters  /wind-new, pv-new, csp-new/

         told(old) th existing clusters   /nuc-st-old, coal-st-old1, ng-ct-old, ng-cc-old, ng-st-old/
         tnew(new) th potential clusters  /nuc-st-new, coal-igcc-new,coal-igcc-ccs-new, ng-cc-new,ng-cc-ccs-new, ng-ct-new/
;
display i, th, rn, co, ng, nu, PV, CSP, wi, old, new, rold, rnew, told, tnew;

ALIAS (i,ii);

SETS
         t       time periods (years)    /1*3/
         ss      season                  /spring, summer, fall, winter/
         s       subperiods
;
display t, ss;
SET      r       load node (ERCOT regions)   /Northeast, West, Coastal, South, Panhandle/

ALIAS (t,tt,ttt)
      (s,s_)
      (r,r_);

********************************************************************************
*************************** Load-related data ***********************************
********************************************************************************

PARAMETER        L_NE(s,ss)          load demand in Northeast region for subperiod s in season ss in the 1st year of the time horizon(MW)
                 L_W(s,ss)           load demand in West region for subperiod s in season ss of the 1st year in the time horizon(MW)
                 L_C(s,ss)           load demand in Coastal region for subperiod s in season ss of the 1st year in the time horizon(MW)
                 L_S(s,ss)           load demand in South region for subperiod s in season ss of the 1st year in the time horizon(MW)
                 L_PH(s,ss)          load demand in Panhandle region for subperiod s in season ss of the 1st year in the time horizon(MW)
;

$onecho > task.txt
dset=s           rng=LoadData_hour!n4:n27    rdim=1
par=L_NE         rng=LoadData_hour!n31:r55   rdim=1   cdim=1
par=L_W          rng=LoadData_hour!t31:x55   rdim=1   cdim=1
par=L_C          rng=LoadData_hour!z31:ad55  rdim=1   cdim=1
par=L_S          rng=LoadData_hour!n59:r83   rdim=1   cdim=1
par=L_PH         rng=LoadData_hour!t59:x83   rdim=1   cdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOAD    s
$LOADDC  L_NE, L_W, L_C, L_S, L_PH
$GDXIN

PARAMETER L_growth       load annual growth rate         /0.014/;

PARAMETER L(r,t,ss,s)      load demand per region for subperiod s in season ss of year t(MW);
L('Northeast',t,ss,s)=L_NE(s,ss)*(1+(ORD(t)-1)*L_growth);
L('West',t,ss,s)=L_W(s,ss)*(1+(ORD(t)-1)*L_growth);
L('Coastal',t,ss,s)=L_C(s,ss)*(1+(ORD(t)-1)*L_growth);
L('South',t,ss,s)=L_S(s,ss)*(1+(ORD(t)-1)*L_growth);
L('Panhandle',t,ss,s)=L_PH(s,ss)*(1+(ORD(t)-1)*L_growth);

DISPLAY s;
DISPLAY L;

PARAMETER        n_ss(ss)        days per season
/spring  128.142857142857
 summer  77
 fall    97
 winter  62.8571428571429/
;
display n_ss;
PARAMETER total_n;
total_n=sum(ss, n_ss(ss));
DISPLAY total_n;

PARAMETER load_year_1;
load_year_1 = sum((r,ss),sum(s,L(r,'1',ss,s)*n_ss(ss)));
DISPLAY load_year_1;

SCALAR    hs     duration of the subperiod s of year y (hr) /1/;
display hs;

PARAMETER        L_max(t)          peak load in year t (MW);
$call GDXXRW GTEPdata_rev.xlsx trace=3 par=L_max rng=PeakLoad!A2:B31   rdim=1
$GDXIN GTEPdata_rev.gdx
$LOADDC L_max
$GDXIN

Display L_max;

********************************************************************************
*************************** Capacity factor of RES *****************************
********************************************************************************

PARAMETER cf(i,r,t,ss,s)   capacity factor

          cf_csp_NE(s,ss)   capacity factor of solar CSP clusters in Northeast region
          cf_pvsat_NE(s,ss) capacity factor of solar PVSAT clusters in Northeast region
          cf_windold_NE(s,ss)  capacity factor of old wind clusters in Northeast region
          cf_windnew_NE(s,ss)  capacity factor of new wind clusters in Northeast region

          cf_csp_W(s,ss)   capacity factor of solar CSP clusters in West region
          cf_pvsat_W(s,ss) capacity factor of solar PVSAT clusters in West region
          cf_windold_W(s,ss)  capacity factor of old wind clusters in West region
          cf_windnew_W(s,ss)  capacity factor of new wind clusters in West region

          cf_csp_C(s,ss)   capacity factor of solar CSP clusters in Coastal region
          cf_pvsat_C(s,ss) capacity factor of solar PVSAT clusters in Coastal region
          cf_windold_C(s,ss)  capacity factor of old wind clusters in Coastal region
          cf_windnew_C(s,ss)  capacity factor of new wind clusters in Coastal region

          cf_csp_S(s,ss)   capacity factor of solar CSP clusters in South region
          cf_pvsat_S(s,ss) capacity factor of solar PVSAT clusters in South region
          cf_windold_S(s,ss)  capacity factor of old wind clusters in South region
          cf_windnew_S(s,ss)  capacity factor of new wind clusters in South region

          cf_csp_PH(s,ss)   capacity factor of solar CSP clusters in Panhandle region
          cf_pvsat_PH(s,ss) capacity factor of solar PVSAT clusters in Panhandle region
          cf_windold_PH(s,ss)  capacity factor of old wind clusters in Panhandle region
          cf_windnew_PH(s,ss)  capacity factor of new wind clusters in Panhandle region
;
$onecho > task.txt
par=cf_csp_NE          rng=CapFactor_hour!ad34:ah58    rdim=1 cdim=1
par=cf_pvsat_NE        rng=CapFactor_hour!aj34:an58    rdim=1 cdim=1
par=cf_windold_NE      rng=CapFactor_hour!ap34:at58    rdim=1 cdim=1
par=cf_windnew_NE      rng=CapFactor_hour!av34:az58    rdim=1 cdim=1

par=cf_csp_W           rng=CapFactor_hour!ad63:ah87    rdim=1 cdim=1
par=cf_pvsat_W         rng=CapFactor_hour!aj63:an87    rdim=1 cdim=1
par=cf_windold_W       rng=CapFactor_hour!ap63:at87    rdim=1 cdim=1
par=cf_windnew_W       rng=CapFactor_hour!av63:az87    rdim=1 cdim=1

par=cf_csp_C           rng=CapFactor_hour!ad92:ah116   rdim=1 cdim=1
par=cf_pvsat_C         rng=CapFactor_hour!aj92:an116   rdim=1 cdim=1
par=cf_windold_C       rng=CapFactor_hour!ap92:at116   rdim=1 cdim=1
par=cf_windnew_C       rng=CapFactor_hour!av92:az116   rdim=1 cdim=1

par=cf_csp_S           rng=CapFactor_hour!ad121:ah145  rdim=1 cdim=1
par=cf_pvsat_S         rng=CapFactor_hour!aj121:an145  rdim=1 cdim=1
par=cf_windold_S       rng=CapFactor_hour!ap121:at145  rdim=1 cdim=1
par=cf_windnew_S       rng=CapFactor_hour!av121:az145  rdim=1 cdim=1

par=cf_csp_PH          rng=CapFactor_hour!ad150:ah174  rdim=1 cdim=1
par=cf_pvsat_PH        rng=CapFactor_hour!aj150:an174  rdim=1 cdim=1
par=cf_windold_PH      rng=CapFactor_hour!ap150:at174  rdim=1 cdim=1
par=cf_windnew_PH      rng=CapFactor_hour!av150:az174  rdim=1 cdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  cf_csp_NE, cf_pvsat_NE, cf_windold_NE, cf_windnew_NE
$LOADDC  cf_csp_W, cf_pvsat_W, cf_windold_W, cf_windnew_W
$LOADDC  cf_csp_C, cf_pvsat_C, cf_windold_C, cf_windnew_C
$LOADDC  cf_csp_S, cf_pvsat_S, cf_windold_S, cf_windnew_S
$LOADDC  cf_csp_PH, cf_pvsat_PH, cf_windold_PH, cf_windnew_PH
$GDXIN

cf(CSP,'Northeast',t,ss,s)=cf_csp_NE(s,ss);
cf(PV,'Northeast',t,ss,s)=cf_pvsat_NE(s,ss);
cf('wind-old','Northeast',t,ss,s)=cf_windold_NE(s,ss);
cf('wind-new','Northeast',t,ss,s)=cf_windnew_NE(s,ss);

cf(CSP,'West',t,ss,s)=cf_csp_W(s,ss);
cf(PV,'West',t,ss,s)=cf_pvsat_W(s,ss);
cf('wind-old','West',t,ss,s)=cf_windold_W(s,ss);
cf('wind-new','West',t,ss,s)=cf_windnew_W(s,ss);

cf(CSP,'Coastal',t,ss,s)=cf_csp_C(s,ss);
cf(PV,'Coastal',t,ss,s)=cf_pvsat_C(s,ss);
cf('wind-old','Coastal',t,ss,s)=cf_windold_C(s,ss);
cf('wind-new','Coastal',t,ss,s)=cf_windnew_C(s,ss);

cf(CSP,'South',t,ss,s)=cf_csp_S(s,ss);
cf(PV,'South',t,ss,s)=cf_pvsat_S(s,ss);
cf('wind-old','South',t,ss,s)=cf_windold_S(s,ss);
cf('wind-new','South',t,ss,s)=cf_windnew_S(s,ss);

cf(CSP,'Panhandle',t,ss,s)=cf_csp_PH(s,ss);
cf(PV,'Panhandle',t,ss,s)=cf_pvsat_PH(s,ss);
cf('wind-old','Panhandle',t,ss,s)=cf_windold_PH(s,ss);
cf('wind-new','Panhandle',t,ss,s)=cf_windnew_PH(s,ss);

cf(th,r,t,ss,s)=1;

Display cf;





