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
                     "net_sent INTEGER,"
                     "net_recv INTEGER,"
                     "io_bytesread INTEGER,"
                     "io_byteswrite INTEGER,"
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
    
    VEQ_SUMMARY_COLS = ("id INTEGER PRIMARY KEY,"
                        "video_name TEXT,"
                        "video_url TEXT, "
                        "video_codec TEXT,"
                        "video_height TEXT,"
                        "video_width TEXT,"
                        "mean_power REAL, "
                        "mean_cpu REAL, "
                        "mean_memory REAL, "
                        "mean_gpu REAL,"
                        "mean_bandwidth REAL,"
                        "data_transferred REAL,"
                        "file_size REAL,"
                        "sys_info_FK INTEGER, "
                        "video_info_FK INTEGER, "
                        "FOREIGN KEY (sys_info_FK) REFERENCES sys_info(id), "
                        "FOREIGN KEY (video_info_FK) REFERENCES video_info(id)" )
    

    def __init__(self,db_loc=None): #consider overriding this to input a filepath  for the DB to be stored, if possible
        '''
        Constructor
        '''
        default_loc = '../vEQ_db' 
        if db_loc is None:
            db_loc = default_loc
        try:
            self.db = lite.connect(db_loc, check_same_thread = False) 
            self.videoinfo_index = 0
            self.sysinfo_index = 0
            self.readings_index = 0
            self.summary_index = 0
        except lite.Error, e:
            print "Error %s:" % e.args[0]
            sys.exit(1)
#         finally:
#             if self.db:
#                 self.db.commit()
    
    def printTablesinDB(self):
        with self.db as db:
            print db
            cursor = db.cursor() 
            cursor.executescript("SELECT name FROM sqlite_master WHERE type='table';")  
            print tuple(cursor)
                      
    def getDB(self):
        return self.db
                        
    
    def initDB(self):
#         TODO clean the COLS strings first to avoid injection
        with self.db as db:
            cursor = db.cursor()  
            cursor.execute("CREATE TABLE if NOT exists sys_info (%s);" % self.SYS_INFO_COLS) 
            cursor.execute("CREATE TABLE if NOT exists video_info (%s);" % self.VIDEO_INFO_COLS) 
            cursor.execute("CREATE TABLE if NOT exists ps_readings (%s);" % self.PS_READINGS_COLS) 
            cursor.execute("CREATE TABLE if NOT exists power_readings (%s);" % self.POWER_READINGS_COLS) 
            cursor.execute("CREATE TABLE if NOT exists veq_summary (%s);" % self.VEQ_SUMMARY_COLS) 
 
    def clearDB(self):
        with self.db as db:
            cursor = db.cursor()
            print "Dropping tables"
            cursor.execute('PRAGMA FOREIGN_KEYS=OFF')
            cursor.executescript("DROP TABLE IF EXISTS power_readings;")
            cursor.executescript("DROP TABLE  IF EXISTS ps_readings;")
            cursor.executescript("DROP TABLE IF EXISTS sys_info;")
            cursor.executescript("DROP TABLE IF EXISTS video_info;")
            cursor.executescript("DROP TABLE IF EXISTS veq_summary;")
      

    def insertIntoReadingsTable(self, values):
        '''
        Insert given list of values into the Reading table
        
        Argument:
        values - a list of (a single-tuple of) values to be input into the readings table
                 format is values = [timestamp, power, cpu_percent, mem_percent, rss, net_sent, net_recv, ioread, iowrite, sys_info_FK, video_info_FK)  
        '''
        with self.db:
            cursor = self.db.cursor()  
            cursor.execute("INSERT INTO ps_readings VALUES (null,?,?,?,?,?,?,?,?,?,?)", values)
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
        
    def insertIntoVEQSummaryTable(self, values):
        '''
        Insert given summary values into veq_summary table
        params:
        values - a list of values for the table
                 [ "id INTEGER PRIMARY KEY," "video_name TEXT, video_url TEXT, " 
                 "video_codec TEXT, video_height TEXT, video_width TEXT," 
                 "mean_power REAL, mean_cpu REAL,  mean_memory REAL, " 
                 "mean_gpu REAL" "mean_bandwidth REAL" "data_transferred REAL," 
                 "file_size REAL," "sys_info_FK INTEGER, " 
                 "video_info_FK INTEGER," ]
        '''
        with self.db:
            cursor = self.db.cursor()  
            cursor.execute("INSERT INTO veq_summary VALUES (null,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
            self.summary_index = cursor.lastrowid
            return self.summary_index
        
        
    def getValuesFromPowerTable(self, start_time, end_time):
        '''
        Get readings from the Power Table that fall between these times
        '''    
        with self.db as db:
            cursor = db.cursor()
            db.row_factory = lambda cursor, row: row[0]
            cursor.execute("SELECT power FROM power_readings WHERE timestamp BETWEEN ? AND ?", (start_time, end_time))
            values = cursor.fetchall()
        return values
        
    def getCPUValuesFromPSTable(self, start_time, end_time):
        '''
        Get readings from the Power Table that fall between these times
        '''    
        with self.db as db:
            cursor = db.cursor()
            db.row_factory = lambda cursor, row: row[0]
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
            db.row_factory = lambda cursor, row: row[0]
            cursor = db.cursor()
            cursor.execute("SELECT mem_percent FROM ps_readings WHERE timestamp BETWEEN ? AND ?", (start_time, end_time))
            values = cursor.fetchall()
        return values
    
    def getValuesFromPSTable(self, column_name, start_time, end_time):
        '''
        Get readings from the Power Table that fall between these times
        '''    
        with self.db as db:
            db.row_factory = lambda cursor, row: row[0]
            cursor = db.cursor()
            execute_string = ' '.join(("SELECT ", column_name, "FROM ps_readings WHERE timestamp BETWEEN ? AND ?"))
            cursor.execute(execute_string, (start_time, end_time))
            values = cursor.fetchall()
        return values
    
if __name__ == '__main__':
    vEQdb = vEQ_database()
#     vEQdb.clearDB()
#     vEQdb.initDB()
    vEQdb.printTablesinDB()
    vEQdb.clearDB()
    vEQdb.printTablesinDB()
#     import processmonitor.processMonitor as procMon
#     import time
#     timestamp = time.time()
#     proc = procMon.get_processor()
#     os = procMon.get_os()
# 
#     values = [timestamp,os,proc,"gpu","specs"]
#     vEQdb.insertIntoSysInfoTable(values)
#     vEQdb.clearDB()

        