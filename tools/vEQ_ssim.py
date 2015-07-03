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
from subprocess import Popen
import re

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

ENV_DICT["PATH"] = PATH_TO_FFMPEG + os.pathsep + PATH_TO_MEDIAINFO +  os.pathsep + ENV_DICT["PATH"] 

logging.getLogger().setLevel(logging.DEBUG)

def getLocalVideoInfo(video):
    '''
    Returns the codec, width and height of a video using MediaInfo
    '''
    try:
        '''
        if mediainfo isn't in the python environment path then this wont work.
        '''
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
        print fileName
        
        filePath = os.path.dirname(video)
        print filePath
#         replace all spaces with and UNDERSCORE
        fileName = re.sub(r"\s+", '-', fileName)
#         remove sub all non-word characters and replACE WITH underscore
        fileName = re.sub(r"[\W]+", '_', fileName).lower()
        fileName = "_".join([codec,str(width),str(height),fileName])
        outfile = os.path.join(filePath, fileName + '.yuv') 
        print outfile
        command = ["ffmpeg", "-i", video, outfile ]
        p = Popen(command, env=ENV_DICT)
        p.communicate(input)
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
    file_dir, base_file = os.path.split(filename)
    print "file: " + base_file
#     file_wo_ext = os.path.basename(base_file)
#         print fileName
    new_filename = re.sub(r"\s+", '-', base_file)
    print new_filename
    new_filename = re.sub(r"[^.\w]+", '_', new_filename).lower()
    print new_filename
    new_filename = os.path.join(file_dir, new_filename)
    return new_filename

def main(argv=None):
    logging.getLogger().setLevel(logging.INFO)
    parser = argparse.ArgumentParser(description="vEQ_ssim tool: A utilty tool for objective quality measurements")
    parser.add_argument("video" , metavar="VIDEO", help="A local file or URL(Youtube, Vimeo etc.) for the video to be benchmarked")
    parser.add_argument("-s", "--source", metavar="source", dest="source", help="A location or url for a video file (HD) to be used as a reference for the comparison")
    
    args = parser.parse_args()    
    video = args.video
    source = args.source
    
    if not validURLMatch(video) and not (os.access(video, os.R_OK)):
        print('Error: %s file not readable' % video)
        logging.error('Error: %s file not readable' % video)
        sys.exit(1)
    
    if validURLMatch(video):
        logging.debug("Found online video")
        
        if validYoutubeURLMatch(video):
            logging.debug("Found Youtube video")
            """
            try to download the video using youtube-dl
             and then get info about the downloaded file
            """
        from os.path import expanduser
        home = expanduser("~")
        print home
        video_downloads = os.path.join(home,"vEQ-benchmark","Downloads")
        
        
        if not os.path.exists(video_downloads): 
            os.makedirs(video_downloads)
            
        print video_downloads
        
        youtube_dl_opts = {
                         'outtmpl' : video_downloads+ '/%(resolution)s-%(format_id)s-%(title)s-%(id)s.%(ext)s',
                    }
        
        with YoutubeDL(youtube_dl_opts) as ydl:
            try: 
#                 check if file has already been downloaded   
                info_dict =  ydl.extract_info(video, download=False)
        
                filename = ydl.prepare_filename(info_dict)
                print filename
                
                new_filename = prepareFileName(filename)
                print new_filename
                
                if os.path.exists((new_filename)):
                    logging.warn("File already downloaded at : " + new_filename)
                
                else:
                    logging.info("File now being downloaded")
                    info_dict = ydl.extract_info(video, download=True)
                
                    logging.info("Download Complete: now renaming file") 
                    os.rename(filename, new_filename)
                    logging.info("Video file now at : " + new_filename)
      
            except:
                logging.error("YDL Error")
                traceback.print_exc()
                sys.exit(1)
            
            video =  new_filename
    
    if not validURLMatch(video) and (os.access(video, os.R_OK)):
        logging.debug("Found regular video")  
        codec, width, height = getLocalVideoInfo(video)
        test_yuv_file = convertToYUV(video, codec=codec, width=width, height=height)
      
        
#         reference_video = getSourceVideoInfo(source)
                
   
    
if __name__ == '__main__':  
    main() 
#     get video from arguments;

#     get height and width using mediainfo;
#     convert to yuv;
     
#     get best source from commandline or use youtube-dl; 
#     check height and width;
#     convert to ssim;
     
#     if height and width different from sample;
#     rescale;
#     
#     run vqmt and/or tiny_ssim
#     
#     save scores into db, save plots if needed
    
    
    
    