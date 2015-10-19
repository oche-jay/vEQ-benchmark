'''
Created on 24 Feb 2015

@author: oche
'''
import sys
import logging
import sqlite3 as lite
import os
import traceback
from os.path import expanduser


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
    
    VIDEO_QUALITY_COLS = ("id INTEGER PRIMARY KEY,"
                        "timestamp REAL, " 
                        "video TEXT, "
                        "url TEXT, "
                        "reference_videoname TEXT,"
                        "metric1_ypsnr TEXT, "
                        "metric2_apsnr TEXT, "
                        "metric3_yssim TEXT, "
                        "metric4_assim TEXT, "
                        "metric5_other TEXT, "
                        "metric6_other TEXT, " 
                        "metric7_other TEXT, "
                        "metric8_other TEXT, "
                        "metric9_other TEXT, "
                        "metric10_other TEXT "
                         )
                    
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
        db_loc : location to store db or just "memory" to store in memory
        '''
        home = expanduser("~")
        default_loc = os.path.join(home, 'vEQ_db.sqlite')
        print default_loc
        
        if db_loc is None:
            db_loc = default_loc
        elif db_loc.lower() == "memory":
            db_loc = ':memory:'
        
        try:
            self.db = lite.connect(db_loc, check_same_thread = False) 
            cwd = os.getcwd()
            
#             pathname = os.path.dirname(cwd)
#             pwdb = os.path.normpath(os.path.join(pathname,db_loc) )
            logging.debug("DB located at " + db_loc)
            
            print "DB located at " + db_loc
            self.videoinfo_index = 0
            self.sysinfo_index = 0
            self.readings_index = 0
            self.summary_index = 0
            self.initDB()
        except lite.Error, e:
            print(traceback.format_exc())
            logging.error( "Error %s:" % e.args[0])
            sys.exit(1)
#         finally:
#             if self.db:
#                 self.db.commit()
    
    def printTablesinDB(self):
        with self.db as db:
            print db
            cursor = db.cursor() 
            cursor.executescript("SELECT name FROM sqlite_master WHERE type='table';")  
            print "Tables in DB: %s" % str(tuple(cursor))
                      
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
    
#     TODO: complete this method
    def getJoinResultsForRunandExport(self,video_key_id):
        with self.db as db:
            cursor = db.cursor()
            data = cursor.execute("select *  from power_readings NATURAL LEFT OUTER JOIN ps_readings"
                           "where power_readings.video_info_FK = ?", (video_key_id))
     
    
    def getQuerybyNameandHeight(self, video_name, video_height):
        with self.db as db:
            cursor = db.cursor()
            cursor.execute("""
            select video_name, video_height, mean_power as pow from veq_summary 
            where video_name is ("%s")
            and video_height in (%s) 
            order by video_name
            """ % (video_name, video_height))
        values = cursor.fetchall()  
        return values  
        
    def getDistinctVideoCodecsfromDB(self):  
        '''
        Returns all distinct video_codecs, and the mean power in the DB, ordered by the average power
        '''
        with self.db as db:
            cursor = db.cursor()
            cursor.execute("SELECT video_codec, avg(mean_power) as pow FROM veq_summary GROUP BY video_codec ORDER BY pow;")
            values = cursor.fetchall()  
        return values 
    

# <<<<<<< HEAD
    def getDistinctColumnfromDBwithHeightFilter(self, column_name, height_filter):
        '''
        Returns columnname , mean power, and mean_cpu for a giveng height
        '''
        with self.db as db:
            try:
                cursor = db.cursor()
                cursor.execute("""
                SELECT %s , avg(mean_power) as pow, avg(mean_cpu) FROM veq_summary 
                where %s is NOT NULL
                and video_height in ( %s)
                GROUP BY %s 
                ORDER BY %s;
                """ % (column_name, column_name, height_filter, column_name, column_name) )
                values = cursor.fetchall() 
            except:
                traceback.print_exc()
                sys.exit()
        return values 
     
    def getDistinctColumnfromDB(self, column_name):  
        '''
        Returns all distinct COLUMN_NAME, and the mean power in the DB, ordered by the height, 
        height_filter: optional paramaeter to get a certain height
        '''
        with self.db as db:
            try:
                cursor = db.cursor()
                cursor.execute("""
                SELECT %s , avg(mean_power) as pow FROM veq_summary 
                where %s is NOT NULL
                GROUP BY %s 
                ORDER BY pow;
                """ % (column_name, column_name,column_name))
                values = cursor.fetchall() 
            except:
                traceback.print_exc()
                sys.exit()
        return values
    
    def getDistinctVideoHeightfromDB(self, min_height=0):  
        '''
        Returns all distinct video_heights greater than min_height, and the mean power in the DB, ordered by the height
        '''
        with self.db as db:
            cursor = db.cursor()
            cursor.execute("""
            SELECT cast(video_height as number) as vh, avg(mean_power) as pow , count(video_height)
            FROM veq_summary 
            WHERE vh > ?
            GROUP BY video_height ORDER BY vh;
            """, [min_height])
            values = cursor.fetchall()  
        return values 
    
    def getSummaryfromVeqDB(self):
        '''
        Get individual readings for power, cpu from the veq_summary table
        '''    
        with self.db as db:
#             cursor = db.cursor()
#             db.row_factory = lambda cursor, row: row[0]
            cursor = db.cursor()
#             SELECT  distinct video_codec as vc,  avg(mean_power)  as pow, avg(mean_cpu) as cpu FROM veq_summary group by video_codec order by vc
            cursor.execute("""
             SELECT video_codec, mean_power, mean_cpu, video_name FROM veq_summary 
             where video_name is NOT NULL
             order by video_codec;
             """)
            values = cursor.fetchall()
#         i=0
#         for v in values:
#             i+=1
#             print i,v
        return values

    
    def getSummarybyMovieandHeight(self):
        '''
            Returns all the average power of the individual movies grouped by heights
        '''
        with self.db as db:
            cursor = db.cursor
            cursor.execute("""
            select video_name, video_height, avg(mean_power) as pow, avg(mean_cpu), count(mean_power) as count from veq_summary 
            where video_name is NOT NULL
            group by video_name 
            order by pow;
            """)
            
    def getSummaryfromVeqDBbyTitle(self):
        '''
        Get individual readings for video_height, mean_power, mean_cpu, video_name from the veq_summary table
        '''    
        with self.db as db:
#             cursor = db.cursor()
#             db.row_factory = lambda cursor, row: row[0]
            cursor = db.cursor()
            cursor.execute("SELECT video_height, mean_power , mean_cpu, video_name FROM veq_summary order by video_title;")
            values = cursor.fetchall()
        return values
    
    
    def selectAllIndvidualReadings(self):
        with self.db as db:
            cursor = db.cursor()
            cursor.execute("""
            SELECT mean_cpu, mean_memory, mean_bandwidth, mean_power FROM veq_summary 
            WHERE mean_power > 1 
            """)
            values = cursor.fetchall()
            return values
            
    
    def getSummaryfromVeqDBbyHeight(self, min_cpu=0, min_power=0, min_height=0):
        '''
        Get individual readings for video_height, mean_power, mean_cpu from the veq_summary table
        Only get values where the video height is greater than min_height(default 0), 
        CPU is greater than min_cpu(e.g 2%) as anything less means its quite likely 
        there was no video playback and Power Values greater than min_power e.g 2.5W for RPI  as it consumes around 2.7W)
        '''    
    
        with self.db as db:
#             cursor = db.cursor()
#             db.row_factory = lambda cursor, row: row[0]
            cursor = db.cursor()
            cursor.execute("""
            SELECT cast(video_height as number) as vh, mean_power, mean_cpu FROM veq_summary 
            WHERE vh > ? 
            AND cast(mean_cpu as int) > ? 
            AND cast(mean_power as int) > ?
            ORDER by vh;
            """, [min_height, min_cpu, min_power])
            values = cursor.fetchall()
        return values
    
    def getSummaryofValuefromVeqDBbyHeight(self, colname):
        '''
        Get individual readings for video_height, \'colname\', mean_cpu from the veq_summary table
        '''    
        with self.db as db:
#             cursor = db.cursor()
#             db.row_factory = lambda cursor, row: row[0]
            cursor = db.cursor()
            cursor.execute("SELECT video_height, mean_power, mean_cpu FROM veq_summary order by video_height;")
            values = cursor.fetchall()
        return values
    
#     def getSummaryfromVideoTitle(self):
#         '''
#         Get individual readings for video_height, mean_power, mean_cpu from the veq_summary table
#         '''    
#         with self.db as db:
#     #             cursor = db.cursor()
#     #             db.row_factory = lambda cursor, row: row[0]
#             cursor = db.cursor()
#             cursor.execute("SELECT video, avg(mean_power) , mean_cpu FROM veq_summary order by video_height;")
#             values = cursor.fetchall()
#         return values
        
    
if __name__ == '__main__':
    logging.basicConfig( 
                        format = '[vEQ_database] %(levelname)-7.7s %(message)s'
                        )
    dbpath = os.path.abspath('C:/Users/ooe/Documents/git/vEQ_db.sqlite')
    dbpath = os.path.abspath('/Users/oche/Dropbox/vEQ_db.sqlite')

    vEQdb = vEQ_database(dbpath)
    vEQdb.printTablesinDB()
    
    vEQdb.getSummaryfromVeqDB()
    vEQdb.getDistinctVideoCodecsfromDB()
    vals = vEQdb.getDistinctVideoHeightfromDB()
    for v in vals:
        print v

    vEQdb = vEQ_database(dbpath)
    vEQdb.printTablesinDB()
    
    vEQdb.getSummaryfromVeqDB()
    vEQdb.getDistinctVideoCodecsfromDB()
    
    vals = vEQdb.getDistinctColumnfromDB("video_name")
    
    for v in vals:
        print v


        
