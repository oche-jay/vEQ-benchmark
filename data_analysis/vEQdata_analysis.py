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

# PATH_TO_DB = 'C:/Users/ooe/Documents/linux_vEQ_db.sqlite'

# PATH_TO_DB = 'C:/Users/ooe/Documents/git/vEQ_db.sqlite'
# PATH_TO_DB = 'C:/Users/ooe/Documents/linux_vEQ_db.sqlite'
PATH_TO_DB = '/Users/oche/Dropbox/vEQ_db.sqlite'
# PATH_TO_DB = '/Users/oche/linux_vEQ_db.sqlite'
# PATH_TO_DB = 'C:/Users/ooe/Documents/git/vEQ_db.sqlite'
# PATH_TO_DB = 'C:/Users/ooe/Documents/linux_vEQ_db.sqlite'


dbpath = os.path.abspath(PATH_TO_DB)
vEQdb = vqdb.vEQ_database(dbpath)
s =time.time()
# vEQdb.printTablesinDB()

def getMatchListFromTuple(movieList, tupleList, indexToRetrieve=1):
    '''
    Util function to get you the matching index for a list of titles
    '''
    matchingValues=[]
    for title in movieList:
        for x in tupleList:
            value = 0
            if title in x[0]:
                pow_value = x[indexToRetrieve]
                break   
        matchingValues.append(pow_value)
    return  matchingValues

def plotMultiplePowerBarsForTitle(x0=None, x0_errs=None, x1=None, x1_errs=None, x2=None, x2_errs=None, **kwargs):
    """
    Plot up to multiple series on a bar chart
    x
    x1
    x3: the 3rd of the series to plot
    
    """
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%H%M%S')
    xlabel = kwargs.get('xlabel', "Default X Lable")
    title = kwargs.get('title', "HD and UHD Power Usage")
    filename = kwargs.get('filename', "")    
    plt.rcParams['pdf.fonttype']=42 #to fix issue with wierd percentage symbols on Mac OSX

    N = len(x0)

    ind = numpy.arange(N)  # the x locations for the groups
    width = 0.25       # the width of the bars

    fig, ax = plt.subplots()
    padding = 0.5 
    rects1 = ax.bar(padding+ind, x0, width, color='g', yerr=x0_errs, ecolor='b')
    rects2 = ax.bar(padding+ind+width, x1, width, color='y', yerr=x1_errs, ecolor='b')
    rects3 = ax.bar(padding+ind+width+width, x2, width, color='b', yerr=x2_errs, ecolor='b')

    ax.set_ylim([40,120])
    ax.set_xticks(padding+ind+width+(width/2))
    ax.set_xticklabels(xlabel, rotation=45, ha='right')
    ax.set_ylabel(r'System Power $- P_a$ (W)' );
    ax.legend( (rects1[0], rects2[0], rects3[0]), ('720p', '1080p', '2160p') )
    ax.grid(True)
    plt.title(title)


    def autolabel(rects):
        # attach some text labels
        for rect in rects:
            height = rect.get_height()
            ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                    ha='center', va='bottom')
#     
#     autolabel(rects1)
#     autolabel(rects2)
    plt.gcf().tight_layout()
    plt.savefig("/Users/oche/Dropbox/Documents/Papers/ism2015/figures/benchmark-results-by-title-HD.eps")
#     plt.show()

def plotPowerandCPU(x_values, allsummary, targets=[], **kwargs):
    """
    values is a list or tuple of distinct values in the zeroth column for the x asis 
    targets is a list of matches for VALUES that you want to see in the plot, if not specified everything will be show
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
    for vcodec in x_values:
        vc = vcodec[0]
        print vc
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
            cpu_np = numpy.array(cpu_tup)
            vc = vc[0:4]
            vcs.append(vc)
            powers.append(power_np[power_np>0].mean())
            power_confs.append(getConfidence(power_np[power_np>0]))
            cpus.append(cpu_np.mean())
            cpus_confs.append(getConfidence(cpu_np))
        
    ind = numpy.arange(len(vcs))
    ind = ind+0.5  # the x locations for the groups
    width = 0.35       # the width of the bars
    
    fig, ax1 = plt.subplots()
#     plt.xticks(rotation=90)
    rects1 = ax1.bar(ind, powers, color='g', yerr=power_confs)
    
#     ax1.set_ylim([40,120])
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel('Bitrate (Mbps)')
    ax1.grid(True)
    
    power_np = numpy.array(power_tup)
    print vc, power_np
    cpu_np = numpy.array(cpu_tup)
    
    plt.xticks(ind+0.4, vcs)
    # plt.setp(ax1[1].xaxis.get_majorticklabels(), )

    #Tweak spacing to prevent clipping of tick-labels
    plt.subplots_adjust(bottom=0.25)
    plt.title(title)
    
    if not os.path.exists("plots"): 
        os.makedirs("plots")
        
    plt.savefig(filename)
    
    plt.show()       
    print time.time()-s
    
def plotBW(x_values, allsummary, targets=[], **kwargs):
    """
    values is a list or tuple of distinct values in the zeroth column for the x asis 
    targets is a list of matches for VALUES that you want to see in the plot, if not specified everything will be show
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
    
    for vcodec in x_values:
        vc = vcodec[0]
        print vc
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
            cpu_np = numpy.array(cpu_tup)
            vc = vc[0:4]
            vcs.append(vc)
            powers.append(power_np[power_np>0].mean())
            power_confs.append(getConfidence(power_np[power_np>0]))
            cpus.append(cpu_np.mean())
            cpus_confs.append(getConfidence(cpu_np))
        
    ind = numpy.arange(len(vcs))
    ind = ind+0.5  # the x locations for the groups
    width = 0.35       # the width of the bars
    
    fig, ax1 = plt.subplots()
#     plt.xticks(rotation=90)
    rects1 = ax1.bar(ind, powers, color='g', yerr=power_confs)
    
#     ax1.set_ylim([40,120])
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel('Bitrate (Mbps)')
    ax1.grid(True)
      
    # You can specify a rotation for the tick labels in degrees or with keywords.
    
    plt.xticks(ind+0.4, vcs)
    # plt.setp(ax1[1].xaxis.get_majorticklabels(), )

    #Tweak spacing to prevent clipping of tick-labels
    plt.subplots_adjust(bottom=0.25)
    plt.title(title)
    
    if not os.path.exists("plots"): 
        os.makedirs("plots")
        
    plt.savefig(filename)
    
    plt.show()       
    print time.time()-s
    
def getConfbyTitleandHeightAbeg(movies_720,h):
    confs = []
    for title in movies_720:
        h = 1080
        vals = vEQdb.getQuerybyNameandHeight(title, h)
        print title, vals
        if vals:
            p = zip(*vals)[2]
            np_ar = numpy.array(p)
            confs.append(getConfidence(np_ar) )
        else: 
           confs.append(0)
    return confs

itags=["243 - 640x360 (DASH video)", "43 - 640x360", "243 - 640x360 (DASH video)", 
       "136 - 1280x640 (DASH video)", "244 - 854x480 (DASH video)", 
       "135 - 854x480 (DASH video)", "136 - 1280x720 (DASH video", 
       "247 - 1280x720 (DASH video)", "137 - 1920x1080 (DASH video)", 
       "248 - 1920x1080 (DASH video)", "264 - 2560x1440 (DASH video)",
       "272 - 3840x2160 (DASH video)", "266 - 3840x2160 (DASH video)"
       "138 - 3840x2160 (DASH video)", "313 - 3840x2160 (DASH video)" ]

heights = ['320','480','720','1080','1440','2160']

title1 = 'vEQ-benchmark - Summary results\n (Linux workstation, YouTube videos )\n'
title1 = 'vEQ-benchmark - Summary results\n (Windows workstation, YouTube videos )\n'

plat="-windows"
filename1 = "benchmark-results-by-height" + plat
filename2 = "benchmark-results-by-itags" + plat 

vcodecs = vEQdb.getDistinctVideoCodecsfromDB()
allsummary = vEQdb.getSummaryfromVeqDB()

vheights = vEQdb.getDistinctVideoHeightfromDB()
heightssummary = vEQdb.getSummaryfromVeqDBbyHeight()

vtitles = vEQdb.getDistinctColumnfromDB("video_name")
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')

xvalues = vEQdb.getDistinctColumnfromDBwithHeightFilter("video_name", height_filter=720)
x2values =  vEQdb.getDistinctColumnfromDBwithHeightFilter("video_name", height_filter=1080)
x3values =  vEQdb.getDistinctColumnfromDBwithHeightFilter("video_name", height_filter=2160)

movies_720 = zip(*xvalues)[0]
powers_720 = list(zip(*xvalues)[1])
cpus_720 =  list(zip(*xvalues)[2])

cpus_1080=[]
powers_2160=[]
cpus_2160=[]

powers_1080 = getMatchListFromTuple(movies_720, x2values, 1)
powers_2160 = getMatchListFromTuple(movies_720, x3values, 1)

cpus_1080 = getMatchListFromTuple(movies_720, x2values, 2)
cpus_2160 = getMatchListFromTuple(movies_720, x3values, 2)


    
movie_labels = [item[0:16] for item in movies_720]

power720errs = getConfbyTitleandHeightAbeg(movies_720, 720)
power1080errs = getConfbyTitleandHeightAbeg(movies_720, 1080)
power2160errs = getConfbyTitleandHeightAbeg(movies_720, 2160)
print power720errs

# plotPowerandCPU(vcodecs, allsummary, targets=itags, xlabel='itags (YouTube)', title=title1, filename=filename2)
# plotPowerandCPU(vcodecs, allsummary, targets=heights, xlabel='itags (YouTube)', title=title1, filename=filename2)

# print "HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n\n\n"
plotPowerandCPU(vheights, heightssummary, targets=heights, xlabel='Video height (Youtube)', title="Mean Bitrate for Youtube Videos", filename="kk.png")
# plotPowerandCPU(vtitles, allsummary)

# plotMultiplePowerBarsForTitle(x0=powers_720, x0_errs=power720errs, x1=powers_1080, x1_errs=power1080errs, x2_errs=power2160errs, x2=powers_2160, xlabel=movie_labels)

