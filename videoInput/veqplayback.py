''' 
Created on 13 Feb 2015

@author: oche
'''

import time


import vlc, sys, os, psutil
from PyQt4 import QtCore
from PyQt4 import QtGui

import logging
# from profilehooks import profile

# TODO: Extract a parent class from this class
class  VLCPlayback:
    
    '''
    Class encapsulating the playback of a video using the VLC Media Player
    '''
    process =  psutil.Process()
    monitoring_thread = None
       
    def __init__(self,workload,db,args,meter):
        """
        Params
        workload: the workload (video ) to playback
        db: the sqlite db that stats will be written to
        args: args to startup vlc
        meter: a source for power readings - eg killawatt meter, voltcraft meter, acpi, smc, etc etc
        """
        self.player = self.getPlayer(workload,args) 
        self.db = db
        self.meter = meter
        self.duration = None
        self.resized = False
        self.vlcWidget = None
        self.playstart_time = 0
        self.polling_interval = 1
    
    def end_callback(self, event):
        self.cleanExit(0)
         
    def getPlayer(self,video,args):
        '''
         Setup and return a VLC Player 
         @param video: URL or File location for the video or video to be played 
        '''
#       
#         For darwin, there is an issue with the vlc pluginpath since 2.2 I believe that should be dealt with
#         ideally in code or fixed by Videolan Developers in a future release.
#         Hot fix was to make a symbolic link between 
#          /Applications/VLC.app/Contents/MacOS/lib/vlc/plugins and /Applications/VLC.app/Contents/MacOS/plugins
#          the latter being where the actual plugins are, the former being where VLC thinks they are
        
        if sys.platform.startswith("darwin"):
            logging.debug("Seting VLC_PLUGIN_PATH")
            os.environ["VLC_PLUGIN_PATH"] = "/Applications/VLC.app/Contents/MacOS/plugins"
        instance = vlc.Instance(args)
        
        if instance  is None:
            logging.error("Media Player Instance not created")
            sys.exit(-1)
#       Need to create a MediaListPlayer and add videos to the playlist. This 
#       appears to be the only way to start back Youtube videos.
        try:
            media = instance.media_new(video) 
            media_list = instance.media_list_new([video]) #a list of one video
        except NameError:
            print('NameError: %s (%s vs LibVLC %s)' % (sys.exc_info()[1],
                                                       vlc.__version__,
                                                       vlc.libvlc_get_version()))
            sys.exit(1)
       
        player = instance.media_player_new()
        player.set_media(media)
        
        list_player =  instance.media_list_player_new()
        list_player.set_media_player(player)
        list_player.set_media_list(media_list)
        
        event_manager = player.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.end_callback)
    
        return player    
    
    def setupPlayback(self,player):
        '''
        
        '''
        vlcApp = QtGui.QApplication(sys.argv)
        self.vlcWidget = QtGui.QFrame()
       
        self.vlcWidget.setWindowTitle("vEQ_benchmark")  
#         TODO: set window size here
        self.vlcWidget.show()
        self.vlcWidget.raise_()
        
        if sys.platform == "win32":
            player.set_hwnd(self.vlcWidget.winId())
        elif sys.platform == "darwin":
            # We have to use 'set_nsobject' since Qt4 on OSX uses Cocoa
            # framework and not the old Carbon.
            player.set_nsobject(self.vlcWidget.winId())
#             display.vlcMediaPlayer.set_nsobject(win_id)
        else:
            # for Linux using the X Server
            player.set_xwindow(self.vlcWidget.winId())
            self.has_own_widget = True

    #   Shift the communication with the UI to another QThread called obJThread
        self.qThread = QtCore.QThread()
        qobjectformainloop = self.QObjectThreadforMainLoop(self,self.db,self.meter,self.duration) #create the thread handler thing and move it to the new qhtread created
        qobjectformainloop.moveToThread(self.qThread)
        
#       register that when qobjectformainloop finished signal is emitted call monitoring_thread.quit i.e qthrad.quit is the slot for the 'finsighed' signal
        qobjectformainloop.finished.connect(self.qThread.exit)
#        register that whenever monitoring_thread's started signal is emmitted, call qobjectformainlop longrunning method slot'
        self.qThread.started.connect(qobjectformainloop.longRunning)
    #   this gets called when when the finished signal is emmited by thread or somethingf
        self.qThread.finished.connect(vlcApp.exit)
        player.play()
        self.qThread.start()

        self.playstart_time = time.time()
        
        window_size = player.video_get_size(0)
        if window_size[0] and window_size[1] > 479: 
#             (maximize video above 480p)
            self.vlcWidget.showMaximized()
            self.resized = True
            logging.info("Maxmizing Window")
        elif window_size[0] and window_size[1] > 10: 
            logging.info("Setting window size to: " + str(window_size))
            self.vlcWidget.resize(window_size[0],window_size[1])
            self.resized = True
        elif True: #TODO: try to get the size from elsewhere
            pass

        self.cleanExit(vlcApp.exec_())
        
    
    def cleanExit(self,i): 
        self.qThread.exit(0)
           
        
    def print_info(self,player):
        """Print information about the media"""
        try:
            media = player.get_media()
            print('State: %s' % player.get_state())
            print('Media: %s' % vlc.bytes_to_str(media.get_mrl()))
            print('Position: %s' % player.get_position())
            print('FPS: %s (%d ms)' % (player.get_fps(), int(1000 // (player.get_fps() or 25))))
            print('Rate: %s' % player.get_rate())
            print('Video size: %s' % str(player.video_get_size(0)))  # num=0
            print('Scale: %s' % player.video_get_scale())
            print('Aspect ratio: %s' % player.video_get_aspect_ratio())
            #print('Window:' % player.get_hwnd()
            
        except Exception:
            print('Error: %s' % sys.exc_info()[1])
    
           
    def startPlayback(self,duration=None):
        '''
        Start the action for the duration (start the video) for the duration
        '''
        self.duration = duration
        self.setupPlayback(self.player)
        
    # Subclassing QObject and using moveToThread
    # http://blog.qt.digia.com/blog/2007/07/05/qthreads-no-longer-abstract
    # http://stackoverflow.com/questions/6783194/background-thread-with-monitoring_thread-in-pyqt
    class QObjectThreadforMainLoop(QtCore.QObject):
        finished = QtCore.pyqtSignal()
             
        def __init__(self,a_playback_obj,db,meter,duration):
            super(VLCPlayback.QObjectThreadforMainLoop, self).__init__()
            self.vlc_playback_object = a_playback_obj
            self.db = db
            self.meter = meter
            self.duration = duration
        
#         @profile
        def longRunning(self):
            '''
            This method is the "longrunning" thread that handles data collection  for the video playback process in a seperate thread
            '''
            count = 0
            vlcProcess = self.vlc_playback_object.process
            sys_index_FK = self.db.sysinfo_index
            video_index_FK = self.db.videoinfo_index   
            cpu_val = vlcProcess.cpu_percent()
            mempercent_val = vlcProcess.memory_percent()
            marq_str = str.format("CPU: %3.1f%%%%\nMEM: %3.1f%%%%\n" % (cpu_val,mempercent_val)) #need to escape %% twice
            
            player = self.vlc_playback_object.player
            player.video_set_marquee_int(vlc.VideoMarqueeOption.Enable, 1)
            player.video_set_marquee_int(vlc.VideoMarqueeOption.Size, 50)  # pixels
            player.video_set_marquee_int(vlc.VideoMarqueeOption.Position, vlc.Position.TopRight)
            

            if self.vlc_playback_object.resized is False:
                window_size = player.video_get_size(0)

                if window_size[0] and window_size[1] > 479: 
#                 (maximize video above 480p)
                    self.vlcWidget.showMaximized()
                    self.resized = True
                    logging.info("Maxmizing Window")
                elif window_size[0] and window_size[1] > 10: 
                    logging.info("Setting window size to: " + str(window_size))
                    self.vlcWidget.resize(window_size[0],window_size[1])
                    self.resized = True
           
                    qr =  self.vlc_playback_object.vlcWidget.frameGeometry()
                    cp = QtGui.QDesktopWidget().availableGeometry().center()
                    qr.moveCenter(cp)
                    self.vlc_playback_object.vlcWidget.move(qr.topLeft())
                    print "should move"

            while True:
                count += 1 
                print "goteem"
                #                 try to resize the playback window
                if self.vlc_playback_object.resized is False:
                    window_size = player.video_get_size(0)

                    if window_size[0] and window_size[1] > 479:
                        logging.info("Maximizing window " + str(window_size))
                        self.vlc_playback_object.vlcWidget.showMaximized()
                        self.vlc_playback_object.resized = True
#                         This is crashing on the Mac
                        self.vlc_playback_object.resize = True  
                    elif window_size[0] and window_size[1] > 10:
                        logging.info("Setting window size to: " + str(window_size))
                        self.vlc_playback_object.vlcWidget.resize(window_size[0],window_size[1])
                        self.vlc_playback_object.resized = True
                    
                    if sys.platform.startswith("win"): 
#                         This appears to only work on windows    
                        qr =  self.vlc_playback_object.vlcWidget.frameGeometry()
                        print "qr" + str(qr)
                        cp = QtGui.QDesktopWidget().availableGeometry().center()
                        print "cp" + str(cp)
                        qr.moveCenter(cp)
                        self.vlc_playback_object.vlcWidget.move(qr.topLeft())
                        print "should move"

                timestamp = time.time()
                cpu_val = vlcProcess.cpu_percent()
                mempercent_val = vlcProcess.memory_percent()
                mem_val = vlcProcess.memory_info()
                rss =  mem_val.rss
                if sys.platform.startswith("darwin"):
#               Theres no way to capture this  on bsd unix apparently #
                    io_read = -1
                    io_write = -1
                else:
                    io_read = vlcProcess.io_counters().read_bytes
                    io_write = vlcProcess.io_counters().write_bytes
  
                if self.meter is not None:
                    power_val = self.meter.getReading()
                    logging.debug("Got power measurement: " +  str(power_val))
                    power_v = float(power_val)
                else:
                    power_val = -1
                    power_v = -1
                
                marq_str = str.format("CPU: %3.1f%%%%\nMEM: %3.1f%%%%\nPOWR: %3.1fW\n" % (cpu_val,mempercent_val,power_val)) #need to escape %% twice
                player.video_set_marquee_string(vlc.VideoMarqueeOption.Text, marq_str)
# 
                sent_now = psutil.net_io_counters().bytes_sent
                recv_now = psutil.net_io_counters().bytes_recv
       
                values = [timestamp, cpu_val, mempercent_val, rss, sent_now, recv_now, io_read, io_write, sys_index_FK, video_index_FK]
                powers = [timestamp,power_v,sys_index_FK, video_index_FK] 
                self.db.insertIntoReadingsTable(values)
                self.db.insertIntoPowerTable(powers)
                
                elapsed = timestamp - self.vlc_playback_object.playstart_time
                logging.info("Time elapsed: " + str(elapsed))
                
                if self.duration > 0 and elapsed  >= self.duration:
                    logging.info("Benchmark duration completed...Exiting")
                    self.finished.emit()
                    break
                
                time.sleep(self.vlc_playback_object.polling_interval) #TODO: set this to a polling interval that can be set in args
            
#                     print_info(self.player)   
            def emitFinished():
                logging.debug("Video playback completed...Exiting")
                self.finished.emit()



if __name__ == '__main__':
    if sys.argv[1:] and sys.argv[1] not in ('-h', '--help'):
        video = os.path.expanduser(sys.argv[1])
        if not os.access(video, os.R_OK):
            print('Error: %s file not readable' % video)
            sys.exit(1)
        vlcPlayback = VLCPlayback(video)
        vlcPlayback.startPlayback()
    else:
        print('Usage: %s <movie_filename>' % sys.argv[0])
        


    



