'''
Created on 24 Feb 2015

@author: oche
'''
import os
import sys
import time

import database.vEQ_database as DB
import vEQ_benchmark.processmonitor.processMonitor as procmon
from vEQ_benchmark.pymediainfo import MediaInfo
import vEQ_benchmark.videoInput.vlc_localplayback as vlc


if __name__ == '__main__':
    vEQdb = DB.vEQ_database()
    timestamp = time.time()

    proc = procmon.get_processor()
    os_info = procmon.get_os()

    values = [timestamp,os_info,proc]
    
#     write system information to database
    vEQdb.insertIntoSysInfoTable(values)
    
    if sys.argv[1:] and sys.argv[1] not in ('-h', '--help'):
#         write to vid info db
        movie = os.path.expanduser(sys.argv[1])
        print movie
        if not os.access(movie, os.R_OK):
            print('Error: %s file not readable' % movie)
            sys.exit(1)
            
        movie_info = MediaInfo.parse(movie)
        movie_data = movie_info.to_json()
        
        print movie_data
        
        for track in movie_info.tracks:
            if track.track_type == 'Video':
                movie_codec = track.codec
                movie_height = track.height
                movie_width = track.width
        
#         write info to videoinfo database
        """
         video =values = [timestamp INT, name TEXT, specs TEXT, codec TEXT, width TEXT, height TEXT
        """
        video_values = [timestamp,movie,movie_data,movie_codec,movie_width,movie_height] 
        video_index = vEQdb.insertIntoVideoInfoTable(video_values)
        
        vlcPlayback = vlc.VLCLocalPlayback(movie,vEQdb)
        vlcPlayback.play()    
    else:
        print('Usage: %s <movie_filename>' % sys.argv[0])
 # Cleanup