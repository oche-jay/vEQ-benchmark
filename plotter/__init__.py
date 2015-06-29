'''
Created on 13 Feb 2015

@author: oche
'''
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
import os
import re
import gc
import time

def plot(alist, title=None, filename=None, show=False):
    plt.plot(alist)
    plt.ylabel(title)
    if not os.path.exists("plots"): 
            os.makedirs("plots")
    plt.savefig("plots/" + str(filename) + ".jpg")
      
    if show:
        plt.show()
  
    plt.clf()
    plt.close()
    gc.collect()
    
# TODO change this to use kwargs instead of this long list of stuff
def makeSubPlot(start_time=None, figure_title=None, powers=None, cpus=None, memorys=None, gpus=None, bitrate=None, to_save=True, to_show=True, filename=None ):    
    start_time =  str(start_time)
    
    NUMBER_OF_PLTS = 4
    if gpus:
        NUMBER_OF_PLTS = 5
        
    
    fig = plt.figure()
    
    gs1 = gridspec.GridSpec(NUMBER_OF_PLTS, 1)
    ax_list = [fig.add_subplot(ss) for ss in gs1]

    fig.suptitle(str(figure_title), fontsize=16, fontweight='bold') 
#     fig.subplots_adjust(top=0.85)  
    ''' subplot for power'''
    powfig = ax_list[0]
    powfig.plot(powers)
    powfig.set_title("Instantenous Power Usage")
    powfig.set_ylabel("Power (W)")
#     TODO: plot a line for idle power

    ax_list[0] = powfig
    
    ''' subplot for cpu'''
    cpufig = ax_list[1]
    cpufig.plot(cpus)
    cpufig.set_title("Instantenous CPU Util(%)")
    cpufig.set_ylabel("CPU Util(%)")
  
    
    ''' subplot for mem'''
    memfig = ax_list[2]
    memfig.plot(memorys)
    memfig.set_title("Instantenous Memory Usage(%)")
    memfig.set_ylabel("Mem Util(%)")
 
    
    ''' subplot for bitrate'''
    bitratefig = ax_list[3]
    bitratefig.plot(bitrate)
    bitratefig.set_title("Instantenous Bitrate (Mbps)")
    bitratefig.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, pos: ('%.2f')%(y*1e-6)))
    bitratefig.set_ylabel("Bitrate (Mbps)")
  
    if gpus:
        gpusfig = ax_list[4]
        gpusfig.plot(bitrate)
        gpusfig.set_title("Instantenous GPU Util(%)")
        gpusfig.set_ylabel("Bitrate (Mbps)")
     
    gs1.tight_layout(fig, rect=[0, 0.03, 1, 0.97]) 
        
    if to_save:
        if not filename:
            if not figure_title:
                figure_title = "vEQ-benchmark Generic File"
            figure_title = re.sub(r"[^\w\s]", '', figure_title)
            filename = str(start_time) + "_" + re.sub(r"\s+", '_', figure_title)
        plt.savefig("plots/" + str(filename) + ".jpg") 
        
    if to_show:
        plt.show()
        
    