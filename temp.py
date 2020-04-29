from multiprocessing import Pool

import time

work = [("A", 5), ("B", 2), ("C", 1), ("D", 3)]


def work_log(data1, data2):
    print(" Process %s waiting %s seconds" % (data1, data2))
    time.sleep(int(data2))
    print(" Process %s Finished." % data1)
    return {data1:data2}


def pool_handler():
	p = Pool(2)
	returnvalue = p.starmap(work_log, work)
	p.close()
	return returnvalue

if __name__ == '__main__':
    returnvalue = pool_handler()