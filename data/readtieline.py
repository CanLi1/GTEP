import sqlite3 as sql
import os
import pandas as pd
curPath = "~/work/GETP"
tielines_df = pd.read_csv(os.path.join(curPath, 'data/tielines.csv'), index_col=0, header=0).iloc[:, :]
tielines = []
#"Far West" "West" are both "West", "South" and "South Central" are both "South"
#"North Central" and "East" are both "Northeast"
areaMap = {'Coast':'Coastal', 'South':'South', 'South Central':'South', 'East':'Northeast', \
			'West':'West', 'Far West':'West', 'North':'Northeast', 'North Central':'Northeast'}

for i in range(tielines_df.shape[0]):
	if areaMap[tielines_df.iat[i,0]] == areaMap[tielines_df.iat[i,1]]:
		continue
	temp_line = {}
	temp_line['Near Area Name'] = areaMap[tielines_df.iat[i,0]]
	temp_line['Far Area Name'] = areaMap[tielines_df.iat[i,1]]
	temp_line['B'] = tielines_df.iat[i,2]
	temp_line['Voltage'] = tielines_df.iat[i,5]
	temp_line['Distance'] = tielines_df.iat[i,7]
	tielines.append(temp_line)
