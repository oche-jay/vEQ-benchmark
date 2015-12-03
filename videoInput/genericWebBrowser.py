'''
Created on 19 Oct 2015

@author: ooe
'''
import sys
import time
import logging
from videoInput.genericPlayback import GenericPlayback
from selenium import webdriver
import psutil
import database.vEQ_database as DB

class GenericWebBrowserPlayback(GenericPlayback):
    def __init__(self,workload=None,db=None,cmd=None,meter=None):
        GenericPlayback.__init__(self, workload, db, cmd, meter)
        self.url = "http://videoserv.cs.st-andrews.ac.uk/dash.js/samples/dash-if-reference-player/index.html" 
        self.workload = "http://dash.edgesuite.net/akamai/streamroot/050714/Spring_4Ktest.mpd"
        self.p = PATHSTOCHROMEDRIVER =   {
                                    "darwin": "/usr/local/bin/chromedriver", 
                                    "win32": "../lib/chromedriver.exe", 
                                    "linux": "" 
                                    }
        self.webdriver = None                                    
        self.pathtochromedriver = PATHSTOCHROMEDRIVER.get(sys.platform,"")
        print self.pathtochromedriver
    
    def startBrowser(self,duration):
        self.playstart_time = time.time()
        px = psutil.Process()
       
        self.webdriver = drv = webdriver.Chrome(self.pathtochromedriver)
        drv.get(self.url)
        time.sleep(2)
#         Not so generic methods to playback video on dash 
        inputBar =  drv.find_element_by_tag_name("input")
        inputBar.send_keys(self.workload)
        loadButton = drv.find_element_by_xpath("//button[@ng-click='doLoad()']");
        loadButton.click()
        
        self.monitorProcess(px, duration)
        self.stopPlayback()
  
    def startPlayback(self, duration=None):
        self.startBrowser(duration)
    
    def stopPlayback(self):
        self.webdriver.close()
        
        
    def main(self):
        duration = 100
        self.startBrowser(duration)

logging.getLogger().setLevel(logging.DEBUG)
db = DB.vEQ_database("memory")
from powermonitor.voltcraftmeter import VoltcraftMeter
implementedPowerMeters = {
                              "voltcraft": VoltcraftMeter()
                            }
    
meter = implementedPowerMeters.get('voltcraft',None)
meter.initDevice()
obj = GenericWebBrowserPlayback(db=db,meter=meter)
obj.main()

        