'''
Created on 13 Feb 2015

@author: oche
'''

import time

import database.vEQ_database as vEQdb
import vlc, sys, os, psutil
 #Might work on Linux and Windows
from PyQt4 import QtCore
from PyQt4 import QtGui


class VLCLocalPlayback:
    '''
    Class encapsulating the playback of a video using the VLC Media Player
    '''
    vlcProcess =  psutil.Process()
    qthread = None
       
    def __init__(self,movie,db):
        """
        Params
        movie: the movie to playback
        db: the sqlite db that stats will be written to
        """
        self.player = self.getPlayer(movie) 
        self.db = db
         
    def getPlayer(self,movie):
        '''
         Setup and return a VLC Player 
         @param video: A string location for the movie or video to be played 
        '''
        print 'Creating Player'
        instance = vlc.Instance("--video-title-show --video-title-timeout 10 --sub-source marq --sub-filter marq --verbose -1 ")
          
        try:
            media = instance.media_new(movie)
        except NameError:
            print('NameError: %s (%s vs LibVLC %s)' % (sys.exc_info()[1],
                                                       vlc.__version__,
                                                       vlc.libvlc_get_version()))
            sys.exit(1)
       
        player = instance.media_player_new()
        player.set_media(media)
        
        print 'Player Created'
        return player    
    
    def setupPlayback(self,player):
        '''
         VLC playback on a Darwin Machine (MAC OS X) 
        '''
        vlcApp = QtGui.QApplication(sys.argv)
        vlcWidget = QtGui.QFrame()  
        vlcWidget.setWindowTitle("vEQ_benchmark")  
        vlcWidget.show()
#         vlcWidget.raise_()
        
        if sys.platform == "win32":
            player.set_hwnd(vlcWidget.winId())
        elif sys.platform == "darwin":
            # We have to use 'set_nsobject' since Qt4 on OSX uses Cocoa
            # framework and not the old Carbon.
            player.set_nsobject(vlcWidget.winId())
#             display.vlcMediaPlayer.set_nsobject(win_id)
        else:
            # for Linux using the X Server
            player.set_xwindow(vlcWidget.winId())
            self.has_own_widget = True
         
        player.play()

        
    #   Shift the communication with the UI to another QThread called obJThread
        self.qThread = QtCore.QThread()
        qobjectformainloop = self.QObjectThreadforMainLoop(self,self.db) #create the thread handler thing and move it to the new qhtread created
        qobjectformainloop.moveToThread(self.qThread)
       
#       register that when qobjectformainloop finished signal is emitted call qthread.quit i.e qthrad.quit is the slot for the 'finsighed' signal
        qobjectformainloop.finished.connect(self.qThread.quit)
       
#         register that whenever qthread's started signal is emmitted, call qobjectformainlop longrunning method slot'
        self.qThread.started.connect(qobjectformainloop.longRunning)
    #   this gets called when when the finished signal is emmited by thread or somethingf
#         self.qThread.finished.connect(vlcApp.exit)
        
        self.qThread.start()
        
#         loop to play video bck ?
        self.cleanExit(vlcApp.exec_())
        
    
    def cleanExit(self,int): 
        self.qThread.exit(0)
        sys.exit(int)   
        
    def print_info(self,player):
       """Print information about the media"""
       try:
           media = player.get_media()
           print('State: %s' % player.get_state())
           print('Media: %s' % vlc.bytes_to_str(media.get_mrl()))
           print('Track: %s/%s' % (player.video_get_track(), player.video_get_track_count()))
           print('Current time: %s/%s' % (player.get_time(), media.get_duration()))
           print('Position: %s' % player.get_position())
           print('FPS: %s (%d ms)' % (player.get_fps(), int(1000 // (player.get_fps() or 25))))
           print('Rate: %s' % player.get_rate())
           print('Video size: %s' % str(player.video_get_size(0)))  # num=0
           print('Scale: %s' % player.video_get_scale())
           print('Aspect ratio: %s' % player.video_get_aspect_ratio())
          #print('Window:' % player.get_hwnd()
       except Exception:
           print('Error: %s' % sys.exc_info()[1])
           
    def play(self):
           self.setupPlayback(self.player)
     


    # Subclassing QObject and using moveToThread
    # http://blog.qt.digia.com/blog/2007/07/05/qthreads-no-longer-abstract
    # http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
    class QObjectThreadforMainLoop(QtCore.QObject):
             
        finished = QtCore.pyqtSignal()
                
        def __init__(self,a_playback_obj,db):
            super(VLCLocalPlayback.QObjectThreadforMainLoop, self).__init__()
            self.vlc_playback_object = a_playback_obj
            self.db = db
    
        '''
        This method is the "longrunning" thread that handles data collection  for the videeo playback process in a seperate thread
        '''
        def longRunning(self):
            count = 0
            vlcProcess = self.vlc_playback_object.vlcProcess
#             vlcProcess.cpu_percent(interval=1)
            
            sys_index_FK = self.db.sysinfo_index
            video_index_FK = self.db.videoinfo_index
                
            cpu_val = vlcProcess.cpu_percent()
            mempercent_val = vlcProcess.memory_percent()
            marq_str = str.format("CPU: %3.1f%%%%\nMEM: %3.1f%%%%\n" % (cpu_val,mempercent_val)) #need to escape %% twice
            
            player = self.vlc_playback_object.player
            player.video_set_marquee_int(vlc.VideoMarqueeOption.Enable, 1)
            player.video_set_marquee_int(vlc.VideoMarqueeOption.Size, 50)  # pixels
            player.video_set_marquee_int(vlc.VideoMarqueeOption.Position, vlc.Position.TopRight)
            
            while True:
                count += 1
#               perhaps move this to the process monitor class or nah?
                timestamp = time.time()
                cpu_val = vlcProcess.cpu_percent()
                mempercent_val = vlcProcess.memory_percent()
                mem_val = vlcProcess.memory_info()
                net_sent_val = psutil.net_io_counters().bytes_sent
                net_recv_val = psutil.net_io_counters().bytes_recv
                power_val = 55 #procmon.getSystemPower() or something
                rss =  mem_val.rss
                
#                 cpu_valString = str.format("CPU: %3.1f%%%%\n" % cpu_val)
#                 mem_valString = str.format("MEM: %3.1f%%%%\n" % mempercent_val)
#                 net_valString = str.format("MEM: %3.1f%%%%\n" % net_recv_val)
#                 power_valString = str.format("POWER: %3.1f%%%%W\n" % power_val)              
#                 print sys_index_FK, video_index_FK
                                
                powval = "55 W"
                marq_str = str.format("CPU: %3.1f%%%%\nMEM: %3.1f%%%%\n" % (cpu_val,mempercent_val)) #need to escape %% twice
                player.video_set_marquee_string(vlc.VideoMarqueeOption.Text, marq_str)
#                 print self.db
                print marq_str,
                print vlcProcess.connections(kind='inet')
#                 print mem_val.rss
                print mem_val
#                 print psutil.net_io_counters().bytes_sent
                print psutil.net_io_counters()
                
                values = [timestamp, power_val, cpu_val, mempercent_val, rss, sys_index_FK, video_index_FK]
                self.db.insertIntoReadingsTable(values)
                
                if sys.platform != 'darwin': # Availability: all platforms except OSX
                    print vlcProcess.io_counters()
                    
                time.sleep(1) 
    
#                     print_info(self.player)   
            def emitFinsished():
                print "Object Finisiing"
                self.finished.emit()



if __name__ == '__main__':
    if sys.argv[1:] and sys.argv[1] not in ('-h', '--help'):
        movie = os.path.expanduser(sys.argv[1])
        if not os.access(movie, os.R_OK):
            print('Error: %s file not readable' % movie)
            sys.exit(1)
        vlcPlayback = VLCLocalPlayback(movie)
        vlcPlayback.play()

        
    else:
        print('Usage: %s <movie_filename>' % sys.argv[0])
        


    



