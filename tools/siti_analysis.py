"""
SI and TI Calculations
Copyright (c) 2014 Oche Ejembi, Alex Izvorski

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys

if __package__ is None and not hasattr(sys, "frozen"):
    # direct call of __main__.py
    import os.path
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(os.path.dirname(path)))
    
import numpy
import re
import scipy.misc
import sys
import os
import logging
from subprocess import Popen
import glob
import traceback

from scipy import ndimage
from vEQ_ssim.vEQ_ssim import convertToYUV 
from __main__ import traceback

logging.basicConfig( 
    format = '[vEQ_SITI analyis] %(levelname)-7.7s %(message)s'
    )

FFMPEG_LOC = "/usr/local/bin/ffmpeg"

SI_array= []
TI_array = []
#import ssim_theano
def img_greyscale(img):
    return 0.299 * img[:,:,0] + 0.587 * img[:,:,1] + 0.114 * img[:,:,2]

def img_read_yuv(src_file, width, height):
    y_img = numpy.fromfile(src_file, dtype=numpy.uint8, count=(width * height)).reshape( (height, width) )
    y_img = y_img.astype("int64")
    u_img = numpy.fromfile(src_file, dtype=numpy.uint8, count=((width/2) * (height/2))).reshape( (height/2, width/2) )
    v_img = numpy.fromfile(src_file, dtype=numpy.uint8, count=((width/2) * (height/2))).reshape( (height/2, width/2) )
    return (y_img, u_img, v_img)

def createMotionandSobelVideos():
    j = glob.glob1(os.getcwd(), '*sobel*.jpg')
    k = glob.glob1(os.getcwd(), '*motion*.jpg')
    
    from natsort import natsorted as ns
    j = ns(j)
    k = ns(k)
      
    with open("sobel.txt", "w") as sobeltxt:
        for x in j:
            sobeltxt.write("file %s\n" % str(x))
            
    with open("motion.txt", "w") as motiontxt:
        for x in k:
            motiontxt.write("file %s\n" % str(x)) 
            
    outfile = "sobel.mp4"
    outfile2 = "motion.mp4"
    
#     ffmpeg -f concat -i spatial.txt -vf fps=10 -pix_fmt yuv420p sobel.mp4
    command = [FFMPEG_LOC, "-y", "-f", "concat", "-i", "sobel.txt", "-vf", "fps=10", "-pix_fmt", "yuv420p", outfile]
    command2 = [FFMPEG_LOC, "-y","-f", "concat", "-i", "motion.txt", "-vf", "fps=10" ,"-pix_fmt", "yuv420p", outfile2]   
    
    for it in command:
        print it,
    print "\n" 
    p = Popen(command)
    p.communicate()
    p = Popen(command2)
    p.communicate()
        
# print ref_file

# createMotionandSobelVideos()
# sys.exit()
def getSITI(ref_file, makeVideo=True):
    width = 0 
    height = 0
    frame_num = 0 
    pref = 0
    maxSI = 0
    maxTI = 0
    pmag = 0
   
    if ".yuv" in ref_file:
        # Inputs are uncompressed video in YUV420 planar format
        # Get resolution from file name
        m = re.search(r"(\d+)x(\d+)", ref_file)
        
        if not m:
            print "Could not find resolution in file name: %s" % (ref_file)
            exit(1)
    
        width, height = int(m.group(1)), int(m.group(2))
        print width, height
        print "Getting ST and TI of %s, resolution %d x %d" % (ref_file, width, height)
    else:
        ref_file = convertToYUV(ref_file)
        m = re.search(r"(\d+)x(\d+)", ref_file)
        
        if not m:
            print "Could not find resolution in file name: %s" % (ref_file)
            exit(1)
    
        width, height = int(m.group(1)), int(m.group(2))
    
    ref_fh = open(ref_file, "rb")    
    first_frame = True
        
    while True:
        try:
            logging.debug("REading YUV frame")
            ref, _, _ = img_read_yuv(ref_fh, width, height)
        except:
            traceback.print_exc()
            break
    
        dx = ndimage.sobel(ref, 0)  # horizontal derivative
        dy = ndimage.sobel(ref, 1)  # vertical derivative    
        mag= numpy.hypot(dx, dy) 
        mag= numpy.array(mag, dtype=numpy.uint64)
#         mx = numpy.max(mag)
  
        if makeVideo:
#             logging.debug("Saving image to %s " %  os.getcwd())
#             scipy.misc.imsave(str(frame_num)+'y_orig.jpg', ref)
#             scipy.misc.imsave(str(frame_num)+'u_orig.jpg', uref)
#             scipy.misc.imsave(str(frame_num)+'v_orig.jpg', vref)
            scipy.misc.imsave(str(frame_num)+'sobel.jpg', mag)
            scipy.misc.imsave(str(frame_num)+'motion.jpg', pref - ref)
             
        SI = mag.std()
        TI = (ref - pref).std()
        
        SI_array.append(SI)
        TI_array.append(TI)
        
        if first_frame:
            first_frame = False
            frame_num += 1
            TI = 0
              
        maxSI = max(maxSI, SI)
        maxTI = max(maxTI, TI)
        
        print "Frame=%d SI=%f, TI=%f, max SI=%f, max TI=%f" % (frame_num, SI, TI, maxSI, maxTI)
        frame_num += 1
        pref = ref
        pmag = mag
    
        res =  "%f, %f" % (maxSI, maxTI)
    
        with open("results.txt", "a") as resfile:
            resfile.write("%s %s\n" % (ref_file, res))
        
    return maxSI, maxTI

def main():
    
    logging.getLogger().setLevel(logging.ERROR)
    ref_file = sys.argv[1]
    getSITI(ref_file, makeVideo=False) 

    import matplotlib.pyplot as plt
    
    plt.plot(SI_array, label="SI", color="red")
    plt.plot(TI_array, label="TI", color="blue")
    plt.legend()
    plt.show()
           
    createMotionandSobelVideos()

PROFILE = True   
if PROFILE:
    import cProfile
    import pstats
    import os
    if not os.path.exists("../profile"): 
        os.makedirs("../profile")
    sys.stderr.write("Starting Profiling\n")
    profile_filename = "../profile/siti_analysis.txt"
    cProfile.run('main()',profile_filename)
    statsfile =  open("../profile/siti_anlaysis_stats.txt", "wb")
    p = pstats.Stats(profile_filename, stream=statsfile)
    stats = p.strip_dirs().sort_stats('cumulative')
    stats.print_stats()
    statsfile.close()
    sys.exit(0)
else:
    sys.exit(main())   
 

