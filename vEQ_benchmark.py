'''
Created on 24 Feb 2015

@author: oche
'''
from __future__ import unicode_literals
from __future__ import division

import argparse
import os
import sys
import time
import re
import logging
import json
import numpy
from plotter import makeSubPlot
from os.path import expanduser
from util import validURLMatch, validYoutubeURLMatch

from decimal import *
getcontext().prec = 3


try:
    from pymediainfo import MediaInfo
except:
    from util.pymediainfo import MediaInfo
        
# //add youtube-dl to the python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)) , "youtube-dl"))

from util import cleanResults
from util import getMean
from youtube_dl import YoutubeDL
import database.vEQ_database as DB
import processmonitor.processMonitor as procmon
from powermonitor.voltcraftmeter import VoltcraftMeter

# TODO: Set logging level from argument

def makeDefaultDBFolder():
    home = expanduser("~")
    print home
    video_download_folder = os.path.join(home, "vEQ-benchmark")
    if not os.path.exists(video_download_folder):
        os.makedirs(video_download_folder)
    return video_download_folder

vlc_verbosity = -1
default_youtube_quality= 'bestvideo'
benchmark_duration = 20#or -1 for length of video
meter = None

default_folder= makeDefaultDBFolder()
default_database = os.path.join( default_folder, "vEQ_db.sqlite")

logging.getLogger().setLevel(logging.DEBUG)

def main(argv=None):
    parser = argparse.ArgumentParser(description="vEQ-benchmark: A Benchmarking and Measurement Tool for Video")
    parser.add_argument("video" , metavar="VIDEO", help="A local file or URL(Youtube, Vimeo etc.) for the video to be benchmarked")
    parser.add_argument("-y", "--youtube-format", metavar="format", dest="youtube_quality", default=default_youtube_quality, help="For Youtube videos, a value that corressponds to the quality level see youtube-dl for details")
    parser.add_argument("-m", "--power-meter", metavar="meter", dest="meter", default='voltcraft',   help="The meter to use for power measurement TODO: Expand this")
    parser.add_argument("-d", "--duration", metavar="Duration", dest="benchmark_duration", default=60, type=int, help="The length of time in seconds for the benchmark to run.")
    parser.add_argument("-D", "--Database-location", dest="db_loc", metavar ="location for database file or \'memory\'", help = "A absolute location for storing the database file ")
    parser.add_argument("-P", "--plot", dest="to_plot", action='store_true', help="Flag to set if this session should be plotted")
    parser.add_argument("-S", "--show", dest="to_show", action='store_true', help="Flag to set if the plot of this should be displayed on the screen after a session is completed")
    parser.add_argument("-p", "--player", metavar="player", dest="system_player", default="libvlc", help="The Player to use to playback video - default is VLC MediaPlayer")
    parser.add_argument("--hwdecode", dest="hw_decode", action='store_true', help="VLC Specific, turn hardware decoding on")

#     TODO: implement dynamic power metering VoltcraftMeter
    args = parser.parse_args()    
    video = args.video
    benchmark_duration = args.benchmark_duration
    youtube_quality =args.youtube_quality
    db_loc = args.db_loc
    to_show = args.to_show
    to_plot = args.to_plot
    m = args.meter
    system_player = args.system_player
    hw_decode = args.hw_decode
    
    
    video_title = None
    video_data = None
    video_codec = None
    video_height = None
    video_width = None
    file_size = None
    video_url = None
    online_video = False

    if db_loc is None:
        db_loc = default_database
    
    logging.info("Started VEQ_Benchmark")
    
    #TODO: Extract this from here
    implementedPowerMeters = {
                              "voltcraft": VoltcraftMeter()
                            }
    
    meter = implementedPowerMeters.get(m,None) 
    
#    can inject dependency here i.e power meter or smc or bios or batterty
#    meter_type = parser.parse_args().meter
#    meter = Meter(meter_type)

    if meter is None:
        logging.warning("No power monitoring device found") 
        
    elif meter.initDevice() is None:
        meter = None
        logging.warning("No power monitoring device found") 
    
    vEQdb = DB.vEQ_database(db_loc)
    start_time = time.time()
    
    cpu = procmon.get_processor()
    os_info = procmon.get_os()
    gpu = procmon.get_gpu()
    specs =procmon.get_specs()
    
    values = [start_time,os_info,cpu, gpu,specs]
    sys_info_index = vEQdb.insertIntoSysInfoTable(values)
    
    if not validURLMatch(video) and not (os.access(video, os.R_OK)):
        print('Error: %s file not readable' % video)
        logging.error('Error: %s file not readable' % video)
        sys.exit(1)
     
    try:
        if not validURLMatch(video): 
            logging.debug("Found regular video - using MediaInfo to extract details")  
            video_url = video
            video_info = MediaInfo.parse(video)
            video_data = video_info.to_json()
            for track in video_info.tracks:
                if track.track_type == 'Video':
                    video_title = track.title
                    video_codec = track.codec
                    video_height = track.height
                    video_width = track.width
        elif validURLMatch(video):
            online_video = True
            logging.debug("Found online video: Using youtube-dl to get information")
            if validYoutubeURLMatch(video):
                logging.debug("Found YouTube video: Using Youtube-dl to get information")
                youtube_dl_opts = {
                         'format' : youtube_quality,
                         'quiet' : True
                    }
                with YoutubeDL(youtube_dl_opts) as ydl:
                    try:
                        def getInfoDictValue(value, infodict):
                            try:
                                return infodict.get(value,"N,A")
                            except:
                                string = "Couldn't retrieve value " + str(value) +" from YoutubeDL"
                                logging.error(string)
                                sys.stderr.write(string)
                                if value == 'url':
                                    sys.exit(1)
                                return "N/A"
                                
                        info_dict = ydl.extract_info(video, download=False)
                        video = getInfoDictValue("url", info_dict)
                        video_title = info_dict.get('title',"None")
                        video_data = str(json.dumps(info_dict)) 
                        video_codec = info_dict['format']
                        video_height = info_dict['height']
                        video_width = info_dict['width']
                        file_size = info_dict.get('filesize', "None")
                        video_url = video
                    except:
                        error = sys.exc_info()
                        logging.error("Unexpected error while retrieve details using Youtube-DL: " + str(error))
                        video_codec, video_height, video_width = "Null",-1,-1

            
    except:
        error = sys.exc_info()
        logging.error("Could not retrive video format information: " + str(error))
        video_data = str(error)
        video_codec, video_height, video_width = "Null",-1,-1

    """
     values = [timestamp INT, name TEXT, specs TEXT, codec TEXT, width TEXT, height TEXT ]
    """
    
    video_values = [start_time,video,video_data,video_codec,video_width,video_height] 
    video_index = vEQdb.insertIntoVideoInfoTable(video_values)
    
#==========================================VLC VIDEO SPECIFIC =============== 
    if system_player == "libvlc":
        from videoInput.veqplayback import VLCPlayback
        vlc_args = "--video-title-show --video-title-timeout 10 --sub-source marq --sub-filter marq " + "--verbose " + str(vlc_verbosity)
        	
        if hw_decode:
            vlc_args = vlc_args + "--avcodec-hw=any"

        vEQPlayback = VLCPlayback(video,vEQdb,vlc_args,meter)
    
        logging.debug("Starting Playback with VLC")
    
        vEQPlayback.startPlayback(benchmark_duration)
   
    else:
#         use subprocess to start video player and montioring!
#         GenericPlaybackObject.startPlayback(benchmarkduration)
        from videoInput.genericPlayback import GenericPlayback
        generic_command = "/usr/bin/omxplayer"
        generic_command = '/usr/bin/vlc-wrapper --avcodec-hw=any'
        generic_command = 'start chrome'
        workload =  "../gopro.mp4" #          pass this from cmd line or something       
        genericPlayback =  GenericPlayback(workload=video,db=vEQdb,cmd=generic_command,meter=meter)
        genericPlayback.startPlayback(benchmark_duration)
  
    end_time = time.time()
    total_duration = end_time - start_time
    
    powers = vEQdb.getValuesFromPowerTable(start_time, end_time)
    cpus = vEQdb.getCPUValuesFromPSTable(start_time, end_time)
    memorys = vEQdb.getMemValuesFromPSTable(start_time, end_time)
    reads = vEQdb.getValuesFromPSTable("io_bytesread", start_time, end_time) 
    writes = vEQdb.getValuesFromPSTable("io_byteswrite", start_time, end_time) 
    net_r = vEQdb.getValuesFromPSTable("net_recv", start_time, end_time) 
    
    def getDataRateFromArray(arry):
        data_volume = 0
        try:
            data_volume = arry[-1] - arry[0]
        except IndexError:
            logging.error("Something went wrong with collecting data from array: " + str(arry.__namespace))
        return data_volume
    
    data_transferred = getDataRateFromArray(net_r) 
    data_read_from_io = getDataRateFromArray(reads)
    data_writes_from_io = getDataRateFromArray(writes)

    '''
    http://stackoverflow.com/questions/4029436/subtracting-the-current-and-previous-item-in-a-list 
    '''
    bitrate =  [y - x for x,y in zip(net_r,net_r[1:])]
    io_readrate = [y - x for x,y in zip(reads,reads[1:])]
    io_writerate = [y - x for x,y in zip(writes,writes[1:])]

    p = numpy.array(powers)
    c = numpy.array(cpus)
    m = numpy.array(memorys)
    
#     get rid of zeros and negatives
    p = p[p>0]
    c = c[c>0]
    m = m[m>0]

    
    mean_power = getMean(p)
    mean_cpu =  getMean(c)
    mean_memory = getMean(m)
    
    mean_gpu = -1 
    
    #TODO: IMplement GPU 
    mean_bandwidth = str(Decimal(data_transferred * 8) / Decimal(1000000* total_duration))
    
    mean_io_read = str(Decimal(data_read_from_io * 8) / Decimal(1048576 * total_duration))
    mean_io_write = str(Decimal(data_writes_from_io * 8) / Decimal(1048576 * total_duration))

    video_values = [start_time,video,video_data,video_codec,video_width,video_height] 
    summary_keys = ("video_name" , "video_url", "video_codec", "video_height", "video_width", "mean_power", "mean_cpu", "mean_memory", "mean_gpu" , "mean_bandwidth" ,"data_transferred", "file_size", "sys_info_FK", "video_info_FK")
    summary_values = (video_title, video_url , video_codec, video_height, video_width, mean_power, mean_cpu,
                      mean_memory, mean_gpu , mean_bandwidth ,data_transferred, file_size, sys_info_index, video_index)

    summary_dict = dict(zip(summary_keys, summary_values))
#             print summary_dict
    
    vEQdb.insertIntoVEQSummaryTable(summary_values)
#           write this to a summary file json and a database
    print video_title
    try:
    	video_title = s = re.sub(r"[^\w\s]", '', video_title)
    except:
	video_title = video
	
    print "============================================="
    print "vEQ-Summary"
    print "============================================="
    print "Video Name: " + str(video_title)
    if online_video:
        print "Video URL: " + video
    print "Benchmark Duration: " + str(end_time - start_time) + "secs"
    print "Video Codec: " + str(video_codec)
    print "Width: " + str(video_width)  
    print "Height: " + str(video_height)
    print "Mean Power: " + str(mean_power) + "W"
    print "Mean CPU Usage: " + str(mean_cpu) + "%"
    print "Mean Memory Usage: " + str(mean_memory) + "%"
  
    print "Video Filesize " + "Not Implemented (TODO)"
    if online_video:
        print "Mean Bandwidth: "+ mean_bandwidth + "Mbps"
        print "Video Data Transferred: " + str(float( data_transferred / (1024**2))) + " MB"
    print data_read_from_io
    print "Video Data read from I/O: " + str(float( data_read_from_io / (1024**2))) + " MB"
    print "Video Data written to I/O: " + str(float( data_writes_from_io / (1024**2))) + " MB"
    print "============================================="
    print "System Information"
    print "============================================="
    print "O/S: " + os_info
    print "CPU Name: " + cpu 
    print "GPU Name: " + gpu
    print "Memory Info: " + "Not Yet Implemented"
    print "Disk Info: " + "Not Yet Implemented"
    print "Active NIC Info: " + "Not Yet Implemented"
    print "============================================="

#     to_plot = True
#     to_show = False
#     TODO implemtent GPU monitoring    
#     gpus=None
#     plot_title = str(video_codec) + "- (" + str(video_title) + ")"
#     if True:
# #     if to_plot:
#         makeSubPlot(start_time=start_time, figure_title=plot_title, cpus=cpus, memorys=memorys, bitrate=bitrate, powers=powers, gpus=gpus, to_show=to_show)

#     to_plot = False
    to_show = True
 
#     TODO implemtent GPU monitoring    
    gpus=None
    plot_title = str(video_codec) + "- (" + str(video_title) + ")"
    if to_plot:
        makeSubPlot(start_time=start_time, figure_title=plot_title, cpus=c, memorys=m, bitrate=bitrate, powers=powers, gpus=gpus, to_show=to_show)


if __name__ == '__main__':'['
    main()


    
