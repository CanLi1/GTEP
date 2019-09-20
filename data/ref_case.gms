* Generation and Transmission Expansion model for ERCOT region
* Author: C.L. Lara and I.E. Grossmann
* Last revision: 05/18/2016

********************************************************************************
********************************** REFERENCE CASE ******************************
********************************************************************************

PARAMETER        PEN(t)          'penalty for not meeting the RES quota target during year t ($/MWh)';
PEN(t)= 5000;
display PEN;

PARAMETER        PENc            'penalty for curtailment';
PENc= 0;
display PENc;

PARAMETERS       tx_CO2(t)       'carbon tax in year t ($/kg CO2)'
                 RES_min(t)      minimum RES production requirement during year t (per unit of annual demand)
;

*carbon tax (kg CO2/MWh)
tx_CO2(t)=0;
DISPLAY tx_CO2;

*min RES production quota
$onecho > task.txt
par=RES_min            rng=RESquota!a5:b34          rdim=1
$offecho

$call GDXXRW GTEPdata_rev.xlsx trace=3 @task.txt
$GDXIN   GTEPdata_rev.gdx
$LOADDC  RES_min
$GDXIN
DISPLAY RES_min;
