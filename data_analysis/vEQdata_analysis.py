'''
Created on 15 Jun 2015

@author: ooe
'''

import os, time
from database import vEQ_database as vqdb
import numpy
from util import getConfidence

# TODO: Make this portable or more sensibel
PATH_TO_DB = 'C:/Users/ooe/Documents/git/vEQ_db.sqlite'
# PATH_TO_DB = 'C:/Users/ooe/Documents/linux_vEQ_db.sqlite'

dbpath = os.path.abspath(PATH_TO_DB)
vEQdb = vqdb.vEQ_database(dbpath)

s =time.time()
vEQdb.printTablesinDB()

vcodecs = vEQdb.getDistinctVideoCodecsfromDB()

allsummary = vEQdb.getSummaryfromVeqDB()



vcs = []
powers= []
power_confs = []
cpus = []
cpus_confs = []

for vcodec in vcodecs:
    vc = vcodec[0]
    power_tup = []
    cpu_tup = []
    for each_tuple in allsummary:
        if vc in each_tuple:
            val = each_tuple[1]
            if val is not None:
                power_tup.append(each_tuple[1])
                cpu_tup.append(each_tuple[2])
#         print vc, power_tup
    
    power_np = numpy.array(power_tup)
    print vc, power_np
    cpu_np = numpy.array(cpu_tup)
    
    vcs.append(vc)
    powers.append( power_np[power_np>0].mean())
    power_confs.append( getConfidence(power_np[power_np>0]))
    
    cpus.append(cpu_np.mean())
    cpus_confs.append(getConfidence(cpu_np))
    
import matplotlib.pyplot as plt



ind = numpy.arange(len(vcs))  # the x locations for the groups
width = 0.35       # the width of the bars

fig, ax1 = plt.subplots()
plt.xticks(rotation=90)
rects1 = ax1.bar(ind, powers, color='g', yerr=power_confs)

ax1.set_ylim([60,120])
ax1.set_xlabel('Formats (Youtube)')
ax1.set_ylabel('Power (W)')
ax1.grid(True)

ax2 = ax1.twinx()
ax2.set_ylim([0,200])
ax2.plot(ind+0.35, cpus, color='r')
ax2.errorbar(ind+0.35, cpus, yerr=cpus_confs, color='r', ecolor='r', fmt='o')
ax2.set_ylabel('CPU(%)',color='r')

# You can specify a rotation for the tick labels in degrees or with keywords.

plt.xticks(ind+0.35, vcs)
# plt.setp(ax1[1].xaxis.get_majorticklabels(), )


#Tweak spacing to prevent clipping of tick-labels
plt.subplots_adjust(bottom=0.25)
plt.title('vEQ-benchmark - Summary results (Linux workstation, HD+ videos )\n')

plt.show()       
print time.time()-s