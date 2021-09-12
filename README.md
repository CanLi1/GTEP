<h1>Input data </h1>


| Set notation    | definition                                | Example                                                                                                                                                                                                                       |
|-----------------|-------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|         m.r     |  regions                                  | ['Northeast', 'West', 'Coastal', 'South', 'Panhandle']                                                                                                                                                                        |
|         m.i     |  generators                               |    ['coal-st-old1', 'ng-ct-old', 'ng-cc-old', 'ng-st-old', 'pv-old', 'wind-old',  'wind-new', 'pv-new', 'csp-new', 'coal-igcc-new', 'coal-igcc-ccs-new', 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new','nuc-st-old','nuc-st-new'] |
|         m.th    |  thermal generators                       | ['coal-st-old1', 'coal-igcc-new', 'coal-igcc-ccs-new','ng-ct-old', 'ng-cc-old', 'ng-st-old', 'ng-cc-new', 'ng-cc-ccs-new','ng-ct-new','nuc-st-old', 'nuc-st-new']                                                             |
|         m.rn    |  renewable generators                     | ['pv-old', 'pv-new', 'csp-new', 'wind-old', 'wind-new']                                                                                                                                                                       |
|         m.co    |  coal-based generators                    | ['coal-st-old1', 'coal-igcc-new', 'coal-igcc-ccs-new']                                                                                                                                                                        |
|         m.ng    |  natural gas (NG) generators              | ['ng-ct-old', 'ng-cc-old', 'ng-st-old', 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new']                                                                                                                                            |
|         m.nu    |  nuclear generators                       | ['nuc-st-old', 'nuc-st-new']                                                                                                                                                                                                  |
|         m.pv    |  solar photovoltaic generators            | ['pv-old', 'pv-new']                                                                                                                                                                                                          |
|         m.csp   |  concentrated solar panels                | ['csp-new']                                                                                                                                                                                                                   |
|         m.wi    |  wind turbines                            | ['wind-old', 'wind-new']                                                                                                                                                                                                      |
|         m.old   |  subset of existing generators            | ['coal-st-old1', 'ng-ct-old', 'ng-cc-old', 'ng-st-old', 'pv-old','wind-old','nuc-st-old']                                                                                                                                     |
|         m.new   |  subset of potential generators           | ['wind-new', 'pv-new', 'csp-new', 'coal-igcc-new','coal-igcc-ccs-new', 'ng-cc-new', 'ng-cc-ccs-new', 'ng-ct-new','nuc-st-new']                                                                                                |
|         m.rold  |  subset of existing renewable generators  | ['pv-old', 'wind-old']                                                                                                                                                                                                        |
|         m.rnew  |  subset of potential renewable generators | ['wind-new', 'pv-new', 'csp-new']                                                                                                                                                                                             |
|         m.told  |  subset of existing thermal generators    | ['coal-st-old1', 'ng-ct-old', 'ng-cc-old', 'ng-st-old','nuc-st-old']                                                                                                                                                          |
|         m.tnew  |  subset of potential thermal generators   | ['coal-igcc-new', 'coal-igcc-ccs-new', 'ng-cc-new','ng-cc-ccs-new', 'ng-ct-new','nuc-st-new']                                                                                                                                 |
|         m.j     |  clusters of potential storage unit       | ['Li\_ion', 'Lead\_acid', 'Flow']                                                                                                                                                                                               |
|         m.d     |  set of representative days               | RangeSet(15)                                                                                                                                                                                                                  |
|         m.hours |  set of subperiods within the days        | RangeSet(24)                                                                                                                                                                                                                  |
|         m.t     |  set of time periods                      | RangeSet(15)                                                                                                                                                                                                                  |
|         m.l     |  set of transmission lines                | RangeSet(nlines)                                                                                                                                                                                                              |
|         m.l\_old |  set of existing transmission lines       |                                                                                                                                                                                                                               |
|         m.l\_new |  set of prospective transmission lines    |                                                                                                                                                                                                                               |
|         m.stage |  set of stages in the scenario tree       | RangeSet(stages)                                                                                                                                                                                                              |


| Parameter notation       | Definition                                                                                                                                                |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
|     m.L                  |  load demand in region r in sub-period s of representative day d of year t (MW)                                                                           |
|     m.n\_d                |  weight of representative day d                                                                                                                           |
|     m.L\_max              |  peak load in year t (MW)                                                                                                                                 |
|     m.cf                 |  capacity factor of renewable generation cluster i in region r at sub-period s, of representative day d of r  year t (fraction of the nameplate capacity) |
|     m.Qg\_np              |  generator nameplate capacity (MW)                                                                                                                        |
|     m.Ng\_max             |  max number of generators in cluster i of region r                                                                                                        |
|     m.Qinst\_UB           |  Yearly upper bound on installation capacity by generator type                                                                                            |
|     m.LT                 |  expected lifetime of generation cluster i (years)                                                                                                        |
|     m.Tremain            |  remaining time until the end of the time horizon at year t (years)                                                                                       |
|     m.Ng\_r               |  number of generators in cluster i of region r that achieved their expected lifetime                                                                      |
|     m.q\_v                |  capacity value of generation cluster i (fraction of the nameplate capacity)                                                                              |
|     m.Pg\_min             |  minimum operating output of a generator in cluster i ∈ ITH (fraction of the nameplate capacity)                                                          |
|     m.Ru\_max             |  maximum ramp-up rate for cluster i ∈ ITH (fraction of nameplate capacity)                                                                                |
|     m.Rd\_max             |  maximum ramp-down rate for cluster i ∈ ITH (fraction of nameplate capacity)                                                                              |
|     m.f\_start            |  fuel usage at startup (MMbtu/MW)                                                                                                                         |
|     m.C\_start            | fixed startup cost for generator cluster i ($/MW)                                                                                                         |
|     m.frac\_spin          |  maximum fraction of nameplate capacity of each generator that can contribute to spinning reserves   (fraction of nameplate capacity)                     |
|     m.frac\_Qstart        |  maximum fraction of nameplate capacity of each generator that can contribute to quick-start reserves  (fraction of nameplate capacity)                   |
|     m.t\_loss             |  transmission loss factor between region r and region r ̸= r (%/miles)                                                                                    |
|     m.t\_up               |  transmission line capacity                                                                                                                               |
|     m.dist               |  distance between region r and region r′ ̸= r (miles)                                                                                                     |
|     m.if\_                |  discount factor for year t                                                                                                                               |
|     m.ED                 |  energy demand during year t (MWh)                                                                                                                        |
|     m.Rmin               |  system's minimum reserve margin for year t (fraction of the peak load)                                                                                   |
|     m.hr                 |  heat rate of generator cluster i (MMBtu/MWh)                                                                                                             |
|     m.P\_fuel             |  price of fuel for generator cluster i in year t ($/MMBtu)                                                                                                |
|     m.EF\_CO2             |  full lifecycle CO2 emission factor for generator cluster i (kgCO2/MMBtu)                                                                                 |
|     m.FOC                |  fixed operating cost of generator cluster i ($/MW)                                                                                                       |
|     m.VOC                |  variable O&M cost of generator cluster i ($/MWh)                                                                                                         |
|     m.CCm                |  capital cost multiplier of generator cluster i (unitless)                                                                                                |
|     m.DIC                |  discounted investment cost of generator cluster i in year t ($/MW)                                                                                       |
|     m.TIC                |  investment cost of tranmission line l ($)                                                                                                                |
|     m.LEC                |  life extension cost for generator cluster i (fraction of the investment cost of corresponding new generator)                                             |
|     m.PEN                |  penalty for not meeting renewable energy quota target during year t ($/MWh)                                                                              |
|     m.PENc               |  penalty for curtailment during year t ($/MWh)                                                                                                            |
|     m.tx\_CO2             |  carbon tax in year t ($/kg CO2)                                                                                                                          |
|     m.susceptance        |  susceptance of transmission line l [Siemenns]                                                                                                            |
|     m.line\_capacity      | capacity of transmission line l (MW)                                                                                                                      |
|     m.RES\_min            |  minimum renewable energy production requirement during year t (fraction of annual energy demand)                                                         |
|     m.hs                 |  duration of sub-period s (hours)                                                                                                                         |
|     m.ir                 |  interest rate                                                                                                                                            |
|     m.storage\_inv\_cost   |  investment cost of storage unit of type j in year t [$/MW]                                                                                               |
|     m.P\_min\_charge       |  min power storage charge for unit j [MW]                                                                                                                 |
|     m.P\_max\_charge       |  max power storage charge for unit j [MW]                                                                                                                 |
|     m.P\_min\_discharge    |  min power storage discharge for unit j [MW]                                                                                                              |
|     m.P\_max\_discharge    |  max power storage discharge for unit j [MW]                                                                                                              |
|     m.min\_storage\_cap    |  min storage capacity for unit j [MWh]                                                                                                                    |
|     m.max\_storage\_cap    |  max storage capacity for unit j [MWh]                                                                                                                    |
|     m.eff\_rate\_charge    |  efficiency rate to charge energy in storage unit j                                                                                                       |
|     m.eff\_rate\_discharge |  efficiency rate to discharge energy in storage unit j                                                                                                    |
|     m.storage\_lifetime   |  storage lifetime (years)                                                                                                                                 |
<h1>Installation</h1>
CPLEX has to be installed to run the Bender algorithm. Installation instructions can be found [here](https://or.stackexchange.com/questions/4366/downloading-and-setting-up-cplex-for-pyomo)

The required python package can be found in requirements.txt. To install on linux, type
```
pip install -r requirements.txt
```
<h1>User Interface </h1>
In order to solve with a given algorithm, run the following line of code in run.py

```python
from gtep import *
newinstance = GTEP(repn_day_method="input", time_limit=100000, tee=True, algo="fullspace", clustering_algorithm = "kmeans", num_repn_days=15, time_horizon=5, formulation="improved")
newinstance.solve_model()
newinstance.write_gtep_results()
```
The options are shown in config_options.py