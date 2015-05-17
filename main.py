'''
Created on 24 Feb 2015

@author: oche
'''
import os
import sys
import time
import logging

from util.pymediainfo import MediaInfo
from youtube_dl import YoutubeDL
import json

import database.vEQ_database as DB
import processmonitor.processMonitor as procmon
import videoInput.veqplayback as vlc
from powermonitor.voltcraftmeter import VoltcraftMeter

verbosity = -1
default_youtube_quality= 'bestvideo'
# duration to run benchmark or -1 for length of video
bench_duration= 120  #or -1

#move to a util or stats class

   
if __name__ == '__main__':
    # TODO: Set logging level from argument
    logging.getLogger().setLevel(logging.WARNING)
    logging.info("Started VEQ_Benchmark")

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
        video = os.path.expanduser(sys.argv[1])
        if ("http" or "www") not in video and not (os.access(video, os.R_OK)):
            print('Error: %s file not readable' % video)
            logging.warning('Error: %s file not readable' % video)
            sys.exit(1)
#         we might be able to gety some of this info form vlc herself although mediainfo tends to have much more info
        try: 
            if ("yout" or "goog") not in video: #this is weak, use a better regex to capture youtube or googlevideo urls
                logging.debug("Found regular video")  
                video_info = MediaInfo.parse(video)
                video_data = video_info.to_json()
                for track in video_info.tracks:
                    if track.track_type == 'Video':
                        video_codec = track.codec
                        video_height = track.height
                        video_width = track.width
            elif ("yout"  in video):
                logging.debug("Found Youtube video: Using youtube-dl to get information")
                youtube_dl_opts = {
                         'format' : default_youtube_quality,
                         'quiet' : True
                    }
                with YoutubeDL(youtube_dl_opts) as ydl:
                    try:
                        info_dict = ydl.extract_info(video, download=False)
                        video = info_dict['url']
                        video_data = str(json.dumps(info_dict)) #get json file from youtube dl or lua if possible
                        video_codec = info_dict['format']
                        video_height = info_dict['height']
                        video_width = info_dict['width']
                    except:
                        error = sys.exc_info()
                        logging.error("Unexpected error while retrieve details using Youtube-DL: " + str(error))
#                 call youtube-dl for now
                
        except:
            error = sys.exc_info()
            logging.error("Unexpected error: " + str(error))
            video_data = str(error)
            video_codec, video_height, video_width = "Null",0,0

#       Write info to videoinfo database
        """
         values = [timestamp INT, name TEXT, specs TEXT, codec TEXT, width TEXT, height TEXT ]
        """
        video_values = [start_time,video,video_data,video_codec,video_width,video_height] 
        video_index = vEQdb.insertIntoVideoInfoTable(video_values)
        
        vlcPlayback = vlc.VEQPlayback(video,vEQdb,vlc_args,meter)
        vlcPlayback.play(bench_duration)  
        end_time = time.time()
        powers = vEQdb.getValuesFromPowerTable(start_time, end_time)
        cpus = vEQdb.getCPUValuesFromPSTable(start_time, end_time)
        memorys = vEQdb.getMemValuesFromPSTable(start_time, end_time)
    
        
        import numpy
        p = numpy.asarray(util.cleanResults(powers))
        c = numpy.asarray(util.cleanResults(cpus))
        print p.mean()
        print c.mean()
          
        
    else:
        print('Usage: %s <movie_filename>' % sys.argv[0])
 # Cleanup