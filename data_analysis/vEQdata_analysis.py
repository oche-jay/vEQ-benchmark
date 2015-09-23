'''
Created on 15 Jun 2015

@author: ooe
'''

import os, time, datetime
import traceback
from database import vEQ_database as vqdb
import numpy
from util import getConfidence
import logging
import matplotlib.pyplot as plt


logging.getLogger().setLevel(logging.DEBUG)
PATH_TO_DB = '/Users/oche/vEQ-benhmark_i5/vEQ-benchmark/vEQ_db.sqlite'
PATH_TO_DB = '/Users/oche/vEQ-benhmark_PI/vEQ-benchmark/vEQ_db.sqlite'
# PATH_TO_DB = 'C:/Users/ooe/Documents/linux_vEQ_db.sqlite'
dbpath = os.path.abspath(PATH_TO_DB)
vEQdb = vqdb.vEQ_database(dbpath)
s =time.time()


def getMatchListFromTuple(movieList, tupleList, indexToRetrieve=1):
    '''
    Util function to get you the matching index for a list of titles
    '''
    matchingValues=[]
    for title in movieList:
            
        value = 0
        for x in tupleList:
        
            if title in x[0]:
                value = x[indexToRetrieve]
#                 matchingValues.append(value)
                break #go to next title
        matchingValues.append(value)  
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
        for rect in rects:
            height = rect.get_height()
            ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                    ha='center', va='bottom')
#     
#     autolabel(rects1)
#     autolabel(rects2)
    plt.gcf().tight_layout()
    plt.savefig("/Users/oche/Dropbox/Documents/Papers/ism2015/figures/benchmark-results-by-title-HD.eps")
    plt.show()

def processPowerandCPUdata(x_values, summary_by, targets):
    vcs = []
    powers= []
    power_confs = []
    cpus = []
    cpus_confs = []
    
    targets_isNumerical = False
    
    logging.debug("targets=%s" % targets)
    d = {}
    
    if targets:
        try:
            targets = map(int, targets) 
#             trying to group target heights to accommodate intemediary heights
            targets_isNumerical = True
            logging.debug("targets is numerical")
        except:
            print "not an numerical array"
            traceback.print_exc()
            pass
        finally:
#             create a dict for grouped values
             d = {vc : {"cpu": [],"pow":[]} for vc in targets}

    else:
        d = {vc : {"cpu": [],"pow":[]} for vc in (x[0] for x in x_values)}

    """ideally, xvalues is a summary of all distinct heights or codecs in the database (sorted)"""
    for value in x_values:
        vc = str(value[0])
        if (vc == ("-1" or None or "NULL" or -1) ):
            logging.warn("found %s for height - continue" % vc)
            continue
        oldvc = vc
        if targets_isNumerical:
            """
            For numerical targets (values for the x axis), i.e. a list of numbers for heights, approximate the height of a video e.g 286 from the databse
            to a standard video height e.g. 240. It is better to do this via a query than to change the data from the database.
            Especially, when its time to do regression analyses/
            Note that targets may not always be numerical e.g a list of codecs or itags to plot on the xaxs
            """
#                 http://stackoverflow.com/questions/12141150/from-list-of-integers-get-number-closest-to-a-given-val
            vc  = min(targets, key=lambda x : abs(x-int(vc)   ))
            logging.info("old value, new value:%s, %s" % (oldvc, vc) )
            
        print summary_by
        for each_tuple in summary_by:
            logging.debug(each_tuple)
#             this code isnt ideal as it has (O(n x m) running time, where n is the length of the returned values )
#             it could be slighlty less, even though it wont be ideal either, where n reduces for every iteration
            seen = False
            if str(oldvc) in str(each_tuple):
                d[vc]['pow'].append(each_tuple[1])
                d[vc]['cpu'].append(each_tuple[2])
            else:
                if seen: 
                    break
                else:
                    continue
                
        if targets:
            vcs = targets
        else:
            vcs = (x for x[0] in x_values )

    for vc in vcs:
         power_tup=d[vc]['pow']
         cpu_tup= d[vc]['cpu']
         power_np = numpy.array(power_tup)
         cpu_np = numpy.array(cpu_tup)   
#         vc = str(vc)[0:4]
#         vcs.append(vc)
         mp = power_np[power_np>0].mean()
         powers.append(mp)
         power_confs.append(getConfidence(power_np[power_np>0]))
         cpus.append(cpu_np.mean())
         cpus_confs.append(getConfidence(cpu_np))  
    
    return vcs, powers, power_confs, cpus, cpus_confs
         
         
def plotPowerandCPU(x_values, summary_by, targets=[], **kwargs):
    """
        X_values is a list or tuple of distinct values in the zeroth column for the x axis
        targets is a list of matches for VALUES that you want to see in the plot, if not specified everything will be shown
    """
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%H%M%S')
    xlabel = kwargs.get('xlabel', "Default X Lable")
    title = kwargs.get('title', "Default Title")
    filename = kwargs.get('filename', "")
    idle_power = kwargs.get('idle_power', 2.6)

    plt.rcParams['pdf.fonttype']=42 #to fix issue with wierd percentage symbols on Mac OSX
    
    vcs = []
    powers= []
    power_confs = []
    cpus = []
    cpus_confs = []
    
#     print summary_by
    vcs, powers, power_confs, cpus, cpus_confs =  processPowerandCPUdata(x_values, summary_by, targets)
    
    ind = numpy.arange(len(vcs))
    ind = ind+0.5  # the x locations for the groups
    width = 0.35   # the width of the bars
    
    fig, ax1 = plt.subplots()
#     plt.xticks(rotation=90
    rects1 = ax1.bar(ind, powers, color='g', yerr=power_confs)
#     ax1.set_ylim([40,120])
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(r'System Power $- P_a$ (W)' )
    ax1.grid(True)
    
    ax1.axhline(idle_power, color='blue', linewidth=2)
    
    ax2 = ax1.twinx()
    ax2.set_ylim([0,20])
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
        
    plt.savefig(filename)
    
    plt.show()       
    print time.time()-s
        
def plotBW(x_values, summary_by_codec, targets=[], **kwargs):
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
       
        if not targets or ((targets) and (vc in targets)):
            power_tup = []
            cpu_tup = []
            for each_tuple in summary_by_codec:
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
#         h = 1080
        vals = vEQdb.getQuerybyNameandHeight(title, h)
#         logging.debug("Title: %s, Value %s "  % (title, vals))
        if vals:
            p = zip(*vals)[2]
#             print p
            np_ar = numpy.array(p)
            np_ar = np_ar[np_ar>0]
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

# heights = ['320','480','720','1080','1440','2160']
# heights = ['240','360','480','720','1080', '1440', '2160']
heights = ['240','360','480','720','1080']

title1 = 'vEQ-benchmark - Summary results\n (Linux workstation, YouTube videos )\n'
title1 = 'vEQ-benchmark - Summary results\n (Windows workstation, YouTube videos )\n'

plat="-windows"
filename1 = "benchmark-results-by-height" + plat
filename2 = "benchmark-results-by-itags" + plat 

vcodecs = vEQdb.getDistinctVideoCodecsfromDB()
summary_by_codec = vEQdb.getSummaryfromVeqDB()

vheights = vEQdb.getDistinctVideoHeightfromDB(min_height=0)
values_by_height = vEQdb.getSummaryfromVeqDBbyHeight(min_cpu=2,min_power=1,min_height=0)
vtitles = vEQdb.getDistinctColumnfromDB("video_name")

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')

plotPowerandCPU(vheights, values_by_height, targets=heights, xlabel='Video height (Youtube)', title='System Power usage by rPI2' , idle_power=2.5, filename="raspeberyPI.png")


# xvalues = vEQdb.getDistinctColumnfromDBwithHeightFilter("video_name", height_filter=720)
# for v in xvalues:
#     print v
# print
# 
# x2values =  vEQdb.getDistinctColumnfromDBwithHeightFilter("video_name", height_filter=1080)
# for v in x2values:
#     print v
# print
# 
# x3values =  vEQdb.getDistinctColumnfromDBwithHeightFilter("video_name", height_filter=2160)
# 
# for v in x3values:
#     print v
# print
# 
# movies_720 = zip(*xvalues)[0]
# powers_720 = list(zip(*xvalues)[1])
# cpus_720 =  list(zip(*xvalues)[2])
# 
# cpus_1080=[]
# powers_2160=[]
# cpus_2160=[]
# 
# powers_1080 = getMatchListFromTuple(movies_720, x2values, 1)
# powers_2160 = getMatchListFromTuple(movies_720, x3values, 1)
# 
# cpus_1080 = getMatchListFromTuple(movies_720, x2values, 2)
# cpus_2160 = getMatchListFromTuple(movies_720, x3values, 2)
#     
# movie_labels = [item[0:16] for item in movies_720]
# 
# power720errs = getConfbyTitleandHeightAbeg(movies_720, 720)
# power1080errs = getConfbyTitleandHeightAbeg(movies_720, 1080)
# power2160errs = getConfbyTitleandHeightAbeg(movies_720, 2160)

# print movie_labels
# print powers_720
# print powers_1080
# print powers_2160


# print power720errs, power1080errs, power1080errs
# plotPowerandCPU(vcodecs, summary_by_codec, targets=itags, xlabel='itags (YouTube)', title=title1, filename=filename2) 
# plotPowerandCPU(vcodecs, summary_by_codec, targets=heights, xlabel='heights (YouTube)', title=title1, filename=filename2)

# print "vheight"
# for v in vheights: 
#     print "vheight: " + str(v)
    
# plotPowerandCPU(vheights, summary_by_heights, targets=heights, xlabel='Video height (Youtube)', title="Mean Bitrate for Youtube Videos", filename="kk.png")

# plotPowerandCPU(vtitles, summary_by_codec)

# plotMultiplePowerBarsForTitle(x0=powers_720, x0_errs=power720errs, x1=powers_1080, x1_errs=power1080errs, x2_errs=power2160errs, x2=powers_2160, xlabel=movie_labels)

