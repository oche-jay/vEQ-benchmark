'''
Created on 21 Sep 2015

@author: oche
'''

"""
SI and TI Calculations
Copyright (c) 2014 Alex Izvorski <aizvorski@gmail.com>

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

import numpy
import re
import scipy.misc
import sys
import os
from subprocess import Popen
import glob

import niqe
import psnr
import reco
import ssim
import vifp

from scipy import ndimage, Inf
from __builtin__ import len

FFMPEG_LOC = "/usr/local/bin/ffmpeg"
#import ssim_theano
def img_greyscale(img):
    return 0.299 * img[:,:,0] + 0.587 * img[:,:,1] + 0.114 * img[:,:,2]

def img_read_yuv(src_file, width, height):
    y_img = numpy.fromfile(src_file, dtype=numpy.uint8, count=(width * height)).reshape( (height, width) )
    y_img = y_img.astype("int64")
    u_img = numpy.fromfile(src_file, dtype=numpy.uint8, count=((width/2) * (height/2))).reshape( (height/2, width/2) )
    v_img = numpy.fromfile(src_file, dtype=numpy.uint8, count=((width/2) * (height/2))).reshape( (height/2, width/2) )
    return (y_img, u_img, v_img)

ref_file = sys.argv[1]

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

if ".yuv" in ref_file:
    # Inputs are uncompressed video in YUV420 planar format
    # Get resolution from file name
    m = re.search(r"(\d+)x(\d+)", ref_file)
    if not m:
        print "Could not find resolution in file name: %s" % (ref_file)
        exit(1)

    width, height = int(m.group(1)), int(m.group(2))
    print "Getting ST and TI of %s, resolution %d x %d" % (ref_file, width, height)

    ref_fh = open(ref_file, "rb")
#     dist_fh = open(dist_file, "rb")

    frame_num = 0 
    pref = 0
    maxSI = 0
    maxTI = 0
    pmag = 0
    
    first_frame = True
    
    while True:
        try:
            ref, uref, vref = img_read_yuv(ref_fh, width, height)
        except:
            break
    
        dx = ndimage.sobel(ref, 0)  # horizontal derivative
        dy = ndimage.sobel(ref, 1)  # vertical derivative    
        mag= numpy.hypot(dx, dy) 
        mag= numpy.array(mag, dtype=numpy.uint64)
        mx = numpy.max(mag)
        mag *= 255.0 / mx  # normalize (Q&D)
        # magnitude

        scipy.misc.imsave(str(frame_num)+'y_orig.jpg', ref)
        scipy.misc.imsave(str(frame_num)+'u_orig.jpg', uref)
        scipy.misc.imsave(str(frame_num)+'v_orig.jpg', vref)
        scipy.misc.imsave(str(frame_num)+'sobel.jpg', mag)
        scipy.misc.imsave(str(frame_num)+'motion.jpg', pref - ref)
         
#         print dx.std(), dy.std(), 
        SI = mag.std()
        TI = (ref - pref).std()
        
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
    print res
    createMotionandSobelVideos()
    with open("results.txt", "a") as resfile:
        resfile.write("%s %s\n" % (ref_file, res))
 
    
  

