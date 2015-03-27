'''
Created on 24 Feb 2015

@author: oche
'''
import os
import sys
import time

from pymediainfo import MediaInfo

import database.vEQ_database as DB
import processmonitor.processMonitor as procmon
import videoInput.vlc_localplayback as vlc


if __name__ == '__main__':
    vEQdb = DB.vEQ_database()
    vEQdb.initDB()
    timestamp = time.time()

    proc = procmon.get_processor()
    os_info = procmon.get_os()

    values = [timestamp,os_info,proc]
    
#     write system information to database
    vEQdb.insertIntoSysInfoTable(values)
    
    if sys.argv[1:] and sys.argv[1] not in ('-h', '--help'):
#         write to vid info db
        movie = os.path.expanduser(sys.argv[1])
        if not os.access(movie, os.R_OK):
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
         video =values = [timestamp INT, name TEXT, specs TEXT, codec TEXT, width TEXT, height TEXT
        """
        video_values = [timestamp,movie,movie_data,movie_codec,movie_width,movie_height] 
        video_index = vEQdb.insertIntoVideoInfoTable(video_values)
        
        vlcPlayback = vlc.VLCLocalPlayback(movie,vEQdb)
        vlcPlayback.play()    
    else:
        print('Usage: %s <movie_filename>' % sys.argv[0])
 # Cleanup