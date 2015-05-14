

'''
Python code to read from VC 870 meter adapted from C++ and Perl Code from 
Created on 28 Mar 2015

@author: ooe
'''
import hid
import sys
import traceback
import time
import logging

PROFILE = True
PROFILE_DURATION = 0 # (20 takes about 1 sec)
BAUD_SPEED = int(9600)

# TODO: Make a parent class for all types of energymeter
class VoltcraftMeter():
    logging.debug("Initializing Voltcraft VC 870 meter")
    hid_device = None
    
    def main(self,argv=None):
        try:
            hid_device = self.initDevice()
            count = 0
            while True and hid_device:
                if PROFILE:
                    logging.debug("Profiling ON")
                    if (count == (PROFILE_DURATION + 1) ):
                        print count, "Break "
                        break 
                    count += 1 
                outputstring = self.get_device_reading()
                print str(outputstring) + " W"
            if hid_device:
                hid_device.close()
    
        except Exception as e:
            print e
            traceback.print_exc(e)
    
    def initDevice(self):
        ''' 
        Open and return the VC870 Hid device
        
        Returns: 
        hid_device : An instance of the hid device itself which is ready to be read from
        
    #         Apparently in C and C++ and network programming, to fit a big Number
    #         in an char array you place it in the thefirst slot in the array, which 
    #         turncates it, then right shift it by 8, 16 and 24 in the next array slots 
    #         or indexes. In this case I used 128 because python wouldnt truncate 9600
    #         propperly that is get the value in the first 8 bits of 9600.
    #         
    #         Explanation   
    #         9600 to binary is 0b10010110000000
    #         Forcing this 14 bit digit into 8 bits will leave you with 0b10000000 (128 in decimal)
    #         6 of the most sigificant bit have been lost, but apparently shifting 
    #         the original number by 8 and 16, somehow gives you back the number.
    #         
    #         Should have made more attention as an undergrad   
    '''
        try:
            self.hid_device = hid.device()
            dev = hid.enumerate(0x1a86, 0xe008)
           
            if dev:
                self.hid_device.open(0x1a86, 0xe008)
           
                bps = BAUD_SPEED         
                buf = [0x0, 128, BAUD_SPEED>>8, BAUD_SPEED>>16, BAUD_SPEED>>24, 0x03]
                res = self.hid_device.send_feature_report(buf);
        
                logging.debug("HID device feature report sent -Value returned: " + str(res))
                if res > 0:
                    logging.debug("HID device sucessfully initiated at " + str(self.hid_device)) 
                    return self.hid_device
                else: 
                    logging.warning('Unable to open hid device')
                    return None
            else:
                logging.error("Couldn't open device")
                return None
            
        except:
                logging.error("Couldn't open device")
                traceback.print_exc(file=sys.stdout)
                return None
        
    
    def get_device_reading(self):
        '''
        Reads the Device and returns a string representing the reading
        This can take up to form 0.012s - 1 sec if everything is working well
        If it takes longer than a second then there might be a problem with the devoce
        See for Github VX970_USB_Catalog for details on the string format
        '''
        outputstring = ""
        count = 0
    # TODO move this loop to end_time
        if self.hid_device is not None:
            while count < 80:     #if count gets to 80 then maybe the device isnt on, return nothing so that caller doesnt wait longer than necessaru
                res = 0;
                while (res == 0):
                    res = self.hid_device.read(256);
                    count+=1
                
                if (res < 0):
                    sys.stderr.write("Unable to read()")
                    continue   
                else:
                    length = res[0] & 7; # the first byte contains the length in the lower 3 bits ( 111 = 7 )       
                    logging.debug("Recieved a packet of size: " + str(length) + " from device" )
                    prevchar = None 
                    currentchar = None 
                        
                    if length:
                        for i in xrange(0,length):
                            val = res[i+1] & 0x7f #bitwise and with 0111 1111, mask the upper bit which is always 1
                            currentchar = hex(val)[-1]                       
        #                     
                            if currentchar == "d":
                                prevchar = currentchar
                                continue
                            if  (prevchar == "d") and (currentchar == "a"):
            #                     0x0d 0x0a or newline encountered so this can retrurn a value
            #                     In the original C++ code, sysout appears to be able to deal with this newline automatically 
                                return self.processPowerOutputString(outputstring)
                            outputstring +=str(currentchar) 
            logging.warning("Count for VC meter exceeded: returning -1 for measurement")
            return -1
        
        else:
            logging.warning("No device detected")
            return -1 #should never get here
    
    def processPowerOutputString(self,outputstring):
        vc_function = outputstring[0:2]
        measurement1 = outputstring[3:8]
        measurement2 = outputstring[9:14]
        logging.debug("VC Fucntion: " + vc_function + "Measuremnt: " + measurement1)
        try:
            if vc_function == "90":
                
                return float(measurement1)/10 # + " Watts"
            else:
                logging.warning("VC870 Function Not yet implemented: " + str(vc_function))  
                return -1
        except Exception as e:
            sys.stderr.write(e)
            return None
                
          
if __name__ == '__main__': 
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Started VC meter")
    vc = VoltcraftMeter() 
    if PROFILE:
        import cProfile
        import pstats
        import os
        if not os.path.exists("../profile"): 
            os.makedirs("../profile")
        sys.stderr.write("Starting Profiling\n")
        profile_filename = "../profile/voltcraftmeter_profile.txt"
        cProfile.run('vc.end_time()',profile_filename)
        statsfile =  open("../profile/voltcraft_profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(vc.main())
