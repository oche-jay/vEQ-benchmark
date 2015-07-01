'''
Created on 15 Jun 2015

@author: ooe
'''

import os, time, datetime
from database import vEQ_database as vqdb
import numpy
from util import getConfidence
import matplotlib.pyplot as plt

# TODO: Make this portable or more sensibel
# PATH_TO_DB = 'C:/Users/ooe/Documents/git/vEQ_db.sqlite'
# PATH_TO_DB = 'C:/Users/ooe/Documents/linux_vEQ_db.sqlite'
PATH_TO_DB = '/Users/oche/Dropbox/vEQ_db.sqlite'
# PATH_TO_DB = '/Users/oche/linux_vEQ_db.sqlite'

dbpath = os.path.abspath(PATH_TO_DB)
vEQdb = vqdb.vEQ_database(dbpath)

s =time.time()
vEQdb.printTablesinDB()

# uncomment for grouping according to youtube format/codc
vcodecs = vEQdb.getDistinctVideoCodecsfromDB()
allsummary = vEQdb.getSummaryfromVeqDB()

# for grouping according to video_height
vheights = vEQdb.getDistinctVideoHeightfromDB()
heightssummary = vEQdb.getSummaryfromVeqDBbyHeight()

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')

def plotPowerandCPU(vcodecs, allsummary, targets=[], **kwargs):
    """
    targets is a list of matches that you want to see in the plot
    """
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%H%M%S')
    xlabel = kwargs.get('xlabel', "Default X Lable")
    title = kwargs.get('title', "Default Title")
    filename = kwargs.get('filename', "")
    
    plt.rcParams['pdf.fonttype']=42 #to fix issue with wierd percentage symbols on Mac OSX
    vcs = []
    powers= []
    power_confs = []
    cpus = []
    cpus_confs = []
    
    for vcodec in vcodecs:
        vc = vcodec[0]
        print vc,
        if not targets or ((targets) and (vc in targets)):
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
            print len(power_np)
            cpu_np = numpy.array(cpu_tup)
            
            vc = vc[0:4]
            vcs.append(vc)
            
            powers.append( power_np[power_np>0].mean())
            power_confs.append( getConfidence(power_np[power_np>0]))
            
            cpus.append(cpu_np.mean())
            cpus_confs.append(getConfidence(cpu_np))
        
    ind = numpy.arange(len(vcs))
    ind = ind+0.5  # the x locations for the groups
    width = 0.35       # the width of the bars
    
    fig, ax1 = plt.subplots()
#     plt.xticks(rotation=90)
    rects1 = ax1.bar(ind, powers, color='g', yerr=power_confs)
    
    ax1.set_ylim([40,120])
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel('Power (W)')
    ax1.grid(True)
    
    ax2 = ax1.twinx()
    ax2.set_ylim([0,200])
    ax2.plot(ind+0.4, cpus, color='r')
    ax2.errorbar(ind+0.4, cpus, yerr=cpus_confs, color='r', ecolor='r', fmt='o')
    ax2.set_ylabel('CPU(%)',color='r')
    
    # You can specify a rotation for the tick labels in degrees or with keywords.
    
    plt.xticks(ind+0.4, vcs)
    # plt.setp(ax1[1].xaxis.get_majorticklabels(), )
    
    
    #Tweak spacing to prevent clipping of tick-labels
    plt.subplots_adjust(bottom=0.25)
    plt.title(title)
    
    if not os.path.exists("plots"): 
        os.makedirs("plots")
        
    plt.savefig("plots/" + st + "-" + filename + ".pdf")
    
#     plt.show()       
    print time.time()-s

itags=["243 - 640x360 (DASH video)", "43 - 640x360", "243 - 640x360 (DASH video)", 
       "136 - 1280x640 (DASH video)", "244 - 854x480 (DASH video)", 
       "135 - 854x480 (DASH video)", "136 - 1280x720 (DASH video", 
       "247 - 1280x720 (DASH video)", "137 - 1920x1080 (DASH video)", 
       "248 - 1920x1080 (DASH video)", "264 - 2560x1440 (DASH video)",
       "272 - 3840x2160 (DASH video)", "266 - 3840x2160 (DASH video)"
       "138 - 3840x2160 (DASH video)", "313 - 3840x2160 (DASH video)" ]

heights = ['320','480','720','1080','1440','2160']

title1 = 'vEQ-benchmark - Summary results\n (Linux workstation, Youtube videos )\n'
title1 = 'vEQ-benchmark - Summary results\n (Windows workstation, Youtube videos )\n'

plat="-windows"
filename1 = "benchmark-results-by-height" + plat
filename2 = "benchmark-results-by-itags" + plat

plotPowerandCPU(vcodecs, allsummary, targets=itags, xlabel='itags (YouTube)', title=title1, filename=filename2)
plotPowerandCPU(vheights, heightssummary, targets=heights, xlabel='Video height (Youtube)', title=title1, filename=filename1)




