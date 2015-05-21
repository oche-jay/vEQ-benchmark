'''
Created on 24 Feb 2015

@author: oche
'''
import argparse
import os
import sys
import time
import logging
import json
import numpy
from decimal import *
getcontext().prec = 3


try:
    from util.pymediainfo import MediaInfo
except:
    from pymediainfo import MediaInfo    

# //add youtube-dl to the python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)) , "youtube-dl"))
from util import cleanResults
from youtube_dl import YoutubeDL
import database.vEQ_database as DB
import processmonitor.processMonitor as procmon
import videoInput.veqplayback as vlc
from powermonitor.voltcraftmeter import VoltcraftMeter
# TODO: Set logging level from argument

online_video = False
verbosity = -1
default_youtube_quality= '137'
benchmark_duration= 30 #or -1 for length of video
meter = None


# Available Formats for Youtube
# format code  extension  resolution note
# # 140          m4a        audio only DASH audio  129k , m4a_dash container, aac  @128k (44100Hz), 3.89MiB
# 171          webm       audio only DASH audio  145k , audio@128k (44100Hz), 3.97MiB
# 141          m4a        audio only DASH audio  255k , m4a_dash container, aac  @256k (44100Hz), 7.72MiB
# 160          mp4        256x144    DASH video  110k , 15fps, video only, 3.13MiB
# 278          webm       256x144    DASH video  117k , webm container, VP9, 15fps, video only, 2.67MiB
# 133          mp4        426x240    DASH video  247k , 30fps, video only, 6.99MiB
# 242          webm       426x240    DASH video  264k , 30fps, video only, 5.99MiB
# 243          webm       640x360    DASH video  493k , 30fps, video only, 11.22MiB
# 134          mp4        640x360    DASH video  648k , 30fps, video only, 13.84MiB
# 244          webm       854x480    DASH video  932k , 30fps, video only, 20.44MiB
# 135          mp4        854x480    DASH video 1189k , 30fps, video only, 26.78MiB
# 247          webm       1280x720   DASH video 1898k , 30fps, video only, 41.76MiB
# 136          mp4        1280x720   DASH video 2368k , 30fps, video only, 52.74MiB
# 248          webm       1920x1080  DASH video 3557k , 30fps, video only, 72.85MiB
# 137          mp4        1920x1080  DASH video 4571k , 30fps, video only, 98.81MiB
# 264          mp4        2560x1440  DASH video 10898k , 30fps, video only, 234.73MiB
# 271          webm       2560x1440  DASH video 15630k , 30fps, video only, 222.74MiB
# 266          mp4        3840x2160  DASH video 22239k , h264, 30fps, video only, 547.67MiB
# 313          webm       3840x2160  DASH video 26253k , VP9, 30fps, video only, 449.06MiB
# 138          mp4        3840x2160  DASH video 26455k , 30fps, video only, 610.05MiB
# 272          webm       3840x2160  DASH video 29628k , 30fps, video only, 533.46MiB
# 17           3gp        176x144    
# 36           3gp        320x240    
# 5            flv        400x240    
# 43           webm       640x360    
# 18           mp4        640x360    
# 22           mp4        1280x720   (best)

def real_main(video):
            if ("http" or "www") not in video and not (os.access(video, os.R_OK)):
                print('Error: %s file not readable' % video)
                logging.error('Error: %s file not readable' % video)
                sys.exit(1)
            try: 
                if ("http" or "www") not in video: 
                    logging.debug("Found regular video")  
                    video_url = video
                    video_info = MediaInfo.parse(video)
                    video_data = video_info.to_json()
                    for track in video_info.tracks:
                        if track.track_type == 'Video':
                            video_title = track.title
                            video_codec = track.codec
                            video_height = track.height
                            video_width = track.width
                elif ("http" or "www" in video):
                    online_video = True
                    logging.debug("Found online video: Using youtube-dl to get information")
                    if "yout" or "goog" in video:
                        logging.debug("Found online video: Using youtube-dl to get information")
                        youtube_dl_opts = {
                                 'format' : default_youtube_quality,
                                 'quiet' : True
                            }
                        with YoutubeDL(youtube_dl_opts) as ydl:
                            try:
                                info_dict = ydl.extract_info(video, download=False)
                                video = info_dict['url']
                                video_title = info_dict['title']
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
                logging.error("Unexpected error: " + str(error))
                video_data = str(error)
                video_codec, video_height, video_width = "Null",-1,-1
    
    #       Write info to videoinfo database
            """
             values = [timestamp INT, name TEXT, specs TEXT, codec TEXT, width TEXT, height TEXT ]
            """
            video_values = [start_time,video,video_data,video_codec,video_width,video_height] 
            video_index = vEQdb.insertIntoVideoInfoTable(video_values)
            
            vlcPlayback = vlc.VEQPlayback(video,vEQdb,vlc_args,meter)
            vlcPlayback.play(benchmark_duration)
        
            end_time = time.time()
          
            real_duration = end_time - start_time
            
            powers = vEQdb.getValuesFromPowerTable(start_time, end_time)
            cpus = vEQdb.getCPUValuesFromPSTable(start_time, end_time)
            memorys = vEQdb.getMemValuesFromPSTable(start_time, end_time)
            net_r = vEQdb.getValuesFromPSTable("net_recv", start_time, end_time) 
            data_transferred = net_r[-1] - net_r[0]
            
#             http://stackoverflow.com/questions/4029436/subtracting-the-current-and-previous-item-in-a-list
# zip concats the items in two list at the same index as a tuple
# so basically we concat the list with a slice of itself starting at index 1, and the use the comprehension to find the fdifference
            bitrate =  [y - x for x,y in zip(net_r,net_r[1:])]
#             print bitrate TODO: use matpolotlip to plot results for bitrate cpu and power
        
            def getmean(numpy_array):
                try:
                    return numpy_array.mean()
                except:
                    logging.error(sys.exc_info()[1])
                    return "N/A"
        
        
            p = numpy.array(powers)
            c = numpy.array(cpus)
            m = numpy.array(memorys)
            
            mean_power = getmean(p)
            mean_cpu =  getmean(c)
            mean_memory = getmean(m)
            mean_gpu = -1 #TODO: IMplement GPU 
            mean_bandwidth = str(Decimal(data_transferred * 8) / Decimal(1000000* real_duration))

            video_values = [start_time,video,video_data,video_codec,video_width,video_height] 
            summary_keys = ("video_name" , "video_url", "video_codec", "video_height", "video_width", "mean_power", "mean_cpu", "mean_memory", "mean_gpu" , "mean_bandwidth" ,"data_transferred", "file_size", "sys_info_FK", "video_info_FK")
            summary_values = (video_title, video_url , video_codec, video_height, video_width, mean_power, mean_cpu,
                              mean_memory, mean_gpu , mean_bandwidth ,data_transferred, file_size, sys_info_index, video_index)
   
            summary_dict = dict(zip(summary_keys, summary_values))
#             print summary_dict
            
            vEQdb.insertIntoVEQSummaryTable(summary_values)
#         write this to a summary file json and a database
            print "============================================="
            print "vEQ-Summary"
            print "============================================="
            print "Video Name: " + video_title
            if online_video:
                print "Video URL: " + video
            print "Benchmark Duration: " + str(end_time - start_time) + "secs"
            print "Video Codec: " + video_codec
            print "Width: " + str(video_width)  
            print "Height: " + str(video_height)
            print "Mean Power: " + str(p.mean()) + "W"
            print "Mean CPU Usage: " + str(c.mean()) + "%"
            print "Mean Memory Usage: " + str(m.mean()) + "%"
          
            print "Video Filesize " + "Not Implemented (TODO)"
            if online_video:
                print "Mean Bandwidth: "+ "Not Implemented (TODO)"
                print "Video Data Transferred " + str(float( data_transferred / (1024**2))) + " MB"
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

   
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="vEQ-benchmark: A Benchmarking and Measurement Tool for Video")
    parser.add_argument("video" , metavar="VIDEO", help="A local file or URL(Youtube, Vimeo etc.) for the video to be benchmarked")
    parser.add_argument("-y" , "--youtube-format", metavar="format", dest="default_youtube_quality", help="For Youtube videos, a value that corressponds to the quality level see youtube-dl for details")
    parser.add_argument("-p" , "--power-meter", metavar="meter", dest="meter", help="The meter to use for power measurement TODO: Expand this")
    parser.add_argument("-d", "--duration", metavar="Duration", dest="benchmark_duration", default=benchmark_duration, type=int, help="The length of time in seconds for the benchmark to run.")
#     
    args = parser.parse_args()
    
    video = args.video
    benchmark_duration = args.benchmark_duration
 
 
    vlc_args = "--video-title-show --video-title-timeout 10 --sub-source marq --sub-filter marq " + "--verbose " + str(verbosity)
    
    logging.getLogger().setLevel(logging.ERROR)

    logging.info("Started VEQ_Benchmark")

#     make voltcraftmeter and any other meters callable somehow
    meter = VoltcraftMeter() #can inject dependency here i.e power meter or smc or bios or batterty
    
#     meter_type = parser.parse_args().meter
#     meter = Meter(meter_type)
#     
    
    if meter is None:
        logging.warning("device wasn't found") 
    elif meter.initDevice()  is None:
        logging.warning("device wasn't found") 
    
    
    vEQdb = DB.vEQ_database()
    vEQdb.initDB()
    
    start_time = time.time()
    cpu = procmon.get_processor()
    os_info = procmon.get_os()
    gpu = procmon.get_gpu()
    specs =procmon.get_specs()
    
    values = [start_time,os_info,cpu, gpu,specs]
    
#     write system information to database
    sys_info_index = vEQdb.insertIntoSysInfoTable(values)
    
#     TODO: Add the functionality to monitor GPUs with nvidia-smi,  intel-gpu-tools and others

#     if sys.argv[1:] and sys.argv[1] not in ('-h', '--help'):
# #         write to vid info db
# #         video = os.path.expanduser(sys.argv[1])
#        
    real_main(video)
            
#     else:
# #         print usage
#         pass
  
    