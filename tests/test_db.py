'''
Created on 16 May 2015

@author: ooe
'''
import unittest

import database.vEQ_database as test_db

tables =  map(unicode,('sys_info','video_info','ps_readings','power_readings', 'veq_summary'))

class Test(unittest.TestCase):
    def setUp(self):
        self.tdb = test_db.vEQ_database(":memory:")
        self.tdb.initDB()

    def testDBcreated(self):
        self.assertIsNotNone(self.tdb.getDB())
    
    def testInitDB(self):
        print self.tdb
        cursor = self.tdb.getDB().cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        self.tdb.getDB().commit()
        res = tuple(cursor.fetchall()) 
#         ((u'sys_info',) , (u'video_info',), (u'ps_readings',), (u'power_readings',))
        res = list(sum(res,())) #flatten the resutl
        self.assertEquals(tables, res)
        pass
    
    def testDropTables(self):
        print self.tdb
        cursor = self.tdb.getDB().cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        res = tuple(cursor.fetchall()) 
        print res
        self.tdb.clearDB()
        cursor = self.tdb.getDB().cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        res = tuple(cursor.fetchall()) 
        self.assertEqual(res.__len__(),0)
        
    def testGetValuesFromPSTable(self):
        print self.tdb
        values = [  "1431824413.343" ,   "43.1"  ,  "1.1322905470656"   , "193830912" ,   "98136216",    "1458167781" ,   "11763736"  ,  "412066" ,   "1"   , "1"
]
        self.tdb.insertIntoReadingsTable(values)
        retval = self.tdb.getValuesFromPSTable("net_recv", 1431824413, 1431824415)
        self.assertEqual(retval[0],1458167781)
        
        retval = self.tdb.getValuesFromPSTable("cpu_percent", 1431824413, 1431824415)
        self.assertEqual(retval[0],43.1)

    def testInsertintoSummaryTable(self):
        print self.tdb
        values = [ "1431824413.343" ,   "43.1"  , " ", " ",  " ", " ", "1.1322905470656"   , "193830912" ,   "98136216",    "1458167781" ,   "11763736"  ,  "412066" ,   "1"   , "1"]
        retval = self.tdb.insertIntoVEQSummaryTable(values)
        self.assertEqual(retval,1)
        cursor = self.tdb.getDB().cursor()
        cursor.execute("SELECT * from veq_summary")
        cursor.fetchone()
        print cursor.description.__len__()
        cursor.execute("PRAGMA table_info(veq_summary)")
        res = tuple(cursor.fetchall()) 
#         res = list(sum(res,()))
        print res
        
        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()