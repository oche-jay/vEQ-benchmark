'''
Created on 1 Jul 2015

@author: oche
'''
from __future__ import unicode_literals
import sys 
import argparse
import os
import logging
import traceback
from util import validURLMatch, validYoutubeURLMatch
import subprocess
from subprocess import Popen
import re
from os.path import expanduser
from youtube_dl.utils import DownloadError
import pickle
import datetime
import time
import database.vEQ_database as DB

try:
    from youtube_dl import YoutubeDL
except ImportError:
    logging.error("Try installing for python Youtube-DL from PiP or similar")

try:
    from pymediainfo import MediaInfo
except:
    logging.warn("Using our own lib version of pymediainfo")
    from util.pymediainfo import MediaInfo


ENV_DICT = os.environ

# PATH_TO_MEDIAINFO = "C:/MediaInfo" #Put this in a seperate PREFS file or something
PATH_TO_MEDIAINFO = "/usr/local/bin"
PATH_TO_FFMPEG = "/usr/local/bin"
PATH_TO_TINYSSIM = "/Users/oche/ffmpeg/tests"
PATH_TO_EPFL_VQMT = ""

ONLINE_VIDEO = False
LOCAL_VIDEO = False
video_url = ""

ENV_DICT["PATH"] = PATH_TO_TINYSSIM +  os.pathsep + PATH_TO_FFMPEG + os.pathsep + PATH_TO_MEDIAINFO +  os.pathsep + ENV_DICT["PATH"] 

logging.getLogger().setLevel(logging.INFO)

def getLocalVideoInfo(video):
    '''
    Returns the codec, width and height of a video using MediaInfo
    '''
    try:
        '''
        if mediainfo isn't in the python environment path then this wont work.
        '''
        logging.info("Getting mediainfo for %s", video)
        video_info = MediaInfo.parse(video)
        for track in video_info.tracks:
            if track.track_type == 'Video':
                logging.info(" ".join(["Extracted info with MediaInfo: ", track.codec, str(track.width) , str(track.height)]) )
                return track.codec, track.width, track.height
    
    except OSError as oe:
        logging.error("OS Error:", sys.exc_info())
        sys.stderr.write("OS Error: Probably couldn't find MediaInfo \nIs it in ENV_DICT[\"PATH\"] ?\n")
        sys.stderr.write(os.environ["PATH"]+"\n")
        traceback.print_exc()
    except:
        logging.error("Unexpected error:", sys.exc_info())
        traceback.print_exc()
        sys.exit(1)

def scaledownYUV(video, orig_width=None, orig_height=None, target_width=None, target_height=None):
    '''
    Scale down a raw yuv file fro
    '''
#     first use the filename to check if a suitable scaledown version exists????
    logging.debug("Scaling down YUV file")
    fileName = os.path.basename(video)
    filePath = os.path.dirname(video)
#         replace all spaces with and UNDERSCORE
    fileName = re.sub(r"\s+", '-', fileName)
#         remove sub all non-word characters and replACE WITH underscore
    fileName = re.sub(r"[^.\w]+", '_', fileName)
    
    fileName = 'scaled_' + str(target_width) +"x" + str(target_height) + "_" + fileName
    outfile = os.path.join(filePath, fileName)
    
    if os.path.exists((outfile)):
                logging.warn("File already downloaded at : " + outfile)
                return outfile
                
    else:        
#       ffmpeg -s:v 1920x1080 -r 25 -i input.yuv -vf scale=960:540 -c:v rawvideo -pix_fmt yuv420p out.yuv
        videosize_arg = str(orig_width)+"x"+str(orig_height)
        codec_arg = 'rawvideo'
        input_arg = video
        scale_arg = "scale="+str(target_width) +':' + str(target_height)
        command = ["ffmpeg", "-video_size", videosize_arg, "-i", input_arg, "-vf", scale_arg, "-codec:v", codec_arg, outfile]
        for it in command:
            print it, 
        print "\n"      
        p = Popen(command, env=ENV_DICT)
        p.communicate(input)
    return outfile
    
        
def convertToYUV(video, **kwargs):
    codec = kwargs.get('codec', None)
    width = kwargs.get('width', None)
    height = kwargs.get('height', None)
    
    if codec or width or height is None:
        try:
            codec,width,height= getLocalVideoInfo(video)
        except:
            logging.error("Could not retrieve details from video\n using generic defaults")
            codec = kwargs.get('codec', "codc")
            width = kwargs.get('width', "width")
            height = kwargs.get('height', "height")
  
    try:
        fileName = os.path.basename(video)
        filePath = os.path.dirname(video)
  
#         replace all spaces with and UNDERSCORE
        fileName = re.sub(r"\s+", '-', fileName)
#         remove sub all non-word characters and replACE WITH underscore
        fileName = re.sub(r"[\W]+", '_', fileName).lower()
        fileName = "_".join([codec,str(width),str(height),fileName])
        outfile = os.path.join(filePath, fileName + '.yuv') 
   
        
        if os.path.exists((outfile)):
                logging.warn("File already downloaded at : " + outfile)
                
        else:
            command = ["ffmpeg", "-i", video, outfile ]
            p = Popen(command, env=ENV_DICT)
            p.communicate(input)
        
        print "outfile: " + outfile
        return outfile
    
    except OSError as oe:
        logging.error("OS Error:", sys.exc_info())
        sys.stderr.write("OS Error: Probably couldn't find FFMPEG \nIs it in ENV_DICT[\"PATH\"] ?\n")
        sys.stderr.write(os.environ["PATH"]+"\n")
        traceback.print_exc()
    except:
        logging.error("Unexpected error:", sys.exc_info())
        traceback.print_exc()
        sys.exit(1)

def prepareFileName(filename):
    logging.info("Preparing file name")
    file_dir, base_file = os.path.split(filename)
    logging.info("Original file name: %s " , filename)
#     file_wo_ext = os.path.basename(base_file)o
#         print fileName
    new_filename = re.sub(r"\s+", '-', base_file)

    new_filename = re.sub(r"[^.\w]+", '_', new_filename).lower()
    new_filename = os.path.join(file_dir, new_filename)
    logging.info("New file name: %s " , new_filename)
    return new_filename


def downloadAndRenameVideo(video, video_download_folder, **kwargs):
    """
    Downloads a video using Youtube-dl and renames it to a conisintent filename
    """
    if not kwargs["quality"]:
        logging.warn("No Qualuty level specified, will use youtube-dl best quality")    
    quality = kwargs.get('quality',"best") #18 for youtube is h264, mp, 360p
    youtube_dl_opts = {
                       'outtmpl':video_download_folder + '/%(resolution)s-%(format_id)s-%(title)s-%(id)s.%(ext)s',
                       'format':quality
                       }
    with YoutubeDL(youtube_dl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(video, download=False)
            filename = ydl.prepare_filename(info_dict)
            logging.info("YOUTUBE_DL Downloaded file will be saved as: %s", filename)
            
            new_filename = prepareFileName(filename)
            print new_filename
            if os.path.exists((new_filename)):
                logging.warn("File already downloaded at : " + new_filename)
            else:
                logging.info("File now being downloaded")
                info_dict = ydl.extract_info(video, download=True)
                logging.info("Download Complete: now renaming file")
                os.rename(filename, new_filename)
                logging.info("Video file now at : " + new_filename) #check if file has already been downloaded
        except DownloadError as de:
            logging.error("YDL-Download Error")
           
            sys.exit(1)
        except:
            logging.error("YDL Error")
            traceback.print_exc()
            sys.exit(1)
             
        video = new_filename
    return video


def makeDownloadsFolder():
    home = expanduser("~")
    print home
    video_download_folder = os.path.join(home, "vEQ-benchmark", "Downloads")
    if not os.path.exists(video_download_folder):
        os.makedirs(video_download_folder)
    return video_download_folder


def tiny_ssim(testvideo_width, testvideo_height, test_yuv_file, reference_video_yuv):
    commandx = ["tiny_ssim", reference_video_yuv, test_yuv_file, str(testvideo_width) + "x" + str(testvideo_height)]
    for it in commandx:
        print it
    
    print " " #     http://blog.endpoint.com/2015/01/getting-realtime-output-using-python.html
    '''
    Calling Popen with universal_newlines=True because tiny_ssim 
    ouputs each line with ^M newline character - which maybe makes sense only
    on Windows or something, 
    In any case, this causes problems if not set
    '''
    p = Popen(commandx, env=ENV_DICT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
#     out, err = p.communicate(input) //communicate() is potentially memory intensive
    output_arr = []
    while True:
        output = p.stdout.readline()
        if output == '' and p.poll() is not None:
#             break
            print ""
        if output:
            output_arr.append(output)
            logging.info(output.strip())
    
    ssim_outfile = open("out_ssim.txt", "wb")
    pickle.dump(output_arr, ssim_outfile)
    ssim_arr = []
#         Frame 1849 | PSNR Y:60.957  U:67.682  V:67.326  All:62.262 | SSIM Y:0.99984 U:0.99984 V:0.99982 All:0.99984 (37.96369)
#         Frame 1850 | PSNR Y:60.920  U:67.682  V:67.326  All:62.228 | SSIM Y:0.99984 U:0.99984 V:0.99982 All:0.99984 (37.94860)
#     last_val = 'Total 1851 frames | PSNR Y:45.039  U:52.712  V:52.995  All:46.454 | SSIM Y:0.98834 U:0.99602 V:0.99642 All:0.99096 (20.43960)\n'
    last_val = output_arr[-1]
   
    for it in output_arr:
        ssim_arr.append(re.split(r"[^\d.]+", it))
    
    tiny_ssim_results = re.split(r"[^\d.]+", last_val)
   
    return tiny_ssim_results

def main(argv=None):
    logging.getLogger().setLevel(logging.INFO)
    parser = argparse.ArgumentParser(description="vEQ_ssim tool: A utilty tool for objective quality measurements")
    parser.add_argument("video" , metavar="VIDEO", help="A local file or URL(Youtube, Vimeo etc.) for the video to be benchmarked")
    parser.add_argument("-r", "--reference", metavar="reference video", dest="reference", help="A location or url for a video file (HD) to be used as a reference for the comparison")
    parser.add_argument("-f", "--format", metavar="format", dest="format", help="The format of the Youtube DL file being tested for the comparison")
    parser.add_argument("-l", "--databse-location", dest="db_loc", metavar ="location for database file or \'memory\'", help = "A absolute location for storing the database file ")
    
    args = parser.parse_args()    
    video = args.video
    test_format = args.format
    reference_video = args.reference
    
# ================================================   
#     DATABASE SETUP
# ==============================================
    vEQdb = DB.vEQ_database()
    db =vEQdb.getDB()
    cursor = db.cursor()
    cursor.execute("CREATE TABLE if NOT exists video_quality_info (%s);" % vEQdb.VIDEO_QUALITY_COLS) 
    
#================================================================================================   
#     DATABASE SETUP ENDS
#================================================================================================
    
    if not validURLMatch(video) and not (os.access(video, os.R_OK)):
        print('Error: %s file not readable' % video)
        logging.error('Error: %s file not readable' % video)
        sys.exit(1)
    
    if validURLMatch(video):
        ONLINE_VIDEO = True
        logging.debug("Found online video")
        
        if validYoutubeURLMatch(video):
            logging.debug("Found Youtube video")
        
        """
        try to download the video using youtube-dl
        and then get info about the downloaded file
        """
        video_download_folder = makeDownloadsFolder()
        video_url =  video
        video = downloadAndRenameVideo(video, video_download_folder, quality=test_format)
    
    else:
        LOCAL_VIDEO = True

#     should get here even if it was a Youtubeurl as the video file 
#      should have been downloaded from Youtube etc  
    if not validURLMatch(video) and (os.access(video, os.R_OK)):
        logging.debug("Found regular video")  
        codec, testvideo_width, testvideo_height = getLocalVideoInfo(video)
        
        test_yuv_file = convertToYUV(video, codec=codec, testvideo_width=testvideo_width, testvideo_height=testvideo_height)

    if ONLINE_VIDEO: #youtube
        # Now try to get the best quality video if an online, or a reference source file if local
        if not reference_video:
            logging.debug("Trying to get best quality video from remote server") 
            reference_video = downloadAndRenameVideo(video_url, video_download_folder, quality="bestvideo") 
            
            ref_codec,  ref_width, ref_height = getLocalVideoInfo(reference_video)
            logging.info("Format and size of best video available is: " + ref_codec +", " + str(ref_width) + "x" + str(ref_height))
            
            logging.debug("Converting Reference (best quality video) to YUV")
            reference_video_yuv = convertToYUV(reference_video)
            
            if (ref_width != testvideo_width) or (ref_height != testvideo_height ):
                logging.debug("Scaling best quality reference video from %sx%s to %sx%s", ref_width, ref_height, testvideo_width, testvideo_height )
                #but first check if an appropriate scaled down HD version already exists
                reference_video_yuv = scaledownYUV(reference_video_yuv,orig_width=ref_width, orig_height=ref_height, target_width=testvideo_width, target_height=testvideo_height)
            
    else:
        logging.debug("Trying to get best quality video from local server")
        if not reference_video:
            logging.error("No reference video found")
            sys.exit()
            
#         0.98834 

    TESTING = True
    
    if TESTING:
        ssim_in = open( "out_ssim.txt", "rb" )
        output_arr =  pickle.load(ssim_in)
        ssim_arr = [] 
        last_val = output_arr[-1]
        tiny_ssim_results = re.split(r"[^\d.]+", last_val) 
    else:
        tiny_ssim_results = tiny_ssim(testvideo_width, testvideo_height, test_yuv_file, reference_video_yuv)
    
    ypsnr = str(tiny_ssim_results[2])
    apsnr = str(tiny_ssim_results[5])
    yssim =  str(tiny_ssim_results[6])
    assim = str(tiny_ssim_results[7])
#     
#     "id INTEGER PRIMARY KEY,"
#                         "timestamp REAL, " 
#                         "video TEXT, "
#                         "url TEXT, "
#                         "reference_videoname TEXT"
#                         "metric1_ypsnr TEXT, "
#                         "metric2_apsnr TEXT, "
#                         "metric3_yssim TEXT, "
#                         "metric4_assim TEXT, "
#                         "metric5_other TEXT, "
#                         "metric6_other TEXT, " 
#                         "metric7_other TEXT, "
#                         "metric8_other TEXT, "
#                         "metric9_other TEXT, "
#                         "metric10_other TEXT, "
    
    timestamp =   datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
    values = [timestamp, video, video_url, reference_video ,ypsnr, apsnr, yssim, assim, 0,0,0,0,0,0 ] #15 vlues
    

    retcode = cursor.execute("INSERT INTO video_quality_info VALUES (null,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    db.commit()
    print retcode
    
#         reference_video = getSourceVideoInfo(source)
                    
if __name__ == '__main__':  
    TESTING = False
    if TESTING:
        vEQdb = DB.vEQ_database(":memory:")
        db =vEQdb.getDB()
        cursor = db.cursor()
        print vEQdb.VIDEO_QUALITY_COLS
        cursor.execute("CREATE TABLE if NOT exists video_quality_info (%s);" % vEQdb.VIDEO_QUALITY_COLS) 
        ssim_in = open( "out_ssim.txt", "rb" )
        output_arr =  pickle.load(ssim_in)
        ssim_arr = []
        #         Frame 1849 | PSNR Y:60.957  U:67.682  V:67.326  All:62.262 | SSIM Y:0.99984 U:0.99984 V:0.99982 All:0.99984 (37.96369)                
        #         Frame 1850 | PSNR Y:60.920  U:67.682  V:67.326  All:62.228 | SSIM Y:0.99984 U:0.99984 V:0.99982 All:0.99984 (37.94860)                
        last_val = 'Total 1851 frames | PSNR Y:45.039  U:52.712  V:52.995  All:46.454 | SSIM Y:0.98834 U:0.99602 V:0.99642 All:0.99096 (20.43960)\n'
        last_val = output_arr[-1]
        
        for it in output_arr:
            ssim_arr.append(re.split(r"[^\d.]+",it)) 
        
        psnrs = zip(*ssim_arr)[1] 
        print psnrs[0:-1][-1]
        import matplotlib.pyplot as plt
        #         
        #         plt.plot(psnrs[0:-1])
        # #         plt.ylim(0.8,1)
        #         plt.show()
        tiny_ssim_results =  re.split(r"[^\d.]+", last_val)
        
        print("AVG YPSNR: " + str(tiny_ssim_results[2]))
        print("AVG ALL PSNR: " + str(tiny_ssim_results[5]))
        print("AVG YSSIM: " + str(tiny_ssim_results[6]))
        print("AVG All SSIM: " + str(tiny_ssim_results[7]))
        
        timestamp =  st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
        values = [timestamp, "video", video_url, "reference_video" ,"ypsnr", "apsnr", "yssim", "assim", 0,0,0,0,0,0 ] #15 vlues
    
        cursor = db.cursor()    
        cursor.execute("INSERT INTO video_quality_info VALUES (null,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)

        sys.exit()
     
    else:
        main() 
  
    
    
    
    