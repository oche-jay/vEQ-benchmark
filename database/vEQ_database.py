'''
Created on 24 Feb 2015

@author: oche
'''
import sys
import sqlite3 as lite


class vEQ_database(object):
    '''
    Creates or opens an sqlite database for data to be written to
    '''
    
    SYS_INFO_COLS = ("id INTEGER PRIMARY KEY, "
                     "timestamp REAL, "
                     "name TEXT, "
                     "cpu TEXT, "
                     "gpu TEXT, "
                     "specs TEXT ")
    
    VIDEO_INFO_COLS =  ("id INTEGER PRIMARY KEY,"
                        "timestamp REAL, " 
                        "name TEXT, "
                        "specs TEXT, "
                        "codec TEXT, "
                        "width TEXT, "
                        " height TEXT")
                    
    PS_READINGS_COLS = ("id INTEGER PRIMARY KEY,"
                     "timestamp REAL,"
                     "cpu_percent REAL, "
                     "mem_percent REAL, "
                     "resident_set_size INTEGER, "
                     "sys_info_FK INTEGER, "
                     "video_info_FK INTEGER, "
                     "FOREIGN KEY (sys_info_FK) REFERENCES sys_info(id), "
                     "FOREIGN KEY (video_info_FK) REFERENCES video_info(id)" )
    
    POWER_READINGS_COLS = ("id INTEGER PRIMARY KEY,"
                           "timestamp REAL,"
                           "power REAL, "
                           "sys_info_FK INTEGER, "
                           "video_info_FK INTEGER, "
                           "FOREIGN KEY (sys_info_FK) REFERENCES sys_info(id), "
                           "FOREIGN KEY (video_info_FK) REFERENCES video_info(id)" )
    

    def __init__(self): #consider overriding this to input a filepath  for the DB to be stored, if possible
        '''
        Constructor
        '''
        try:
            self.db = lite.connect('../vEQ_db', check_same_thread = False) #TODO: Make this file in a more sensible location
            videoinfo_index = 0
            sysinfo_index = 0
            readings_index = 0
        except lite.Error, e:
            print "Error %s:" % e.args[0]
            sys.exit(1)
#         finally:
#             if self.db:
#                 self.db.commit()
                
    def getDB(self):
        return self.db
                        
    
    def initDB(self):
        with self.db as db:
            cursor = db.cursor()  
            cursor.execute("CREATE TABLE if NOT exists sys_info (%s);" % self.SYS_INFO_COLS) 
            cursor.execute("CREATE TABLE if NOT exists video_info (%s);" % self.VIDEO_INFO_COLS) 
            cursor.execute("CREATE TABLE if NOT exists ps_readings (%s);" % self.PS_READINGS_COLS) 
            cursor.execute("CREATE TABLE if NOT exists power_readings (%s);" % self.POWER_READINGS_COLS) 
            #This is an SQL injection vulnerability but 
#             1. This should not be exposed to users 
#             2. Makes it easier to change the structure of the table by changing the COLS string at 
#                 the top of the class rather than within the code.
    
    def clearDB(self):
        with self.db as db:
            cursor = db.cursor()
            print "Dropping tables"
            db.execute('PRAGMA FOREIGN_KEYS=OFF')
            db.execute("DROP TABLE power_readings;")
            db.execute("DROP TABLE ps_readings;")
            db.execute("DROP TABLE sys_info;")
            db.execute("DROP TABLE video_info;")
      

    def insertIntoReadingsTable(self, values):
        '''
        Insert given list of values into the Reading table
        
        Argument:
        values - a list of (a single-tuple of) values to be input into the readings table
                 format is values = [timestamp, power, cpu_percent, mem_percent, rss, sys_info_FK, video_info_FK)
            
        '''
        with self.db:
            cursor = self.db.cursor()  
            cursor.execute("INSERT INTO ps_readings VALUES (null,?,?,?,?,?,?)", values)
            global readings_index 
            readings_index = cursor.lastrowid
            return readings_index
            # values =[timestamp, power, cpupercent, memprectent, rss, sys_info_FK, video_info_FK)
            
    
    def insertIntoSysInfoTable(self, values):
        '''
        Insert given values into sysinfo table
        params:
        values: a list of values for the sys info table
                id INT PRIMARY KEY, timestamp INT, name TEXT, specs TEXT, cpu TEXT, gpu TEXT"
        returns: the last index of the sysinfo table
        '''
        with self.db:
            cursor = self.db.cursor()  
            #           id INT PRIMARY KEY, name TEXT, specs TEXT, timestamp INT,
            cursor.execute("INSERT INTO sys_info VALUES (null,?,?,?,?,?);", values)
#             global sysinfo_index
            self.sysinfo_index = cursor.lastrowid
            return self.sysinfo_index

      
    def insertIntoVideoInfoTable(self, values):
        '''
        Insert given values into video_info table
        params:
        values - a list of values for the sys info table
                 [ id INT PRIMARY KEY,  timestamp INT, name TEXT, specs TEXT, codec TEXT, width TEXT, height TEXT]
        '''
        with self.db:
            cursor = self.db.cursor()  
            cursor.execute("INSERT INTO video_info VALUES (null,?,?,?,?,?,?)", values)
            self.videoinfo_index = cursor.lastrowid
            return self.videoinfo_index
           
#          ftamp INT, name TEXT, specs TEXT, codec TEXT, width TEXT, height TEXT
        
           
    def insertIntoPowerTable(self, values):
        '''
        Insert given values into video_info table
        params:
        values - a list of values for the power readings table
                 [ "id INTEGER PRIMARY KEY,"
                           "timestamp REAL,"
                           "power REAL", 
                           "FOREIGN KEY (sys_info_FK) REFERENCES sys_info(id), "
                        "FOREIGN KEY (video_info_FK) REFERENCES video_info(id)" ]
        '''
        with self.db:
            cursor = self.db.cursor()  
            cursor.execute("INSERT INTO power_readings VALUES (null,?,?,?,?)", values)
            self.videoinfo_index = cursor.lastrowid
            return self.videoinfo_index
        
        
    def getValuesFromPowerTable(self, start_time, end_time):
        '''
        Get readings from the Power Table that fall between these times
        '''    
        with self.db as db:
            cursor = db.cursor()
            cursor.execute("SELECT power FROM power_readings WHERE timestamp BETWEEN ? AND ?", (start_time, end_time))
            values = cursor.fetchall()
        return values
        
    def getCPUValuesFromPSTable(self, start_time, end_time):
        '''
        Get readings from the Power Table that fall between these times
        '''    
        with self.db as db:
            cursor = db.cursor()
            cursor.execute("SELECT cpu_percent FROM ps_readings WHERE timestamp BETWEEN ? AND ?", (start_time, end_time))
            values = cursor.fetchall()
        return values
    
    def getMemValuesFromPSTable(self, start_time, end_time):
        '''
        Get readings from the Power Table that fall between these times
        '''    
        with self.db as db:
            cursor = db.cursor()
            cursor.execute("SELECT mem_percent FROM ps_readings WHERE timestamp BETWEEN ? AND ?", (start_time, end_time))
            values = cursor.fetchall()
        return values
    
    
if __name__ == '__main__':
    vEQdb = vEQ_database()
#     vEQdb.clearDB()
#     vEQdb.initDB()
    vEQdb.clearDB()
#     import processmonitor.processMonitor as procMon
#     import time
#     timestamp = time.time()
#     proc = procMon.get_processor()
#     os = procMon.get_os()
# 
#     values = [timestamp,os,proc,"gpu","specs"]
#     vEQdb.insertIntoSysInfoTable(values)
#     vEQdb.clearDB()

        