'''
Created on 24 Feb 2015

@author: oche
'''
import os
import sys
import time
import logging
import json
import numpy

from util.pymediainfo import MediaInfo

from util import cleanResults
from youtube_dl import YoutubeDL
import database.vEQ_database as DB
import processmonitor.processMonitor as procmon
import videoInput.veqplayback as vlc
from powermonitor.voltcraftmeter import VoltcraftMeter

# TODO: Set logging level from argument
logging.getLogger().setLevel(logging.ERROR)
logging.info("Started VEQ_Benchmark")

verbosity = -1
default_youtube_quality= '266'
# duration to run benchmark or -1 for length of video
bench_duration= 120

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



#         move to a util or stats class
   
if __name__ == '__main__':

    vlc_args = "--video-title-show --video-title-timeout 10 --sub-source marq --sub-filter marq " + "--verbose " + str(verbosity)
    
    meter = VoltcraftMeter() #can inject dependency here i.e power meter or smc or bios or batterty
    
#     TODO: move this elsewherse since meter will not always be there
    if meter.initDevice() is None:
        logging.warning("device wasn't opened") #some kind of polymoprphism is needed here so that meter can be any type of device
    
    vEQdb = DB.vEQ_database()
    vEQdb.initDB()
    
    start_time = time.time()
    cpu = procmon.get_processor()
    os_info = procmon.get_os()
    gpu = procmon.get_gpu()
    specs =procmon.get_specs()
    
    values = [start_time,os_info,cpu, gpu,specs]
    
#     write system information to database
    vEQdb.insertIntoSysInfoTable(values)
    
    if sys.argv[1:] and sys.argv[1] not in ('-h', '--help'):
#         write to vid info db
        movie = os.path.expanduser(sys.argv[1])
        if ("http" or "www") not in movie and not (os.access(movie, os.R_OK)):
            print('Error: %s file not readable' % movie)
            logging.warning('Error: %s file not readable' % movie)
            sys.exit(1)
#         we might be able to gety some of this info form vlc herself although mediainfo tends to have much more info
        try: 
            if ("yout" or "goog") not in movie: #this is weak, use a better regex to capture youtube or googlevideo urls
                logging.debug("Found regular movie")  
                movie_info = MediaInfo.parse(movie)
                movie_data = movie_info.to_json()
                for track in movie_info.tracks:
                    if track.track_type == 'Video':
                        movie_codec = track.codec
                        movie_height = track.height
                        movie_width = track.width
            elif ("yout"  in movie):
                logging.debug("Found Youtube video: Using youtube-dl to get information")
                youtube_dl_opts = {
                         'format' : default_youtube_quality,
                         'quiet' : True
                    }
                with YoutubeDL(youtube_dl_opts) as ydl:
                    try:
                        info_dict = ydl.extract_info(movie, download=False)
                        movie = info_dict['url']
                        movie_data = str(json.dumps(info_dict)) #get json file from youtube dl or lua if possible
                        movie_codec = info_dict['format']
                        movie_height = info_dict['height']
                        movie_width = info_dict['width']
                    except:
                        error = sys.exc_info()
                        logging.error("Unexpected error while retrieve details using Youtube-DL: " + str(error))
                        movie_codec, movie_height, movie_width = "Null",0,0

#                 call youtube-dl for now
                
        except:
            error = sys.exc_info()
            logging.error("Unexpected error: " + str(error))
            movie_data = str(error)
            movie_codec, movie_height, movie_width = "Null",0,0

#       Write info to videoinfo database
        """
         values = [timestamp INT, name TEXT, specs TEXT, codec TEXT, width TEXT, height TEXT ]
        """
        video_values = [start_time,movie,movie_data,movie_codec,movie_width,movie_height] 
        video_index = vEQdb.insertIntoVideoInfoTable(video_values)
        
        vlcPlayback = vlc.VEQPlayback(movie,vEQdb,vlc_args,meter)
        vlcPlayback.play(bench_duration)
        end_time = time.time()
        
        powers = vEQdb.getValuesFromPowerTable(start_time, end_time)
        cpus = vEQdb.getCPUValuesFromPSTable(start_time, end_time)
        memorys = vEQdb.getMemValuesFromPSTable(start_time, end_time)
    
        try:
            p = numpy.array(cleanResults(powers))
            c = numpy.array(cleanResults(cpus))
            m = numpy.array(cleanResults(memorys))
        except:
            print "err"
        
        
#         write this to a summary file .eg json or html or a database
        print "============================================="
        print "vEQ-Summary"
        print "============================================="
        print "Video Name: " 
        print "Benchmark Duration: " + str(end_time - start_time) + "secs"
        print "Video Codec: " + movie_codec
        print "Resolution: " + str(movie_width) + "x" + str(movie_height)
        print "Mean Power: " + str(p.mean()) + "W"
        print "Mean CPU Usage: " + str(c.mean()) + "%"
        print "Mean Memory Usage: " + str(m.mean()) + "%"
        print "Mean Bandwidth: "+ "Not Implemented (TODO)"
        print "Video Filesize " + "Not Implemented (TODO)"
        print "============================================="
        print "System Information"
        print "============================================="
        print "O/S: " + os_info
        print "CPU Name: " + cpu 
        print "GPU Name: " + gpu
        print "Memory Info: " + "Not Yet Implemented"
        print "Active NIC Info: " + "Not Yet Implemented"
        print "============================================="
       
        
          
        
    else:
        print('Usage: %s <movie_filename>' % sys.argv[0])
 # Cleanup