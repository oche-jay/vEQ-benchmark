'''
Created on 28 Mar 2015

@author: ooe
'''
import hid
import sys
import traceback
import time


BAUD_SPEED = int(9600);

if __name__ == '__main__':   
    try:
        print "Opening Device"
        hid = hid.device()
        hid.open(0x1a86, 0xe008)
        
        print "Manufacturer: %s" % hid.get_manufacturer_string()
        print "Product: %s" % hid.get_product_string()
        print "Serial No: %s" % hid.get_serial_number_string()
        
#         // Send a Feature Report to the device
       
        bps = BAUD_SPEED
                          
        buf = [0x0, 128, bps>>8, bps>>16, bps>>24, 0x03]
        print buf
        buff = ''.join(map(chr, buf))
        print buff
        res = hid.send_feature_report(buf);
        print res 
        
        while True:
            if (res < 0):
                sys.stderr.write("Unable to send a feature report.\n");
        
            res = hid.read(256);
            if (res == 0):
                print "waiting.."
            if (res < 0):
                sys.stderr.write("Unable to read()")
            time.sleep(1)
            
            # format data 
            len = res[0] & 7; # the first byte contains the length in the lower 3 bits ( 111 = 7 )
            print len
            for i in xrange(0,len):
                res[i+1] &= 0x7f # bitwise and with 0111 1111, mask the upper bit which is always 1
                print res[i+1]
    #         if(len>0)
    #         {  
    #             fwrite(buf+1, 1, len, stdout); // write data directly to stdout to enable pipeing to interpreter app
    #             fflush(stdout);
    #         }
    # 
    # 
    #         }while(res>=0);
    #       //  printf("%s",hid_error(handle));
            print res
        hid.close()

    

    except Exception as e:
        print e
        traceback.print_exc(e)
