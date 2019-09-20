* Generation and Transmission Expansion model for ERCOT region
* Author: C.L. Lara and I.E. Grossmann
* Last revision: 05/17/2016

********************************************************************************
************************************ Data **************************************
********************************************************************************

*Select between hourly, half-hourly and quarter-hourly information
$include GTEP_hourly
*$include GTEP_hourly_dayofweek
*$include GTEP_half_hourly.gms
*$include GTEP_quarter_hourly.gms
*$include GTEP_hourly_week
*$include GTEP_hourly_week_proportional
*$include GTEP_hourly_3days
*$include GTEP_hourly_4days
*$include GTEP_hourly_5days
*$include GTEP_hourly_11daysyear
*$include GTEP_hourly_10daysyear
*$include GTEP_hourly_9daysyear
*$include GTEP_hourly_8daysyear
*$include GTEP_hourly_7daysyear
*$include GTEP_hourly_6daysyear
*$include GTEP_hourly_5daysyear
*$include GTEP_hourly_3daysyear
*$include GTEP_hourly_2daysyear
*$include GTEP_hourly_1dayyear

*Include general data
$include GTEP_general_data

*Select case scenario:
$include ref_case
*$include case1.gms
*include case2.gms
*$include case3.gms
*$include case4.gms

Execute_unload 'GTEP_data.gdx';
