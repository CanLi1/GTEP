using TimeSeriesClustering, CSV, DataFrames
ts_input_data = load_timeseries_data("/home/canl1/work/GETP/NSRDB_wind/for_cluster", T=24, years=[2012])
for t=4:12
	clust_res = run_clust(ts_input_data;method="kmeans",n_clust=t)
	ts_clust_data = clust_res.clust_data
	for (k,v) in ts_clust_data.data
		a = DataFrame(hcat(collect(1:24),v))
		if !isdir(string(t,"days"))
			mkdir(string(t,"days"))
		end
		CSV.write(string(t,"days/", k, ".csv"), a)
	end
end