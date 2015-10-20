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
        self.args = [cmd , workload]
        self.db = db
        self.meter = meter
        self.duration = None
        self.playstart_time = 0
        self.count = 0
        self.polling_interval = 1
        self.proc = None
        
        ENV_DICT = os.environ
        logging.basicConfig( 
                            format = '[genericPlayback] %(levelname)-7.7s %(message)s'
                            )

        logging.debug("Path: " + ENV_DICT["PATH"])  
#         "add expected location for known locations of"
    
    
    def monitorProcess(self,px=None,duration=None):
        '''
        Loop to monitor a process
        '''
        while True:
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
            
            if sys.platform.startswith("darwin"):
            #            Theres no way to capture this  on bsd unix apparently #
                io_read = -1
                io_write = -1
            else:
                io_read = px.io_counters().read_bytes
                io_write = px.io_counters().write_bytes
            
            if self.meter is not None:
                power_val = self.meter.getReading()
                logging.debug("Power: " +  str(power_val))
                power_v = float(power_val)
            else:
                power_val = -1
                power_v = -1
            
            sent_now = psutil.net_io_counters().bytes_sent
            recv_now = psutil.net_io_counters().bytes_recv
                
            marq_str = str.format("CPU: %3.1f%% MEM: %3.1f%% POWR: %3.1fW" % (cpu_val,mempercent_val,power_val)) #need to escape %% twice
            logging.info(marq_str)
            
            values = [timestamp, cpu_val, mempercent_val, rss, sent_now, recv_now, io_read, io_write, sys_index_FK, video_index_FK]
            powers = [timestamp,power_v,sys_index_FK, video_index_FK] 
            self.db.insertIntoReadingsTable(values)
            self.db.insertIntoPowerTable(powers)
             
            self.count+=1
            now = time.time()
            elapsed = now - self.playstart_time 
            
            if duration and  elapsed  >= duration:
                break
             
            # wait for the time in milliseconds left to complete one second or not at all 
            time.sleep(max(0,1-(now-loop_starttime)))

        
    def startPlayback(self,duration=None):
        self.playstart_time = time.time() 
        self.proc = px = psutil.Popen(self.args, stdout=PIPE)
        logging.debug(px.cpu_percent(interval=0.1))
        self.count = 0
        self.monitorProcess(px=self.proc,duration=duration)
        self.stopPlayback()
        return 1
    
    def stopPlayback(self):
        px = self.proc
        if px:
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
        logging.basicConfig( 
                            format = '[genericPlayback] %(levelname)-7.7s %(message)s'
                            )

        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Starting generic playback test")
         
        db = DB.vEQ_database("memory")
        from powermonitor.voltcraftmeter import VoltcraftMeter
        implementedPowerMeters = {
                              "voltcraft": VoltcraftMeter()
                            }
    
        meter = implementedPowerMeters.get('voltcraft',None)
        meter.initDevice()
        
        workload = "/home/system/480p_transformerts.mp4"
        workload = "http://videoserv.cs.st-andrews.ac.uk/dash.js/samples/dash-if-reference-player/index.html"
        youtube_quality = ""
       
       
        cmd= "/Applications/VLC.app/Contents/MacOS/VLC -vv "
        
        
        cmd = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        cmd = r"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        os.system('taskkill /f /im chrome.exe')

        gpb = GenericPlayback(cmd=cmd,workload=workload,db=db,meter=None)
        try:
            gpb.startPlayback(duration=240) 
            print "here"
        except:
            traceback.print_exc()
            gpb.stopPlayback()
#             clean exit
            sys.exit(1)  
 
