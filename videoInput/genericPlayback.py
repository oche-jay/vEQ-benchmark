'''
Created on 28 Aug 2015

@author: oche
'''

import shlex
import subprocess
import os
import sys
import time
import traceback
from subprocess import PIPE
import psutil
import logging
import database.vEQ_database as DB

class GenericPlayback(object):
    '''   
    '''
    def __init__(self,workload=None,db=None,cmd=None,meter=None):
        '''
        Params
        workload: the workload (video ) to playback
        db: the sqlite db that stats will be written to
        args: args to startup vlc
        meter: a source for power readings - eg killawatt meter, voltcraft meter, acpi, smc, etc etc
        '''
        self.cmd = cmd
        self.workload = workload
        self.args = shlex.split(cmd + " " + workload)
        self.db = db
        self.meter = meter
        self.duration = None
        self.playstart_time = 0
        self.polling_interval = 1
        self.proc = None
        
        
        ENV_DICT = os.environ
        logging.debug("Path: " + ENV_DICT["PATH"])  
#         "add expected location for known locations of"
        
    def startPlayback(self,duration=None):
         ENV_DICT = os.environ
#  	 print ENV_DICT["PATH"]
#	 print self.args
	 self.playstart_time = time.time() 
         logging.debug(self.args)
	 self.proc = px = psutil.Popen(self.args, stdout=PIPE)
         logging.debug(px.cpu_percent(interval=0.1))
         count = 0
	
         while True:
	    # print "count is: " + str(count)
            # if duration and count >= duration:
            #   break
             
             timestamp = loop_starttime = time.time()
             sys_index_FK = self.db.sysinfo_index
             video_index_FK = self.db.videoinfo_index   
             
             cpu_val = px.cpu_percent()
             mempercent_val = px.memory_percent()
             mem_val = px.memory_info()
             rss =  mem_val.rss
             
	     for proc in px.children(recursive=True):
             	cpu_val += proc.cpu_percent()
                mempercent_val += proc.memory_percent()
                rss +=  mem_val.rss
		

             print "cpu " + str(cpu_val)
             print "mem " + str(mempercent_val)
             marq_str = str.format("CPU: %3.1f%%%%\nMEM: %3.1f%%%%\n" % (cpu_val,mempercent_val)) #need to escape %% twice
           
             
             if sys.platform.startswith("darwin"):
#            Theres no way to capture this  on bsd unix apparently #
                io_read = -1
                io_write = -1
             else:
                io_read = px.io_counters().read_bytes
                io_write = px.io_counters().write_bytes
  
             if self.meter is not None:
                power_val = self.meter.getReading()
                logging.debug("Got power measurement: " +  str(power_val))
                power_v = float(power_val)
             else:
                power_val = -1
                power_v = -1
                
             marq_str = str.format("CPU: %3.1f%%%%\nMEM: %3.1f%%%%\nPOWR: %3.1fW\n" % (cpu_val,mempercent_val,power_val)) #need to escape %% twice


             sent_now = psutil.net_io_counters().bytes_sent
             recv_now = psutil.net_io_counters().bytes_recv
       
             values = [timestamp, cpu_val, mempercent_val, rss, sent_now, recv_now, io_read, io_write, sys_index_FK, video_index_FK]
             powers = [timestamp,power_v,sys_index_FK, video_index_FK] 
             self.db.insertIntoReadingsTable(values)
             self.db.insertIntoPowerTable(powers)
             
             count+=1
	     now = time.time()
	     elapsed = now - self.playstart_time 
	     if duration and  elapsed  >= duration:
		break 
             
	     # wait for the time left to complete one second, 
             # if it's a negative number, it means the loop took 
	     # longer than 1 second to complete. 
	     # In this case no need to wait at all
	     time.sleep(max(0,1-(now-loop_starttime)))

         self.stopPlayback()
         return 1
    
    
    def stopPlayback(self):
        px = self.proc
        for proc in px.children(recursive=True):
            proc.kill()
        px.kill()
        

if __name__ == '__main__':
        #     http://blog.endpoint.com/2015/01/getting-realtime-output-using-python.html
        '''
        Calling Popen with universal_newlines=True because tiny_ssim 
        ouputs each line with ^M newline character - which maybe makes sense only
        on Windows or something, 
        In any case, this causes problems if not set
        '''
        workload = "/home/system/480p_transformerts.mp4"
        youtube_quality = ""
        args = ["/usr/bin/omxplayer", workload]
        db = DB.vEQ_database("memory")
        cmd= "/Applications/VLC.app/Contents/MacOS/VLC -vv "  + workload
        args = shlex.split(cmd)
        print args
        gpb = GenericPlayback(args=args,db=db)
        try:
            gpb.startPlayback(20) 
            print "here"
        except:
            traceback.print_exc()
            gpb.stopPlayback()
#             clean exit
            sys.exit(1)  
 
