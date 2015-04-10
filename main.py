'''
Created on 24 Feb 2015

@author: oche
'''
import os
import sys
import time
import logging

from pymediainfo import MediaInfo

import database.vEQ_database as DB
import processmonitor.processMonitor as procmon
import videoInput.veqplayback as vlc
from powermonitor.voltcraftmeter import VoltcraftMeter

logging.getLogger().setLevel(logging.DEBUG)
logging.info("Started VEQ_Benchmark")

   
if __name__ == '__main__':

    vlc_args = "--video-title-show --video-title-timeout 10 --sub-source marq --sub-filter marq --verbose -1"
    
    meter = VoltcraftMeter()
    
    if meter.initDevice() is None:
        sys.stderr.write("device wasn't opened") #some kind of polymoprphism is needed here so that meter can be any type of device
    
    vEQdb = DB.vEQ_database()
#     vEQdb.clearDB()
#     sys.exit()
    vEQdb.initDB()
    
    timestamp = time.time()
    cpu = procmon.get_processor()
    os_info = procmon.get_os()
    gpu = procmon.get_gpu()
    specs =procmon.get_specs()
    
    values = [timestamp,os_info,cpu, gpu,specs]
    
#     write system information to database
    vEQdb.insertIntoSysInfoTable(values)
    
    if sys.argv[1:] and sys.argv[1] not in ('-h', '--help'):
#         write to vid info db
        
        movie = os.path.expanduser(sys.argv[1])
        if ("http" or "www") not in movie and not (os.access(movie, os.R_OK)):
            print('Error: %s file not readable' % movie)
            sys.exit(1)
   
#         we might be able to gety some of this info form vlc herself although mediainfo tends to have much more info
        try:    
            movie_info = MediaInfo.parse(movie)
            movie_data = movie_info.to_json()
            for track in movie_info.tracks:
                if track.track_type == 'Video':
                    movie_codec = track.codec
                    movie_height = track.height
                    movie_width = track.width
        except:
            error = sys.exc_info()
            print "Unexpected error:", error
            movie_data = str(error)
            movie_codec, movie_height, movie_width = "Null",0,0

#       Write info to videoinfo database
        """
         values = [timestamp INT, name TEXT, specs TEXT, codec TEXT, width TEXT, height TEXT ]
        """
        video_values = [timestamp,movie,movie_data,movie_codec,movie_width,movie_height] 
        video_index = vEQdb.insertIntoVideoInfoTable(video_values)
        
        vlcPlayback = vlc.VEQPlayback(movie,vEQdb,vlc_args,meter)
        vlcPlayback.play()    
    else:
        print('Usage: %s <movie_filename>' % sys.argv[0])
 # Cleanup