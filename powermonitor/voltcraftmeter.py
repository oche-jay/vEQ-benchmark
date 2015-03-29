'''
Python code to read from VC 870 meter adapted from C++ and Perl Code from 
Created on 28 Mar 2015

@author: ooe
'''
import hid
import sys
import traceback
import time

BAUD_SPEED = int(9600)

# my %fun_sel = (
#     '00' => 'DCV',
#     '01' => 'ACV',
#     '10' => 'DCmV',
#     '11' => 'TEMP',
#     '20' => 'RES',
#     '21' => 'CTN',
#     '30' => 'CAP',
#     '40' => 'DIO',
#     '50' => 'FREQ',
#     '51' => '(4~20)mA',
#     '60' => 'DCuA',
#     '61' => 'ACuA',
#     '70' => 'DCmA',
#     '71' => 'ACmA',
#     '80' => 'DCA',
#     '81' => 'ACA',
#     '90' => 'Act+Apar_Power',
#     '91' => 'PowFactor+Freq',
#     '92' => 'VoltEff+CurrEff'
# );

def processOutputString(outputstring):
    vc_function = outputstring[0:2]
    measurement1 = outputstring[3:8]
    measurement2 = outputstring[9:14]
    
    if vc_function == "90":
        print str(float(measurement1)/10) # + " Watts"
    else:
        sys.stderr.write("VC870 Function Not yet implemented")
    
    
if __name__ == '__main__':   
    try:
        print "Opening Device"
        hid = hid.device()
        hid.open(0x1a86, 0xe008)
    
        bps = BAUD_SPEED 
        
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
#         Should have made more attention as an udnergrad           
        
        buf = [0x0, 128, BAUD_SPEED>>8, BAUD_SPEED>>16, BAUD_SPEED>>24, 0x03]
#         buff = ''.join(map(chr, buf))
#         print buff
        res = hid.send_feature_report(buf);
     
        print"-data start-"
        time.sleep(1)
        outputstring = ""
        while True:
            res = 0;
            
            while (res == 0):
                res = hid.read(256);
           
            if (res < 0):
                sys.stderr.write("Unable to read()")
                continue
            
            else:
                length = res[0] & 7; # the first byte contains the length in the lower 3 bits ( 111 = 7 )
                
                prevchar = "x" #this is just a dirty hack to emulate newline behaviour
                currentchar = "y" 
                
                
                if length:
                    for i in xrange(0,length):
                        val = res[i+1] & 0x7f #bitwise and with 0111 1111, mask the upper bit which is always 1
                        currentchar = hex(val)[-1]
                        
#                         In the original C++ code when sysout encounters 
#                         0x0d 0x0a, it knows to 
#                         output a newline character. 
#                         I dont know how to do this with Python
                        if currentchar == "d":
                            prevchar = currentchar
                            continue
                        if (currentchar == "a") and (prevchar == "d"):
#                             sys.stdout.write("\n")
#                             outputstring+="\n"
#                             print "out " + outputstring
                            processOutputString(outputstring)
                            outputstring = ""
                            continue
                        outputstring +=str(currentchar) 
#                         sys.stdout.write(currentchar) #get the lowest byte of this hex
        hid.close()

    except Exception as e:
        print e
        traceback.print_exc(e)
